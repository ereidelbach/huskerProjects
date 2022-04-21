#!/usr/bin/env python3.7
# -*- coding: utf-8 -*-
"""
Created on Sat Apr 16 16:43:52 2022

@author: reideej1

:DESCRIPTION: Analyze height/weight of position groups across all 2022
    Big Ten Football rosters.
    
    Data sourced from official team rosters on April 21, 2022

:REQUIRES: See Package Import section for required packages
   
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

def processRawRosters():
    '''
    Purpose: Read in the latest Big Ten Rosters, clean up the data, and 
        create new variables (as required)

    Inputs   
    ------
        NONE
            
    Outputs
    -------
        df : Pandas DataFrame
            Contains final, cleaned, engineered rosters across all Big Ten Football teams
    '''
    # Load latest rosters
    df = pd.read_csv(r'data/2022_Big_Ten_Rosters.csv')
    
    # clean up years
    list_years = df.YEAR
    list_years = list_years.replace('R-So.', 'So.')
    list_years = list_years.replace('R-Jr.', 'Jr.')
    list_years = list_years.replace('R-Sr.', 'Sr.')
    list_years = list_years.replace('RS Fr.', 'R-Fr.')
    list_years = list_years.replace('5th', 'Sr.')
    list_years = list_years.replace('6th', 'Sr.')
    list_years.value_counts()
    df.YEAR = list_years
    
    # clean up positions
    list_positions = df['POS.']
    list_positions = list_positions.replace('CB', 'DB')
    list_positions = list_positions.replace('DE', 'DL')
    list_positions = list_positions.replace('S', 'DB')
    list_positions = list_positions.replace('DT', 'DL')
    list_positions = list_positions.replace('OLB', 'LB')
    list_positions = list_positions.replace('ILB', 'LB')
    list_positions = list_positions.replace('SAF', 'DB')
    list_positions = list_positions.replace('SN', 'LS')
    list_positions = list_positions.replace('NT', 'DL')
    list_positions = list_positions.replace('ATH', 'WR')
    list_positions = list_positions.replace('OT', 'OL')
    list_positions = list_positions.replace('WB', 'WR')
    list_positions = list_positions.replace('OG', 'OL')
    list_positions = list_positions.replace('RB/S', 'RB')
    list_positions = list_positions.replace('C', 'OL')
    list_positions = list_positions.replace('OL/DL', 'OL')
    list_positions = list_positions.replace('TE/FB', 'TE')
    list_positions = list_positions.replace('TE/WR', 'TE')
    list_positions = list_positions.replace('WR/RS', 'WR')
    list_positions = list_positions.replace('DE/lB', 'DL')
    list_positions = list_positions.replace('LB/S', 'LB')
    list_positions = list_positions.replace('TE/K', 'TE')
    list_positions = list_positions.replace('LB/DE', 'LB')
    list_positions = list_positions.replace('DE/LB', 'DL')
    list_positions = list_positions.replace('PK', 'K')
    list_positions = list_positions.replace('K/P', 'K')
    list_positions.value_counts()
    df['Pos_Std'] = list_positions
    
    
    # Generate new height variable in inches
    list_height = df['HT.']
    df['height_inches'] = [int(x.split('-')[0])*12 + int(x.split('-')[1]) for x in list_height]
    
    # Rename variables
    df.columns = ['School', '#', 'Name', 'Pos', 'Height', 'Weight', 'Class',
       'Hometown', 'High_School', 'Prev_School', 'Pos_Std', 'Height_Inches']
    
    # Reorder variables
    df = df[['School', '#', 'Name', 'Pos', 'Pos_Std', 'Height', 
             'Height_Inches', 'Weight', 'Class']]
    
    # Rename teams
    df = renameSchool(df, 'School')
    
    return df

def computePositionStats(df, path_dir):
    '''
    Purpose: Compute median/mean height/weight for each team's position groups
        and for the conference as a whole

    Inputs   
    ------
        df : Pandas DataFrame
            Contains the rosers of every Big Ten team
        path_dir : pathlib Path
            path to project root directory
            
    Outputs
    -------
        df_stats : Pandas DataFrame
            Height/Weight stats by position group for each Big Ten Team and Conference
    '''
    # calculate height mean by position group
    list_height_mean = df.groupby(['School', 'Pos_Std'])['Height_Inches'].mean()
    list_height_mean = list_height_mean.reset_index(drop = False)
    list_height_mean = list_height_mean.rename(columns = {'Height_Inches':
                                                          'Height_Inches_Mean'})
    
    # calculate height median by position group
    list_height_median = df.groupby(['School', 'Pos_Std'])['Height_Inches'].median()
    list_height_median = list_height_median.reset_index(drop = False)
    list_height_median = list_height_median.rename(columns = {'Height_Inches':
                                                              'Height_Inches_Median'})
    
    # calculate weight mean by position group
    list_weight_mean = df.groupby(['School', 'Pos_Std'])['Weight'].mean()
    list_weight_mean = list_weight_mean.reset_index(drop = False)
    list_weight_mean = list_weight_mean.rename(columns = {'Weight':
                                                          'Weight_Mean'})
    
    # calculate weight median by position group
    list_weight_median = df.groupby(['School', 'Pos_Std'])['Weight'].median()
    list_weight_median = list_weight_median.reset_index(drop = False)
    list_weight_median = list_weight_median.rename(columns = {'Weight':
                                                              'Weight_Median'})
        
    # Join data together
    df_stats = pd.merge(list_height_mean, list_height_median, how = 'left', 
                        on = ['School', 'Pos_Std'])
    df_stats = pd.merge(df_stats, list_weight_mean, how = 'left', 
                        on = ['School', 'Pos_Std'])
    df_stats = pd.merge(df_stats, list_weight_median, how = 'left', 
                        on = ['School', 'Pos_Std'])
    df_stats = df_stats.rename(columns = {'Pos_Std':'Pos'})
    
    # compute mean/median across the whole conference
    conf_height_mean   = df.groupby(['Pos_Std'])['Height_Inches'].mean()
    conf_height_mean   = conf_height_mean.reset_index(drop = False)
    conf_height_mean   = conf_height_mean.rename(columns = {'Height_Inches':
                                                            'Height_Inches_Mean'})
    conf_height_median = df.groupby(['Pos_Std'])['Height_Inches'].median()
    conf_height_median = conf_height_median.reset_index(drop = False)
    conf_height_median = conf_height_median.rename(columns = {'Height_Inches':
                                                              'Height_Inches_Median'})
    conf_weight_mean   = df.groupby(['Pos_Std'])['Weight'].mean()
    conf_weight_mean   = conf_weight_mean.reset_index(drop = False)
    conf_weight_mean   = conf_weight_mean.rename(columns = {'Weight':
                                                            'Weight_Mean'})
    conf_weight_median = df.groupby(['Pos_Std'])['Weight'].median()
    conf_weight_median = conf_weight_median.reset_index(drop = False)
    conf_weight_median = conf_weight_median.rename(columns = {'Weight':
                                                              'Weight_Median'})
    
    # make conference dataframe
    df_stats_conf = pd.merge(conf_height_mean, conf_height_median, how = 'left', 
                        on = ['Pos_Std'])
    df_stats_conf = pd.merge(df_stats_conf, conf_weight_mean, how = 'left', 
                        on = ['Pos_Std'])
    df_stats_conf = pd.merge(df_stats_conf, conf_weight_median, how = 'left', 
                        on = ['Pos_Std'])
    df_stats_conf = df_stats_conf.rename(columns = {'Pos_Std':'Pos'})
    
    # make school name for the conference
    df_stats_conf['School'] = 'Big Ten'
    
    # reorder conference columns
    df_stats_conf = df_stats_conf[['School', 'Pos', 'Height_Inches_Mean', 
                                   'Height_Inches_Median', 'Weight_Mean', 
                                   'Weight_Median']]
    
    # append Conference Stats to Team Stats
    df_stats = df_stats.append(df_stats_conf)
    
    # Remove positions we don't care about
    #   -- LS, FB, K, P
    df_stats = df_stats[~df_stats['Pos'].isin(['LS', 'FB', 'K', 'P'])]
    
    # Add Logos to table
    list_image_paths = []
    for school in df_stats['School']:
        list_image_paths.append(rf'images/logos_school_square/{school}.png')
        # list_image_paths.append(str(path_dir.joinpath('images', 
        #                                               'logos_school_square', 
        #                                               school + '.png')))
    df_stats['Logo'] = list_image_paths
    
    return df_stats

def plotStats(df, name_position):
    # Set font and background colour
    # plt.rcParams.update({'font.family':'Avenir'})
    bgcol = '#fafafa'
    
    # Create initial plot
    fig, ax = plt.subplots(figsize=(6, 4), dpi=1200)
    ax.scatter(df['Weight_Mean'], df['Height_Inches_Mean'], c=bgcol)
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
        return OffsetImage(plt.imread(path), zoom=.4, alpha = 1)
    
    for index, row in df.iterrows():
        ab = AnnotationBbox(getImage(row['Logo']), (
            row['Weight_Mean'], row['Height_Inches_Mean']), frameon=False)
        if row['School'] != 'Big Ten':
            ax.add_artist(ab)
        
    # Ensure X-Axis are whole numbers
    def round_down(m, n):
        return m // n * n
    def round_up(n):
        return n + (5 - n) % 5
    min_xaxis = round_down(math.floor(df['Weight_Mean'].min()),5)
    max_xaxis = round_up(math.ceil(df['Weight_Mean'].max()))
    new_xaxis = range(min_xaxis, max_xaxis+5, 5)
    ax.set_xticks(list(new_xaxis))
    
    # Set Y-Axis to traditional height values (i.e. 6'1" etc)
    min_yaxis = math.floor(df['Height_Inches_Mean'].min())
    max_yaxis = math.ceil(df['Height_Inches_Mean'].max())
    new_yaxis = range(min_yaxis, max_yaxis+1)
                      
    ax.set_yticks(list(new_yaxis))
    yaxis_labels = [str(x) for x in new_yaxis]
    yaxis_labels = [str(math.floor(int(y)/12)) + '-' + str(int(y)%12) for y in yaxis_labels]
    ax.set_yticklabels(yaxis_labels)
    
    # Add average lines
    plt.hlines(float(df_pos[df_pos['School'] == 'Big Ten']['Height_Inches_Mean']), 
               min_xaxis, 
               max_xaxis, 
               color='#c2c1c0')
    plt.vlines(float(df_pos[df_pos['School'] == 'Big Ten']['Weight_Mean']), 
               min_yaxis, 
               max_yaxis, 
               color='#c2c1c0')
         
    fig.text(.15,.98,f'Big Ten {name_position}',size=20)
    fig.text(.15,.93,'Average Height and Weight as of April 2022', size=12)
    
    # Set Axis Labels
    ax.set_xlabel('Average Weight (lbs).')
    ax.set_ylabel('Average Height')
    
    # Add Made by to bottom of image
    fig.text(.68, .02, 'Created by @Stewmanji', size=8, color='#c2c1c0')
    
    ## Save plot
    plt.savefig(f'images/plots/{name_position}.png', dpi=1200, bbox_inches = "tight")
    plt.savefig(f'images/plots/{name_position}.pdf', format = 'pdf', bbox_inches = "tight")
    
#==============================================================================
# Working Code
#==============================================================================

# Set the project working directory
path_dir = pathlib.Path(r'C:\Users\reideej1\Projects\a_Personal\huskerProjects\20220421_BigTenFootballRosters2022')
os.chdir(path_dir)

# Load roster
df = processRawRosters()

# Compute stats
df_stats = computePositionStats(df, path_dir)

# Plot Defensive Line
dict_pos = {'OL':'Offensive Linemen', 
            'TE':'Tight Ends',
            'RB':'Running Backs',
            'LB':'Linebackers',
            'QB':'Quarterbacks',
            'DB':'Defensive Backs',
            'DL':'Defensive Linemen',
            'WR':'Wide Receivers'}
for key,value in dict_pos.items():
    df_pos = df_stats[df_stats.Pos == key]
    plotStats(df_pos, value)
