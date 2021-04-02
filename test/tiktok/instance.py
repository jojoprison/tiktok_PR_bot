import asyncio
import sys

from TikTokApi import TikTokApi

api = TikTokApi.get_instance(use_test_endpoints=True, custom_verifyFp="verify_adjaksdjakwj", use_selenium=True)
tt_api = TikTokApi.get_instance(use_test_endpoints=True, custom_verifyFp=TT_VERIFY_FP,
                                    use_selenium=True)
# bot = commands.Bot(command_prefix='>')


if __name__ == '__main__':
    print(api.trending())
