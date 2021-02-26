import asyncio

from functional.functions_tt import *

loop = asyncio.get_event_loop()
forecast = loop.run_until_complete(user_balance_tt_aio(92957440))
loop.close()

