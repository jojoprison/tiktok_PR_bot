import asyncio
from sys import platform

import asyncpg
from sshtunnel import SSHTunnelForwarder


class DbConnect:
    def __init__(self):
        self.os = platform
        self.connect = None

    async def get_pg_tt_connect(self):
        # проверяем ось, с которой запускается бот
        if self.os.startswith('linux'):
            # траим локальный коннект, т.к. база на серваке лежит
            get_conn_task = asyncio.create_task(self._get_pg_local_connect())
        elif self.os == 'win32':
            # траим коннект через ssh шлюз (ШЛЮХ)))
            get_conn_task = asyncio.create_task(self._get_pg_remote_connect())
        else:
            # если ось не винда и не линух
            raise OSError

        try:
            conn = await get_conn_task
            return conn

        except (OSError, asyncio.TimeoutError,
                asyncpg.CannotConnectNowError,
                asyncpg.PostgresConnectionError):
            await asyncio.sleep(1)

        except asyncpg.PostgresError as postgres_error:
            return postgres_error

    async def _get_pg_remote_connect(self):
        try:
            # придумать где закрывать шлюз к серваку
            server = SSHTunnelForwarder(
                ('', 22),
                ssh_username='',
                ssh_password='',
                remote_bind_address=('localhost', 5432)
            )

            server.start()
            print('server connected')

            db_params = {
                'database': '',
                'user': '',
                'password': '',
                'host': '',
                'port': server.local_bind_port
            }

            print('run')

            # придумать где закрывать коннект к базе
            # TODO разобраться че лучше юзать пул коннектов или один коннект
            # con = await asyncpg.create_pool(**db_params)
            con = await asyncpg.connect(**db_params)

            print('got conn remote')

            return con

        except:
            print('connect failed')

    async def _get_pg_local_connect(self):
        params = {
            'database': '',
            'user': '',
            'password': '',
            'host': '',
        }

        print('connect local')

        # придумать где закрывать коннект к базе
        # con = await asyncpg.create_pool(**params)
        con = await asyncpg.connect(**params)

        return con

    # метод для теста асинк коннекта из других мест
    async def get_connect(self):
        if not self.connect:
            # получаем коннект к базе через текущий луп (т.к. файл запускается первым, то луп создается тута)
            self.connect = asyncio.get_event_loop().run_until_complete(self.get_pg_tt_connect())

        print(self.connect)
        return self.connect


# меняем токен бота в зависимости от нужды, вводим через консоль число
console_input = input('enter DB location: 0 - local, 1 - pub (FOR DEBUG)\n')

# флаг цикла корректности введенного числа
location_invalid = True
location_chooser = None

while location_invalid:
    try:
        location_chooser = int(console_input)
        location_invalid = False
    except Exception as e:
        print(e)
        print('invalid location number, enter valid location number')

if location_chooser == 0:
    # получаем коннект к базе, передаем переменную в другие методы
    conn = asyncio.get_event_loop().run_until_complete(DbConnect()._get_pg_local_connect())
    print('DEV DB location')
else:
    conn = asyncio.get_event_loop().run_until_complete(DbConnect().get_pg_tt_connect())
    print('PUB DB location')
