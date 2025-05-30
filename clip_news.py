import requests, urllib.parse, os, re
from html import unescape
from datetime import datetime

# ✅ HTML 태그 제거 + HTML 엔티티 디코딩
def clean_text(text):
    text = re.sub(r"<[^>]+>", "", text)   # <b>, <i> 같은 태그 제거
    return unescape(text)                 # &quot; → ", &apos; → ', etc

# 환경 변수에서 가져옴 (GitHub Secrets와 연동됨)
NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

# 뉴스 검색
def search_news(query):
    quoted_query = f'"{query}"' 
    enc_query = urllib.parse.quote(quoted_query)
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

# Notion에 추가
def add_to_notion(title, url, keyword, summary):
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
            "Summary": { "rich_text": [{ "text": { "content": summary } }] },
            "Date": { "date": { "start": datetime.today().strftime("%Y-%m-%d") } }
        }
    }
    res = requests.post(notion_url, headers=headers, json=data)
    if res.status_code == 200:
        print(f"✅ Notion 업로드 성공: {title}")
    else:
        print(f"❌ Notion 업로드 실패: {res.status_code}")
        print(res.text)

# 메인 실행
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
            title = clean_text(news["title"])
            summary = clean_text(news["description"])
            link = news["link"]
            add_to_notion(title, link, keyword, summary)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"🔥 예외 발생: {e}")
