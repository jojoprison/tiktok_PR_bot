from TikTokApi import TikTokApi

from config.settings import TT_VERIFY_FP

s_v_web_id = 'verify_klv5c5xg_nEikqRKz_up6a_4o0n_Bzh2_qD4CuJUGbEDh'

tt_api = TikTokApi.get_instance(custom_verifyFp=TT_VERIFY_FP)

url = 'https://vm.tiktok.com/ZSKfUvw8/'
headers = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36",
    "accept": "*/*"}


diz = tt_api.byUsername('squalordf')
print(tt_api.search_for_music('ViolA - телепортируюсь', 1))

print(tt_api.bySound('6889603433188296706', 1))

# diz = api.getUser('squalordf')
# print(api.getUser('ugadai5'))
# diz = api.getUser('1xboys')






# soup = BeautifulSoup(data.text, 'html.parser')

# print(soup)

# response = urllib.request.urlopen(url)
# new_url = response.geturl()
# print(new_url)

#
#
#
# select_item = soup.find('div', class_='share-title-container')
#
# username = select_item.find('h2')
#
# return username.get_text()
#




# diz = diz.get('items')
#
# last_3_clips = list()
# for i in range(0, 1):
#     last_3_clips.append(diz[i])
#
# for clip in last_3_clips:
#     clip_created = clip.get('createTime')
#
#     moscow_tz = pytz.timezone('Europe/Moscow')
#
#     now = datetime.now().astimezone(moscow_tz)
#     clip_created = datetime.utcfromtimestamp(clip_created).astimezone(moscow_tz)
#
#     delta = now - clip_created
#     print(delta)
#     seconds = delta.total_seconds()
#     hours = seconds // 3600
#     print(hours)


# if now.date() == clip_created.date():
#     print('DATES MATCH')
# else:
#     print('fuck dates')
#
# now_time = now.time().strftime("%H:%M:%S")
#
# formatted_clip = clip_created.time().strftime("%H:%M:%S")
#
# hours, minutes, seconds = formatted.split(':')
# seconds = int(seconds) + (int(minutes) * 60)
# print(seconds <= (59 * 60))


# print(api.getTikTokByUrl('https://vm.tiktok.com/ZSEpG69D/'))

# print('https://vm.tiktok.com/ZSEpv49b/')

# get_Video_By_Url

# for tiktok in diz:
# Prints the id of the tiktok
# print(tiktok)

# print(len(diz))
