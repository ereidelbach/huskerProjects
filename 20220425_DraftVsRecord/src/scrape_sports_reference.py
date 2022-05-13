#!/usr/bin/env python3.7
# -*- coding: utf-8 -*-
"""
Created on Fri Mar  1 11:58:43 2019

@author: ejreidelbach

:DESCRIPTION: Scrapes player data from ProFootball-Reference and Sports-Reference
    'https://www.sports-reference.com/cfb/years/2018-passing.html'
    'https://www.pro-football-reference.com/years/2018/passing.htm'

:REQUIRES:
   
:TODO:
"""
 
#==============================================================================
# Package Import
#==============================================================================
import datetime
import html5lib
import os  
import pandas as pd
import pathlib
import requests
import tqdm
import time

from bs4 import BeautifulSoup
from requests.packages.urllib3.util.retry import Retry
from string import digits

#==============================================================================
# Reference Variable Declaration
#==============================================================================
list_categories_nfl = ['passing', 'rushing', 'receiving', 'scrimmage',
                       'defense', 'kicking', 'returns', 'scoring']
list_categories_cfb = ['passing', 'rushing', 'receiving', 'kicking',
                       'punting', 'scoring']

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
    
    r = session.get(url)
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
    df_school_names = pd.read_csv('data/raw/school_abbreviations_and_pictures.csv')
     
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
 
def scrapeCfbSchoolsAllYears(year = 1970):
    '''
    Purpose: Scrape school data (i.e. teams, wins, losses) by sports-reference.com
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
    
    # create a dataframe for storing coach information for all years
    df_history = pd.DataFrame()
    
    # iterate over each school and scrape their history table
    for index, row in df_schools.iterrows():
        school = row['School']
        url = row['URL']
        
        # Scrape data for the specific team
        url = 'https://www.sports-reference.com' + url
        soup = soupifyURL(url)
        
        # Test for a year with no data (happens in new year w/o combine)
        if 'Page Not Found' in str(soup):
            print('ERROR: Data not found for: ' + school)
            continue
    
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
            columns = ['Rk', 'Year', 'Conf', 'Overall_W', 'Overall_L', 'Overall_T', 
                       'Overall_Pct', 'Conf_W', 'Conf_L', 'Conf_T', 'Conf_Pct',
                       'SRS', 'SOS', 'AP_Pre', 'AP_High', 'AP_Post', 'Coach(es)',
                       'Bowl', 'Notes', 'url_coach']
            df_school.columns = columns
        
        # Remove header rows from the table
        df_school = df_school[df_school['Year'] != 'Year']
        
        # Reduce the table to only current schools   
        df_school['Year'] = pd.to_numeric(df_school['Year'], errors = 'coerce')
        df_school = df_school[df_school['Year'] >= year]
        
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
    # df_history = pd.DataFrame()
    
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
        ts = datetime.date.fromtimestamp(time.time())
        df_history_school.to_csv(rf'data\raw\Team History\records_{school}_{scrape_year}.csv', index = False)
        
    # print('*** DONE WITH ALL SCRAPING ***')
    # ts = datetime.date.fromtimestamp(time.time())
    # df_history.to_csv(rf'data\raw\Team History\records_all_schools_{ts}.csv', index = False)    
    
    # return df_history
    return

def scrapeNflDraft(year = ''):
    '''
    Purpose: Scrape the NFL draft results for the specified years from sports-reference.com
        
    Inputs
    ------
        year : int
            The year to retrieve NFL draft info for (default: 2000 to current year)
    
    Outputs
    -------
        df_draft : Pandas DataFrame
            Contains draft information for all specified years
    '''      
    if year == '':
        year_start = 2000
        year_end = datetime.datetime.now().year
    else:
        year_start = year
        year_end = year
        
    # create a dataframe for storing all records for the specific school
    df_draft = pd.DataFrame()
    
    for scrape_year in range(year_start, year_end):
        # Scrape data for the specific year
        soup = soupifyURL(f'https://www.pro-football-reference.com/years/{scrape_year}/draft.htm')
    
        # Test for a year with no data (happens in new year w/o combine)
        if 'Page Not Found' in str(soup):
            print('ERROR: Draft data not found for: ' + scrape_year)
            continue
    
        # Retrieve the HTML of the combine table
        table = soup.find('table', {'class':'sortable stats_table'})        
        
        # Convert HTMl to table
        df_year = pd.read_html(str(table), flavor = None, header = [0])[0]
        
        # Make the first row the column headers
        df_year.columns = df_year.iloc[0]
        
        # Subset the table to columns of interest
        df_year = df_year[['Rnd', 'Pick', 'Tm', 'Player', 'Pos', 'Age', 'To',
                           'AP1', 'PB', 'St', 'CarAV', 'DrAV', 'G', 'College/Univ']]
        
        # Rename columns
        df_year.columns = ['Draft_Rnd', 'Draft_Pick_Overall', 'Draft_Team', 
                           'Player', 'Pos', 'Age', 'Last_Year_NFL', 
                           'All_Pro', 'Pro_Bowl', 'Starts', 'AV_Career',
                           'AV_Drafted_Team', 'Games', 'School']
        
        # Remove rows with header information
        df_year = df_year[df_year['Draft_Rnd'] != 'Rnd']
        
        # Convert rows to numeric values (if applicable)
        df_year = df_year.apply(pd.to_numeric, errors = 'ignore')
            
        # Standardize School Names
        df_year = renameSchool(df_year, 'School')
        
        # add year column to table
        df_year['Year'] = scrape_year
        
        # reorder columns
        df_year = df_year[['Year', 'Draft_Rnd', 'Draft_Pick_Overall', 'Player', 
                   'Draft_Team', 'School', 'Pos', 'Age', 'Last_Year_NFL', 
                   'All_Pro', 'Pro_Bowl', 'Starts', 'Games', 'AV_Career',
                   'AV_Drafted_Team']]
        
            
        print(f' -- Done with: {scrape_year}')
        
        time.sleep(1)
        
        df_year.to_csv(rf'data\raw\NFL Draft\nfl_draft_{scrape_year}.csv', index = False)
        
        if len(df_draft) == 0:
            df_draft = df_year.copy()
        else:
            df_draft = df_draft.append(df_year)
        
    print('*** DONE WITH ALL SCRAPING ***')
    df_draft.to_csv(rf'data\raw\NFL Draft\nfl_draft_all_{year_start}_to_{year_end}.csv', index = False)
    
    return df_draft

#=============================================================================
# Working Code
#==============================================================================

# # Set the project working directory
# path_dir = pathlib.Path('/home/ejreidelbach/Projects/cfbAnalysis/')
# os.chdir(path_dir)

# #--- NFL
# for category in list_categories_nfl:
#     # Scrape Data for all years
#     df_nfl = scrapeNflPlayersAllYears(category)
    
#     # Write files to disk
#     df_nfl.to_csv(('data/raw/SportsReference/nfl_' + category + '.csv'), 
#                   index = False)

# #--- CFB
# for category in list_categories_cfb:
#     # Scrape Data for all years
#     df_cfb = scrapeCfbPlayersAllYears(category)
    
#     # Write files to disk
#     df_cfb.to_csv(('data/raw/SportsReference/cfb_' + category + '.csv'), 
#                   index = False)

    # Scrape Data for specific years
    #df = scrapeCombineSpecificYear(2019)    
    
# df = scrapeCbbSchoolsAllYears()