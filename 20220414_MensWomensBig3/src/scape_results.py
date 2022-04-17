#!/usr/bin/env python3.7
# -*- coding: utf-8 -*-
"""
Created on Fri Apr 15 08:16:47 2022

@author: reideej1

:DESCRIPTION: Scrape data for men's football, basketball and baseball as
    compared to women's volleyball, basketball and softball for all D1 schools
    from 2006-07 to 2021-22

:REQUIRES: See Package Import section for required packages
   
:TODO:
"""
 
#==============================================================================
# Package Import
#==============================================================================
import datetime
import os  
import pandas as pd
import pathlib
import requests
import time

from bs4 import BeautifulSoup
from requests.packages.urllib3.util.retry import Retry

#==============================================================================
# Reference Variable Declaration
#==============================================================================

#==============================================================================
# Function Definitions
#==============================================================================
def soupifyURL(url):
    '''
    Purpose: Turns a specified URL into BeautifulSoup formatted HTML 

    Inputs
    ------
        url : string
            Link to the designated website to be scraped
    
    Outputs
    -------
        soup : html
            BeautifulSoup formatted HTML data stored as a complex tree of 
            Python objects
    '''
    session = requests.Session()
    retry = Retry(connect=3, backoff_factor=0.5)
    adapter = requests.adapters.HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    
    r = session.get(url, verify = False)
    #r = requests.get(url)
    soup = BeautifulSoup(r.content,'html.parser')   
    return soup

def renameSchool(df, name_var):
    '''
    Purpose: Rename a school/university to a standard name as specified in 
        the file `school_abbreviations.csv`

    Inputs
    ------
        df : Pandas Dataframe
            DataFrame containing a school-name variable for which the names
            need to be standardized
        name_var : string
            Name of the variable which is to be renamed/standardized
    
    Outputs
    -------
        list(row)[0] : string
            Standardized version of the school's name based on the first value
            in the row in the file `school_abbreviations.csv`
    '''  
    # read in school name information
    df_school_names = pd.read_csv('data/school_abbreviations_and_pictures.csv')
     
    # convert the dataframe to a dictionary such that the keys are the
    #   optional spelling of each school and the value is the standardized
    #   name of the school
    dict_school_names = {}
    
    for index, row in df_school_names.iterrows():
        # isolate the alternative name columns
        names = row[[x for x in row.index if 'Name' in x]]
        # convert the row to a list that doesn't include NaN values
        list_names = [x for x in names.values.tolist() if str(x) != 'nan']
        # add the nickname to the team names as an alternative name
        nickname = row['Nickname']
        list_names_nicknames = list_names.copy()
        for name in list_names:
            list_names_nicknames.append(name + ' ' + nickname)
        # extract the standardized team name
        name_standardized = row['Team']
        # add the standardized name
        list_names_nicknames.append(name_standardized)
        # add the nickname to the standardized name
        list_names_nicknames.append(name_standardized + ' ' + nickname)
        # for every alternative spelling of the team, set the value to be
        #   the standardized name
        for name_alternate in list_names_nicknames:
            dict_school_names[name_alternate] = name_standardized
            
    # df[name_var] = df[name_var].apply(
    #         lambda x: dict_school_names[x] if str(x) != 'nan' else '')
    df[name_var] = df[name_var].apply(
            lambda x: rename_school_helper(x, dict_school_names))
        
    return df   

def rename_school_helper(name_school, dict_school_names):
    try:
        if str(name_school) != 'nan':
            return dict_school_names[name_school]
        else:
            return ''
    except:
        print(f'School not found in school abbreviations .csv file: {name_school} ')
        return name_school

def scrapeCfbSchoolLinks():
    '''
    Purpose: Scrapes the names and links to all school pages on CFB reference
        [https://www.sports-reference.com/cfb/schools/]
        
    Inputs
    ------
    None.
    
    Outputs
    -------
        df_teams : Pandas DataFrame
            Contains a table of school information (name / link) for current schools
    '''   
    # process all available years
    year_end = datetime.datetime.now().year
    
    # Scrape data for all available years
    url = 'https://www.sports-reference.com/cfb/schools/'
    soup = soupifyURL(url)
    
    # Retrieve the HTML of the combine table
    table = soup.find('table', {'id':'schools'})
    
    # Extract school URLs from the html data
    url_schools = [[td.a['href'] if td.find('a') else ''
             for td in row.find_all('td')] for row in table.find_all('tr')]
    
    # Remove the first two rows as they apply to headers
    url_schools = url_schools[2:]
    url_schools = [x[0] if x != [] else [] for x in url_schools]
    
    # Convert the table to a dataframe
    df_schools = pd.read_html(str(table), flavor = None, header = [1])[0]
    
    # Add the URLs to the table
    df_schools['URL'] = url_schools
    
    # Reduce the table to only current schools    
    if not all(df_schools['To'].str.contains(str(year_end))):
        df_schools = df_schools[df_schools['To'] == str(year_end - 1)]
    else:
        df_schools = df_schools[df_schools['To'] == str(year_end)]
        
    # Remove unnecessary tables
    df_schools = df_schools[['School', 'URL', 'From', 'To']]
            
    return df_schools

def scrapeCbbSchoolsAllYears():
    '''
    Purpose: Scrape school data (i.e. teams, wins, losses) by sports-reference.com
        - also includes coach names and links to coach pages
        
    Inputs
    ------
        N/A
    
    Outputs
    -------
        df_history : Pandas DataFrame
            Contains team information for all schools currently playing
            football dating back to the default year
    '''  
    # retrieve the links to each school
    df_schools = scrapeCfbSchoolLinks()
    
    # replace 'cfb' with 'cbb
    df_schools.URL = [x.replace('cfb', 'cbb') for x in list(df_schools.URL)]
    
    # create a dataframe for storing coach information for all years
    df_history = pd.DataFrame()
    
    # iterate over each school and scrape their history table
    for index, row in df_schools.iterrows():
        school = row['School']
        url = row['URL']
        
        if 'middle-tennessee-state' in url:
            url = '/cbb/schools/middle-tennessee'
        
        # Scrape data for the specific team
        url = 'https://www.sports-reference.com' + url
        soup = soupifyURL(url)
    
        # Retrieve the HTML of the combine table
        table = soup.find('table', {'class':'sortable stats_table'})        
        
        # Extract URLs from the html data
        url_coaches = [[td.a['href'] if td.find('a') else ''
                 for td in row.find_all('td')] for row in table.find_all('tr')]
        
        # Isolate the coach URLs
        url_coaches = [x[11] if x != [] else [] for x in url_coaches]
        
        # Remove the first row as that is the header row
        url_coaches = url_coaches[1:]
        
        # Make the full link to coach URL
        url_coaches = ['https://www.sports-reference.com' + x if x != [] else [] for x in url_coaches]
        
        # Convert the table to a dataframe
        df_school = pd.read_html(str(table), flavor = None, header = [0])[0]
        
        # Add the URLs to the table
        df_school['url_coach'] = url_coaches
        
        # if the header is in row 0, handle it
        if df_school.iloc[0,0] == 'Rk':
            columns = ['Rk', 'Season', 'Conf', 'Overall_W', 'Overall_L', 'Overall_Pct', 
                       'Conf_W', 'Conf_L', 'Conf_Pct', 'SRS', 'SOS', 'PPG', 'Opp_PPG',
                       'AP_Pre', 'AP_High', 'AP_Final', 'NCAA_Tourny', 'NCAA_Seed',
                       'Coach(es)', 'url_coach']
            df_school.columns = columns
        
        # Remove header rows from the table
        df_school = df_school[df_school['Season'] != 'Season']
        
        # Add School name to table
        df_school['Rk'] = school
        df_school = df_school.rename(columns = {'Rk':'School'})
        
        # Append school data to history table
        if len(df_history) == 0:
            df_history = df_school.copy()
        else:
            df_history = df_history.append(df_school)
            
        print('Done with: ' + school)
        
        time.sleep(1)
        
    # print('*** DONE WITH ALL SCRAPING ***')
    ts = datetime.date.fromtimestamp(time.time())
    df_history.to_csv(rf'data\records_mbb_{ts}.csv', index = False)    
    
    return df_history
    
def scrapeCfbResultsAllYears(year = 1970):
    '''
    Purpose: Scrape week-by-week results for all schools from sports-reference.com
        - also includes coach names and links to coach pages
        
    Inputs
    ------
        year : int
            The starting year for evaluating team data (default: 1970)
    
    Outputs
    -------
        df_history : Pandas DataFrame
            Contains team information for all schools currently playing
            football dating back to the default year
    '''  
    # retrieve the links to each school
    df_schools = scrapeCfbSchoolLinks()
    
    # # create a dataframe for storing all records for all schools
    df_history = pd.DataFrame()
    
    # process all available years
    year_end = datetime.datetime.now().year
    
    # iterate over each school and scrape their history table
    for index, row in df_schools.iterrows():
        school = row['School']
        url = row['URL']
        
        print(f'*** STARTING SCRAPING: {school} ***')
        
        # create a dataframe for storing all records for the specific school
        df_history_school = pd.DataFrame()
        
        for scrape_year in range(year, year_end+1):
            # Scrape data for the specific team
            soup = soupifyURL(f'https://www.sports-reference.com{url}{scrape_year}-schedule.html')
        
            # Test for a year with no data (happens in new year w/o combine)
            if 'Page Not Found' in str(soup):
                print('ERROR: Data not found for: ' + school)
                continue
        
            # Retrieve the HTML of the combine table
            table = soup.find('table', {'class':'sortable stats_table'})        
            
            # Extract URLs from the html data
            url_games = [[td.a['href'] if td.find('a') else ''
                     for td in row.find_all('td')] for row in table.find_all('tr')]
            # Remove the first row as that is the header row
            url_games = url_games[1:]
            
            # Isolate the year URLs
            url_boxscores = []
            for line in url_games:
                url_boxscores.append(line[0])
            
            # Make the full link to coach URL
            url_boxscores = ['https://www.sports-reference.com' + x for x in url_boxscores]
            
            # Convert the table to a dataframe
            df_school = pd.read_html(str(table), flavor = None, header = [0])[0]
            
            # find Home/Away and Result columns
            col_names = [x for x in df_school.columns if 'Unnamed' in x]
            
            # Fix Home/Away Column
            df_school[col_names[0]] = df_school[col_names[0]].apply(lambda x: 'Home' if pd.isna(x) else 
                                                                   ('Neutral' if x == 'N' else 'Away'))
            df_school = df_school.rename(columns = {col_names[0]:'Home_Away'})
            
            # Fix Result column
            df_school = df_school.rename(columns = {col_names[1]:'Result'})
            
            # Rename other columns
            df_school = df_school.rename(columns = {'W':'Cum_W', 'L':'Cum_L'})
            
            # Create Team and Opp Ranking columns
            df_school['Rank'] = df_school['School'].apply(lambda x: x.split(')\xa0')[0].replace('(','') if x[0] == '(' else '')
            df_school['School'] = df_school['School'].apply(lambda x: x.split(')\xa0')[1] if x[0] == '(' in x else x)
            df_school['Rank_Opp'] = df_school['Opponent'].apply(lambda x: x.split(')\xa0')[0].replace('(','') if x[0] == '(' in x else '')
            df_school['Opponent'] = df_school['Opponent'].apply(lambda x: x.split(')\xa0')[1] if x[0] == '(' in x else x)
            
            # Reorder columns
            num_cols = [3, 6]
            if 'Time' in df_school.columns:
                num_cols = [4, 7]
            rank_col = df_school.pop('Rank')
            df_school.insert(num_cols[0], 'Rank', rank_col)
            rank_opp_col = df_school.pop('Rank_Opp')
            df_school.insert(num_cols[1], 'Rank_Opp', rank_opp_col)
            
            # Add the URLs to the table
            df_school['url_boxscore'] = url_boxscores
            
            # # Append school data to all schools history table
            # if len(df_history) == 0:
            #     df_history = df_school.copy()
            # else:
            #     df_history = df_history.append(df_school)
            
            # Append school data to individual school's history table
            if len(df_history_school) == 0:
                df_history_school = df_school.copy()
            else:
                df_history_school = df_history_school.append(df_school)
                
            print(f' -- Done with: {scrape_year}')
            
            time.sleep(1)
        
        print(f'*** FINISHED SCRAPING: {school} ***')            
        # Append school data to individual school's history table
        if len(df_history) == 0:
            df_history = df_history_school.copy()
        else:
            df_history = df_history.append(df_history_school)
        # ts = datetime.date.fromtimestamp(time.time())
        # df_history_school.to_csv(rf'data\records_{school}_{scrape_year}.csv', index = False)
        
    # print('*** DONE WITH ALL SCRAPING ***')
    ts = datetime.date.fromtimestamp(time.time())
    df_history.to_csv(rf'data\records_cfb_{ts}.csv', index = False)    
    
    return df_history

def scrapeWarrenNolan(sport):
    '''
    Purpose: Scrape historical RPI information for a given sport/year combo
        from warrenolan.com
        
    Inputs
    ------
        sport : string
            Sports abbreviation...options are:
                - baseball    (Men's Baseball)
                - basketball  (Men's Basketball)
                - basketballw (Women's Basketball)
    
    Outputs
    -------
        NONE
    '''  
    if sport not in ['baseball', 'basketball', 'basketballw']:
        print('Error: Incorrect sport abbreviation used!')
        return
    else:
        url_prefix  = 'https://www.warrennolan.com/'
        url_sport   = sport + '/'
        url_postfix = '/rpi-live'
        
    # create a renaming dictionary
    dict_sport = {'baseball':'MBA', 'basketball':'MBB', 'basketballw':'WBB'}

    # Scrape data for all available years
    # for year in list(range(2020,2023)):
    for year in list(range(2022,2023)):
        # Setup url for given sport/year combo
        url = url_prefix + url_sport + str(year) + url_postfix 
        
        # create a season variable based on the school year (fall to spring)
        season = f'{str(year-1)}-{str(year)[2:]}'
        
        # Scrape data for the specific sport/year combo
        soup = soupifyURL(url)
    
        # Test for a year with no data (happens in new year w/o combine)
        if ('Page Not Found' in str(soup)) or ('404 Not Found' in str(soup)):
            print(f'ERROR: Data not found for: {year}')
            continue
    
        # Create a dataframe for the given season
        df_year = pd.DataFrame()
        
        # Retrieve the HTML from the website
        try:
            div_table = soup.find('div', {'class':'datatable'})
            table_rpi = div_table.find('table')
        except:
            div_table = soup.find('div', {'class':'full-width-box-x'})
            table_rpi = div_table.find('table')
        
        # Convert the html to a dataframe
        df_year = pd.read_html(str(table_rpi), flavor = None, header = [0])[0]
        
        # remove header rows
        df_year = df_year[df_year['RPI'] != 'RPI']
        df_year = df_year[~df_year['RPI'].str.contains('freestar')]
        
        # Split win/loss columns
        df_year['W'] = df_year['Record'].apply(lambda x: x.split('-')[0])
        df_year['L'] = df_year['Record'].apply(lambda x: x.split('-')[1])
        
        # Add season and sport to table            
        df_year['Season'] = season
        df_year['Sport'] = dict_sport[sport]
        
        # rename RPI to rank
        df_year = df_year.rename(columns = {'RPI':'Rank'})
        
        # Reorder and isolate columns of interest
        df_year = df_year[['Sport', 'Season', 'Rank', 'Team', 'W', 'L']]
        
        # Separate team name from conference/record
        list_conferences = ['ACC', 'America East', 'American Athletic', 
                            'Atlantic 10', 'Atlantic Sun', 'ASUN', 'Big 12', 
                            'Big East', 'Big Sky', 'Big South', 'Big Ten', 
                            'Big West', 'Colonial Athletic', 'Conference USA',
                            'Horizon League', 'Ivy League', 'MAAC', 'MEAC',
                            'Mid-American', 'Missouri Valley', 'Mountain West',
                            'Northeast', 'Ohio Valley', 'Pac-12', 'Patriot League',
                            'SEC', 'Southern', 'Southland', 'Sun Belt', 'SWAC', 
                            'The Summit League',
                            'West Coast', 'Western Athletic']
        for conf in list_conferences:
            df_year['Team'] = df_year['Team'].apply(
                lambda x: x.replace(conf +  ' (', ' ('))
        df_year['Team'] = df_year['Team'].apply(lambda x: x.split('  ')[0])
          
        # save individual year to disk
        df_year.to_csv(f'data/csv/{dict_sport[sport]}/{dict_sport[sport]}_{season}.csv', 
                       index = False)         
        
        print(f"Done scraping {sport} data for {season}")   
        
        time.sleep(1)
        
    return

def scrapeSoftballRPI(): 
    '''
    Purpose: Scrape historical RPI information for softball since 2020
        
    Inputs
    ------
        NONE
    
    Outputs
    -------
        NONE
    '''  
    url_prefix  = 'https://d1softball.com/nitty-gritty/'
    sport = 'WSB'

    # Scrape data for all available years
    # for year in list(range(2021,2023)):
    for year in list(range(2022,2023)):
        # Setup url for given sport/year combo
        url = url_prefix + str(year)
        
        # create a season variable based on the school year (fall to spring)
        season = f'{str(year-1)}-{str(year)[2:]}'
        
        # Scrape data for the specific sport/year combo
        soup = soupifyURL(url)
    
        # Test for a year with no data (happens in new year w/o combine)
        if ('Page Not Found' in str(soup)) or ('404 Not Found' in str(soup)):
            print(f'ERROR: Data not found for: {year}')
            continue
    
        # Create a dataframe for the given season
        df_year = pd.DataFrame()
        
        # Retrieve the HTML from the website
        table_rpi = soup.find_all('table')
        
        # iterate over each section of the table
        for table_rpi_section in table_rpi:
        
            # Convert the html to a dataframe
            df_subgroup = pd.read_html(str(table_rpi_section), flavor = None, header = [1])[0]
            
            # remove header rows
            df_subgroup = df_subgroup[df_subgroup['RPI'] != 'RPI']
            
            # Split win/loss columns
            df_subgroup['W'] = df_subgroup['Record'].apply(lambda x: x.split('-')[0])
            df_subgroup['L'] = df_subgroup['Record'].apply(lambda x: x.split('-')[1])
            
            # Add season and sport to table            
            df_subgroup['Season'] = season
            df_subgroup['Sport']  = sport
            
            # rename RPI to rank
            df_subgroup = df_subgroup.rename(columns = {'RPI':'Rank'})
            
            # Reorder and isolate columns of interest
            df_subgroup = df_subgroup[['Sport', 'Season', 'Rank', 'Team', 'W', 'L']]
            
            # Separate team name from conference/record
            list_conferences = ['ACC', 'America East', 'American Athletic', 
                                'Atlantic 10', 'Atlantic Sun', 'ASUN', 'Big 12', 
                                'Big East', 'Big Sky', 'Big South', 'Big Ten', 
                                'Big West', 'Colonial Athletic', 'Conference USA',
                                'Horizon League', 'Ivy League', 'MAAC', 'MEAC',
                                'Mid-American', 'Missouri Valley', 'Mountain West',
                                'Northeast', 'Ohio Valley', 'Pac-12', 'Patriot League',
                                'SEC', 'Southern', 'Southland', 'Sun Belt', 'SWAC', 
                                'The Summit League',
                                'West Coast', 'Western Athletic']
            for conf in list_conferences:
                df_subgroup['Team'] = df_subgroup['Team'].apply(
                    lambda x: x.replace(conf +  ' (', ' ('))
            df_subgroup['Team'] = df_subgroup['Team'].apply(lambda x: x.split('  ')[0])
            
            # add subgroup to year table
            if len(df_year) == 0:
                df_year = df_subgroup.copy()
            else:
                df_year = df_year.append(df_subgroup)
          
        # save individual year to disk
        df_year.to_csv(f'data/csv/{sport}/{sport}_{season}.csv', 
                       index = False)         
        
        print(f"Done scraping {sport} data for {season}")   
        
        time.sleep(1)
        
    return
    
def scrapeSportsResults(sport):
    '''
    Purpose: Scrape historical RPI information for a given sport/year combo
        from espn.com or the ncaa RPI archives
        
    Inputs
    ------
        sport : string
            Sports abbreviation...options are:
                - MBSB (Men's Baseball)
                - MBB (Men's Basketball)
                - MFB (Men's Football)
                - WBB (Women's Basketball)
                - WVB (Women's Volleyball)
                - WSB (Women's Softball)
    
    Outputs
    -------
        df_all_years : Pandas DataFrame
            contains team win/loss and RPI rankings for all available years
                for the given sport
    '''  
    if sport == 'MFB':
        url_prefix  = 'https://www.espn.com/college-football/fpi/_/season/'
        url_sport   = ''
        url_postfix = ''
    elif sport not in ['MBB', 'MBA', 'WBB', 'WSB', 'WVB']:
        print('Error: Incorrect sport abbreviation used!')
        return
    else:
        url_prefix  = 'https://web1.ncaa.org/app_data/weeklyrpi/'
        url_sport   = sport
        url_postfix = 'rpi1.html'
        
    # create dataframe for storing results for all available years
    df_all_years = pd.DataFrame()
    
    # Scrape data for all available years
    for year in list(range(2006,2023)):
        # Setup url for given sport/year combo
        url = url_prefix + str(year) + url_sport + url_postfix 
        
        # create a season variable based on the school year (fall to spring)
        if sport in ['MFB', 'WVB']:
            season = f'{str(year)}-{str(year+1)[2:]}'
        else:
            season = f'{str(year-1)}-{str(year)[2:]}'
        
        # Scrape data for the specific sport/year combo
        soup = soupifyURL(url)
    
        # Test for a year with no data (happens in new year w/o combine)
        if ('Page Not Found' in str(soup)) or ('404 Not Found' in str(soup)):
            print(f'ERROR: Data not found for: {year}')
            continue
    
        # Process Football data from ESPN
        df_year = pd.DataFrame()
        if sport == 'MFB':
            # Retrieve the team table
            table = soup.find('table', {
                'class':'Table Table--align-right Table--fixed Table--fixed-left'})  
            df_teams = pd.read_html(str(table), flavor = None, header = [0])[0]
            # Retrieve the rankings table
            table = soup.find('table', {
                'class':'Table Table--align-right'})
            df_ranks = pd.read_html(str(table), flavor = None, header = [1])[0]
            # Merge tables together
            df_year = pd.concat([df_teams, df_ranks], axis = 1)
            # Split win/loss columns
            df_year['W'] = df_year['W-L'].apply(lambda x: x.split('-')[0])
            df_year['L'] = df_year['W-L'].apply(lambda x: x.split('-')[1])    
            # Add season and sport to table           
            df_year['Season'] = season
            df_year['Sport'] = sport 
            # Rename variables
            df_year = df_year.rename(columns = {'RK':'Rank'})
            # Reorder and isolate columns of interest
            df_year = df_year[['Sport', 'Season', 'Rank', 'Team', 'W', 'L']]   
        # Process other sport data from NCAA
        else:
            # Retrieve the team table
            table_rpi = soup.find_all('table')[1]
            df_year = pd.read_html(str(table_rpi), flavor = None, header = [0])[0]
            if len(df_year.columns) == 9:
                df_year.columns = ['Rank', 'Rank_Prev', 'Team', 'Conf', 'W-L',
                                   'Road', 'Neut', 'Home', 'Non-Div-I']
            else:
                df_year.columns = ['Rank', 'Team', 'Conf', 'W-L',
                                   'Road', 'Neut', 'Home', 'Non-Div-I']                    
            # Split win/loss columns
            df_year['W'] = df_year['W-L'].apply(lambda x: x.split('-')[0])
            df_year['L'] = df_year['W-L'].apply(lambda x: x.split('-')[1])
            # Add season and sport to table            
            df_year['Season'] = season
            df_year['Sport'] = sport
            # Reorder and isolate columns of interest
            df_year = df_year[['Sport', 'Season', 'Rank', 'Team', 'W', 'L']]
          
        # save individual year to disk
        df_year.to_csv(f'data/csv/{sport}/{sport}_{season}.csv', index = False)         
        
        print(f"Done scraping {sport} data for {season}")

        # add year table to all-years table
        df_all_years = df_all_years.append(df_year)      
        
        time.sleep(1)
        
    # save data for all years to disk
    df_all_years.to_csv(f'data/csv/{sport}/{sport}_all_years.csv', index = False)
        
    return df_all_years

#==============================================================================
# Working Code
#==============================================================================

# # Set the project working directory
path_dir = pathlib.Path(r'C:\Users\reideej1\Projects\a_Personal\collegeSportsMenWomen')
os.chdir(path_dir)

# # Scrape NCAA Men's Baseball
# df_mba = scrapeSportsResults('MBA')
scrapeWarrenNolan('baseball')

# # Scrape NCAA Men's Basketball
# # df_mbb = scrapeCbbSchoolsAllYears()
# df_mbb = scrapeSportsResults('MBB')
# scrapeWarrenNolan('basketball')

# # Scrape NCAA Men's Football
# # df_cfb = scrapeCfbResultsAllYears(2000)
# df_mfb = scrapeSportsResults('MFB')

# # Scrape NCAA Women's Basketball
# df_wbb = scrapeSportsResults('WBB')
# scrapeWarrenNolan('basketballw')

# # Scrape NCAA Women's Softball
# df_wsb = scrapeSportsResults('WSB')
scrapeSoftballRPI()

# # Scrape NCAA Women's Volleyball
# df_wvb = scrapeSportsResults('WVB')