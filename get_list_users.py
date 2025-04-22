import os
import numpy as np
import pandas as pd
from tqdm import tqdm


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

options = webdriver.ChromeOptions()
#options.add_argument("--headless")
options.add_argument("--disable-blink-features=AutomationControlled")

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

with open("Movie-for-the-evening/data/users_schedule.txt", "r") as f:
    users_schedule = set(map(lambda x: x.strip(), f.readlines()))

with open("Movie-for-the-evening/data/users_listed.txt", "r") as f:
    users_listed = set(map(lambda x: x.strip(), f.readlines()))

#print(users_schedule, users_parsed)

#users = set()
i=0
while i <= 1000:
    i += 1
    if not users_schedule:
        break
    username = users_schedule.pop()
    print(i, username)
    users = parse_user_network(username, driver, to_parse_users=users_schedule, parsed_users=users_listed)
    users_listed.add(username)
    users_schedule.update(users)
    print(len(users_schedule), len(users_listed))

    if i % 10 == 0:
        with open("Movie-for-the-evening/data/users_schedule.txt", "w") as f:
            f.write("\n".join(str(item) for item in users_schedule))

        with open("Movie-for-the-evening/data/users_listed.txt", "w") as f:
            f.write("\n".join(str(item) for item in users_listed))
        print("Saved")