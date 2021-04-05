import asyncio
import datetime

import asyncpg
import requests
from TikTokApi import TikTokApi
import urllib.parse as url_parser

from config.settings import TT_VERIFY_FP
from functional.functions_tt import parse_music_id_from_url


async def run():
    params = {
        'database': 'tiktok_bot',
        'user': 'postgres',
        'password': 'postgres',
        'host': 'localhost',
    }
    conn = await asyncpg.connect(**params)

    # clips = await conn.fetch('SELECT order_id, tt_music_id, tt_music_link '
    #                          'FROM clips WHERE tt_music_id = 2 and status = 1')
    # for clip in clips:
    #     print(clip)
    #     input()

    await conn.execute('DELETE FROM clips WHERE status = 2')

    #
    # tt_api = TikTokApi.get_instance(custom_verifyFp=TT_VERIFY_FP,
    #                                 use_selenium=True)
    #
    # headers = {
    #     "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36",
    #     "accept": "*/*"}
    #
    # session = requests.Session()
    # html = session.get(url=short_clip_url, headers=headers)
    # full_clip_url = html.url
    # # print(short_clip_url)
    # # print(full_clip_url)
    #
    # full_clip_url_converted = url_parser.urlparse(full_clip_url).path
    # print(full_clip_url_converted)
    #
    # music_id = parse_music_id_from_url(full_clip_url_converted)
    #
    # music = tt_api.get_music_object_full(music_id)
    # print(music)
    #
    # async with conn.transaction():
    #     insert = await conn.fetchval('INSERT INTO tasks(user_id, order_id, tt_item_id, status, date) '
    #                                  'VALUES($1, $2, $3, $4, $5) RETURNING task_id',
    #                                  1, 2, 3, 2, datetime.datetime.now())
    #
    # print(type(insert))
    # print(insert)

    await conn.close()

loop = asyncio.get_event_loop()
loop.run_until_complete(run())
