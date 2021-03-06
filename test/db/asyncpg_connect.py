import asyncio

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

            values = await conn.fetch(
                'SELECT * FROM users WHERE user_id = $1',
                92957440,
            )
            print(values)

            await conn.close()

    except:
        print('connected failed')


loop = asyncio.get_event_loop()
loop.run_until_complete(run())
