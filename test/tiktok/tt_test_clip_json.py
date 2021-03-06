from TikTokApi import TikTokApi
import requests
import urllib.parse as url_parser
from config.settings import TT_VERIFY_FP

tt_api = TikTokApi.get_instance(custom_verifyFp=TT_VERIFY_FP)

url = 'https://vm.tiktok.com/ZSKfUvw8/'
headers = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36",
    "accept": "*/*"}

session = requests.Session()
data = session.get(url=url, headers=headers)

new_url = data.url

link_parsed = url_parser.urlparse(new_url)
path = link_parsed.path
clip_id = path.split("/v/")[1].split('.')[0]

clip = tt_api.getTikTokById(clip_id)
info = clip.get('itemInfo')
struct = info.get('itemStruct')
music = struct.get('music')
music_id = music.get('id')
print(music_id)
