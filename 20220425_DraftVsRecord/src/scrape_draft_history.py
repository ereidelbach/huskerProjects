#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr  2 14:26:57 2018

@author: ejreidelbach

:DESCRIPTION:
    - This script will scrape the site: http://www.drafthistory.com/ in order 
    to obtain a complete listing of all players drafted in NFL history
    
:REQUIRES:
   
:TODO:
"""
 
#==============================================================================
# Package Import
#==============================================================================
import datetime
import json
import os
import requests
import operator
import pandas as pd
import time

from bs4 import BeautifulSoup
from requests.packages.urllib3.util.retry import Retry

#==============================================================================
# Reference Variable Declaration
#==============================================================================
positionList = ['T','G','C']
positionAbbrList = ['OT','OG','OC']

dict_nfl_teams = {'49ers':'San Francisco 49ers',
            'Bears':'Chicago Bears',
            'Bengals':'Cincinnati Bengals',
            'Bills':'Buffalo Bills',
            'Broncos':'Denver Broncos',
            'Browns':'Cleveland Browns',
            'Buccaneers':'Tampa Bay Buccaneers',
            'Cardinals':'Arizona Cardinals',
            'Chargers':'Los Angeles Chargers',
            'Chiefs':'Kansas City Chiefs',
            'Colts':'Indianapolis Colts',
            'Cowboys':'Dallas Cowboys',
            'Dolphins':'Miami Dolphins',
            'Eagles':'Philadelphia Eagles',
            'Falcons':'Atlanta Falcons',
            'Giants':'New York Giants',
            'Jaguars':'Jacksonville Jaguars',
            'Jets':'New York Jets',
            'Lions':'Detroit Lions',
            'Oilers':'Tennessee Titans',
            'Packers':'Green Bay Packers',
            'Panthers':'Carolina Panthers',
            'Patriots':'New England Patriots',
            'Raiders':'Oakland Raiders',
            'Rams':'Los Angeles Rams',
            'Ravens':'Baltimore Ravens',
            'Redskins':'Washington Redskins',
            'Team':'Washington Commodores',
            'Saints':'New Orleans Saints',
            'Seahawks':'Seattle Seahawks',
            'Steelers':'Pittsburgh Steelers',
            'Texans':'Houston Texans',
            'Titans':'Tennessee Titans',
            'Vikings':'Minnesota Vikings',
            'redskins':'Washington Redskins',
        }

#==============================================================================
# Function Definitions / Reference Variable Declaration
#==============================================================================
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
    df_school_names = pd.read_csv('references/school_abbreviations_and_pictures.csv')
     
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

def scrapeDraftHistory():
    '''
    Purpose: Scrapes all players drafted for all available years from
        drafthistory.com
        
    Inputs
    ------
    None.
    
    Outputs
    -------
        df_draft : Pandas DataFrame
            Contains all recorded draft picks from all available years
    '''   
    # Set the link that we will be scraping
    url = r'http://www.drafthistory.com/index.php/years/'
    
    # Iterate through every subsequent page in the position group
    soup = soupifyURL(url)
    table = soup.find('table')
    
    url_list = []
    for row in table.find_all('td'):
        temp_dict = {}
        if (len(row.text) > 1):
            temp_dict['year'] = row.text
            temp_dict['url'] = row.find('a')['href']
            url_list.append(temp_dict)
            
    # sort the url_list by year
    url_list.sort(key=operator.itemgetter('year'))
            
    df_draft = pd.DataFrame()
    # Extract data for all available drafts
    for url in url_list:
        # retrieve the html data and convert it to BS4 format
        soup = soupifyURL(url['url'])
        
        # Retrieve the HTML of the draft table
        table = soup.find('table')
        
        # Convert the table to a dataframe
        df_year = pd.read_html(str(table), flavor = None, header = [1])[0]
        
        # drop any players not in a round (i.e. Sam Mills, 1981)
        df_year = df_year[df_year['Round'] != 0]
            
        # Change the names of all teams to reflect the format used by NFL.com
        #   and fill in missing round values
        list_teams = []
        list_rounds = []
        draft_round = 0
        for index, row in df_year.iterrows():
            # handle team names
            if row['Team'] in dict_nfl_teams.keys():
                list_teams.append(dict_nfl_teams[row['Team']])
            else:
                list_teams.append(row['Team'])
                
            # handle draft round
            if not pd.isna(row['Round']):
                draft_round = row['Round']
            list_rounds.append(draft_round)
                
        df_year['Team'] = list_teams
        df_year['Round'] = list_rounds
        
        # add year to table
        df_year['Year'] = url['year']
        
        # reorder table variables
        df_year.columns = [x.lower() for x in list(df_year.columns)]
        df_year = df_year[['year', 'round', 'pick', 'player', 'name', 'team', 
                           'position', 'college']]
        
        # standardize College team names
        df_year = renameSchool(df_year, 'college')
        
        # add year to table for all years
        if len(df_draft) == 0:
            df_draft = df_year.copy()
        else:
            df_draft = df_draft.append(df_year)
                
        print('Done with: ' + url['year'])
        
    # print('*** DONE WITH ALL SCRAPING ***')
    ts = datetime.date.fromtimestamp(time.time())
        
    # Write the historic list to a .csv file    
    df_draft.to_csv(f'data/historic_draft_data_{ts}.csv', index=False)

#==============================================================================
# Working Code
#==============================================================================

# Set the project working directory
os.chdir(r'C:\Users\reideej1\Projects\a_Personal\huskerProjects\20220425_DraftVsRecord')

# Scrape Draft History
scrapeDraftHistory()