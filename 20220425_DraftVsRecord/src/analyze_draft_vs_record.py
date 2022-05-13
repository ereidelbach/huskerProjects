#!/usr/bin/env python3.7
# -*- coding: utf-8 -*-
"""
Created on Mon Apr 25 10:00:41 2022

@author: reideej1

:DESCRIPTION: Determine how many players are drafted from each D1 school every
    year and compare that to the records of those teams.
    
    In the 2022 NFL draft, Nebraska is projected to have 4 draft picks despite 
    going 3-9 on the regular season. Has this ever happened before?

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

#==============================================================================
# Working Code
#==============================================================================

# Set the project working directory
path_dir = pathlib.Path(r'C:\Users\reideej1\Projects\a_Personal\huskerProjects\20220425_DraftVsRecord')

# ingest the latest draft data
df_draft = pd.read_csv(max(glob.iglob(
    r'data\historic_draft_*.csv'), key=os.path.getmtime))
df_coaches = df_coaches.apply(pd.to_numeric, errors = 'ignore')

# ingest the latest CFB results data