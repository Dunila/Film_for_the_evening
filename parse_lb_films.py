from bs4 import BeautifulSoup


def get_soup(url, driver):
    driver.get(url)
    html = driver.page_source
    soup = BeautifulSoup(html)
    return soup

def get_film_name(soup):
    name = soup.find("h1", "headline-1 primaryname")
    if not name:
        return {"name": None}
    return {"name": name.text}

def get_film_year(soup):
    try:
        year = soup.find("div", "metablock").find("a")
    except Exception as e:
        return {"year": None}
    try:
        return {"year": int(year.text)}
    except ValueError:
        return {"year": None}
    except Exception as e:
        return {"year": None}
    
def get_film_description(soup):
    description = soup.find("div", "truncate")
    try:
        return {"description": description.find("p").text}
    except Exception as e:
        #print("Failed to get description: {e}")
        return {"description": None}

def get_film_ratings(soup):
    try:
        ratings = soup.find("div", "rating-histogram clear rating-histogram-exploded").find_all("a", "ir tooltip")
    except Exception as e:
        return {
            1: None, 2: None, 3: None, 4: None, 
            5: None, 6: None, 7: None, 8: None, 
            9: None, 10: None, "rating": None
        }
    ratings = list(map(lambda x: int(x.text.split("\xa0")[0].replace(",", "")), ratings))
    ratings = dict(zip(range(1, 11), ratings))
    ratings["rating"] = round(sum(key*count for key, count in ratings.items())/sum(count for count in ratings.values()), 2)
    return ratings

def get_film_interactions(soup):
    watched_cnt = soup.find("a", "has-icon icon-watched icon-16 tooltip")
    liked_cnt = soup.find("a", "has-icon icon-like icon-liked icon-16 tooltip")
    top = soup.find("a", "has-icon icon-top250 icon-16 tooltip")
    return {
        "watched": watched_cnt.text if watched_cnt else None, 
        "liked": liked_cnt.text if liked_cnt else None, 
        "top": top.text if top else None
    }

def get_film_cast(soup):
    try:
        actors = soup.find("div", "cast-list text-sluglist").find_all("a")[:10]
    except Exception as e:
        return {"actors": []}
    if not actors:
        return {"actors": []}
    return {"actors": list(map(lambda x: x.text if x else None, actors))}

def get_film_popular_reviews(soup):
    try:
        popular_reviews = soup.find("ul", "film-popular-review").find_all("li")
        return {"popular_reviews": list(map(lambda x: x.find("div", "body-text -prose js-review-body js-collapsible-text").text.strip(), popular_reviews))}
    except Exception as e:
        return {"popular_reviews": []}

def get_flim_tagline(soup):
    try:
        return {"tagline": soup.find("h4", "tagline").text.replace('\xa0', ' ')}
    except Exception as e:
        return {"tagline": None}
    
def get_film_duration(soup):
    try:
        return {"duration": int(soup.find("p", "text-link text-footer").text.replace('\xa0', ' ').strip().split()[0])}
    except ValueError:
        #print(f"Value error: {soup.find("p", "text-link text-footer").text.replace('\xa0', ' ').strip().split()[0]}")
        return {"duration": None}
    except Exception as e:
        #print("Failed get duration error: {e}")
        return {"duration": None}
    
def crew_role(persons, role):
    inrolled = list(filter(lambda x: x[0] == role, persons))
    if not inrolled:
        return {role: None}
    return {role: inrolled[0][-1]}

def get_film_crew(soup):
    try:
        crew = soup.find("div", "tabbed-content-block column-block -crewroles").find_all("div", "text-sluglist")
        crew = list(map(lambda x: (x.find("a", "text-slug")["href"].split("/")[1], x.find("a", "text-slug").text), crew))
    except Exception as e:
        #print(f"Failed getting crew error {e}")
        return {"director": None, "writer": None, "producer": None, "cinematography": None, "composer": None}
    crew_dict = {}
    for role in ["director", "writer", "producer", "cinematography", "composer"]:
        crew_dict.update(crew_role(crew, role))
    return crew_dict

def get_film_studio(soup):
    try:
        studios = soup.find("div", "tabbed-content-block column-block").find("span", string=["Studio", "Studios"]).find_next().find_all("a")
        studios = list(map(lambda x: x.text, studios))
        return {"studio": studios}
    except Exception as e:
        #print(f"Failed getting studio error {e}")
        return {"studio": []}

def get_film_country(soup):
    try:
        countries = soup.find("div", "tabbed-content-block column-block").find("span", string=["Country", "Countries"]).find_next().find_all("a")
        countries = list(map(lambda x: x.text, countries))
        return {"country": countries}
    except Exception as e:
        #print(f"Failed getting studio error {e}")
        return {"country": []}

def get_film_genres(soup):
    try:
        genres = soup.find("span", string=["Genre", "Genres"]).find_next().find_all("a")
        genres = list(map(lambda x: x.text, genres))
        return {"genres": genres}
    except Exception as e:
        #print(f"Failed getting studio error {e}")
        return {"genres": []}

def get_film_themes(soup):
    try:
        themes = soup.find("span", string=["Theme", "Themes"]).find_next().find_all("a")
        themes = list(map(lambda x: x.text, themes))
        if themes[-1] == "Show All…":
            themes.pop()
        return {"themes": themes}
    except Exception as e:
        #print(f"Failed getting studio error {e}")
        return {"themes": []}

def parse_film(soup):
    film_features = dict()
    film_features.update(get_film_name(soup))
    film_features.update(get_film_year(soup))
    film_features.update(get_film_description(soup))
    film_features.update(get_film_ratings(soup))
    film_features.update(get_film_interactions(soup))
    film_features.update(get_film_popular_reviews(soup))
    film_features.update(get_flim_tagline(soup))
    film_features.update(get_film_duration(soup))
    film_features.update(get_film_cast(soup))
    film_features.update(get_film_crew(soup))
    film_features.update(get_film_studio(soup))
    film_features.update(get_film_country(soup))
    film_features.update(get_film_genres(soup))
    film_features.update(get_film_themes(soup))
    return film_features