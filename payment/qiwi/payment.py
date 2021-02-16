import sqlite3
import requests
from payment.qiwi.comment_generation import generate_comment
import datetime

conn = sqlite3.connect('D:\\PyCharm_projects\\SubVPbot\\db\\ttdb.db')

QIWI_TOKEN = '543fa02d3b1823ca6a9d536ca749dba7'
QIWI_ACCOUNT = '+79100938360'


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


def add_user_payment(user_id, money_amount):
    payment_comment = generate_comment(user_id)

    cur = conn.cursor()
    # cur.execute(f"INSERT INTO qiwi_test VALUES({user_id}, {phone}, {money_amount}, {random_code}, {0}, {None})")
    cur.execute(
        '''INSERT INTO qiwi_test(user_id, sum, comment, status, payment_date) 
        VALUES(?,?,?,?,?)''', (user_id, money_amount, payment_comment, 0, datetime.datetime.now()))
    # забираем последнюю запись об оплате из таблицы
    payment_id = cur.execute('''SELECT MAX(payment_id) FROM qiwi_test''').fetchall()[0][0]

    cur.execute(
        '''INSERT INTO user_payments(user_id, payment_id) 
        VALUES(?,?)''', (user_id, payment_id))
    conn.commit()

    return payment_comment, payment_id


def add_withdraw_funds(user_id, funds_amount):
    cur = conn.cursor()
    cur.execute(
        '''INSERT INTO withdraw_funds(user_id, funds_amount, status, date) 
        VALUES(?,?,?,?)''', (user_id, funds_amount, 0, datetime.datetime.now()))
    # забираем последнюю запись об оплате из таблицы
    conn.commit()
    # withdraw_id = cur.execute('''SELECT MAX(withdraw_id) FROM withdraw_funds''').fetchall()[0][0]

    # return withdraw_id


def get_last_withdraw():
    cur = conn.cursor()
    withdraw_id = cur.execute('''SELECT MAX(withdraw_id) FROM withdraw_funds''').fetchall()[0][0]

    return withdraw_id


def update_withdraw_status(withdraw_id, new_status):
    cur = conn.cursor()
    cur.execute('''UPDATE withdraw_funds SET status = ? WHERE withdraw_id = ?''', (new_status, withdraw_id))
    conn.commit()

    return True


def update_withdraw_location(withdraw_id, location, number):
    cur = conn.cursor()
    cur.execute('''UPDATE withdraw_funds SET location = ?, number = ? WHERE withdraw_id = ?''',
                (location, number, withdraw_id))
    conn.commit()

    return True


def view_payment(payment_id):
    cur = conn.cursor()
    result = cur.execute(
        f"SELECT * FROM qiwi_test WHERE payment_id = {payment_id}").fetchone()  # достаем данные из таблицы

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
                cur.execute('''UPDATE qiwi_test SET status = ?, phone = ? WHERE payment_id = ?''',
                            (payment_success_status, req['data'][i]['account'], payment_id,))
                conn.commit()
                return payment_success_status, payment_amount

    return current_payment_status, payment_amount


def qiwi_req():
    s = requests.Session()
    s.headers['authorization'] = 'Bearer ' + QIWI_TOKEN
    # кол-во элементов в запросе
    parameters = {'rows': '50'}

    # не больше 100 запросов в минуте, иначе бан на 5 мин.
    h = s.get('https://edge.qiwi.com/payment-history/v2/persons/' + QIWI_ACCOUNT + '/payments',
              params=parameters)

    return h.json()


if __name__ == '__main__':
    # create_table()
    # create_user_payment_table()
    create_withdraw_funds_table()
    # add_user(12)
    # check_payment(12)
