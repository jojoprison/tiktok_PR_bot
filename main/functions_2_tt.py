import datetime
import sqlite3

conn = sqlite3.connect('ttdb.db')


def save_tt_video(**client):
    client_id = client['client']
    link = client['video_link']

    if 'goal' in client:
        goal = client['goal']
    else:
        goal = 0

    # TODO подумать как по другому проверять параметры на валидность
    if client_id:
        conn.execute(
            '''INSERT INTO videos(tt_id_video, client, goal, status, abusers) VALUES(?,?,?,?,?)''',
            (link, client_id, goal, 1, str({})))
        conn.commit()

        number = conn.execute('''SELECT MAX(number) FROM videos''').fetchall()[0][0]

        return number


def update_tt_video_goal(goal):
    cur = conn.cursor()

    last_video_id = cur.execute('''SELECT MAX(number) FROM videos''').fetchall()[0][0]

    cur.execute('''UPDATE videos SET goal = ? WHERE number = ?''', (goal, last_video_id,))
    conn.commit()

    return last_video_id


def videos_for_work(user_id):
    videos = conn.execute('''SELECT * FROM videos WHERE status = 1 AND goal >= 1''')
    videos_list = videos.fetchall()

    if len(videos_list) >= 1:
        good_videos = {}
        for video in videos_list:
            if len(eval(video[5])) < video[3] and user_id not in eval(video[5]):
                good_videos[video[1]] = video[0]
            # TODO удалять видос если больше не промится (хотя можно заносить в другую базу чтоб инфу собирать)
            # else:
            #     delete_channel_from_db(x[0])
        if len(good_videos) >= 1:
            return good_videos
        else:
            return 0
    else:
        return 0


# TODO сделать методв проверки видосов, которые не нужно показывать в продвижении (и сделать таймаут для них)
def get_skipped_videos(user_id):
    cur = conn.cursor()
    videos = cur.execute('''SELECT skipped_videos FROM users WHERE id = ?''', (user_id,))
    skipped_videos = videos.fetchall()

    return eval(skipped_videos)


def edit_promo_status(number, status):
    cur = conn.cursor()
    sql = cur.execute('''SELECT COUNT(number), tt_id_video, client, goal, status, abusers
                        FROM videos WHERE number = ?''', (number,))

    sql_fetchall = sql.fetchall()
    print(sql_fetchall[0][0])
    print(sql_fetchall[0][1])
    print(sql_fetchall[0][2])
    print(sql_fetchall[0][3])
    print(sql_fetchall[0][4])
    print(sql_fetchall[0][5])

    if sql_fetchall[0][0] == 1 and status == 0:
        cur.execute('''UPDATE videos SET status = ? WHERE number = ?''', (status, number,))

        # TODO непонятно, меняет баланс в случае если бот в канале не админ
        delta = len(eval(sql_fetchall[0][5])) - sql_fetchall[0][3]
        print(delta)
        delta = abs(delta) * 0.5
        print(delta)
        delta = round(delta, 0)
        print(delta)

        client_id = sql_fetchall[0][2]
        cur.execute('''UPDATE users SET balance = balance + ? WHERE id = ?''', (delta, client_id,))
        conn.commit()

        cur.close()

        return client_id


def delete_tt_video_from_db(number):
    number = int(number)

    status = conn.execute('''SELECT status FROM videos WHERE number = ?''', (number,))

    if status.fetchall()[0][0] == 0:
        conn.cursor().execute('''DELETE FROM videos WHERE number = ?''', (number,))
        conn.commit()
    else:
        return 1


def is_user_in_db_tt(used_id):
    count_of_user_id_in_db = conn.execute(f'''SELECT COUNT(id) FROM users WHERE id = {used_id}''')
    return count_of_user_id_in_db.fetchall()[0][0]


def add_user_to_db_tt(user_id):
    conn.cursor().execute(
        '''INSERT INTO users(id, balance, alltime_videos, referals, skipped_videos) VALUES(?,?,?,?,?)''',
        (user_id, 0, 0, str([]), str({})))
    conn.commit()


def add_video_to_skipped(user_id, video_id):
    user_id = int(user_id)

    sql = conn.execute('''SELECT skipped_videos FROM users WHERE id = ?''', (user_id,))
    sql_fetchall = sql.fetchall()

    skipped_videos = sql_fetchall[0][0]
    # преобразует словарь пропущенных видосов до нормального вида
    skipped_videos = eval(skipped_videos)

    skipped_videos[video_id] = datetime.datetime.now()
    conn.cursor().execute('''UPDATE users SET skipped_videos = ? WHERE id = ?''', (str(skipped_videos), user_id))
    conn.commit()

    return True


def user_balance_tt(user_id):
    balance = conn.execute(f'''SELECT balance FROM users WHERE id = ?''', (user_id,))
    balance = balance.fetchall()[0][0]

    return balance


def get_video_stat(client_id):
    cur = conn.cursor()

    video_id_sql = cur.execute('''SELECT MAX(number) FROM videos WHERE client = ?''', (client_id,))
    video_id = video_id_sql.fetchall()[0][0]

    stat_list = cur.execute('''SELECT tt_id_video FROM videos WHERE client = ? AND number = ?''',
                            (client_id, video_id,))

    return video_id, stat_list.fetchall()
