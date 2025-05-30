import requests, urllib.parse, os
from datetime import datetime

# 환경 변수에서 가져옴 (GitHub Secrets와 연동됨)
NAVER_CLIENT_ID = os.getenv("E15O4mV9kPm1AhHvw8Ku")
NAVER_CLIENT_SECRET = os.getenv("8vxkv586qE")
NOTION_TOKEN = os.getenv("ntn_A96799520622NYp2fQcRrf4N2UY4Rw4Ausd3l8XFDQz5rk")
NOTION_DATABASE_ID = os.getenv("203240f858be8003af3dc9f287d530cc")

# 뉴스 검색 함수
def search_news(query):
    enc_query = urllib.parse.quote(query)
    url = f"https://openapi.naver.com/v1/search/news.json?query={enc_query}&display=5&sort=date"
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
    }
    res = requests.get(url, headers=headers)
    return res.json()["items"] if res.status_code == 200 else []

# Notion에 데이터 추가
def add_to_notion(title, url, keyword):
    notion_url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    data = {
        "parent": { "database_id": NOTION_DATABASE_ID },
        "properties": {
            "Title": { "title": [{ "text": { "content": title } }] },
            "Link": { "url": url },
            "Keyword": { "rich_text": [{ "text": { "content": keyword } }] },
            "Date": { "date": { "start": datetime.today().strftime("%Y-%m-%d") } }
        }
    }
    res = requests.post(notion_url, headers=headers, json=data)
    if res.status_code != 200:
        print("❌ Notion 업로드 실패:", res.text)

# 메인 실행
if __name__ == "__main__":
    keywords = ["기업교육", "휴넷"]
    for keyword in keywords:
        news_items = search_news(keyword)
        for news in news_items:
            add_to_notion(news["title"], news["link"], keyword)
