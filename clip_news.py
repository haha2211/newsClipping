import requests, urllib.parse, os
from datetime import datetime

# 환경 변수에서 가져옴 (GitHub Secrets와 연동됨)
NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

def search_news(query):
    enc_query = urllib.parse.quote(query)
    url = f"https://openapi.naver.com/v1/search/news.json?query={enc_query}&display=5&sort=date"
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
    }
    res = requests.get(url, headers=headers)
    print(f"📡 [{query}] 뉴스 요청 결과: {res.status_code}")
    if res.status_code != 200:
        print(res.text)
    return res.json().get("items", []) if res.status_code == 200 else []

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
    if res.status_code == 200:
        print(f"✅ Notion 업로드 성공: {title}")
    else:
        print(f"❌ Notion 업로드 실패: {res.status_code}")
        print(res.text)

def main():
    print("🔍 클리핑 스크립트 시작")
    print(f"✅ NAVER_CLIENT_ID 존재 여부: {bool(NAVER_CLIENT_ID)}")

    keywords = ["기업교육", "휴넷"]
    for keyword in keywords:
        print(f"\n🔎 [{keyword}] 뉴스 검색 중...")
        news_items = search_news(keyword)
        if not news_items:
            print("📭 뉴스 없음")
            continue
        for news in news_items:
            add_to_notion(news["title"], news["link"], keyword)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"🔥 예외 발생: {e}")
