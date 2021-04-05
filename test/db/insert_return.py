import asyncio
import datetime

import asyncpg
from sshtunnel import SSHTunnelForwarder


async def run():
    try:
        with SSHTunnelForwarder(
                ('135.181.251.7', 22),
                ssh_username='squalordf',
                ssh_password='149367139Diez',
                remote_bind_address=('localhost', 5432)) as server:

            server.start()
            print('server connected')

            params = {
                'database': 'tiktok_bot',
                'user': 'postgres',
                'password': 'postgres',
                'host': 'localhost',
                'port': server.local_bind_port
            }

            print('run')
            conn = await asyncpg.connect(**params)

            print('got conn')

            async with conn.transaction():
                insert = await conn.fetchval('INSERT INTO tasks(user_id, order_id, tt_item_id, status, date) '
                                             'VALUES($1, $2, $3, $4, $5) RETURNING task_id',
                                             1, 2, 3, 2, datetime.datetime.now())

            print(type(insert))
            print(insert)

            await conn.close()

    except:
        print('connected failed')


loop = asyncio.get_event_loop()
loop.run_until_complete(run())
