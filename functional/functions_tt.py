import asyncio
import datetime
import random
import string
import urllib.parse as url_parser

import pytz
import requests
from TikTokApi import TikTokApi
from bs4 import BeautifulSoup

from config.settings import *
from db.db_connect import conn


async def save_tt_clip(**data):
    client_id = data['client']
    music_link = data['music_link']
    clip_id = data['clip_id']
    music_id = data['music_id']

    if 'goal' in data:
        goal = data['goal']
    else:
        goal = 0

    # TODO подумать как по другому проверять параметры на валидность
    if client_id:
        async with conn.transaction():
            await conn.execute('INSERT INTO clips(client, tt_music_link, tt_clip_id, tt_music_id, '
                               'goal, status, abusers, date) VALUES($1, $2, $3, $4, $5, $6, $7, $8)',
                               client_id, music_link, clip_id, music_id, goal, 2,
                               str({}), datetime.datetime.now())

        order_id = await conn.fetchval('SELECT MAX(order_id) FROM clips')

        return order_id


async def update_tt_video_goal(goal):
    last_order_id = await conn.fetchval('SELECT MAX(order_id) FROM clips')

    async with conn.transaction():
        await conn.execute('UPDATE clips SET goal = $2 WHERE order_id = $1',
                           last_order_id, goal)

    return last_order_id


async def add_tt_acc_to_user(user_id, tt_acc_link):
    async with conn.transaction():
        await conn.execute('UPDATE users SET tt_acc_link = $2 WHERE telegram_id = $1',
                           user_id, tt_acc_link)

    return True


async def clips_for_work(user_id):
    clip_list = await conn.fetch(
        'SELECT order_id, tt_music_link, goal, abusers FROM clips '
        'WHERE status = 1 AND goal >= 1'
    )

    if len(clip_list) >= 1:

        good_clips = {}

        for clip_info in clip_list:
            order_id = clip_info['order_id']
            tt_music_link = clip_info['tt_music_link']
            goal = clip_info['goal']
            abusers = clip_info['abusers']

            # число записавших меньше нужного числа и пользователь еще не записывал видос
            if len(eval(abusers)) < goal and user_id not in eval(abusers):
                # засовываю еще айди чтоб передавать его в callback_data инлайн кнопки
                good_clips[order_id] = tt_music_link
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
async def get_skipped_videos(user_id):
    skipped_clips_str = await conn.fetchval(
        'SELECT skipped_videos FROM users WHERE telegram_id = $1',
        user_id
    )

    # преобразуем строку до дикта (в базе хранится в типе text)
    skipped_clips = eval(skipped_clips_str)

    return skipped_clips


# TODO переписать под asyncpg
async def edit_promo_status(number, status):
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
        cur.execute('''UPDATE users SET balance = balance + ? WHERE telegram_id = ?''', (delta, client_id,))
        conn.commit()

        cur.close()

        return client_id


async def delete_tt_clip_from_promo_db(order_id):
    status = await conn.fetchval(
        'SELECT status FROM clips WHERE order_id = $1',
        order_id
    )

    if status != 1:
        async with conn.transaction():
            await conn.execute('DELETE FROM clips WHERE order_id = $1',
                               order_id)
        return True
    else:
        return False


async def is_user_in_db_tt(used_id):
    count_of_user_id_in_db = await conn.fetchval(
        'SELECT COUNT(telegram_id) FROM users WHERE telegram_id = $1',
        used_id
    )

    print(count_of_user_id_in_db)
    return count_of_user_id_in_db


async def add_user(new_user_id, username, **ref_father):
    if ref_father:
        ref_father = ref_father['ref_father']

        # TODO воткнуть еще дату
        async with conn.transaction():
            await conn.execute('INSERT INTO users(telegram_id, balance, alltime_clips, referrals, '
                               'skipped_videos, alltime_get_clips, ref_father, username, reg_date)'
                               'VALUES($1, $2 , $3, $4, $5, $6, $7, $8, $9)',
                               new_user_id, 0, 0, str([]), str({}), 0, ref_father, username,
                               datetime.datetime.now())

            referrals_of_ref_father = await conn.fetchval(
                'SELECT referrals FROM users WHERE telegram_id = $1',
                ref_father
            )
            referrals_of_ref_father = eval(referrals_of_ref_father)
            referrals_of_ref_father.append(new_user_id)
            referrals_of_ref_father = str(referrals_of_ref_father)

            await conn.execute('UPDATE users SET referrals = $2 WHERE telegram_id = $1',
                               ref_father, referrals_of_ref_father)

    else:
        async with conn.transaction():
            await conn.execute('INSERT INTO users(telegram_id, balance, alltime_clips, referrals, '
                               'skipped_videos, alltime_get_clips, username, reg_date)'
                               'VALUES($1, $2, $3, $4, $5, $6, $7, $8)',
                               new_user_id, 0, 0, str([]), str({}), 0, username,
                               datetime.datetime.now())


async def add_video_to_skipped(user_id, clip_id):
    skipped_videos = await conn.fetchval(
        'SELECT skipped_videos FROM users WHERE telegram_id = $1',
        user_id
    )

    # преобразует словарь пропущенных видосов до нормального вида (list я так понимаю)
    skipped_videos = eval(skipped_videos)

    skipped_videos[clip_id] = datetime.datetime.now()
    async with conn.transaction():
        await conn.execute('UPDATE users SET skipped_videos = $2 WHERE telegram_id = $1',
                           user_id, (str(skipped_videos)))


async def get_video_stat(client_id):
    last_order_id = await conn.fetchval(
        'SELECT MAX(order_id) FROM clips WHERE client = $1',
        client_id
    )

    return last_order_id


async def confirm_clip_update_status(order_id):
    try:
        prom_info = await conn.fetchrow(
            'SELECT client, goal FROM clips WHERE order_id = $1',
            order_id
        )

        client_id = prom_info[0]
        # общая суммка заказа с учетом стоимости одного клипа
        clip_goal = prom_info[1] * CASH_MIN

        async with conn.transaction():
            await conn.execute('UPDATE clips SET status = 1 WHERE order_id = $1',
                               order_id)
            await conn.execute('UPDATE users SET balance = balance - $2 WHERE telegram_id = $1',
                               client_id, clip_goal)

        return True
    except Exception as e:
        return e


async def get_user_balance_tt(user_id):
    # TODO разобраться че лучше юзать: пулл или коннект и как лучше юзать пулл
    # async with conn.acquire() as connection:
    balance = await conn.fetchval(
        'SELECT balance FROM users WHERE telegram_id = $1',
        user_id,
    )

    return balance


async def get_tt_account_link(user_id):
    tt_acc_link = await conn.fetchval(
        'SELECT tt_acc_link FROM users WHERE telegram_id = $1',
        user_id,
    )

    return tt_acc_link


async def get_alltime_clips(user_id):
    alltime_clips = await conn.fetchval(
        'SELECT alltime_clips FROM users WHERE telegram_id = $1',
        user_id,
    )

    return alltime_clips


async def alltime_get_clips(user_id):
    all_time_get_clips = await conn.fetchval(
        'SELECT alltime_get_clips FROM users WHERE telegram_id = $1',
        user_id,
    )

    return all_time_get_clips


async def get_tt_acc_name(url):
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36",
        "accept": "*/*"}

    session = requests.Session()
    data = session.get(url=url, headers=headers)

    soup = BeautifulSoup(data.text, 'html.parser')

    select_item = soup.find('div', class_='share-title-container')

    username = select_item.find('h2')

    return username.get_text()


async def update_tt_username(user_id):
    tt_acc_link = await conn.fetchval(
        'SELECT tt_acc_link FROM users WHERE telegram_id = $1',
        user_id,
    )

    tt_acc_username = await get_tt_acc_name(tt_acc_link)
    tt_acc_username = tt_acc_username.replace(' ', '')

    async with conn.transaction():
        await conn.execute('UPDATE users SET tt_acc_username = $1 WHERE telegram_id = $2',
                           tt_acc_username, user_id)

    return tt_acc_username


# TODO пока не юзается
async def update_tt_acc_username_all():
    user_tt_links = conn.execute(f'SELECT telegram_id, tt_acc_link FROM users WHERE tt_acc_username IS NULL')
    user_tt_links = user_tt_links.fetchall()

    # TODO флаг на проверку, нужен ли коммит в БД
    db_updated = False

    for user_link_tuple in user_tt_links:
        tt_link = user_link_tuple[1]

        if tt_link is not None:
            tt_username = await get_tt_acc_name(tt_link)
            print(tt_username)

            cur = conn.cursor()
            cur.execute('''UPDATE users SET tt_acc_username = ? WHERE telegram_id = ?''',
                        (tt_username, user_link_tuple[0]))

            db_updated = True

    if db_updated:
        conn.commit()


async def is_return_clip_in_queue(user_id, clip_id):
    skipped_clips = await conn.fetchval(
        'SELECT skipped_videos FROM users WHERE telegram_id = $1',
        user_id,
    )

    # преобразует словарь пропущенных видосов до нормального вида (list я так понимаю)
    skipped_clips = eval(skipped_clips)

    # удаляем клип из списка пропущенных
    del skipped_clips[clip_id]

    async with conn.transaction():
        await conn.execute('UPDATE users SET skipped_videos = $2 WHERE telegram_id = $1',
                           user_id, (str(skipped_clips)))


async def check_clip_recorded(user_id, order_id):
    tt_username = await conn.fetchval(
        'SELECT tt_acc_username FROM users WHERE telegram_id =  $1',
        user_id,
    )

    if not tt_username:
        tt_username = await update_tt_username(user_id)

    tt_username = tt_username.replace(' ', '')

    # tt_api = asyncio.get_event_loop().run_in_executor(TikTokApi.get_instance(custom_verifyFp=TT_VERIFY_FP))
    tt_api = TikTokApi.get_instance(custom_verifyFp=TT_VERIFY_FP, use_selenium=True)

    tt_data = tt_api.get_user(tt_username)
    # print(tt_data)

    tt_clips = tt_data.get('items')

    music_id = await get_music_id_from_order(order_id)

    items_to_check = list()
    for i in range(0, 3):
        clip_music_id = tt_clips[i].get('music').get('id')
        if clip_music_id == music_id:
            items_to_check.append(tt_clips[i])

    for item in items_to_check:
        clip_created = item.get('createTime')

        # moscow_tz = pytz.timezone('Europe/Moscow')

        # now = datetime.datetime.now().astimezone(moscow_tz)
        # местное время в зависимости от локали
        now = datetime.datetime.now()
        # время создания клипа с серваков тиктока -3 часа от мск
        clip_created = datetime.datetime.utcfromtimestamp(clip_created)
        # добавляем 3 часа ручками, т.к. дельта не может нормальн сосчитат часы падла такая
        clip_created = clip_created.replace(hour=clip_created.hour + 3)

        delta = now - clip_created
        print(delta)

        seconds = delta.total_seconds()
        hours = seconds // 3600
        print(hours)

        if hours <= 1:
            item_id = item.get('id')

            is_repeat = await conn.fetchval('SELECT * FROM tasks WHERE user_id = $1 and tt_item_id = $2',
                                            user_id, item_id)

            if not is_repeat:
                async with conn.transaction():
                    task_id = await conn.fetchval('INSERT INTO tasks(user_id, order_id, tt_item_id, '
                                                  'status, date) VALUES($1, $2, $3, $4, $5) '
                                                  'RETURNING task_id',
                                                  user_id, order_id, item_id, 2, datetime.datetime.now())

                return True, task_id

    return False, None


async def get_music_id_from_order(order_id):
    music_id = await conn.fetchval(
        'SELECT tt_music_id FROM clips WHERE order_id =  $1',
        order_id,
    )

    return music_id


async def get_music_id_from_url(short_clip_url):
    tt_api = TikTokApi.get_instance(custom_verifyFp=TT_VERIFY_FP,
                                    use_selenium=True)

    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36",
        "accept": "*/*"}

    session = requests.Session()
    html = session.get(url=short_clip_url, headers=headers)
    full_clip_url = html.url
    # print(short_clip_url)
    # print(full_clip_url)

    full_clip_url_converted = url_parser.urlparse(full_clip_url).path
    print(full_clip_url_converted)

    music_id = parse_music_id_from_url(full_clip_url_converted)

    music = tt_api.get_music_object_full(music_id)
    print(music)
    # clip_id = get_clip_id_from_url(full_clip_url_converted)
    # print(clip_id)

    # lolo = tt_api.trending()[0]

    # print(tt_api.get_user('squalordf'))

    # c_did = ''.join(random.choice(string.digits) for num in range(19))
    # t_data = tt_api.get_tiktok_by_id('6947566665664089346', language='ru')
    # print(t_data)
    # clip_tt = tt_api.get_tiktok_by_id('6947566665664089346')
    # clip_tt = tt_api.get_tiktok_by_id(6947566665664089346)
    # clip_tt = tt_api.get_video_by_url(short_clip_url)
    # music_id = clip_tt.get('itemInfo').get('itemStruct').get('music').get('id')

    # clip_data = {'clip_id': clip_id, 'music_id': music_id}
    # print(clip_data)

    return music_id


def get_clip_id_from_url(url):
    # video_id = re.match(r'https:\/\/m.tiktok.com\/v\/(.*)\.html',
    #                     requests.get(video_url, allow_redirects=False).headers['Location']).group(1)

    url_parts = url.split('/')
    url_video_tag = url_parts[1]

    if url_video_tag.startswith('@'):
        clip_id = url_parts[3]
    else:
        clip_id = url_parts[2].split('.')[0]

    return clip_id


def parse_music_id_from_url(url):
    print(url)
    end_part = url.split('/music/')[1]

    music_id = end_part.split('-')[-1]

    return music_id


async def deposit_money_to_balance(user_id, payment_amount):
    user_balance = await conn.fetchval(
        'SELECT balance FROM users WHERE telegram_id =  $1',
        user_id,
    )

    user_new_balance = user_balance + payment_amount

    async with conn.transaction():
        await conn.execute('UPDATE users SET balance = $2 WHERE telegram_id = $1',
                           user_id, user_new_balance)


async def get_referrals_count(user_id):
    ref_list = await conn.fetchval(
        'SELECT referrals FROM users WHERE telegram_id = $1',
        user_id,
    )

    return len(eval(ref_list))


# TODO придумать куда воткнуть либо удалить
async def pay_all_completed_tasks():
    users_to_pay = await conn.fetch(
        'SELECT user_id FROM tasks WHERE status = 2'
    )

    print(users_to_pay)


async def pay_all_completed_user_tasks(user_id):
    clip_payment_count = await conn.fetchval(
        'SELECT COUNT(*) FROM tasks WHERE user_id = $1 AND status = 2',
        user_id
    )

    async with conn.transaction():
        await conn.execute('UPDATE users SET balance = balance + $2,'
                           'alltime_clips = alltime_clips + $3 WHERE telegram_id = $1',
                           user_id, clip_payment_count * CLIP_PAYMENT, clip_payment_count)

        await conn.execute('UPDATE tasks SET status = 1 WHERE user_id = $1',
                           user_id)

    return clip_payment_count * CLIP_PAYMENT


async def pay_for_task(user_id, task_id):
    async with conn.transaction():
        await conn.execute('UPDATE users SET balance = balance + $2,'
                           'alltime_clips = alltime_clips + $3 WHERE telegram_id = $1',
                           user_id, CLIP_PAYMENT, 1)

        await conn.execute('UPDATE tasks SET status = 1 WHERE task_id = $1',
                           task_id)

    return CLIP_PAYMENT


async def get_unverified_withdraw_funds():
    result_withdraw_list = {}

    withdraw_list = await conn.fetch(
        'SELECT user_id, location, number, funds_amount FROM withdraw_funds WHERE status = 2',
    )

    for withdraw in withdraw_list:
        user_id = withdraw[0]

        tt_user_link = await conn.fetchval(
            'SELECT tt_acc_link FROM users WHERE telegram_id = $1',
            user_id
        )

        withdraw_amount = withdraw['funds_amount']
        location = withdraw['location']
        number = withdraw['number']

        if user_id in result_withdraw_list.keys():
            old_withdraw_amount = result_withdraw_list[user_id]['withdraw_amount']
            withdraw_amount += old_withdraw_amount

        withdraw_info = {'tt_user_link': tt_user_link, 'location': location, 'number': number,
                         'withdraw_amount': withdraw_amount}

        result_withdraw_list[user_id] = withdraw_info

    return result_withdraw_list


async def get_first_unverified_withdraw_funds():
    result_withdraw = {}

    first_unverified_withdraw = await conn.fetchrow(
        'SELECT user_id, location, number FROM withdraw_funds WHERE status = 2',
    )

    if first_unverified_withdraw:
        first_unverified_withdraw_used_id = first_unverified_withdraw['user_id']
        first_unverified_withdraw_location = first_unverified_withdraw['location']
        first_unverified_withdraw_number = first_unverified_withdraw['number']

        user_withdraw_info_list = await conn.fetch(
            'SELECT withdraw_id, location, number, funds_amount FROM withdraw_funds '
            'WHERE user_id = $1 and status = 2 and location = $2 and number = $3',
            first_unverified_withdraw_used_id, first_unverified_withdraw_location,
            first_unverified_withdraw_number
        )

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

            tt_user_link = await conn.fetchval(
                'SELECT tt_acc_link FROM users WHERE telegram_id = $1',
                first_unverified_withdraw_used_id
            )

            withdraw_info = {'withdraw_id_list': withdraw_id_list, 'user_id': first_unverified_withdraw_used_id,
                             'tt_user_link': tt_user_link, 'location': location,
                             'number': number, 'withdraw_amount': withdraw_amount}

            result_withdraw[first_unverified_withdraw_used_id] = withdraw_info

    return result_withdraw


async def increase_balance_tt(user_id, balance_increase):
    count = await conn.fetchval(
        'SELECT COUNT(telegram_id) FROM users WHERE telegram_id = $1',
        user_id
    )

    if count == 1:
        async with conn.transaction():
            await conn.execute('UPDATE users SET balance = balance + $2 WHERE telegram_id = $1',
                               user_id, balance_increase)

        return 'Баланс пользователя был успешно изменён.'
    else:
        return 'Пользователь не был найден в БД или количесиво записей для его id != 1.'


async def change_balance_tt(user_id, new_balance):
    async with conn.transaction():
        await conn.execute('UPDATE users SET balance = $2 WHERE telegram_id = $1',
                           user_id, new_balance)

    return True


# TODO доделать
async def submit_withdraw(withdraw_id):
    async with conn.transaction():
        await conn.execute('UPDATE withdraw_funds SET status = 1 WHERE withdraw_id = $1',
                           withdraw_id)


# Todo доделать
# def add_user_to_clip_abusers(user_id, order_id):


async def get_all_user_id():
    user_id_list = await conn.fetch(
        'SELECT telegram_id FROM users'
    )

    user_id_list = [user_id[0] for user_id in user_id_list]

    return user_id_list


async def add_user_to_clip_abusers(order_id, user_id):
    clip_abusers = await conn.fetchval('SELECT abusers FROM clips WHERE order_id = $1',
                                       order_id)

    # преобразует словарь абьюзеров до нормального вида (list я так понимаю)
    clip_abusers = eval(clip_abusers)

    clip_abusers[user_id] = datetime.datetime.now()

    async with conn.transaction():
        await conn.execute('UPDATE clips SET abusers = $2 WHERE order_id = $1',
                           order_id, str(clip_abusers))

    return True


async def update_user_alltime_get_clips(clip_order_id, add_clip_count):
    user_id = await conn.fetchval('SELECT client FROM clips WHERE order_id = $1',
                                  clip_order_id)

    async with conn.transaction():
        await conn.execute('UPDATE users SET alltime_get_clips = alltime_get_clips + $2 '
                           'WHERE telegram_id = $1', user_id, add_clip_count)

    return True


async def pay_by_referral(user_id):
    ref_father = await conn.fetchval('SELECT ref_father FROM users WHERE telegram_id = $1',
                                     user_id)

    if ref_father:
        async with conn.transaction():
            await conn.execute('UPDATE users SET balance = (balance + $2) WHERE telegram_id = $1',
                               ref_father, REF_BONUS)

        return ref_father

    return None


async def get_table_data(table_name):
    table_data = await conn.fetch(
        f'SELECT * FROM {table_name}'
    )

    if table_data:
        table_columns = [column_name for column_name in table_data[0].keys()]

        return table_data, table_columns
    else:
        return None


async def get_data_all_tables():
    table_name_list = await conn.fetch(
        "SELECT table_name FROM information_schema.tables WHERE table_schema='public'"
    )

    # table_name_list = [c for c = table_name[1] in table_data[0].keys()]
    for index, table_name_record in enumerate(table_name_list):
        table_name_list[index] = table_name_record[0]

    data = []

    for table_name in table_name_list:
        table_data = await get_table_data(table_name)

        if table_data:
            table_dict = dict()
            table_dict[table_name] = table_data

            data.append(table_dict)

    return data


# TODO переделать админский бан юзера
def ban_user(user_id, decision):
    count = conn.execute('''SELECT COUNT(id) FROM black_list WHERE id = ?''', (user_id,))
    user_id = int(user_id)
    decision = int(decision)
    if decision == 1:
        count = count.fetchall()[0][0]
        if count == 1:
            conn.execute('''DELETE FROM black_list WHERE id = ?''')
            conn.commit()
            return 'Пользователь был успешно удален из черного списка.'
        else:
            return 'Пользователь не был найден в черном списке или произошла непредвиденая ошибка'
    if decision == 0:
        count = count.fetchall()[0][0]
        if count == 0:
            conn.execute('''INSERT INTO black_list(id) VALUES(?)''', (user_id,))
            conn.commit()
            return 'Пользователь был успешно добавлен в черный список.'
        else:
            return 'Пользователь уже добавлен в черный список или произошла непредвиденная ошибка.'


async def update_telegram_username(user_id, username):
    async with conn.transaction():
        await conn.execute('UPDATE users SET username = $2 WHERE telegram_id = $1',
                           user_id, username)

    return True
