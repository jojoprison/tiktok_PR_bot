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
                await conn.execute('DELETE FROM clips WHERE status = 2')

            await conn.close()

    except:
        print('connected failed')


loop = asyncio.get_event_loop()
loop.run_until_complete(run())
