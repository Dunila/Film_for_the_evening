import pandas as pd
import numpy as np
import sqlite3
import json
from tqdm import tqdm 
from IPython.display import clear_output

import matplotlib.pyplot as plt
import seaborn as sns

def corr_pearson(vector1, vector2):
    """Returns Pearson's coefficient of correlation of two vectors"""
    v1_mean, v2_mean = vector1.mean(), vector2.mean()
    res1, res2 = vector1 - v1_mean, vector2 - v2_mean
    a = sum(res1*res2) 
    b = np.sqrt(sum(res1**2))*np.sqrt(sum(res2**2))
    #print(a, b)
    if b == 0:
        b = 0.0001
    return np.float64(a / b)
    
def measure_jaccard(vector1, vector2):
    """Returns Jaccard measure or inersection over union measure on two sets.
    Set here are indeces where user left rating or indeces where vector notna. 
    """
    isnan1 = np.isnan(vector1).astype(int)
    isnan2 = np.isnan(vector2).astype(int)
    combined = isnan1 + isnan2
    #print(combined)
    intersection = len(np.where(combined == 0)[0])
    #print(intersection)
    ex_union = len(np.where(combined == 1)[0])
    #print(ex_union+intersection)
    if ex_union == 0:
        return 0
    return np.float64(intersection / (ex_union + intersection))

def common_rated_indices(vec1, vec2):
    """Returns indecies where in vec1 and vec2 at once are ratings."""
    mask = ~np.isnan(vec1) & ~np.isnan(vec2)
    #print(mask)
    return np.where(mask)[0] 

def simularity_user(df, i_user1, i_user2, criterion="combined", theta=0.5):
    """
    params:
        df - pd.DataFrame where rows represents users, columns represents film, value in a cell represents user's rating of film 
        i_user1, i_user2 - int index of users in the df
        criterion - str 
            "pearson" - measure of simularity will be taken from Pearson's correlation coefficient only
            "jaccard" - measure of simularity will be taken from Jaccard's measure only
            "combined" - measure of simularity will be combined from Pearson's correlation coefficient and Jaccard's measure
        theta - float constrainted by [0, 1] - coefficient to wheight influence between types of measures if criterion = combined.
            By default 0.5 so influences are the same. 
            If theta -> 1 so correlation coefficient influences more 
    -----------------------
    returns:
        measure of simularity between two users. Users are recieved from dataframe df by their numeric indecies
    """
    if not criterion in ["combined", "pearson", "jaccard"]:
        criterion = "combined"

    if isinstance(i_user1, str):
        i_user1 = df.index.get_loc(i_user1)
    if isinstance(i_user2, str):
        i_user2 = df.index.get_loc(i_user2)
    
    if i_user1 == i_user2:
        return -0.99
    
    indexes = common_rated_indices(df.iloc[i_user1, :], df.iloc[i_user2, :])
    a = df.iloc[i_user1, indexes]
    b = df.iloc[i_user2, indexes]
    
    if criterion == "pearson":
        simularity = corr_pearson(a, b)
    elif criterion == "jaccard":
        simularity = measure_jaccard(df.iloc[i_user1, :], df.iloc[i_user2, :])
    elif criterion == "combined":
        corr = corr_pearson(a, b)
        measure = measure_jaccard(df.iloc[i_user1, :], df.iloc[i_user2, :])
        simularity = theta*corr + (1-theta)*measure
    else:
        print("No such criterion, picked Pearson")
        simularity = corr_pearson(a, b)
    return simularity

def estimate_rating(df, u, i, simular_users=pd.Series([]), thrashold_corr=0.5, thrashold_cnt=5):
    """
    params:
        df - pd.DataFrame where rows represents users, columns represents film, value in a cell represents user's rating of film
        u -int represents index of user
        i - int represents index of film
        thrashold_corr - float taken as threshold - minimum of simularity measure value to consider users simular.
        thrashold_cnt - int taken as maximum count of users to consider as simular to user u
    returns:
        estimating rating based on collabrative filtration on user2user recomendation. We'll base on hypothesis that simular users will 
        rate same film alike
    """
    if isinstance(u, str):
        #print(u)
        u = df.index.get_loc(u)
        #print(u)
    if isinstance(i, str):
        #print(i)
        i = df.columns.get_loc(i)
        #print(i)

    if simular_users.empty:
        simular_users = df.apply(lambda x: simularity_user(df, u, df.index.get_loc(x.name)), axis=1).sort_values(ascending=False)
    #print(simular_users)
        simular_users = simular_users[simular_users>thrashold_corr][:thrashold_cnt]
    #print(simular_users)
    
    r_of_simulars = df.loc[simular_users.index, df.columns[i]]
    #print(r_of_simulars)

    mask = ~r_of_simulars.isna()
    r_of_simulars = r_of_simulars[mask]
    simular_users = simular_users[mask]
    #clear_output()
    #print("______________")
    #print(r_of_simulars, simular_users)
    #print("______________")
    
    cnt_rating = r_of_simulars.count()

    s = sum(simular_users*r_of_simulars)
    t = sum(np.abs(simular_users))
    #print(s, t)
    if t == 0:
        t = 0.001
    return (round(np.float64(s / t), 4), cnt_rating)

def recommend(matrix: pd.DataFrame, user, cnt_recomended=25, thrashold_cnt=25, thrashold_corr=0.66, criterion="combined", theta=0.5):
    """
    params:
        matrix - pd.DataFrame where rows represents users, columns represents film, value in a cell represents user's rating of film
        user - str index of user for who system makes recommendations
        cnt_recomended - int represents count fo films to recommend
    returns:
        ranged(by estimated rating) dictionary of films as a key and estimated rating as a value limited by cnt_recomended
    """
    if isinstance(user, int):
        user = matrix.index[user]
    
    films_to_estimate = matrix.columns[matrix.loc[user].isna()] #find films that are not already have seen by user
    #print(len(films_to_estimate))

    simular_users = matrix.apply(lambda x: simularity_user(matrix, user, matrix.index.get_loc(x.name), criterion=criterion, theta=theta), axis=1).sort_values(ascending=False)
    simular_users = simular_users[simular_users>thrashold_corr][:thrashold_cnt]

    #TODO: filter matrix to only simular users in rows if empty simular users
    estimated_ratings = {film: estimate_rating(matrix, user, film, simular_users, thrashold_cnt=thrashold_cnt, thrashold_corr=thrashold_corr, ) for film in tqdm(films_to_estimate)}
    estimated_ratings = dict(sorted(estimated_ratings.items(), key=lambda x: -x[1][0]))
    recommended_films = dict(list(estimated_ratings.items())[:cnt_recomended])
    print(simular_users)
    return recommended_films


"""importing films"""
films = []
for i in range(1, 72):
    with open(f"C:\\Users\\danil\\Desktop\\infa\\Film_for_the_evening\\data\\lb_films\\parsed_films_checkpoint{i}.json", "r") as f:
        films1 = json.loads(f.read())
    films.extend(films1)
#print(len(films))
df_films = pd.DataFrame(films)
df_films["un_name"] = df_films.loc[:, "link"].apply(lambda x: x.split("/")[4])
#df_films.head()

"""importing users"""
USERS_PATH = "C:/Users/danil/Desktop/infa/Movie-for-the-evening/data/data_users.json"
df_users = pd.read_json(USERS_PATH)
#users_example = df_users[:25].copy()
#df_users.head()

"""importing ratings"""
DB_PATH = "C:/Users/danil/Desktop/infa/Movie-for-the-evening/data/parsed_data.db"

conn = sqlite3.connect(DB_PATH)
df_ratings = pd.read_sql_query("SELECT * FROM Ratings", conn)
conn.close()
#df_ratings.head()

"""Sampling from datasets"""
START_USER = 0
CNT_OF_USERS = 20_500
END_FILMS = 1_000
END_USER = START_USER + CNT_OF_USERS

users_sample = df_users.loc[START_USER:END_USER, "username"].copy()
if not "xaxamlo" in users_sample.values:
    print("added user")
    users_sample = pd.concat([users_sample, pd.Series(["xaxamlo"], index=[99_999])])
cnt_users = users_sample.shape[0]

films_sample = df_films.loc[:END_FILMS, "un_name"].copy()
cnt_films = films_sample.shape[0]

#ratings_sample = df_ratings[df_ratings["user"].isin(users_sample)]
ratings_sample = df_ratings[(df_ratings["user"].isin(users_sample)) & (df_ratings["film"].isin(films_sample))].copy()
cnt_ratings = ratings_sample.shape[0]

print(f"{cnt_users} of users, {cnt_films} of films, {cnt_ratings} of ratings\n{round(cnt_ratings/(cnt_users*cnt_films)*100, 2)}%")


ratings_matrix = ratings_sample.pivot_table(
    index="user",
    columns="film",
    values="rating"
)

result = recommend(ratings_matrix, "xaxamlo", thrashold_corr=0.0, theta=0.25)
print("RECOMENDED for user")
for film, (score, count) in result.items():
    print(f"{film:<35} {score:>8.4f}   {count:>3}")
