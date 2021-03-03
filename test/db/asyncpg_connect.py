import asyncio
import asyncpg


async def run():
    conn = await asyncpg.connect(user='postgres', password='postgres',
                                 database='postgres', host='127.0.0.1')
    values = await conn.fetch(
        'SELECT * FROM users WHERE user_id = $1',
        92957440,
    )
    print(values)

    await conn.close()

loop = asyncio.get_event_loop()
loop.run_until_complete(run())
