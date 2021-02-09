import sqlite3
from random import randint
import requests
import json

conn = sqlite3.connect('D:\\PyCharm_projects\\SubVPbot\\db\\ttdb.db')

QIWI_TOKEN = '543fa02d3b1823ca6a9d536ca749dba7'
QIWI_ACCOUNT = '+79100938360'


def create_table():
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS qiwi_test(user_id INTEGER, phone TEXT, sum INTEGER, code INTEGER)")
    conn.commit()


def add_user(user_id):
    # создаем иссуственные данные, которые хотим проверить
    phone = '+79999999999'
    sum_ = 100
    random_code = randint(100000, 999999)

    cur = conn.cursor()
    cur.execute(f"INSERT INTO qiwi_test VALUES({user_id}, {phone}, {sum_}, {random_code})")
    conn.commit()


def check_payment(user_id):
    cur = conn.cursor()
    result = cur.execute(
        f"SELECT * FROM qiwi_test WHERE user_id = {user_id}").fetchone()  # достаем данные из таблицы

    # не рекомендую так делать, но это просто для теста (простите)
    phone = result[1]
    sum_ = result[2]
    random_code = result[3]

    # получаем запрос
    req = qiwi_req()
    print(req)

    # проходимся циклом по словарю
    for i in range(len(req['data'])):
        if req['data'][i]['account'] == phone:
            if req['data'][i]['comment'] == random_code:
                if req['data'][i]['sum']['amount'] == sum_:
                    cur.execute(
                        f"DELETE FROM qiwi_test WHERE user_id = {user_id}")  # удаляем временные данные из таблицы
                # код, который сработает, если оплата прошла успешно
                print('DONE')


def qiwi_req():
    s = requests.Session()
    s.headers['authorization'] = 'Bearer ' + QIWI_TOKEN
    parameters = {'rows': '50'}

    h = s.get('https://edge.qiwi.com/payment-history/v1/persons/' + QIWI_ACCOUNT + '/payments',
              params=parameters)
    req = json.loads(h.text)

    return req


if __name__ == '__main__':
    create_table()
    # add_user(12)
    check_payment(12)
