import sqlite3

import functional.paths as paths

conn = sqlite3.connect(paths.get_tt_db_path())


def tt_tasks_table():
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS tasks(task_id INTEGER PRIMARY KEY, user_id INTEGER, "
                "tt_clip_link TEXT, status INTEGER, date TIMESTAMP)")
    conn.commit()


# sql = conn.execute( '''DELETE FROM users''' )
# conn.commit()

# conn.execute('''CREATE TABLE videos (number integer, tt_id_video integer, goals text, goals_need integer, client integer)''')
# conn.commit()

def main_table():
    conn.execute('''CREATE TABLE users (id integer, balance integer, alltime_videos integer, referals text)''')
    conn.commit()


tt_tasks_table()

conn.close()
