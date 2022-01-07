#import applicable modules that will be used
import pandas as pd
import numpy as np
from ipywidgets import widgets, interactive, Layout
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

#reading each csv file into a pandas df
df_15 = pd.read_csv('NBA_PBP_2015-16.csv') 
df_16 = pd.read_csv('NBA_PBP_2016-17.csv')
df_17 = pd.read_csv('NBA_PBP_2017-18.csv')
df_18 = pd.read_csv('NBA_PBP_2018-19.csv')
df_19 = pd.read_csv('NBA_PBP_2019-20.csv')

#inserting a column into each df that specifies the season that row corresponds to
df_15.insert(0,'Season',2015) 
df_16.insert(0,'Season',2016)
df_17.insert(0,'Season',2017)
df_18.insert(0,'Season',2018)
df_19.insert(0,'Season',2019)

#combining the df for each season into one df
df_all = pd.concat([df_15,df_16,df_17,df_18,df_19])
df_all = df_all.reset_index(drop=True)
df_all.info()

#dropping URL column because it's useless
df_all = df_all.drop(columns='URL')

#inserting a new columd 'id' and assigning a unique value for each game
df_all.insert(1,'ID',0) 
df_all['ID'] = df_all.groupby(['Date','Time','AwayTeam','HomeTeam']).ngroup()

#inserting a new column 'team' that tracks which team each play belongs to
df_all.insert(6,'Team','NA')

#converting the columns 'homeplay' and 'awayplay' to string values for comparison purposes
df_all[['HomePlay','AwayPlay']] = df_all[['HomePlay','AwayPlay']].astype(str)

#looping through each index position in the df to check if the away play is 'nan'
for idx in df_all.index:
    
    awayplay = df_all.at[idx,'AwayPlay']
    
    #if the away play is nan, that means the play belongs to the hometeam
    if awayplay == 'nan':
        df_all.at[idx,'Team'] = df_all.at[idx,'HomeTeam']
    else:
        df_all.at[idx,'Team'] = df_all.at[idx,'AwayTeam']

#Regulation NBA game is 4 quarters, quarters 5-8 represent games that went to overtime.
df_all['Quarter'].value_counts()

#creating a df that filters out the df_all for clutch time only plays based on the following criteria:
df_clutch = df_all[(df_all['Quarter']>=4) & 
                   (df_all['SecLeft']<=300) & 
                   (abs(df_all['AwayScore']-df_all['HomeScore']<=5))]
df_clutch = df_clutch.reset_index(drop=True)
df_clutch
    #4th quarter and all subsequent OT periods
    #5 minutes or less
    #Score margin is within 5 points

#creating a df that looks at all other plays that do not meet the criteria of clutch time, this will be used for analysis further down the line
df_non_clutch_1 = df_all[(df_all['Quarter']<4)]
df_non_clutch_2 = df_all[(df_all['Quarter']>=4) & (df_all['SecLeft']>300)]
df_non_clutch_3 = df_all[(df_all['Quarter']>=4) & (df_all['SecLeft']<=300) & (abs(df_all['AwayScore']-df_all['HomeScore']>5))]
df_non_clutch = pd.concat([df_non_clutch_1,df_non_clutch_2,df_non_clutch_3])
df_non_clutch = df_non_clutch.reset_index(drop=True)
df_non_clutch

#getting a count of the values in the shot type column so we know how to categroize between FGA and 3PA
df_clutch['ShotType'].value_counts() 

#creating a function that inserts 4 columns(FGM, FGA, 3PM, 3PA) to track the type of shot taken and made during clutch time
def shot_category(df):
    
    #insert the 4 columns mentoioned above
    df.insert(18,'FGM',0) 
    df.insert(19,'FGA',0)
    df.insert(20,'3PM',0)
    df.insert(21,'3PA',0)
    
    #field goals include both 2 pointers and 3 pointers so every shot attempt is a field goal attempt
    df['FGA'] = 1 
    
    #iterate through each index position in df
    for idx in df.index:
        item = df.at[idx,'ShotType']
        
        #if the value in the ShotType column contains '2-pt' then we know it is not a 3-point attempt
        if '2-pt ' in item:
            df.at[idx, '3PA'] = 0
        else:
            df.at[idx, '3PA'] = 1

        #if the value in the ShotOutcome column is 'make' then we assign it a value of 1 for FGM
        item_2 = df.at[idx,'ShotOutcome']
        if item_2 == 'make':
            df.at[idx,'FGM'] = 1
        else:
            df.at[idx,'FGM'] = 0
        
        #if the value in the ShotType column contains '3-pt' and the value in the ShotOutcome is 'make' then we assign a value of 1 for 3PM
        item_3 = df.at[idx,'ShotType']
        item_4 = df.at[idx,'ShotOutcome']
        if ('3-pt' in item_3) & (item_4 == 'make'):
            df.at[idx,'3PM'] = 1
        else:
            df.at[idx,'3PM'] = 0

#creating a copy of df_clutch that drops rows that have an NA value for ShotType and resetting the index
df_clutch_shooting = df_clutch.dropna(subset=['ShotType']).copy() 
df_clutch_shooting = df_clutch_shooting.reset_index(drop=True)

#pass df_clutch_shooting and df_non_clutch_shooting through the shot_category function            
shot_category(df_clutch_shooting)

#check values for FGA and 3PM to make sure all shots were properly categorized
print(df_clutch_shooting['FGA'].value_counts())
print(df_clutch_shooting['3PA'].value_counts())

#creating a df that looks at non clutch time shooting stats, this is being copied from the non clutch df we made in the previous section
df_nc_shooting = df_non_clutch.dropna(subset=['ShotType']).copy()
df_nc_shooting = df_nc_shooting.reset_index(drop=True)

#passing the non clutch time df through the shot_category function to calculate FG% and 3P% for each player
shot_category(df_nc_shooting)

#check values for FGA and 3PM to make sure all shots were properly categorized
print(df_nc_shooting['FGA'].value_counts())
print(df_nc_shooting['3PA'].value_counts())

#creating a df with just the shooting stats we want to look at during clutch time
clutch_players = df_clutch_shooting[['Season','Shooter','Team','FGM','FGA','3PM','3PA']]

#creating a df with just the shooting stats we want to look at during non clutch time
nc_players = df_nc_shooting[['Season','Shooter','Team','FGM','FGA','3PM','3PA']]

#creating a function to find the top 5 players based on FG%. Pass each seasons clutch_players df through this function
def top_players_FG(df,season):  
    
    #only look at seasons that are passed in the parameters of the function
    df = df[df['Season'].isin(season)]
    
    #group the df by Season and Shooter and sum the FGM, FGA, 3PM, 3PA for each player
    df = df.groupby(['Season','Shooter','Team'],as_index=False).sum()
    
    #calculate the FG% and 3P% for each player
    df['FG%'] = (df['FGM']/df['FGA'])*100
    df['3P%'] = (df['3PM']/df['3PA'])*100
    
    #round columns to 2 decimal places
    df['FG%'] = df['FG%'].astype(float).round(decimals=2)
    df['3P%'] = df['3P%'].astype(float).round(decimals=2)
    
    #only keep players who had a minimum of 100 FGA in clutch time
    df = df[df['FGA']>100]
    
    #get the 10 players with the highest FG%'s
    df = df.nlargest(10,'FG%') 
        
    return df


#creating a function to compare the top 10 players clutch time FG% vs non clutch time FG%
def compare_shooting_FG(df,df2,season):
    
    #only look at seasons that are passed in the parameters of the function
    df = df[df['Season'].isin(season)]
    
    #group the df by Season and Shooter and sum the FGM, FGA, 3PM, 3PA for each player
    df = df.groupby(['Season','Shooter','Team'],as_index=False).sum()
    
    #calculate the FG% and 3P% for each player
    df['FG%'] = (df['FGM']/df['FGA'])*100
    df['3P%'] = (df['3PM']/df['3PA'])*100
    
    #round columns to 2 decimal places
    df['FG%'] = df['FG%'].astype(float).round(decimals=2)
    df['3P%'] = df['3P%'].astype(float).round(decimals=2)
    
    #only keep players who had a minimum of 100 FGA in clutch time
    df = df[df['FGA']>100]
    
    #get the 10 players with the highest FG%'s
    df = df.nlargest(10,'FG%')
    
    #group the df by Season and Shooter and sum the FGM, FGA, 3PM, 3PA for each player
    df2 = df2.groupby(['Season','Shooter','Team'],as_index=False).sum()
    
    #calculate the FG% and 3P% for each player
    df2['FG%'] = (df2['FGM']/df2['FGA'])*100
    df2['3P%'] = (df2['3PM']/df2['3PA'])*100
    
    #round columns to 2 decimal places
    df2['FG%'] = df2['FG%'].astype(float).round(decimals=2)
    df2['3P%'] = df2['3P%'].astype(float).round(decimals=2)
    
    #return a df for players that appear in the top 10 of clutch time FG%
    df2 = df2[df2['Season'].isin(df['Season']) & df2['Shooter'].isin(df['Shooter']) & df2['Team'].isin(df['Team'])]
    
    #Plot the FG% from the 2 df's against each other
    plt.figure(figsize=(20,15))
    plt.scatter(df['FG%'],df2['FG%'],s=200)
   
    #Give both axis a description and give the chart a title
    plt.xlabel('Clutch Time FG%')
    plt.ylabel('Non-Clutch Time FG%')
    plt.title('Clutch TIme vs. Non-Clutch Time FG%',size=20)
    
    #for each point in the scatterplot, add the appropriate player's name for which that point corresponds
    for i, name in enumerate(df['Shooter']):
        plt.annotate(name,(df['FG%'].iat[i]+.1,df2['FG%'].iat[i]))

#visualization widget to see the 10 players with the highest clutch time FG% in each season
season = widgets.Dropdown(
    options=['Top 10 Overall','2015-2016', '2016-2017', '2017-2018', '2018-2019', '2019-2020'],
    value = 'Top 10 Overall',
    description='Clutch Time FG%:',
    style = {'description_width':'initial'},
    layout = Layout(width="30%")
)

#pass top_players function through this function to return the df of the 10 players with the highest clutch time FG% for each season
def get_season(x):
    if x == '2015-2016':
        display(top_players_FG(clutch_players,[2015]))
    elif x == '2016-2017':
        display(top_players_FG(clutch_players,[2016]))
    elif x == '2017-2018':
        display(top_players_FG(clutch_players,[2017]))
    elif x == '2018-2019':
        display(top_players_FG(clutch_players,[2018]))
    elif x == '2019-2020':
        display(top_players_FG(clutch_players,[2019]))
    else:
        display(top_players_FG(clutch_players,[2015,2016,2017,2018,2019])
               )
i = interactive(get_season, x=season)
display(i)

#visualization widget to see the 10 players FG% during clutch time plotted against their FG% during non-clutch time
season = widgets.Dropdown(
    options=['2015-2016', '2016-2017', '2017-2018', '2018-2019', '2019-2020'],
    value = '2015-2016',
    description='Season:',
    style = {'description_width':'initial'},
    layout = Layout(width="30%")
)

#pass compare_shooting_FG function through this function to return the scatterplot of cluch time FG% vs non-clutch time FG% for each season
def get_season(x):
    if x == '2015-2016':
        display(compare_shooting_FG(clutch_players,nc_players,[2015]))
    elif x == '2016-2017':
        display(compare_shooting_FG(clutch_players,nc_players,[2016]))
    elif x == '2017-2018':
        display(compare_shooting_FG(clutch_players,nc_players,[2017]))
    elif x == '2018-2019':
        display(compare_shooting_FG(clutch_players,nc_players,[2018]))
    else:
        display(compare_shooting_FG(clutch_players,nc_players,[2019]))

i = interactive(get_season, x=season)
display(i)

#creating a function to find the top 10 players based on clutch time 3P%. Pass each seasons clutch_players df through this function
def top_players_3P(df,season): 
    
    #only look at seasons that are passed in the parameters of the function
    df = df[df['Season'].isin(season)]
    
    #group the df by Season and Shooter and sum the FGM, FGA, 3PM, 3PA for each player
    df = df.groupby(['Season','Shooter','Team'],as_index=False).sum()
    
    #calculate the FG% and 3P% for each player
    df['FG%'] = (df['FGM']/df['FGA'])*100
    df['3P%'] = (df['3PM']/df['3PA'])*100
    
    #round columns to 2 decimal places
    df['FG%'] = df['FG%'].astype(float).round(decimals=2)
    df['3P%'] = df['3P%'].astype(float).round(decimals=2)
    
    #only keep players who had a minimum of 50 3PA in clutch time
    df = df[df['3PA']>50]
    
    #get the 10 players with the highest 3P%'s
    df = df.nlargest(10,'3P%')
    
    return df

#creating a function to compare the top 10 players clutch time 3P% vs non clutch time 3P%
def compare_shooting_3P(df,df2,season):
    
    #only look at seasons that are passed in the parameters of the function
    df = df[df['Season'].isin(season)]
    
    #group the df by Season and Shooter and sum the FGM, FGA, 3PM, 3PA for each player
    df = df.groupby(['Season','Shooter','Team'],as_index=False).sum()
    
    #calculate the FG% and 3P% for each player
    df['FG%'] = (df['FGM']/df['FGA'])*100
    df['3P%'] = (df['3PM']/df['3PA'])*100
    
    #round columns to 2 decimal places
    df['FG%'] = df['FG%'].astype(float).round(decimals=2)
    df['3P%'] = df['3P%'].astype(float).round(decimals=2)
    
    #only keep players who had a minimum of 50 3PA in clutch time
    df = df[df['3PA']>50]
    
    #get the 10 players with the highest 3P%'s
    df = df.nlargest(10,'3P%')
    
    #group the df by Season and Shooter and sum the FGM, FGA, 3PM, 3PA for each player
    df2 = df2.groupby(['Season','Shooter','Team'],as_index=False).sum()
    
    #calculate the FG% and 3P% for each player
    df2['FG%'] = (df2['FGM']/df2['FGA'])*100
    df2['3P%'] = (df2['3PM']/df2['3PA'])*100
    
    #round columns to 2 decimal places
    df2['FG%'] = df2['FG%'].astype(float).round(decimals=2)
    df2['3P%'] = df2['3P%'].astype(float).round(decimals=2)
    
    #return a df for players that appear in the top 10 of clutch time 3P%
    df2 = df2[df2['Season'].isin(df['Season']) & df2['Shooter'].isin(df['Shooter']) & df2['Team'].isin(df['Team'])]
    
    #Plot the 3P% from the 2 df's against each other
    plt.figure(figsize=(20,15))
    plt.scatter(df['3P%'],df2['3P%'],s=200)
   
    #Give both axis a description and give the chart a title
    plt.xlabel('Clutch Time 3P%')
    plt.ylabel('Non-Clutch Time 3P%')
    plt.title('Clutch Time vs. Non-Clutch Time 3P%',size=20)
    
    #for each point in the scatterplot, add the appropriate player's name for which that point corresponds
    for i, name in enumerate(df['Shooter']):
        plt.annotate(name,(df['3P%'].iat[i]+.2,df2['3P%'].iat[i]))

#visualization widget to see the 10 players with the highest 3P% in each season
season = widgets.Dropdown(
    options=['Top 10 Overall','2015-2016', '2016-2017', '2017-2018', '2018-2019', '2019-2020'],
    value = 'Top 10 Overall',
    description='Clutch Time 3P%:',
    style = {'description_width':'initial'},
    layout = Layout(width="30%")
)

#pass top_players function through this function to return the df from the function above
def get_season(x):
    if x == '2015-2016':
        display(top_players_3P(clutch_players,[2015]))
    elif x == '2016-2017':
        display(top_players_3P(clutch_players,[2016]))
    elif x == '2017-2018':
        display(top_players_3P(clutch_players,[2017]))
    elif x == '2018-2019':
        display(top_players_3P(clutch_players,[2018]))
    elif x == '2019-2020':
        display(top_players_3P(clutch_players,[2019]))
    else:
        display(top_players_3P(clutch_players,[2015,2016,2017,2018,2019]))

i = interactive(get_season, x=season)
display(i)

#visualization widget to see the 10 players 3P% during clutch time plotted against their 3P% during non-clutch time
season = widgets.Dropdown(
    options=['2015-2016', '2016-2017', '2017-2018', '2018-2019', '2019-2020'],
    value = '2015-2016',
    description='Season:',
    style = {'description_width':'initial'},
    layout = Layout(width="30%")
)

#pass compare_shooting_3P function through this function to return the scatterplot of cluch time 3P% vs non-clutch time 3P% for each season
def get_season(x):
    if x == '2015-2016':
        display(compare_shooting_3P(clutch_players,nc_players,[2015]))
    elif x == '2016-2017':
        display(compare_shooting_3P(clutch_players,nc_players,[2016]))
    elif x == '2017-2018':
        display(compare_shooting_3P(clutch_players,nc_players,[2017]))
    elif x == '2018-2019':
        display(compare_shooting_3P(clutch_players,nc_players,[2018]))
    else:
        display(compare_shooting_3P(clutch_players,nc_players,[2019]))

i = interactive(get_season, x=season)
display(i)

#creating a df to track the wins and losses during clutch time for each team in each season
df_wins = df_clutch[['ID','Season','WinningTeam','HomeTeam','AwayTeam']].reset_index(drop=True)
df_wins = df_wins.drop_duplicates(subset='ID',keep='first').reset_index(drop=True)

#iterate through each index position in df
for idx in df_wins.index:
    
    item1 = df_wins.at[idx,'WinningTeam']
    item2 = df_wins.at[idx,'HomeTeam']
    
    #if the winning team is equal to the home team then that means the losing team is the away team. If not, that means the home team is the losing team
    if item1 == item2:
        df_wins.at[idx,'LosingTeam']  = df_wins.at[idx,'AwayTeam']
    else:
        df_wins.at[idx,'LosingTeam'] = df_wins.at[idx,'HomeTeam']

#creating a df that contains each team name, this will be used to calculate the record for each team in each season
df_record = pd.DataFrame(columns=['Team'])
df_record['Team'] = df_wins['HomeTeam'].unique()
df_record = df_record.sort_values(by='Team').reset_index(drop=True)

#creating a function to calculate the record of each team during clutch time for each season
def calc_record(df1,df2,season):
    
    #only look at seasons that are passed in the parameters of the function
    df2 = df2[df2['Season'].isin(season)]
    
    #iterate through each index position in df
    for idx in df1.index:
        team = df1.at[idx,'Team']
        
        #the columns wins and losses in each record df is equal to the number of times that team appears in the winning team or losing team column of the wins df for that season
        df1.at[idx,'Wins'] = df2[df2['WinningTeam'] == team].shape[0]
        df1.at[idx,'Losses'] = df2[df2['LosingTeam'] == team].shape[0]
    
    #converting the wins and losses columns to integer types so they are whole numbers with no decimal places
    df1['Wins'] = df1['Wins'].astype(int)
    df1['Losses'] = df1['Losses'].astype(int)
    
    #making a new column 'record' that formats wins and losses as such 'wins-losses' as a string type
    df1['Record'] = df1['Wins'].astype(str) + '-' + df1['Losses'].astype(str)
    
    #calculating winning percentage for each team
    df1['Winning %'] = df1['Wins']/(df1['Wins'] + df1['Losses'])
    df1['Winning %'] = df1['Winning %'].astype(float).round(decimals=3)
        
    #sorting the df by highest winning % to lowest winning %
    df1 = df1.sort_values(by='Winning %',ascending=False)
    
    #display the 3 columns below from the df when the function is ran
    display(df1[['Team','Record','Winning %']].reset_index(drop=True))
    
    #graphing the sorted df and adding a line to show the average clutch time winning % for each season
    fig, ax = plt.subplots(figsize=(20,15)) 
    graph = sns.barplot(data=df1,x='Winning %',y='Team',palette='rocket',ax=ax,orient='h')
    graph.set_title('Clutch Time Winning Percentage',fontsize=20)
    graph.axvline(df1['Winning %'].mean())
    
    #display the winning percentage for each bar in the graph
    for bar in graph.patches:
        graph.annotate(bar.get_width(),(bar.get_width(),bar.get_y()+bar.get_height()/2))

#visualization widget to see the winning % of teams during clutch time for each season
record = widgets.Dropdown(
    options=['All Seasons','2015-2016', '2016-2017', '2017-2018', '2018-2019', '2019-2020'],
    value = 'All Seasons',
    description='Clutch Time Winning %:',
    style = {'description_width':'initial'},
    layout = Layout(width="30%")
)

#pass calc_record function through this function to return the df and graph from the function above for each season
def get_record(x):
    if x == '2015-2016':
        display(calc_record(df_record,df_wins,[2015]))
    elif x == '2016-2017':
        display(calc_record(df_record,df_wins,[2016]))
    elif x == '2017-2018':
        display(calc_record(df_record,df_wins,[2017]))
    elif x == '2018-2019':
        display(calc_record(df_record,df_wins,[2018]))
    elif x == '2019-2020':
        display(calc_record(df_record,df_wins,[2019]))
    else:
        display(calc_record(df_record,df_wins,[2015,2016,2017,2018,2019]))

i = interactive(get_record, x=record)
display(i)

#creating a copy of df_clutch that drops rows that have an NA value for Assister and resetting the index 
df_clutch_assists = df_clutch.dropna(subset=['Assister']).copy() 
df_clutch_assists = df_clutch_assists.reset_index(drop=True)

#creating a copy of df_clutch that drops rows that have an NA value for TurnoverPlayer and resetting the index 
df_clutch_turnovers = df_clutch.dropna(subset=['TurnoverPlayer']).copy()
df_clutch_turnovers = df_clutch_turnovers.reset_index(drop=True)

#filtering both df's above for only the columns with data we want to look at
clutch_assists = df_clutch_assists[['Season','Team','Assister']]
clutch_turnovers = df_clutch_turnovers[['Season','Team','TurnoverPlayer']]

#creating a function to calculate each team's assist:turnover ratio and plot that against each team's winning % for each season
def assist_to_ratio(df1,df2,df3,df4,season):
    
    #only look at seasons that are passed in the parameters of the function
    df2 = df2[df2['Season'].isin(season)]
    
    #iterate through each index position in df
    for idx in df1.index:
        team = df1.at[idx,'Team']
        
        #the columns wins and losses in each record df is equal to the number of times that team appears in the winning team or losing team column of the wins df for that season
        df1.at[idx,'Wins'] = df2[df2['WinningTeam'] == team].shape[0]
        df1.at[idx,'Losses'] = df2[df2['LosingTeam'] == team].shape[0]
    
    #converting the wins and losses columns to integer types so they are whole numbers with no decimal places
    df1['Wins'] = df1['Wins'].astype(int)
    df1['Losses'] = df1['Losses'].astype(int)
    
    #making a new column 'record' that formats wins and losses as such 'wins-losses' as a string type
    df1['Record'] = df1['Wins'].astype(str) + '-' + df1['Losses'].astype(str)
    
    #calculating winning percentage for each team
    df1['Winning %'] = df1['Wins']/(df1['Wins'] + df1['Losses'])
    df1['Winning %'] = df1['Winning %'].astype(float).round(decimals=3)
    
    #changing the value in each column to a numeric value so we can sum the amounts once we group the df's
    df3['Assister'] = 1
    df4['TurnoverPlayer'] = 1
    
    #group the df's by Season and Team and sum numeric columns
    df3 = df3.groupby(['Season','Team'],as_index=False).sum()
    df4 = df4.groupby(['Season','Team'],as_index=False).sum()
    
    #create a new df that merges df3 and df4 on Season and Team, the result will give us assists and turnover for each team in each season
    df5 = pd.merge(df3,df4,on=['Season','Team'])
    
    #add a column to the new df that calculates assist:turnover ratio
    df5['Assist/Turnover Ratio'] = df5['Assister']/df5['TurnoverPlayer']
    df5['Assist/Turnover Ratio'] = df5['Assist/Turnover Ratio'].astype(float).round(decimals=3)
    
    #filtering the df for the season we are looking at, which is a parameter in this function
    df5 = df5[df5['Season'].isin(df2['Season']) & df5['Team'].isin(df1['Team'])]

    #create a scatter plot that plots Winning % and Assist:Turnover Ratio for each team in the season selected
    #the color of the dots in the scatterplot is scaled based on Winning %
    plt.figure(figsize=(20,15))
    plt.scatter(df5['Assist/Turnover Ratio'],df1['Winning %'],s=200,c=df1['Winning %'],cmap='RdYlGn')
   
    #Give both axis a description and give the chart a title
    plt.xlabel('Clutch Time Assist:Turnover Ratio')
    plt.ylabel('Clutch Time Winning %')
    plt.title('Assist:Turnover Ratio vs. Clutch Time Winning Percentage',size=20)
    
    #for each point in the scatterplot, add the appropriate team's name for which that point corresponds
    for i, name in enumerate(df1['Team']):
        plt.annotate(name,(df5['Assist/Turnover Ratio'].iat[i]+.01,df1['Winning %'].iat[i]))

#visualization widget to see the winning % vs assist:turnover ratio of teams during clutch time for each season
record = widgets.ToggleButtons(
    options=['2015-2016', '2016-2017', '2017-2018', '2018-2019', '2019-2020'],
    value = '2015-2016',
    description='Season:',
    style = {'description_width':'initial'},
    layout = Layout(width="30%")
)

#pass assist_to_ratio function through this function to return the scatterplot from the function above for each season
def get_record(x):
    if x == '2015-2016':
        display(assist_to_ratio(df_record,df_wins,clutch_assists,clutch_turnovers,[2015]))
    elif x == '2016-2017':
        display(assist_to_ratio(df_record,df_wins,clutch_assists,clutch_turnovers,[2016]))
    elif x == '2017-2018':
        display(assist_to_ratio(df_record,df_wins,clutch_assists,clutch_turnovers,[2017]))
    elif x == '2018-2019':
        display(assist_to_ratio(df_record,df_wins,clutch_assists,clutch_turnovers,[2018]))
    else:
        display(assist_to_ratio(df_record,df_wins,clutch_assists,clutch_turnovers,[2019]))

i = interactive(get_record, x=record)
display(i)

#creating a copy of df_clutch that drops rows that have an NA value for TurnoverPlayer and resetting the index 
df_clutch_tf = df_clutch.dropna(subset=['TurnoverPlayer']).copy() 
df_clutch_tf = df_clutch_tf.reset_index(drop=True)

#creating a copy of df_clutch that drops rows that have an NA value for TurnoverPlayer and resetting the index 
df_clutch_turnovers = df_clutch.dropna(subset=['TurnoverPlayer']).copy()
df_clutch_turnovers = df_clutch_turnovers.reset_index(drop=True)
clutch_turnovers = df_clutch_turnovers[['Season','Team','TurnoverPlayer']]

def turnover_margin(df1,df2,df3,df4,season):
       
    #only look at seasons that are passed in the parameters of the function
    df2 = df2[df2['Season'].isin(season)]
    
    #iterate through each index position in df
    for idx in df1.index:
        team = df1.at[idx,'Team']
        
        #the columns wins and losses in each record df is equal to the number of times that team appears in the winning team or losing team column of the wins df for that season
        df1.at[idx,'Wins'] = df2[df2['WinningTeam'] == team].shape[0]
        df1.at[idx,'Losses'] = df2[df2['LosingTeam'] == team].shape[0]
    
    #converting the wins and losses columns to integer types so they are whole numbers with no decimal places
    df1['Wins'] = df1['Wins'].astype(int)
    df1['Losses'] = df1['Losses'].astype(int)
    
    #making a new column 'record' that formats wins and losses as such 'wins-losses' as a string type
    df1['Record'] = df1['Wins'].astype(str) + '-' + df1['Losses'].astype(str)
    
    #calculating winning percentage for each team
    df1['Winning %'] = df1['Wins']/(df1['Wins'] + df1['Losses'])
    df1['Winning %'] = df1['Winning %'].astype(float).round(decimals=3)
    
    #iterate through each index position in the df
    for idx in df3.index:
        
        item1 = df3.at[idx,'Team']
        item2 = df3.at[idx,'HomeTeam']
        
        #a turnover belongs to the team that the possesses the ball
        #so to find out which team forced the turnover, it's just the opposite team
        if item1 == item2:
            df3.at[idx,'Team'] = df3.at[idx,'AwayTeam']
        else:
            df3.at[idx,'Team'] = df3.at[idx,'HomeTeam']
    
    #only keep the columns we want to look at
    df3 = df3[['Season','Team','TurnoverCauser']]
    
    #change to numeric values so we can sum for each season and team
    df3['TurnoverCauser'] = 1
    df4['TurnoverPlayer'] = 1
    
    #group the df's by Season and Team and sum numeric columns
    df3 = df3.groupby(['Season','Team'],as_index=False).sum()
    df4 = df4.groupby(['Season','Team'],as_index=False).sum()
    
    #create a new df that merges df3 and df4 on Season and Team, the result will give us turnovers forced and turnovers committed for each season
    df5 = pd.merge(df3,df4,on=['Season','Team'])

    #add a column to the new df that calculates turnover margin
    df5['Turnover Margin'] = df5['TurnoverCauser']-df5['TurnoverPlayer']
    
    #filtering the df for the season we are looking at, which is a parameter in this function
    df5 = df5[df5['Season'].isin(df2['Season']) & df5['Team'].isin(df1['Team'])]

    #create a scatter plot that plots Winning % and Turnover Margin for each team in the season selected
    #the color of the dots in the scatterplot is scaled based on Winning %
    plt.figure(figsize=(20,15))
    plt.scatter(df5['Turnover Margin'],df1['Winning %'],s=200,c=df1['Winning %'],cmap='RdYlGn')
   
    #Give both axis a description and give the chart a title
    plt.xlabel('Clutch Time Turnover Margin')
    plt.ylabel('Clutch Time Winning %')
    plt.title('Turnover Margin vs. Clutch Time Winning Percentage',size=20)
    
    #add a line at point zero so better to see which teams have a negative and positive turnover margins
    plt.axvline(x=0,color='r')
    
    #for each point in the scatterplot, add the appropriate team's name for which that point corresponds
    for i, name in enumerate(df1['Team']):
        plt.annotate(name,(df5['Turnover Margin'].iat[i],df1['Winning %'].iat[i]+.01))

#visualization widget to see the winning % vs turnover margin of teams during clutch time for each season
record = widgets.ToggleButtons(
    options=['2015-2016', '2016-2017', '2017-2018', '2018-2019', '2019-2020'],
    value = '2015-2016',
    description='Season:',
    style = {'description_width':'initial'},
    layout = Layout(width="30%")
)

#pass turnover_margin function through this function to return the scatterplot from the function above for each season
def get_record(x):
    if x == '2015-2016':
        display(turnover_margin(df_record,df_wins,df_clutch_tf,clutch_turnovers,[2015]))
    elif x == '2016-2017':
        display(turnover_margin(df_record,df_wins,df_clutch_tf,clutch_turnovers,[2016]))
    elif x == '2017-2018':
        display(turnover_margin(df_record,df_wins,df_clutch_tf,clutch_turnovers,[2017]))
    elif x == '2018-2019':
        display(turnover_margin(df_record,df_wins,df_clutch_tf,clutch_turnovers,[2018]))
    else:
        display(turnover_margin(df_record,df_wins,df_clutch_tf,clutch_turnovers,[2019]))

i = interactive(get_record, x=record)
display(i)

