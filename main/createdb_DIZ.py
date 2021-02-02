import sqlite3
import datetime

conn = sqlite3.connect('ttdb.db')

# sql = conn.execute( '''DELETE FROM users''' )
# conn.commit()

# conn.execute('''CREATE TABLE videos (number integer, tt_id_video integer, goals text, goals_need integer, client integer)''')
# conn.commit()

conn.execute('''CREATE TABLE users (id integer, balance integer, alltime_videos integer, referals text)''')
conn.commit()

# for x in sql:
# print(x)

# TABLE other(last_check)

# CREATE TABLE black_list (id integer)
