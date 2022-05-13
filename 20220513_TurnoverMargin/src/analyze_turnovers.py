#!/usr/bin/env python3.7
# -*- coding: utf-8 -*-
"""
Created on Mon Apr 25 10:00:41 2022

@author: reideej1

:DESCRIPTION: Determine trends in turnovers over the last 10 years of college
    football (2012 to 2021). What does an average team look like in terms 
    of turnovers? How far away from average is Nebraska?

:REQUIRES: See Package Import section
   
:TODO: NONE
"""
 
#==============================================================================
# Package Import
#==============================================================================
import glob
import os  
import pandas as pd
import pathlib

#==============================================================================
# Reference Variable Declaration
#==============================================================================

#==============================================================================
# Function Definitions
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

def loadTurnoverData():
    '''
    Purpose: Read in the turnover data for each year 
        (as reported on https://stats.ncaa.org/rankings/)

    Inputs   
    ------
        NONE
            
    Outputs
    -------
        df_all_years : Pandas DataFrame
            Contains turnover data for all FBS teams from 2012-2021
    '''
    # identify file paths for all turnover data
    list_files = list(glob.iglob(r'data\*.xlsx'))
    
    # load turnover data for each year
    df_all_years = pd.DataFrame()
    for fpath in list_files:
        # Load data
        df_year = pd.read_excel(fpath)
        year = int(fpath.split(' ')[-1].replace('.xlsx',''))
        df_year['Year'] = year
        if year == 2012:
            df_year = df_year.rename(
                columns = {'Team':'School', 'Fum Rec':'Opp_Fum', 'Int':'Opp_Int',
                           'Turnovers Gained':'Opp_TO', 'Fum Lost':'Fum', 'Int.1':'Int', 
                           'Turnovers Lost':'TO'})
            df_year['Margin'] = df_year['Opp_TO'] - df_year['TO']
        else:
            df_year = df_year.rename(
                columns = {'Team':'School', 'Fum Rec':'Opp_Fum', 'Opp Int':'Opp_Int',
                           'Turn Gain':'Opp_TO', 'Fum Lost':'Fum', 'Turn Lost':'TO'})
            df_year['Margin/G'] = df_year['Margin']/df_year['G']    
            
        # Retrieve team conference from team name
        df_year['Conf']   = df_year['School'].apply(lambda x: x.split('(')[1].replace(")",""))
        df_year['School'] = df_year['School'].apply(lambda x: x.split(' (')[0])

        # Rename teams
        df_year = renameSchool(df_year, 'School')
    
        if year == 2012:
            # fill in win/loss records for 2012
            df_results = pd.read_csv(r'C:\Users\reideej1\Projects\a_Personal\cfbAnalysis\data\raw\Team History\team_history_fb_1936_to_2020.csv')
            df_results = df_results[['School', 'Year', 'Overall_W', 'Overall_L']]
            df_results = renameSchool(df_results, 'School')
            df_year = pd.merge(df_year, df_results, how = 'left',
                                on = ['Year', 'School'])
            df_year = df_year.rename(columns = {'Overall_W':'W',
                                                  'Overall_L':'L'})
            df_year = df_year[['Year', 'School', 'Conf', 'Rank', 'G', 
                                 'W', 'L', 'Opp_Fum', 'Opp_Int', 'Opp_TO', 
                                 'Fum', 'Int', 'TO', 'Margin', 'Margin/G']]
            # update Idaho's record
            df_year['W'] = df_year['W'].fillna(1)
            df_year['L'] = df_year['L'].fillna(11)
            df_year.to_csv(r'data/2012.csv', index = False)
    
        else:
            # create win/loss columns
            df_year['W'] = df_year['W-L'].apply(lambda x: int(x.split('-')[0]))
            df_year['L'] = df_year['W-L'].apply(lambda x: int(x.split('-')[1]))
            
            df_year = df_year[['Year', 'School', 'Conf', 'Rank', 'G', 
                                 'W', 'L', 'Opp_Fum', 'Opp_Int', 'Opp_TO', 
                                 'Fum', 'Int', 'TO', 'Margin', 'Margin/G']]
            df_year.to_csv(rf'data/Nebraska_{year}.csv', index = False)
            
        if len(df_all_years) == 0:
            df_all_years = df_year.copy()
        else:
            df_all_years = df_all_years.append(df_year)

    return df_all_years

#==============================================================================
# Working Code
#==============================================================================

# Set the project working directory
path_dir = pathlib.Path(
    r'C:\Users\reideej1\Projects\a_Personal\huskerProjects\20220513_TurnoverMargin')
os.chdir(path_dir)

# ingest turnvoer data for all available years
df_turnovers = loadTurnoverData()