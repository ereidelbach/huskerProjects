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
import matplotlib.pyplot as plt
import math
import os  
import pandas as pd
import pathlib
from matplotlib.offsetbox import OffsetImage, AnnotationBbox

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
    df_school_names = pd.read_csv(r'references/school_abbreviations_and_pictures.csv',
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

def importTurnoverFiles():
    list_files = list(glob.iglob(r'data\*.csv'))
    df_turnovers = pd.DataFrame()
    for x in list_files:
        df_turnovers = df_turnovers.append(pd.read_csv(x))
    return df_turnovers

def plotStatsWinPct():
    # Set font and background colour
    # plt.rcParams.update({'font.family':'Avenir'})
    bgcol = '#fafafa'

    # Create initial plot
    fig, ax = plt.subplots(figsize=(6, 4), dpi=1200)
    ax.scatter(df['Margin'], df['Win_Pct'], s = 10, alpha = 0.5)
    fig.set_facecolor(bgcol)
    ax.set_facecolor(bgcol)

    # Change plot spines
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    ax.spines['left'].set_color('#ccc8c8')
    ax.spines['bottom'].set_color('#ccc8c8')

    # Change ticks
    plt.tick_params(axis='x', labelsize=12, color='#ccc8c8')
    plt.tick_params(axis='y', labelsize=12, color='#ccc8c8')

    # Plot badges
    def getImage(path):
        return OffsetImage(plt.imread(path), zoom=.3, alpha = 1)

    for index, row in df.iterrows():
        ab = AnnotationBbox(getImage(row['Logo']), (
            row['Margin'], row['Win_Pct']), frameon=False)
        if row['School'] == 'Nebraska':
            ax.add_artist(ab)
        
    # Ensure X-Axis are whole numbers
    def round_down(m, n):
        return m // n * n
    def round_up(n):
        return n + (5 - n) % 5
    min_xaxis = round_down(math.floor(df['Margin'].min()),5)
    max_xaxis = round_up(math.ceil(df['Margin'].max()))
    # new_xaxis = range(min_xaxis, max_xaxis+5, 5)
    # ax.set_xticks(list(new_xaxis))

    # Set Y-Axis to traditional height values (i.e. 6'1" etc)
    min_yaxis = math.floor(df['Win_Pct'].min())
    max_yaxis = math.ceil(df['Win_Pct'].max())
    new_yaxis = range(min_yaxis, max_yaxis+1)
    new_yaxis = list(range(0, 10, 1))
    new_yaxis = [x/10 for x in new_yaxis]
                      
    # ax.set_yticks(list(new_yaxis))
    # yaxis_labels = [str(x) for x in new_yaxis]
    # yaxis_labels = [str(math.floor(int(y)/12)) + '-' + str(int(y)%12) for y in yaxis_labels]
    # ax.set_yticklabels(yaxis_labels)

    # Add average lines
    plt.hlines(df['Win_Pct'].median(), 
               min_xaxis, 
               max_xaxis, 
               color='#c2c1c0')
    plt.vlines(df['Margin'].median(), 
               min_yaxis, 
               max_yaxis, 
               color='#c2c1c0')
         
    fig.text(.15,.98,'Turnovers in FBS 2012-2021',size=20)
    fig.text(.15,.93,'Winning Pct. vs. Turnover Margin', size=12)

    # Set Axis Labels
    ax.set_xlabel('Tunover Margin.')
    ax.set_ylabel('Win Pct.')

    # Add Made by to bottom of image
    fig.text(.68, .02, 'Created by @Stewmanji', size=8, color='#c2c1c0')

    ## Save plot
    plt.savefig(r'images/plots/turnover_stats_win_pct.png', dpi=1200, bbox_inches = "tight")
    plt.savefig(r'images/plots/turnover_stats_win_pct.pdf', format = 'pdf', bbox_inches = "tight")

def plotStatsMargin():
    # Set font and background colour
    # plt.rcParams.update({'font.family':'Avenir'})
    bgcol = '#fafafa'

    # Create initial plot
    fig, ax = plt.subplots(figsize=(6, 4), dpi=1200)
    ax.scatter(df['TO'], df['Opp_TO'], s = 10, alpha = 0.5)
    fig.set_facecolor(bgcol)
    ax.set_facecolor(bgcol)

    # Change plot spines
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    ax.spines['left'].set_color('#ccc8c8')
    ax.spines['bottom'].set_color('#ccc8c8')

    # Change ticks
    plt.tick_params(axis='x', labelsize=12, color='#ccc8c8')
    plt.tick_params(axis='y', labelsize=12, color='#ccc8c8')

    # Plot badges
    def getImage(path):
        return OffsetImage(plt.imread(path), zoom=.3, alpha = 1)

    for index, row in df.iterrows():
        ab = AnnotationBbox(getImage(row['Logo']), (
            row['TO'], row['Opp_TO']), frameon=False)
        if row['School'] == 'Nebraska':
            ax.add_artist(ab)
        
    # Ensure X-Axis are whole numbers
    def round_down(m, n):
        return m // n * n
    def round_up(n):
        return n + (5 - n) % 5
    min_xaxis = round_down(math.floor(df['TO'].min()),5)
    max_xaxis = round_up(math.ceil(df['TO'].max()))
    # new_xaxis = range(min_xaxis, max_xaxis+5, 5)
    # ax.set_xticks(list(new_xaxis))

    # Set Y-Axis to traditional height values (i.e. 6'1" etc)
    min_yaxis = math.floor(df['Opp_TO'].min())
    max_yaxis = math.ceil(df['Opp_TO'].max())
    new_yaxis = range(min_yaxis, max_yaxis+1)
    new_yaxis = list(range(0, 10, 1))
    new_yaxis = [x/10 for x in new_yaxis]
                      
    # ax.set_yticks(list(new_yaxis))
    # yaxis_labels = [str(x) for x in new_yaxis]
    # yaxis_labels = [str(math.floor(int(y)/12)) + '-' + str(int(y)%12) for y in yaxis_labels]
    # ax.set_yticklabels(yaxis_labels)

    # Add average lines
    plt.hlines(df['TO'].median(), 
               min_xaxis, 
               max_xaxis, 
               color='#c2c1c0')
    plt.vlines(df['Opp_TO'].median(), 
               min_yaxis, 
               max_yaxis, 
               color='#c2c1c0')
         
    fig.text(.15,.98,'Turnovers in FBS 2012-2021',size=20)
    fig.text(.15,.93,'Turnovers Gained vs. Turnovers Lost', size=12)

    # Set Axis Labels
    ax.set_xlabel('Turnovers')
    ax.set_ylabel('Opponent Turnovers')

    # Add Made by to bottom of image
    fig.text(.68, .02, 'Created by @Stewmanji', size=8, color='#c2c1c0')

    ## Save plot
    plt.savefig(r'images/plots/turnover_stats_margin.png', dpi=1200, bbox_inches = "tight")
    plt.savefig(r'images/plots/turnover_stats_margin.pdf', format = 'pdf', bbox_inches = "tight")

#==============================================================================
# Working Code
#==============================================================================

# Set the project working directory
path_dir = pathlib.Path(r'huskerProjects\20220513_TurnoverMargin')
os.chdir(path_dir)

# ingest turnvoer data for all available years
df_turnovers = loadTurnoverData()

df_turnovers = importTurnoverFiles()
df_turnovers['Win_Pct'] = df_turnovers['W']/df_turnovers['G']
df_turnovers['Margin'] = df_turnovers['Opp_TO'] - df_turnovers['TO']
df = df_turnovers[['Year', 'School', 'Conf', 'Rank', 'G', 'W', 'L', 'Win_Pct', 
                   'Opp_Fum', 'Opp_Int', 'Opp_TO', 'Fum', 'Int', 'TO', 
                   'Margin/G', 'Margin']].copy()
# Add Logos to table
list_image_paths = []
for school in df['School']:
    list_image_paths.append(rf'images/logos_school_square/{school}.png')
df['Logo'] = list_image_paths

# plot turnover stats
plotStatsWinPct()
plotStatsMargin()

# what is the avg margin of each 64th placed team
df64 = df[df['Rank'] == 64]