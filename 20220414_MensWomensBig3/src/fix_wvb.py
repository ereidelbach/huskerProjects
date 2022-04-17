df_year = pd.read_csv(r'data/csv/WVB/WVB_2021.csv')

df_year['W'] = df_year['W-L'].apply(lambda x: x.split('-')[0])
df_year['L'] = df_year['W-L'].apply(lambda x: x.split('-')[1])
# Reorder and isolate columns of interest
df_year = df_year[['Sport', 'Season', 'Team', 'W', 'L', 'Rank', 'Conf']]

df_year.to_csv(r'data/csv/WVB/WVB_2021.csv', index = False)