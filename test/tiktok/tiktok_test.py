from TikTokApi import TikTokApi
api = TikTokApi.get_instance()
# If playwright doesn't work for you try to use selenium
# api = TikTokApi.get_instance(use_selenium=True)

results = 10

# Since TikTok changed their API you need to use the custom_verifyFp option.
# In your web browser you will need to go to TikTok, Log in and get the s_v_web_id value.
s_v_web_id = 'verify_kh96hlyt_z40z1rRE_jkcF_4HXZ_AABt_wf2Q6wPRX0Cq'
trending = api.trending(count=results, custom_verifyFp=s_v_web_id)

for tiktok in trending:
    # Prints the id of the tiktok
    print(tiktok['id'])

print(len(trending))
