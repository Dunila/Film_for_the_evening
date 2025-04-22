from bs4 import BeautifulSoup
import time


def get_soup(url, driver):
    driver.get(url)
    html = driver.page_source
    soup = BeautifulSoup(html)
    return soup

def get_pages_cnt(soup):
    pages_list = soup.find_all("li", "paginate-page")
    if not pages_list:
        page_cnt = [1]
    try:
        page_cnt = int(pages_list[-1].text)
    except ValueError:
        print(f"Could not be converted {pages_list[-1].text}")
        page_cnt = 1
    except Exception as e:
        #print(e)
        page_cnt = 1
    return page_cnt

def find_poster_link(poster):
    element = poster.find("div")
    link = element.get("data-target-link")
    if not link:
        link = element.get("data-film-link")
    return link.split("/")[-2]

def find_poster_rating(poster):
    return int(poster.find("p", "poster-viewingdata").find("span")["class"][-1].split("-")[-1])

def find_poster_liked(poster):
    try:
        if poster.find("p", "poster-viewingdata").find("span", "like"):
            liked = 1
        else:
            liked = 0
    except Exception as e:
        liked = 0
    return liked

def find_poster_reviewed(poster):
    try:
        if poster.find("p", "poster-viewingdata").find("a", "review-micro has-icon icon-review tooltip"):
            reviewed = 1
        else:
            reviewed = 0
    except Exception as e:
        reviewed = 0
    return reviewed

def handle_poster(poster, user):
    liked = find_poster_liked(poster)
    link = find_poster_link(poster)
    reviewed = find_poster_reviewed(poster)
    rating = find_poster_rating(poster)
    return {
        "user": user,
        "liked": liked,
        "film": link,
        "reviewed": reviewed,
        "rating": rating
    }

def parse_ratings_page(soup, user):
    try:
        films = soup.find("body").find("ul", "poster-list -p70 -grid film-list clear").find_all("li")
        user_ratings = list(map(lambda x: handle_poster(x, user), films))
        return user_ratings
    except Exception as e:
        print(f"Failed parge rating page. Error: {e}")
        return []

def parse_user_ratings(username, driver, sleep=None):
    init_page = f"https://letterboxd.com/{username}/films/rated/.5-5/"
    soup = get_soup(init_page, driver=driver)
    pages_cnt = get_pages_cnt(soup)
    
    user_ratings = []
    user_ratings.extend(parse_ratings_page(soup, username))
    if pages_cnt > 1:
        for page in range(2, pages_cnt+1):
            if sleep:
                time.sleep(sleep)
            page_url = f"https://letterboxd.com/{username}/films/rated/.5-5/page/{page}/"
            soup = get_soup(page_url, driver=driver)
            user_ratings.extend(parse_ratings_page(soup, username))
    return user_ratings

def find_display_name(soup):
    try:
        display_name = soup.find("span", "displayname tooltip").text
    except Exception as e:
        display_name = None
    return {"display_name": display_name}

def find_status(soup):
    try:
        status = soup.find("span", "badge").text
    except Exception as e:
        status = "member"
    return {"status": status}

def find_tags_on_svg(soup, tag_name, tag_svg):
    try:
        tag = soup.find("div", "profile-metadata js-profile-metadata").find("path", d=tag_svg).find_next("span").text
    except Exception as e:
        print(f"exception {e}")
        tag = None
    if tag and tag_name == "geo":
        tag = [tag] if ',' not in tag else tag.split(', ')
    return {tag_name: tag}

def get_exact_stat(stat):
    try:
        whole_text, value = stat.text, stat.find("span").text
    except:
        return {}
    key = whole_text[len(value):]
    value = int(value.replace(",", ""))
    return (key, value)

def get_stats(soup):
    stats_list = soup.find_all("h4", "profile-statistic")
    stats_list = list(map(get_exact_stat, stats_list))
    stats = {key: value for key, value in stats_list}
    stats.setdefault("Films", None)
    stats.setdefault("This year", None)
    stats.setdefault("Lists", None)
    stats.setdefault("Following", None)
    stats.setdefault("Followers", None)
    return stats

def find_favorities(soup):
    try:
        favs = soup.find_all("li", "favourite-film-poster-container")
        favs = list(map(lambda x: x.find("div")["data-film-slug"], favs))
    except Exception as e:
        favs = []
    return {"favorities": favs}

geo_svg = "M4.25 2.735a.749.749 0 111.5 0 .749.749 0 11-1.5 0zM8 4.75c0-2.21-1.79-4-4-4s-4 1.79-4 4a4 4 0 003.5 3.97v6.53h1V8.72A4 4 0 008 4.75z"

def get_general_user_info(soup):
    result = {}
    result.update(find_display_name(soup))
    result.update(find_status(soup))
    result.update(find_tags_on_svg(soup, "geo", tag_svg=geo_svg))
    result.update(get_stats(soup))
    result.update(find_favorities(soup))
    return result

def parse_user_main(username, driver):
    main_page_url = f"https://letterboxd.com/{username}/"
    soup = get_soup(main_page_url, driver)
    user = {}
    user = get_general_user_info(soup)
    user.update({"username": username})
    return user

def has_next(soup):
    return True if soup.find("a", "next") else False

def parse_user_row(row):
    try:
        username = row.find("a", "avatar -a40")["href"].split("/")[1]
    except Exception as e:
        #print(f"{e} on username")
        username = None
    try:
        watched = int(row.find("a", "icon-watched").text.replace(",", ""))
    except Exception as e:
        #print(f"{e} on watched")
        watched = None
    return (username, watched)

def parse_network_page(soup):
    person_table = soup.find("table", "person-table")
    if person_table:
        rows = person_table.find("tbody").find_all("tr")
    else:
        return None
    users = list(map(parse_user_row, rows))
    users = list(filter(lambda x: x[0] and x[1] >= 50, users))
    users = [username for username, watched in users]
    return users

def parse_user_network(username, driver, to_parse_users=set(), parsed_users=set()):
    init_following_url = f"https://letterboxd.com/{username}/following/"
    init_follower_url = f"https://letterboxd.com/{username}/followers/"

    page = 1
    soup = get_soup(init_following_url, driver)
    users = parse_network_page(soup)
    while has_next(soup):
        page += 1
        following_url = f"https://letterboxd.com/{username}/following/page/{page}/"
        soup = get_soup(following_url, driver)
        page_users = parse_network_page(soup)
        page_users = list(filter(lambda x: not(x in to_parse_users or x in parsed_users), page_users))
        users.extend(page_users)

    page = 1
    soup = get_soup(init_follower_url, driver)
    users = parse_network_page(soup)
    while has_next(soup):
        page += 1
        following_url = f"https://letterboxd.com/{username}/followers/page/{page}/"
        soup = get_soup(following_url, driver)
        page_users = parse_network_page(soup)
        page_users = list(filter(lambda x: not(x in to_parse_users or x in parsed_users), page_users))
        users.extend(page_users)
    
    return set(users)
