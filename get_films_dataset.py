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


from parse_lb_films import *

with open("lb_films_url.txt", "r") as f:
    films_url = list(map(str.strip, f.readlines()))

options = webdriver.ChromeOptions()
#options.add_argument("--headless")
options.add_argument("--disable-blink-features=AutomationControlled")

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

init_point = 30_000
films_url = films_url[init_point:]
films = []
idx = init_point

for film_url in tqdm(films_url):
    time.sleep(0.25)
    soup = get_soup(film_url, driver=driver)
    if not soup:
        soup = get_soup(film_url, driver=driver)
    idx += 1
    if soup:
        film = parse_film(soup)
        film["link"] = film_url
        films.append(film)

    if idx > 0 and idx % 500 == 0:
        with open(f"lb_films/parsed_films_checkpoint{idx//500}.json", "w") as f:
            f.write(json.dumps(films, indent=4))
        films = []
        #driver.quit()
        #driver = webdriver.Chrome(service=service, options=options)
