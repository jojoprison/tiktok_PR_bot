from TikTokApi import TikTokApi

s_v_web_id = 'verify_kh96hlyt_z40z1rRE_jkcF_4HXZ_AABt_wf2Q6wPRX0Cq'

api = TikTokApi.get_instance()

results = 10

# diz = api.byUsername('squalordf')
print(api.search_for_music('ViolA - телепортируюсь', 1))

# print(api.bySound('6889603433188296706', 1))

# print(api.getUser('1xboys'))

# for tiktok in diz:
    # Prints the id of the tiktok
    # print(tiktok)

# print(len(diz))
