#!/usr/bin/env python3.7
# -*- coding: utf-8 -*-
"""
Created on Sat Apr 16 16:43:52 2022

@author: reideej1

:DESCRIPTION: Analyze data for men's football, basketball and baseball as
    compared to women's volleyball, basketball and softball for all D1 schools
    from 2006-07 to 2021-22

:REQUIRES: See Package Import section for required packages
   
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
            in the row in the file `school_abbreviations_and_pictures.csv`
    '''  
    # read in school name information
    df_school_names = pd.read_csv('references/school_abbreviations_and_pictures.csv', 
                                  encoding = 'latin-1')
     
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
    
def rollUpData():
    '''
    Purpose: Import and combine win/loss records for every year for every sport
        on file in the local '.csv' folders

    Inputs   
    ------
        NONE
            
    Outputs
    -------
        NONE
    '''
    # create a list of file paths for every sport
    list_sports = glob.glob(r'data/csv/*')
    list_sports = [os.path.split(x)[1] for x in list_sports]
    
    # iterate over every sport
    for sport in list_sports:
        # create dataframe for storing data for all available sports/years
        df_all = pd.DataFrame()
        
        # create a list of file paths for every .csv file stored locally
        list_files = glob.glob(rf'data/csv/{sport}/*.csv')
        list_files = [x for x in list_files if '_all_years' not in x]
        
        # import all available files
        for file in list_files:
            # read in the file for the specific sport/year combo
            df_file = pd.read_csv(file)
            
            # add the sport/year combo dataframe to the dataframe for all years
            if len(df_all) == 0:
                df_all = df_file.copy()
            else:
                df_all = df_all.append(df_file)
                
        # standardize school names
        df_all = renameSchool(df_all, 'Team')
                
        # save file to disk
        df_all.to_csv(rf'data/csv/{sport}/{sport}_all_years.csv', index = False)
        
        print(f'Done with {sport}')
        
    return

def mergeAllData():
    '''
    Purpose: Combine win/loss records for every sport/year combination
        on file in the local '.csv' folder

    Inputs   
    ------
        NONE
            
    Outputs
    -------
        df_all : Pandas DataFrame
            Contains win/loss record for all available year/sport combinations
    '''
    # create DataFrame for storing all sports/all years
    df_all = pd.DataFrame()
    
    # create a list of file paths for every sport
    list_sports = ['MFB', 'MBA', 'MBB', 'WBB', 'WSB', 'WVB']
    # list_sports = glob.glob(r'data/csv/*')
    # list_sports = [os.path.split(x)[1] for x in list_sports]
    
    # iterate over every sport
    for sport in list_sports:
        
        # import data for sport
        df_sport = pd.read_csv(rf'data/csv/{sport}/{sport}_all_years.csv')
        
        # rename sport variables
        try:
            df_sport = df_sport.drop(columns = {'Sport', 'Conf'})
        except:
            df_sport = df_sport.drop(columns = {'Sport'})
        df_sport = df_sport.rename(columns = {'Rank':f'{sport}_Rank',
                                              'W':f'{sport}_W',
                                              'L':f'{sport}_L'})
        
        # merge sports (left joins starting with football to isolate to FBS teams)
        if len(df_all) == 0:
            df_sport = df_sport[['Season', 'Team', 'MFB_Rank', 'MFB_W', 'MFB_L']]
            df_all = df_sport.copy()
        else:
            df_all = pd.merge(df_all, df_sport, how = 'left', on = ['Season', 'Team'])
    
    # sort data by season/team
    df_all = df_all.sort_values(by = ['Team', 'Season'])
    
    # cast to numeric to ensure data types are all ints
    df_all['MBB_W'] = pd.to_numeric(df_all['MBB_W'])
    
    # save to disk
    df_all.to_csv(r'data/results_all_years.csv', index = False)
    
    return df_all

#==============================================================================
# Working Code
#==============================================================================

# Set the project working directory
path_dir = pathlib.Path(
    r'C:\Users\reideej1\Projects\a_Personal\huskerProjects\20220414_MensWomensBig3')
os.chdir(path_dir)

# Roll up all local data
rollUpData()

# Merge data across all years/sports
df = mergeAllData()

# Load data from .csv on file
df = pd.read_csv(r'data/results_all_years.csv')

# Focus only on school/years that have all 6 sports (drop rows with NaNs)
df = df.dropna()

# Engineer new variables
df['MBA_Win_Pct'] = df['MBA_W'] / (df['MBA_W'] + df['MBA_L'])
df['MBB_Win_Pct'] = df['MBB_W'] / (df['MBB_W'] + df['MBB_L'])
df['MFB_Win_Pct'] = df['MFB_W'] / (df['MFB_W'] + df['MFB_L'])
df['WBB_Win_Pct'] = df['WBB_W'] / (df['WBB_W'] + df['WBB_L'])
df['WSB_Win_Pct'] = df['WSB_W'] / (df['WSB_W'] + df['WSB_L'])
df['WVB_Win_Pct'] = df['WVB_W'] / (df['WVB_W'] + df['WVB_L'])
df['W_Men']   = df['MBA_W'] + df['MBB_W'] + df['MFB_W']
df['L_Men']   = df['MBA_L'] + df['MBB_L'] + df['MFB_L']
df['W_Women'] = df['WBB_W'] + df['WSB_W'] + df['WVB_W']
df['L_Women'] = df['WBB_L'] + df['WSB_L'] + df['WVB_L']
df['win_pct_men']       = df['W_Men'] / (df['W_Men'] + df['L_Men'])
df['win_pct_women']     = df['W_Women'] / (df['W_Women'] + df['L_Women'])
df['win_pct_avg_men']   = df['MBA_Win_Pct']*(1/3) + df['MBB_Win_Pct']*(1/3) + df['MFB_Win_Pct']*(1/3)
df['win_pct_avg_women'] = df['WBB_Win_Pct']*(1/3) + df['WSB_Win_Pct']*(1/3) + df['WVB_Win_Pct']*(1/3)
df['rpi_avg_men']       = df['MBA_Rank']*(1/3) + df['MBB_Rank']*(1/3) + df['MFB_Rank']*(1/3)
df['rpi_avg_women']     = df['WBB_Rank']*(1/3) + df['WSB_Rank']*(1/3) + df['WVB_Rank']*(1/3)
df['Diff_Win_Pct']      = df['win_pct_men'] - df['win_pct_women']
df['Diff_Win_Pct_Avg']  = df['win_pct_avg_men'] - df['win_pct_avg_women']
df['Diff_RPI_Avg']      = df['rpi_avg_men'] - df['rpi_avg_women']
df.columns = [x.lower() for x in list(df.columns)]

# Load conference affiliation for each team
df_teams = pd.read_csv(r'references/school_abbreviations_and_pictures.csv',
                       encoding = 'latin-1')
df_teams = df_teams[['Team', 'ConferenceAbbrev']]
df_teams = df_teams.rename(columns = {'Team':'team', 'ConferenceAbbrev':'conf'})

# Add conference information to each table
df = pd.merge(df, df_teams, how = 'left', on = 'team')
df.reset_index(drop = True)

# Rename columns
df = df.rename(columns = {'mfb_w':'w_mfb', 'mba_w':'w_mba', 'mbb_w':'w_mbb',
                          'mfb_l':'l_mfb', 'mba_l':'l_mba', 'mbb_l':'l_mbb',
                          'wbb_w':'w_wbb', 'wsb_w':'w_wsb', 'wvb_w':'w_wvb',
                          'wbb_l':'l_wbb', 'wsb_l':'l_wsb', 'wvb_l':'l_wvb',
                          'mfb_rank':'fpi_mfb', 'mba_rank':'rpi_mba', 'mbb_rank':'rpi_mbb',
                          'wbb_rank':'rpi_wbb', 'wsb_rank':'rpi_wsb', 'wvb_rank':'rpi_wvb',
                          })

# Reorder columns
df = df[['season', 'team', 'conf', 
         'win_pct_men', 'win_pct_avg_men', 
         'w_men', 'w_mba', 'w_mbb', 'w_mfb',
         'l_men', 'l_mba', 'l_mbb', 'l_mfb',
         'win_pct_women', 'win_pct_avg_women',
         'w_women', 'w_wbb', 'w_wsb', 'w_wvb', 
         'l_women', 'l_wbb', 'l_wsb', 'l_wvb',
         'diff_win_pct', 'diff_win_pct_avg',
         'rpi_avg_men', 'rpi_mba', 'rpi_mbb', 'fpi_mfb', 
         'rpi_avg_women', 'rpi_wbb', 'rpi_wsb', 'rpi_wvb', 
         'diff_rpi_avg']]

# Round the decimal places of variables (2 places for win pct., 0 for RPI)
df = round(df,2)
df['rpi_avg_men']   = round(df['rpi_avg_men'], 0)
df['rpi_avg_women'] = round(df['rpi_avg_women'], 0)
df['diff_rpi_avg']  = round(df['diff_rpi_avg'], 0)

# Rank each variable
df['rank_win_pct_men']        = df['win_pct_men'].rank(ascending = False, method = 'min')
df['rank_win_pct_women']      = df['win_pct_women'].rank(ascending = False, method = 'min')
df['rank_win_pct_avg_men']    = df['win_pct_avg_men'].rank(ascending = False, method = 'min')
df['rank_win_pct_avg_women']  = df['win_pct_avg_women'].rank(ascending = False, method = 'min')
df['rank_diff_win_pct']       = df['diff_win_pct'].rank(ascending = False, method = 'min')
df['rank_diff_win_pct_avg']   = df['diff_win_pct_avg'].rank(ascending = False, method = 'min')
df['rank_diff_rpi_avg']       = df['diff_rpi_avg'].rank(ascending = False, method = 'min')
# absolute values
df['rank_diff_win_pct_abs']       = abs(df['diff_win_pct']).rank(ascending = True, method = 'min')
df['rank_diff_win_pct_avg_abs']   = abs(df['diff_win_pct_avg']).rank(ascending = True, method = 'min')
df['rank_diff_rpi_avg_abs']       = abs(df['diff_rpi_avg']).rank(ascending = True, method = 'min')

df.to_csv('data/teams_2006_to_2022.csv', index = False)

# # Subset the data into a new DataFrame
# df_final = df[['season', 'team', 
#                'win_pct_men', 'win_pct_women', 
#                'win_pct_avg_men', 'win_pct_avg_women', 
#                'rpi_avg_women', 'rpi_avg_men', 
#                'diff_win_pct', 'diff_win_pct_avg', 'diff_rpi_avg']]

# # Reorder columns
# df_print = df_final[['season', 'team', 'conf', 'conf_abbrev', 
#              'win_pct_men', 'win_pct_men_rank', 
#              'win_pct_women', 'win_pct_women_rank', 
#              'win_pct_avg_men', 'win_pct_avg_men_rank', 
#              'win_pct_avg_women', 'win_pct_avg_women_rank',
#              'rpi_avg_men', 'rpi_avg_women', 
#              'diff_win_pct', 'diff_win_pct_rank', 'diff_win_pct_abs_rank', 
#              'diff_win_pct_avg', 'diff_win_pct_avg_rank', 'diff_win_pct_avg_abs_rank', 
#              'diff_rpi_avg', 'diff_rpi_avg_rank', 'diff_rpi_avg_abs_rank']]

# Subset the data into a new DataFrame that's easier to understand
df_print = df[['season', 'team', 'win_pct_men', 'win_pct_women', 
               'diff_win_pct', 'win_pct_avg_men', 'win_pct_avg_women', 
               'rank_win_pct_men', 'rank_win_pct_women', 
               'rank_win_pct_avg_men', 'rank_win_pct_avg_women',
               'rank_diff_win_pct', 'rank_diff_win_pct_abs', 
               'diff_win_pct_avg', 'rank_diff_win_pct_avg', 'rank_diff_win_pct_avg_abs']]
df_print = df_print.assign(diff_win_pct_abs = abs(df_print['diff_win_pct']))
df_print = df_print.assign(diff_win_pct_avg_abs = abs(df_print['diff_win_pct_avg']))
df_print = df_print[['season', 'team', 'win_pct_men', 'rank_win_pct_men', 
                     'win_pct_women', 'rank_win_pct_women', 
                     'diff_win_pct_abs', 'rank_diff_win_pct_abs', 
                     'win_pct_avg_men', 'rank_win_pct_avg_men', 
                     'win_pct_avg_women', 'rank_win_pct_avg_women',
                     'diff_win_pct_avg_abs', 'rank_diff_win_pct_avg_abs']]
df_print.to_csv(r'data/teams_2006_to_2022_summary.csv', index = False)