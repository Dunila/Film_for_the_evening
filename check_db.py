import sqlite3

DB_PATH = "Movie-for-the-evening/data/parsed_data.db"

db = sqlite3.connect(DB_PATH)
c = db.cursor()

sql_print_all = "SELECT * FROM Ratings"
sql_groupby_user = "SELECT user, COUNT(film) AS cnt FROM Ratings GROUP BY user ORDER BY cnt DESC"
sql_groupby_film = "SELECT film, COUNT(user) AS cnt FROM Ratings GROUP BY film ORDER BY cnt DESC"
sql_how_many_ratings = "SELECT COUNT(*) FROM Ratings"
c.execute(sql_how_many_ratings)
print(c.fetchmany(15))