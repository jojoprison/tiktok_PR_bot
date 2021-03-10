import asyncio
import sqlite3
from sys import platform

import asyncpg
from sshtunnel import SSHTunnelForwarder

import functional.paths as paths


class DbConnect:
    def __init__(self):
        self.os = platform
        self.connect = None

    async def get_connect(self):
        if not self.connect:
            # получаем коннект к базе через текущий луп (т.к. файл запускается первым, то луп создается тута)
            self.connect = asyncio.get_event_loop().run_until_complete(self._get_pg_tt_connect())

        print(self.connect)
        return self.connect

    async def _get_pg_tt_connect(self):
        # проверяем ось, с которой запускается бот
        if self.os.startswith('linux'):
            # траим локальный коннект, т.к. база на серваке лежит
            get_conn_task = asyncio.create_task(self.__get_pg_local_connect())
        elif self.os == 'win32':
            # траим коннект через ssh шлюз (ШЛЮХ)))
            get_conn_task = asyncio.create_task(self.__get_pg_remote_connect())
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

    async def __get_pg_remote_connect(self):
        try:
            # придумать где закрывать шлюз к серваку
            server = SSHTunnelForwarder(
                ('135.181.251.7', 22),
                ssh_username='squalordf',
                ssh_password='149367139Diez',
                remote_bind_address=('localhost', 5432))

            server.start()
            print('server connected')

            db_params = {
                'database': 'tiktok_bot',
                'user': 'postgres',
                'password': 'postgres',
                'host': 'localhost',
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
            print('connected failed')

    async def __get_pg_local_connect(self):
        params = {
            'database': 'tiktok_bot',
            'user': 'postgres',
            'password': 'postgres',
            'host': 'localhost',
        }

        print('connect local')

        # придумать где закрывать коннект к базе
        # con = await asyncpg.create_pool(**params)
        con = await asyncpg.connect(**params)

        return con

    def get_sqlite_tt_connect(self):
        sqlite3.connect(paths.get_tt_db_path())

    def get_sqlite_old_connect(self):
        sqlite3.connect(paths.get_old_db_path())


conn = asyncio.get_event_loop().run_until_complete(DbConnect()._get_pg_tt_connect())