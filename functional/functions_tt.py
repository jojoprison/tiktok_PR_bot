import datetime
import sqlite3
import urllib.parse as url_parser

import requests
from TikTokApi import TikTokApi
from bs4 import BeautifulSoup

import paths
from config.settings import *

conn = sqlite3.connect(paths.get_tt_db_path())


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
            '''INSERT INTO clips(client, tt_clip_link, tt_clip_id, tt_music_id, goal, status, abusers, date) 
            VALUES(?,?,?,?,?,?,?,?)''',
            (client_id, clip_link, clip_id, music_id, goal, 2, str({}), datetime.datetime.now()))
        conn.commit()

        order_id = cur.execute('''SELECT MAX(order_id) FROM clips''').fetchall()[0][0]

        return order_id


def update_tt_video_goal(goal):
    cur = conn.cursor()

    last_order_id = cur.execute('''SELECT MAX(order_id) FROM clips''').fetchall()[0][0]

    cur.execute('''UPDATE clips SET goal = ? WHERE order_id = ?''', (goal, last_order_id,))
    conn.commit()

    return last_order_id


def add_tt_acc_to_user(user_id, tt_acc_link):
    cur = conn.cursor()

    cur.execute('''UPDATE users SET tt_acc_link = ? WHERE user_id = ?''', (tt_acc_link, user_id,))
    conn.commit()

    return True


async def clips_for_work(user_id):
    clip_list = conn.execute('SELECT order_id, tt_clip_link, goal, abusers FROM clips '
                             'WHERE status = 1 AND goal >= 1')
    clip_list = clip_list.fetchall()

    if len(clip_list) >= 1:

        good_clips = {}

        for clip_info in clip_list:
            order_id = clip_info[0]
            tt_clip_link = clip_info[1]
            goal = clip_info[2]
            abusers = clip_info[3]

            # число записавших меньше нужного числа и пользователь еще не записывал видос
            if len(eval(abusers)) < goal and user_id not in eval(abusers):
                # засовываю еще айди чтоб передавать его в callback_data инлайн кнопки
                good_clips[order_id] = tt_clip_link
            # TODO удалять видос если больше не промится (хотя можно заносить в другую базу чтоб инфу собирать)
            # else:
            #     delete_channel_from_db(x[0])

        if len(good_clips) >= 1:
            return good_clips
        else:
            return 0
    else:
        return 0


# TODO сделать таймаут для пропущенных видосов (допустим по 10 минут с проверкой после нажатия кнопки юзером)
def get_skipped_videos(user_id):
    cur = conn.cursor()

    videos = cur.execute('''SELECT skipped_videos FROM users WHERE user_id = ?''', (user_id,))
    skipped_videos_fetchall = videos.fetchall()

    skipped_clips = eval(skipped_videos_fetchall[0][0])

    return skipped_clips


def edit_promo_status(number, status):
    cur = conn.cursor()
    sql = cur.execute('''SELECT COUNT(order_id), tt_clip_id, client, goal, status, abusers
                        FROM clips WHERE order_id = ?''', (number,))

    sql_fetchall = sql.fetchall()
    print(sql_fetchall[0][0])
    print(sql_fetchall[0][1])
    print(sql_fetchall[0][2])
    print(sql_fetchall[0][3])
    print(sql_fetchall[0][4])
    print(sql_fetchall[0][5])

    if sql_fetchall[0][0] == 1 and status == 0:
        cur.execute('''UPDATE clips SET status = ? WHERE order_id = ?''', (status, number,))

        # TODO непонятно, меняет баланс в случае если бот в канале не админ
        delta = len(eval(sql_fetchall[0][5])) - sql_fetchall[0][3]
        print(delta)
        delta = abs(delta) * 0.5
        print(delta)
        delta = round(delta, 0)
        print(delta)

        client_id = sql_fetchall[0][2]
        cur.execute('''UPDATE users SET balance = balance + ? WHERE user_id = ?''', (delta, client_id,))
        conn.commit()

        cur.close()

        return client_id


def delete_tt_clip_from_promo_db(number):
    number = int(number)

    status = conn.execute('''SELECT status FROM clips WHERE order_id = ?''', (number,))

    if status.fetchall()[0][0] != 1:
        conn.cursor().execute('''DELETE FROM clips WHERE order_id = ?''', (number,))
        conn.commit()
        return True
    else:
        return False


def is_user_in_db_tt(used_id):
    count_of_user_id_in_db = conn.execute(f'''SELECT COUNT(user_id) FROM users WHERE user_id = {used_id}''')
    return count_of_user_id_in_db.fetchall()[0][0]


def add_user_to_db_tt(new_user_id, **ref_father):
    if ref_father:
        ref_father = ref_father['ref_father']

        cur = conn.cursor()
        cur.execute(
            '''INSERT INTO users(user_id, balance, alltime_clips, referrals, skipped_videos, alltime_get_clips, ref_father) 
                VALUES(?,?,?,?,?,?,?)''', (new_user_id, 0, 0, str([]), str({}), 0, ref_father))

        referrals_of_ref_father = conn.execute(f'''SELECT referrals FROM users WHERE user_id = ?''', (ref_father,))
        referrals_of_ref_father = eval(referrals_of_ref_father.fetchall()[0][0])
        referrals_of_ref_father.append(new_user_id)
        referrals_of_ref_father = str(referrals_of_ref_father)

        cur.execute(f'''UPDATE users SET referrals = ? WHERE user_id = ?''', (referrals_of_ref_father, ref_father,))
        cur.execute('''UPDATE users SET balance = (balance + ?) WHERE user_id = ?''', (REF_BONUS, ref_father,))

        conn.commit()
    else:
        conn.cursor().execute(
            '''INSERT INTO users(user_id, balance, alltime_clips, referrals, skipped_videos, alltime_get_clips) 
                VALUES(?,?,?,?,?,?)''', (new_user_id, 0, 0, str([]), str({}), 0))
        conn.commit()


def add_video_to_skipped(user_id, clip_id):
    clip_id = int(clip_id)

    skipped_clips_sql = conn.execute('''SELECT skipped_videos FROM users WHERE user_id = ?''', (user_id,))
    skipped_videos = skipped_clips_sql.fetchall()[0][0]

    # преобразует словарь пропущенных видосов до нормального вида (list я так понимаю)
    skipped_videos = eval(skipped_videos)

    skipped_videos[clip_id] = datetime.datetime.now()
    conn.cursor().execute('''UPDATE users SET skipped_videos = ? WHERE user_id = ?''', (str(skipped_videos), user_id))
    conn.commit()


def user_balance_tt(user_id):
    balance = conn.execute(f'''SELECT balance FROM users WHERE user_id = ?''', (user_id,))
    balance = balance.fetchall()[0][0]

    return balance


async def user_balance_tt_aio(user_id):
    async with conn.execute(f'''SELECT balance FROM users WHERE user_id = ?''', (user_id,)) as cursor:
        async for row in cursor:
            print(row)


def get_video_stat(client_id):
    cur = conn.cursor()

    last_order_id_sql = cur.execute('''SELECT MAX(order_id) FROM clips WHERE client = ?''', (client_id,))
    last_order_id = last_order_id_sql.fetchall()[0][0]

    return last_order_id


def confirm_clip_promo(order_id):
    try:
        order_id = int(order_id)

        prom_info = conn.execute('''SELECT client, goal FROM clips WHERE order_id = ?''', (order_id,))
        prom_info = prom_info.fetchall()[0]

        client_id = prom_info[0]
        # общая суммка заказа с учетом стоимости одного клипа
        clip_goal = prom_info[1] * CASH_MIN

        conn.execute('''UPDATE clips SET status = 1 WHERE order_id = ?''', (order_id,))
        conn.execute('''UPDATE users SET balance = balance - ? WHERE user_id = ?''', (clip_goal, client_id,))
        conn.commit()

        return True
    except Exception as e:
        return e


def tt_user_balance(user_id):
    balance = conn.execute(f'''SELECT balance FROM users WHERE user_id = ?''', (user_id,))
    balance = balance.fetchall()[0][0]

    return balance


def tt_account_link(user_id):
    tt_acc_link = conn.execute(f'''SELECT tt_acc_link FROM users WHERE user_id = ?''', (user_id,))
    tt_acc_link = tt_acc_link.fetchall()[0][0]

    return tt_acc_link


def alltime_clips(user_id):
    clips = conn.execute(f'''SELECT alltime_clips FROM users WHERE user_id = {user_id}''')
    clips = clips.fetchall()[0][0]

    return clips


def alltime_get_clips(user_id):
    clips = conn.execute(f'''SELECT alltime_get_clips FROM users WHERE user_id = {user_id}''')
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


def update_tt_acc_username_by_id(user_id):
    tt_acc_link = conn.execute(f'SELECT tt_acc_link FROM users WHERE user_id = ?', (user_id,))
    tt_acc_link = tt_acc_link.fetchall()[0][0]

    tt_acc_username = get_tt_acc_name(tt_acc_link)

    cur = conn.cursor()
    cur.execute('''UPDATE users SET tt_acc_username = ? WHERE user_id = ?''', (tt_acc_username, user_id))
    conn.commit()

    return True


def update_tt_acc_username_all():
    user_tt_links = conn.execute(f'SELECT user_id, tt_acc_link FROM users WHERE tt_acc_username IS NULL')
    user_tt_links = user_tt_links.fetchall()

    # TODO флаг на проверку, нужен ли коммит в БД
    db_updated = False

    for user_link_tuple in user_tt_links:
        tt_link = user_link_tuple[1]

        if tt_link is not None:
            tt_username = get_tt_acc_name(tt_link)
            print(tt_username)

            cur = conn.cursor()
            cur.execute('''UPDATE users SET tt_acc_username = ? WHERE user_id = ?''', (tt_username, user_link_tuple[0]))

            db_updated = True

    if db_updated:
        conn.commit()


def is_return_clip_in_queue(user_id, clip_id):
    clip_id = int(clip_id)

    skipped_clips_sql = conn.execute('''SELECT skipped_videos FROM users WHERE user_id = ?''', (user_id,))
    skipped_videos = skipped_clips_sql.fetchall()[0][0]

    # преобразует словарь пропущенных видосов до нормального вида (list я так понимаю)
    skipped_videos = eval(skipped_videos)

    # удаляем клип из списка пропущенных
    del skipped_videos[clip_id]

    conn.cursor().execute('''UPDATE users SET skipped_videos = ? WHERE user_id = ?''', (str(skipped_videos), user_id))
    conn.commit()


# TODO проверка существования клипа на данную музыку
async def check_clip_for_paying(user_id, video_id):
    cur = conn.cursor()
    cur.execute(
        '''INSERT INTO tasks(user_id, tt_clip_id, status, date) 
        VALUES(?,?,?,?)''', (user_id, video_id, 2, datetime.datetime.now()))
    conn.commit()

    # TODO пока заглушка на проверку из-за неработоспособности TT
    # tt_acc_username = conn.execute(f'SELECT tt_acc_username FROM users WHERE id = ?', (user_id,))
    # tt_acc_username = tt_acc_username.fetchall()[0][0]
    # tt_acc_username = tt_acc_username.replace(' ', '')

    # tt_api = await TikTokApi.get_instance()
    #
    # tt_data = await tt_api.getUser(tt_acc_username)
    #
    # tt_clips = await tt_data.get('items')
    #
    # last_3_clips = list()
    # for i in range(0, 3):
    #     last_3_clips.append(tt_clips[i])
    #
    # for clip in last_3_clips:
    #     clip_created = clip.get('createTime')
    #
    #     moscow_tz = pytz.timezone('Europe/Moscow')
    #
    #     now = datetime.datetime.now().astimezone(moscow_tz)
    #     clip_created = datetime.datetime.utcfromtimestamp(clip_created).astimezone(moscow_tz)
    #
    #     delta = now - clip_created
    #     print(delta)
    #
    #     seconds = delta.total_seconds()
    #     hours = seconds // 3600
    #     print(hours)


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


def deposit_money_to_balance(user_id, payment_amount):
    cur = conn.cursor()

    user_balance = conn.execute(f'''SELECT balance FROM users WHERE user_id = ?''', (user_id,))
    user_balance = user_balance.fetchall()[0][0]

    user_new_balance = user_balance + payment_amount

    cur.execute('''UPDATE users SET balance = ? WHERE user_id = ?''', (user_new_balance, user_id))
    conn.commit()


def get_referrals_count(user_id):
    ref_count = conn.execute(f'SELECT referrals FROM users WHERE user_id = {user_id}')

    count = eval(ref_count.fetchall()[0][0])
    count = len(count)

    return count


# TODO придумать куда воткнуть либо удалить
def pay_all_completed_tasks():
    cur = conn.cursor()

    users_to_pay = cur.execute('SELECT user_id FROM tasks WHERE status = 2')
    users_to_pay = users_to_pay.fetchall()
    print(users_to_pay)


def pay_completed_user_tasks(user_id):
    cur = conn.cursor()

    clip_payment_count = cur.execute(f'SELECT count() FROM tasks WHERE user_id = {user_id} AND status = 2')
    clip_payment_count = clip_payment_count.fetchone()[0]

    cur.execute('''UPDATE users SET balance = balance + ?,
                                    alltime_clips = alltime_clips + ? WHERE user_id = ?''',
                (clip_payment_count * CLIP_PAYMENT, clip_payment_count, user_id))
    cur.execute(f'UPDATE tasks SET status = 1 WHERE user_id = {user_id}')
    conn.commit()

    return clip_payment_count * CLIP_PAYMENT


def get_unverified_withdraw_funds():
    cur = conn.cursor()

    result_withdraw_list = {}

    withdraw_list = cur.execute('SELECT user_id, location, number, funds_amount FROM withdraw_funds WHERE status = 2')
    withdraw_list = withdraw_list.fetchall()

    for withdraw in withdraw_list:
        user_id = withdraw[0]

        tt_user_link = cur.execute(f'SELECT tt_acc_link FROM users WHERE user_id = {user_id}')
        tt_user_link = tt_user_link.fetchone()[0]

        withdraw_amount = withdraw[3]
        location = withdraw[1]
        number = withdraw[2]

        if user_id in result_withdraw_list.keys():
            old_withdraw_amount = result_withdraw_list[user_id]['withdraw_amount']
            withdraw_amount += old_withdraw_amount

        withdraw_info = {'tt_user_link': tt_user_link, 'location': location, 'number': number,
                         'withdraw_amount': withdraw_amount}

        result_withdraw_list[user_id] = withdraw_info

    return result_withdraw_list


def get_first_unverified_withdraw_funds():
    cur = conn.cursor()

    result_withdraw = {}

    first_unverified_withdraw = cur.execute('SELECT user_id, location, number FROM withdraw_funds '
                                            'WHERE status = 2')
    first_unverified_withdraw = first_unverified_withdraw.fetchone()

    if first_unverified_withdraw:
        first_unverified_withdraw_used_id = first_unverified_withdraw[0]
        first_unverified_withdraw_location = first_unverified_withdraw[1]
        first_unverified_withdraw_number = first_unverified_withdraw[2]

        user_withdraw_info_list = cur.execute(f'''SELECT withdraw_id, location, number, funds_amount
                                                FROM withdraw_funds
                                                WHERE user_id = ?
                                                and status = 2
                                                and location = ?
                                                and number = ?''', (first_unverified_withdraw_used_id,
                                                                    first_unverified_withdraw_location,
                                                                    first_unverified_withdraw_number))
        user_withdraw_info_list = user_withdraw_info_list.fetchall()

        for user_withdraw_info in user_withdraw_info_list:
            withdraw_id = user_withdraw_info[0]
            withdraw_amount = user_withdraw_info[3]
            location = user_withdraw_info[1]
            number = user_withdraw_info[2]

            if first_unverified_withdraw_used_id in result_withdraw.keys():
                old_withdraw_amount = result_withdraw[first_unverified_withdraw_used_id]['withdraw_amount']
                withdraw_amount += old_withdraw_amount

                withdraw_id_list = result_withdraw[first_unverified_withdraw_used_id]['withdraw_id_list']
                withdraw_id_list.append(withdraw_id)
            else:
                withdraw_id_list = [withdraw_id]

            tt_user_link = cur.execute(f'SELECT tt_acc_link FROM users WHERE user_id = {first_unverified_withdraw_used_id}')
            tt_user_link = tt_user_link.fetchone()[0]

            withdraw_info = {'withdraw_id_list': withdraw_id_list, 'tt_user_link': tt_user_link,
                             'location': location, 'number': number, 'withdraw_amount': withdraw_amount}

            result_withdraw[first_unverified_withdraw_used_id] = withdraw_info

    return result_withdraw


def increase_balance_tt(user_id, balance_increase):
    cur = conn.cursor()

    count = cur.execute('''SELECT COUNT(user_id) FROM users WHERE user_id = ?''', (user_id,))

    if count.fetchall()[0][0] == 1:
        user_id = int(user_id)
        balance_increase = int(balance_increase)

        cur.execute('''UPDATE users SET balance = balance + ? WHERE user_id = ?''', (balance_increase, user_id,))
        conn.commit()

        return 'Баланс пользователя был успешно изменён.'
    else:
        return 'Пользователь не был найден в БД или количесиво записей для его id != 1.'


def change_balance_tt(user_id, new_balance):
    cur = conn.cursor()
    cur.execute('''UPDATE users SET balance = ? WHERE user_id = ?''', (new_balance, user_id,))
    conn.commit()

    return True


# TODO доделать
def submit_withdraw(withdraw_id):
    cur = conn.cursor()

    cur.execute('''UPDATE withdraw_funds SET status = 1 WHERE withdraw_id = ?''', (withdraw_id,))
    conn.commit()


# Todo доделать
# def add_user_to_clip_abusers(user_id, order_id):


def get_all_user_id():
    user_id_fetchall = conn.execute('''SELECT user_id FROM users''').fetchall()

    user_id_list = [user_id[0] for user_id in user_id_fetchall]

    return user_id_list


def add_user_to_clip_abusers(order_id, user_id):
    clip_abusers_sql = conn.execute('''SELECT abusers FROM clips WHERE order_id = ?''',
                                    (order_id,))
    clip_abusers = clip_abusers_sql.fetchall()[0][0]

    # преобразует словарь абьюзеров до нормального вида (list я так понимаю)
    clip_abusers = eval(clip_abusers)

    clip_abusers[user_id] = datetime.datetime.now()

    conn.cursor().execute('''UPDATE clips SET abusers = ? WHERE order_id = ?''',
                          (str(clip_abusers), order_id))
    conn.commit()

    return True


def update_user_alltime_get_clips(clip_order_id, add_clip_count):
    client_sql = conn.execute('''SELECT client FROM clips WHERE order_id = ?''',
                              (clip_order_id,))
    user_id = client_sql.fetchall()[0][0]

    conn.cursor().execute('''UPDATE users SET alltime_get_clips = alltime_get_clips + ? 
                            WHERE user_id = ?''', (add_clip_count, user_id))
    conn.commit()

    return True
