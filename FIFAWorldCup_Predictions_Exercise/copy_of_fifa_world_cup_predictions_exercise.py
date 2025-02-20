# -*- coding: utf-8 -*-
"""Copy of FIFA World Cup Predictions Exercise.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1VeBRxzLcbElrQCrSeynnwzguHbjl8n4Z

Welcome to the FIFA World Cup Machine Learning Predictions Exercise! This was designed by Nicolas Stone Perez (nstonep@mit.edu) in January 2025, an optional exercise as part of the curriculum for the MIT Global Teaching Labs 2025 in Morocco, with the IEG Group, in Lycée Français Guy de Maupassant in Casablanca, and Lycée Français Sophie Germain in Rabat.

This first cell is for preparing the data. The data is loaded and prepared for you already. Scroll below to the instructions, and begin your code below the instructions!

For reference, the data was gathered from publicly available datasets on Kaggle, at the following pages:

https://www.kaggle.com/datasets/piterfm/fifa-football-world-cup

https://www.kaggle.com/datasets/cashncarry/fifaworldranking?utm_source=chatgpt.com

https://www.kaggle.com/datasets/iamsouravbanerjee/world-population-dataset
"""

#run this cell and scroll down
import pandas as pd

import warnings
with warnings.catch_warnings():
    warnings.simplefilter("ignore")

def calculate_result(row):
    """
    Helper function to determine the result of a match:
    - Returns 1 if the home team wins,
    - Returns -1 if the away team wins,
    - Returns 0 if it's a draw.
    """
    if row['Home Goals'] > row['Away Goals']:
        return 1
    elif row['Home Goals'] < row['Away Goals']:
        return -1
    else:
        return 0

# For each World Cup year, select the most recent population data available
def get_most_recent_population(country, year):
    recent_population = population[
        (population['Country'] == country) & (population['Year'] <= year)
    ]
    if not recent_population.empty:  # Check if there are valid population data rows
        return recent_population.iloc[-1]['Population']  # Take the most recent population entry
    else:
        return None  # Return None or NaN if no data found

# Load datasets (URLs)
matches_url_new = 'https://raw.githubusercontent.com/Mabdel-03/MIT_GTL_Morocco_IEG/refs/heads/main/FIFAWorldCup_Predictions_Exercise/matches_1930_2022_summary.csv'
rankings_url = 'https://raw.githubusercontent.com/Mabdel-03/MIT_GTL_Morocco_IEG/refs/heads/main/FIFAWorldCup_Predictions_Exercise/fifa_ranking-2023-07-20.csv'
population_url = 'https://raw.githubusercontent.com/Mabdel-03/MIT_GTL_Morocco_IEG/refs/heads/main/FIFAWorldCup_Predictions_Exercise/world_population.csv'

# Step 1: Load data
matches = pd.read_csv(matches_url_new)
rankings = pd.read_csv(rankings_url)
population = pd.read_csv(population_url)

# Step 2: Clean matches data
matches.loc[:,'Year']=matches['Year'].astype(int)
matches.loc[:, 'Away Team'] = matches['away_team']
matches.loc[:, 'Home Team'] = matches['home_team']
matches.loc[:,'Home Goals'] = matches['home_score']
matches.loc[:,'Away Goals'] = matches['away_score']

# Add match result (-1, 0, 1) for Away Win, Draw, Home Win
matches['Result'] = matches.apply(calculate_result, axis=1)

# Step 3: Process population data
population = population.rename(columns={'Country/Territory': 'Country'})
population = population[['Country', '1970 Population', '1980 Population', '1990 Population',
                         '2000 Population', '2010 Population', '2020 Population']]

# Melt into long format and clean 'Year' column
population = population.melt(id_vars='Country', var_name='Year', value_name='Population')
population['Year'] = population['Year'].str.extract('(\d+)').astype(int)

# Sort the population data by country and year (ascending)
population = population.sort_values(by=['Country', 'Year'])

# Apply the most recent population data for both Home and Away teams
matches['Home Population'] = matches.apply(lambda row: get_most_recent_population(row['Home Team'], row['Year']), axis=1)
matches['Away Population'] = matches.apply(lambda row: get_most_recent_population(row['Away Team'], row['Year']), axis=1)

# Filter for World Cup years
world_cup_years = [1994, 1998, 2002, 2006, 2010, 2014, 2018, 2022]
matches = matches[matches['Year'].isin(world_cup_years)]

# Step 4: Process rankings
rankings.loc[:,'Year'] = pd.to_datetime(rankings['rank_date']).dt.year
rankings.loc[:,'Country'] = rankings['country_full']
rankings.loc[:,'Rank'] = rankings['rank']
rankings = rankings[['Year', 'Country', 'Rank']]
# Average ranks by Country and Year to remove duplicates
rankings = rankings.groupby(['Country', 'Year'], as_index=False).agg({'Rank': 'median'})

matches.loc[:,'Home Team'] = matches['Home Team'].replace('rn">Republic of Ireland', 'Republic of Ireland')
matches.loc[:,'Away Team'] = matches['Away Team'].replace('rn">Republic of Ireland', 'Republic of Ireland')
rankings.loc[:,'Country'] = rankings['Country'].replace('rn">Republic of Ireland', 'Republic of Ireland')

# Merge rankings into matches
matches = matches.merge(rankings, left_on=['Home Team', 'Year'], right_on=['Country', 'Year'], how='left').rename(columns={'Rank': 'Home Rank'})
matches = matches.merge(rankings, left_on=['Away Team', 'Year'], right_on=['Country', 'Year'], how='left').rename(columns={'Rank': 'Away Rank'})

# Step 5: Final cleanup
matches = matches.drop(columns=['home_team', 'away_team', 'Country_x', 'Country_y'])

# Output: Check the structure of the resulting DataFrame
matches=matches[['Home Team', 'Away Team', 'Year', 'Home Population', 'Away Population', 'Home Rank', 'Away Rank', 'Home Goals','Away Goals','Result']]

# Step 5: Add historical goal difference
matches['Home Team Historical Goal Diff'] = None
matches['Away Team Historical Goal Diff'] = None

for index, row in matches.iterrows():
    # Historical goal difference for home team (considering both home and away matches)
    home_team_matches = matches[
        (matches['Home Team'] == row['Home Team']) |  # Include both home and away games
        (matches['Away Team'] == row['Home Team'])  # for the home team
        & (matches['Year'] < row['Year'])  # Only consider previous matches
    ]
    if not home_team_matches.empty:
        matches.at[index, 'Home Team Historical Goal Diff'] = (
            home_team_matches['Home Goals'].sum() - home_team_matches['Away Goals'].sum()
        ) / len(home_team_matches)  # Average goal difference over all previous matches
    else:
        matches.at[index, 'Home Team Historical Goal Diff'] = 0  # Default if no history exists

    # Historical goal difference for away team (considering both home and away matches)
    away_team_matches = matches[
        (matches['Home Team'] == row['Away Team']) |  # Include both home and away games
        (matches['Away Team'] == row['Away Team'])  # for the away team
        & (matches['Year'] < row['Year'])  # Only consider previous matches
    ]
    if not away_team_matches.empty:
        matches.at[index, 'Away Team Historical Goal Diff'] = (
            away_team_matches['Home Goals'].sum() - away_team_matches['Away Goals'].sum()
        ) / len(away_team_matches)  # Average goal difference over all previous matches
    else:
        matches.at[index, 'Away Team Historical Goal Diff'] = 0  # Default if no history exists


matches=matches.loc[matches['Year']>1992]

# Step 6: Feature selection
features = [
    'Home Rank', 'Away Rank', 'Home Population', 'Away Population',
    'Home Team Historical Goal Diff', 'Away Team Historical Goal Diff'
]
X = matches[features]
y = matches['Result']

# Handle missing values
X = X.fillna(0)

# Step 7: Train-test split (before 2022 for train, 2022 for test)
train_data = matches[matches['Year'] < 2022]
test_data = matches[matches['Year'] == 2022]

X_train = train_data[features]
y_train = train_data['Result']

X_test = test_data[features]
y_test = test_data['Result']

# Final output: train-test splits
print("Training features shape:", X_train.shape)
print("Testing features shape:", X_test.shape)

matches.head()

X_train.head()

y_train.head()

X_test.head()

y_test.head()



"""Start the FIFA World Cup Predictions using Machine Learning!

The training data is all FIFA World Cup matches from 1994-2018 (X_train and y_train). With this data, you can train any machine learning model you would like. Once you have this model ready, you can test it using the 2022 World Cup Data (X_test and y_test). Your goal should be to get as many accurate predictions as possible, and you can revise and modify your model, experimenting with different ideas, in order to try and improve the accuracy. We suggest experimenting with at least 3-5 different machine learning models to predict results. You are encouraged to share your results with Nicolas (nstonep@mit.edu), even long after the MIT/IEG 2025 Program is over! All students in Casablanca and Rabat are welcome to do this.

The features to make a prediction:
1. Rank (median rank from that year according to the FIFA World Rankings)
2. Population (from global population data, according to the last census before that edition of the World Cup)
3. Historical Goal Difference (average goal difference for that country in all their previous World Cup matches)

The target label:

1 means a win for the designated home team

0 means a draw

-1 means a win for the designated away team

Calculate accuracy by comparing your predictions with y_test. The accuracy can simply be a percentage from 0%-100%, based on how many of the 64 matches in 2022 you predicted correctly. The pandas, numpy, and scikit-learn Python libraries will be most helpful throughout this exercise.

Note that this is a classification exercise, where 1, 0, and -1 are separate categories. This is not a regression where labels take continuous values. Also, consider the home and away designations for a match meaningless, they are fairly arbitrary and just for FIFA convention. Unless the home team is the host country of the World Cup, there is no perceived advantage for them.

Also note, this is a hard exercise! Do not expect high accuracies right away. It is extremely hard for any technology to correctly predict the outcome of football matches.

Exercise: Using ranking, population, and historical goal difference data, train a classification model to make predictions for Qatar 2022 matches. Then, next year, use your model to make predictions for the 2026 World Cup!
"""

#Your Name: (Example: Nicolas)
#Your Country: (Example: Ireland)
#Your Favorite Football Club: (Example: Inter Miami)

#start your code here

#train using X_train and y_train ...

