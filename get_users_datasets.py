import os
import numpy as np
import pandas as pd
from tqdm import tqdm
import sqlite3

import matplotlib.pyplot as plt
import seaborn as sns

from bs4 import BeautifulSoup
import requests
import json
import time
import datetime

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from parse_lb_users import *


def insert_rating(rating, cursor):
    sql_query = '''
    INSERT INTO Ratings(user, liked, film, reviewed, rating)
    VALUES (?, ?, ?, ?, ?)
    '''
    cursor.execute(sql_query, (
        rating.get("user"),
        rating.get("liked"),
        rating.get("film"),
        rating.get("reviewed"),
        rating.get("rating")
    ))

def insert_user(user, cursor):
    sql_query = f'''
    INSERT INTO Users(username, status, display_name, geo, films, thisyear, lists, following, followers, favorities)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
'''
    geo = user.get("geo")
    if geo:
        if len(geo) == 1:
            geo = geo[0]
        else:
            geo = ", ".join(geo)
    favorities = user.get("favorities")
    if favorities:
        if len(favorities) == 1:
            favorities = favorities[0]
        else:
            favorities = ", ".join(favorities)
    cursor.execute(sql_query, (
        user.get("username"),
        user.get("status"),
        user.get("display_name"),
        geo,
        user.get("Films"),
        user.get("This year"),
        user.get("Lists"),
        user.get("Following"),
        user.get("Followers"),
        favorities
    ))

RATINGS_SAVE_TYPE_JSON = False #True => JSON, False => SQLITE
USERS_SAVE_TYPE_JSON = True #True => JSON, False => SQLITE

USERS_LISTED_PATH = "Movie-for-the-evening/data/users_listed.txt"
USERS_SCHEDULE_PATH = "Movie-for-the-evening/data/users_schedule.txt"
USERS_PARSED_PATH = "Movie-for-the-evening/data/users_parsed.txt"
RATINGS_JSON_PATH = "Movie-for-the-evening/data/data_ratings.json"
USERS_JSON_PATH = "Movie-for-the-evening/data/data_users.json"
DB_PATH = "Movie-for-the-evening/data/parsed_data.db"

MAX_ITERS = 10_000

with open("Movie-for-the-evening/data/users_listed.txt", "r") as f:
    users_listed = set(map(lambda x: x.strip(), f.readlines()))

with open("Movie-for-the-evening/data/users_schedule.txt", "r") as f:
    users_listed.update(set(map(lambda x: x.strip(), f.readlines())))

with open("Movie-for-the-evening/data/users_parsed.txt", "r") as f:
    users_parsed = set(map(lambda x: x.strip(), f.readlines()))

users_listed = users_listed.difference(users_parsed)

db_exists = os.path.exists(DB_PATH)

if not db_exists:
    db = sqlite3.connect(DB_PATH)
    c = db.cursor()
    create_tables_sql_query = """
CREATE TABLE Ratings(
    user TEXT,
    liked INTEGER,
    film TEXT,
    reviewed INTEGER,
    rating INTEGER
);
CREATE TABLE Users(
    username TEXT,
    status TEXT,
    display_name TEXT,
    geo TEXT,
    films INTEGER,
    thisyear INTEGER,
    lists INTEGER,
    following INTEGER,
    followers INTEGER,
    favorities TEXT
);
"""

    c.executescript(create_tables_sql_query)
    db.commit()
    db.close()
    print("tables has created")

data_ratings = []
data_users = []

if RATINGS_SAVE_TYPE_JSON:
    with open("Movie-for-the-evening/data/data_ratings.json", "r") as f:
        file_content = f.read()
        if file_content:
            data_ratings = json.loads(file_content)
        else:
            data_ratings = []


if USERS_SAVE_TYPE_JSON:
    with open("Movie-for-the-evening/data/data_users.json", "r") as f:
        file_content = f.read()
        if file_content:
            data_users = json.loads(file_content)
        else:
            data_users = []

if not RATINGS_SAVE_TYPE_JSON or not USERS_SAVE_TYPE_JSON:
    db = sqlite3.connect(DB_PATH)
    c = db.cursor()

options = webdriver.ChromeOptions()
#options.add_argument("--headless")
options.add_argument("--disable-blink-features=AutomationControlled")
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)


parsed_users_cnt = len(data_users)
parsed_ratings_cnt = 0
i=0
try:
    while i<=MAX_ITERS:
        i += 1
        if not users_listed:
            print("There isn't users to parse")
            break
        username = users_listed.pop()
        users_parsed.add(username)
        print("_____________________________________________")
        print(i, username)
        #print("_____________________________________________")
        
        user = parse_user_main(username, driver)
        parsed_users_cnt += 1 if user else 0
        user_ratings = parse_user_ratings(username, driver)
        parsed_ratings_cnt += len(user_ratings) if user_ratings else 0

        if USERS_SAVE_TYPE_JSON:
            data_users.append(user)
        else:
            insert_user(user, c)
        if RATINGS_SAVE_TYPE_JSON:
            data_ratings.extend(user_ratings)
        else:
            for rating in user_ratings:
                insert_rating(rating, c)

        # print(user)
        # print("________")
        # print(user_ratings)
        # print("________")
        print(parsed_ratings_cnt,  parsed_users_cnt)

        if i % 10 == 0:
            with open("Movie-for-the-evening/data/users_parsed.txt", "w") as f:
                f.write("\n".join(str(item) for item in users_parsed))
            
            if RATINGS_SAVE_TYPE_JSON:
                with open("Movie-for-the-evening/data/data_ratings.json", "w") as f:
                    f.write(json.dumps(data_ratings, indent=4))
            
            if USERS_SAVE_TYPE_JSON:
                with open("Movie-for-the-evening/data/data_users.json", "w") as f:
                    f.write(json.dumps(data_users, indent=4))
                
            if not RATINGS_SAVE_TYPE_JSON or not USERS_SAVE_TYPE_JSON:
                db.commit()

            print("Saved")
except KeyboardInterrupt:
    print("Keybord Interrupt")
except Exception as e:
    print(e)
finally:
    if not RATINGS_SAVE_TYPE_JSON or not USERS_SAVE_TYPE_JSON:
        db.close()