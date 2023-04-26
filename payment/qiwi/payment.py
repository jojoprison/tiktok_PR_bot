import datetime

import requests

from db.db_connect import conn
from payment.qiwi.comment_generation import generate_comment

# мой киви токен:
# киви токен Димаса
QIWI_TOKEN = ''
# и его тел сответственно
QIWI_ACCOUNT = ''


def create_table():
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS qiwi_test(user_id INTEGER, phone TEXT, sum INTEGER, code INTEGER)")
    conn.commit()


def create_user_payment_table():
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS user_payments(user_payment_id INTEGER PRIMARY KEY, user_id INTEGER, "
                "payment_id INTEGER)")
    conn.commit()


def create_withdraw_funds_table():
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS withdraw_funds(withdraw_id INTEGER PRIMARY KEY, user_id INTEGER, "
                "funds_amount INTEGER, status INTEGER, date TIMESTAMP)")
    conn.commit()


# записываем инфу скок пользователь бабок хочет закинуть
async def add_user_payment(user_id, money_amount):
    payment_comment = generate_comment(user_id)

    async with conn.transaction():
        await conn.execute('INSERT INTO payment(user_id, sum, comment, status, payment_date) '
                           'VALUES($1, $2, $3, $4, $5)',
                           user_id, money_amount, payment_comment, 0, datetime.datetime.now())

    # забираем последнюю запись об оплате из таблицы
    payment_id = await conn.fetchval(
        'SELECT MAX(payment_id) FROM payment'
    )

    return payment_comment, payment_id


async def add_withdraw_funds(user_id, funds_amount):
    async with conn.transaction():
        await conn.execute('INSERT INTO withdraw_funds(user_id, funds_amount, status, date) '
                           'VALUES($1, $2, $3, $4)',
                           user_id, funds_amount, 0, datetime.datetime.now())

    # забираем последнюю запись об оплате из таблицы
    # withdraw_id = cur.execute('''SELECT MAX(withdraw_id) FROM withdraw_funds''').fetchall()[0][0]

    # return withdraw_id


async def get_last_withdraw():
    withdraw_id = await conn.fetchval(
        'SELECT MAX(withdraw_id) FROM withdraw_funds'
    )

    return withdraw_id


async def update_withdraw_status(withdraw_id, new_status):
    async with conn.transaction():
        await conn.execute('UPDATE withdraw_funds SET status = $2 WHERE withdraw_id = $1',
                           withdraw_id, new_status)

    funds_amount = await conn.fetchval(
        'SELECT funds_amount FROM withdraw_funds WHERE withdraw_id = $1',
        withdraw_id
    )

    return funds_amount


async def update_withdraw_location(withdraw_id, location, number):
    async with conn.transaction():
        await conn.execute('UPDATE withdraw_funds SET location = $2, number = $3 WHERE withdraw_id = $1',
                           withdraw_id, location, number)

    return True


async def view_payment(payment_id):
    # достаем данные из таблицы
    result = await conn.fetchrow(
        'SELECT * FROM payment WHERE payment_id = $1',
        payment_id
    )

    current_payment_status = result[4]
    # в случае если оплата прошла успеша и зафиксировалась в базе
    if current_payment_status == 1:
        return current_payment_status

    # не рекомендую так делать, но это просто для теста (простите)
    payment_amount = result[2]
    comment = result[3]

    # получаем запрос
    req = qiwi_req()
    # print(req)

    payment_success_status = 1

    # проходимся циклом по словарю
    for i in range(len(req['data'])):
        if req['data'][i]['comment'] == comment:
            if req['data'][i]['sum']['amount'] == payment_amount:
                async with conn.transaction():
                    await conn.execute('UPDATE payment SET status = $2, phone = $3 WHERE payment_id = $1',
                                       payment_id, payment_success_status, req['data'][i]['account'])

                return payment_success_status, payment_amount

    return current_payment_status, payment_amount


def qiwi_req():
    s = requests.Session()
    s.headers['authorization'] = 'Bearer ' + QIWI_TOKEN
    # кол-во элементов в запросе
    parameters = {'rows': '50'}

    # не больше 100 запросов в минуту, иначе бан на 5 мин.
    h = s.get('https://edge.qiwi.com/payment-history/v2/persons/' + QIWI_ACCOUNT + '/payments',
              params=parameters)

    return h.json()


if __name__ == '__main__':
    # create_table()
    # create_user_payment_table()
    # create_withdraw_funds_table()
    # add_user(12)
    # check_payment(12)
    qiwi_req()
