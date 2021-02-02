from bs4 import BeautifulSoup
import requests

URL='https://vm.tiktok.com/ZSEs84LP/'
HEADERS = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36",
    "accept": "*/*"}

session = requests.Session()
data = session.get(url=URL, headers=HEADERS)

soup = BeautifulSoup(data.text, "html.parser")

products = soup.find

select_item = soup.find('div', class_='share-title-container')

name = select_item.find('h2')

print(name.get_text())

