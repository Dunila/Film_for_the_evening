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

# from selenium import webdriver
# from selenium.webdriver.chrome.service import Service
# from webdriver_manager.chrome import ChromeDriverManager

from parse_lb_users import *

# options = webdriver.ChromeOptions()
# #options.add_argument("--headless")
# options.add_argument("--disable-blink-features=AutomationControlled")
# service = Service(ChromeDriverManager().install())
# driver = webdriver.Chrome(service=service, options=options)

# username = "xaxamlo"

data_ratings = []
# data_users = []

# user = parse_user_main(username, driver)
# user_ratings = parse_user_ratings(username, driver)

# data_ratings.extend(user_ratings)
# data_users.append(user)

# with open("Movie-for-the-evening/data/data_ratings.json", "w") as f:
#     f.write(json.dumps(data_ratings, indent=4))

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

with open("Movie-for-the-evening/data/data_ratings.json", "r") as f:
    ratings = json.loads(f.read())

DB_PATH = "Movie-for-the-evening/data/parsed_data.db"
db = sqlite3.connect(DB_PATH)
c = db.cursor()

#print(ratings)
#insert_rating(ratings, c)
#print(c.executemany(""))
for rating in ratings:
    insert_rating(rating, c)

db.commit()
db.close()
# print("Saved")

