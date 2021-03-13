import asyncio

from db.db_connect import DbConnect
from functional.functions_tt import get_referrals_count


if __name__ == '__main__':
    # loop = asyncio.get_event_loop()
    # conn = loop.run_until_complete(db_connect.get_pg_tt_connect())
    # conn = asyncio.run(DbConnect().get_connect())
    # print('asdad' + str(conn))

    refs = asyncio.get_event_loop().run_until_complete(get_referrals_count(92957440))
    print(refs)
