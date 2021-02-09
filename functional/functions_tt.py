import datetime
import sqlite3
from config.settings import *
from bs4 import BeautifulSoup
import requests
from TikTokApi import TikTokApi
from datetime import datetime
import pytz
import urllib.parse as url_parser

conn = sqlite3.connect('D:\\PyCharm_projects\\SubVPbot\\db\\ttdb.db')


def save_tt_clip(**data):
    client_id = data['client']
    clip_link = data['clip_link']
    clip_id = data['clip_id']
    music_id = data['music_id']

    if 'goal' in data:
        goal = data['goal']
    else:
        goal = 0

    # TODO подумать как по другому проверять параметры на валидность
    if client_id:
        cur = conn.cursor()
        cur.execute(
            '''INSERT INTO videos(client, tt_clip_link, tt_clip_id, tt_music_id, goal, status, abusers) 
            VALUES(?,?,?,?,?,?,?)''', (client_id, clip_link, clip_id, music_id, goal, 1, str({})))
        conn.commit()

        db_clip_id = cur.execute('''SELECT MAX(order_id) FROM videos''').fetchall()[0][0]

        return db_clip_id


def update_tt_video_goal(goal):
    cur = conn.cursor()

    last_video_id = cur.execute('''SELECT MAX(order_id) FROM videos''').fetchall()[0][0]

    cur.execute('''UPDATE videos SET goal = ? WHERE order_id = ?''', (goal, last_video_id,))
    conn.commit()

    return last_video_id


def add_tt_acc_to_user(user_id, tt_acc_link):
    cur = conn.cursor()

    cur.execute('''UPDATE users SET tt_acc_link = ? WHERE id = ?''', (tt_acc_link, user_id,))
    conn.commit()

    return True


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


# TODO сделать таймаут для пропущенных видосов (допустим по 10 минут с проверкой после нажатия кнопки юзером)
def get_skipped_videos(user_id):
    cur = conn.cursor()

    videos = cur.execute('''SELECT skipped_videos FROM users WHERE id = ?''', (user_id,))
    skipped_videos_fetchall = videos.fetchall()

    skipped_clips = eval(skipped_videos_fetchall[0][0])

    return skipped_clips


def edit_promo_status(number, status):
    cur = conn.cursor()
    sql = cur.execute('''SELECT COUNT(order_id), tt_clip_id, client, goal, status, abusers
                        FROM videos WHERE order_id = ?''', (number,))

    sql_fetchall = sql.fetchall()
    print(sql_fetchall[0][0])
    print(sql_fetchall[0][1])
    print(sql_fetchall[0][2])
    print(sql_fetchall[0][3])
    print(sql_fetchall[0][4])
    print(sql_fetchall[0][5])

    if sql_fetchall[0][0] == 1 and status == 0:
        cur.execute('''UPDATE videos SET status = ? WHERE order_id = ?''', (status, number,))

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

    status = conn.execute('''SELECT status FROM videos WHERE order_id = ?''', (number,))

    if status.fetchall()[0][0] == 0:
        conn.cursor().execute('''DELETE FROM videos WHERE order_id = ?''', (number,))
        conn.commit()
    else:
        return 1


def is_user_in_db_tt(used_id):
    count_of_user_id_in_db = conn.execute(f'''SELECT COUNT(id) FROM users WHERE id = {used_id}''')
    return count_of_user_id_in_db.fetchall()[0][0]


def add_user_to_db_tt(user_id):
    conn.cursor().execute(
        '''INSERT INTO users(id, balance, alltime_clips, referals, skipped_videos, alltime_get_clips) 
            VALUES(?,?,?,?,?, ?)''', (user_id, 0, 0, str([]), str({}), 0))
    conn.commit()


def add_video_to_skipped(user_id, video_id):
    video_id = int(video_id)

    sql = conn.execute('''SELECT skipped_videos FROM users WHERE id = ?''', (user_id,))
    sql_fetchall = sql.fetchall()

    skipped_videos = sql_fetchall[0][0]
    # преобразует словарь пропущенных видосов до нормального вида
    skipped_videos = eval(skipped_videos)

    skipped_videos[video_id] = datetime.now()
    conn.cursor().execute('''UPDATE users SET skipped_videos = ? WHERE id = ?''', (str(skipped_videos), user_id))
    conn.commit()

    return True


def user_balance_tt(user_id):
    balance = conn.execute(f'''SELECT balance FROM users WHERE id = ?''', (user_id,))
    balance = balance.fetchall()[0][0]

    return balance


def get_video_stat(client_id):
    cur = conn.cursor()

    video_id_sql = cur.execute('''SELECT MAX(order_id) FROM videos WHERE client = ?''', (client_id,))
    video_id = video_id_sql.fetchall()[0][0]

    stat_list = cur.execute('''SELECT tt_clip_id FROM videos WHERE client = ? AND order_id = ?''',
                            (client_id, video_id,))

    return video_id, stat_list.fetchall()


def confirm_clip_promo(clip_number):
    try:
        clip_number = int(clip_number)

        prom_info = conn.execute('''SELECT client, goal FROM videos WHERE order_id = ?''', (clip_number,))
        prom_info = prom_info.fetchall()

        client_id = prom_info[0][0]
        # общая суммка заказа с учетом стоимости одного клипа
        clip_goal = prom_info[0][1] * CASH_MIN

        conn.execute('''UPDATE videos SET status = 1 WHERE order_id = ?''', (clip_number,))
        conn.execute('''UPDATE users SET balance = balance - ? WHERE id = ?''', (clip_goal, client_id,))
        conn.commit()

        return 1
    except Exception as e:
        return e


def tt_user_balance(user_id):
    balance = conn.execute(f'''SELECT balance FROM users WHERE id = ?''', (user_id,))
    balance = balance.fetchall()[0][0]

    return balance


def tt_account_link(user_id):
    tt_acc_link = conn.execute(f'''SELECT tt_acc_link FROM users WHERE id = ?''', (user_id,))
    tt_acc_link = tt_acc_link.fetchall()[0][0]

    return tt_acc_link


def alltime_clips(user_id):
    clips = conn.execute(f'''SELECT alltime_clips FROM users WHERE id = {user_id}''')
    clips = clips.fetchall()[0][0]

    return clips


def alltime_get_clips(user_id):
    clips = conn.execute(f'''SELECT alltime_get_clips FROM users WHERE id = {user_id}''')
    clips = clips.fetchall()[0][0]

    return clips


def get_tt_acc_name(url):
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36",
        "accept": "*/*"}

    session = requests.Session()
    data = session.get(url=url, headers=headers)

    soup = BeautifulSoup(data.text, 'html.parser')

    select_item = soup.find('div', class_='share-title-container')

    username = select_item.find('h2')

    return username.get_text()


def update_tt_acc_username(user_id):
    tt_acc_link = conn.execute(f'''SELECT tt_acc_link FROM users WHERE id = ?''', (user_id,))
    tt_acc_link = tt_acc_link.fetchall()[0][0]

    tt_acc_username = get_tt_acc_name(tt_acc_link)

    cur = conn.cursor()
    cur.execute('''UPDATE users SET tt_acc_username = ? WHERE id = ?''', (tt_acc_username, user_id))
    conn.commit()

    return True


# TODO проверка музыку
async def check_clip_for_paying(user_id, video_id):
    tt_acc_username = conn.execute(f'''SELECT tt_acc_username FROM users WHERE id = ?''', (user_id,))
    tt_acc_username = tt_acc_username.fetchall()[0][0]
    tt_acc_username = tt_acc_username.replace(' ', '')

    tt_api = await TikTokApi.get_instance()

    tt_data = await tt_api.getUser(tt_acc_username)

    tt_clips = await tt_data.get('items')

    last_3_clips = list()
    for i in range(0, 3):
        last_3_clips.append(tt_clips[i])

    for clip in last_3_clips:
        clip_created = clip.get('createTime')

        moscow_tz = pytz.timezone('Europe/Moscow')

        now = datetime.now().astimezone(moscow_tz)
        clip_created = datetime.utcfromtimestamp(clip_created).astimezone(moscow_tz)

        delta = now - clip_created
        print(delta)

        seconds = delta.total_seconds()
        hours = seconds // 3600
        print(hours)


def get_music_id_from_clip_tt(short_clip_url):
    tt_api = TikTokApi.get_instance(custom_verifyFp=TT_VERIFY_FP)

    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36",
        "accept": "*/*"}

    session = requests.Session()
    full_clip_url = session.get(url=short_clip_url, headers=headers).url

    full_clip_url_converted = url_parser.urlparse(full_clip_url).path
    clip_id = get_clip_id_from_url(full_clip_url_converted)

    clip_tt = tt_api.getTikTokById(clip_id)
    # clip_tt = tt_api.getTikTokByUrl(full_clip_url_converted)
    music_id = clip_tt.get('itemInfo').get('itemStruct').get('music').get('id')

    clip_data = {'clip_id': clip_id, 'music_id': music_id}
    print(clip_data)

    return clip_data


def get_clip_id_from_url(url):
    url_parts = url.split('/')
    url_video_tag = url_parts[1]

    if url_video_tag.startswith('@'):
        clip_id = url_parts[3]
    else:
        clip_id = url_parts[2].split('.')[0]

    return clip_id
