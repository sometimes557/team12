import requests
from bs4 import BeautifulSoup

headers={
    "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}
URL="https://ssr1.scrape.center/"
for i in range(1,11):
    URL = f"https://ssr1.scrape.center/page/{i}"
    test_response=requests.get(URL,headers=headers)
    soup=BeautifulSoup(test_response.text,'html.parser')
    all_title=soup.find_all("h2",attrs={"class":"m-b-sm"})
    for title in all_title:
        print(title.string)
