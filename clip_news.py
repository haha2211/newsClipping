import requests, urllib.parse, os, re
from html import unescape
from datetime import datetime

# ✅ HTML 태그 제거 + HTML 엔티티 디코딩
def clean_text(text):
    text = re.sub(r"<[^>]+>", "", text)   # <b>, <i> 같은 태그 제거
    return unescape(text)                 # &quot; → ", &apos; → ', etc

# 환경 변수 (공통)
NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")
NOTION_TOKEN = os.getenv("NOTION_TOKEN")

# ✅ 키워드별 Notion Database 매핑
keywords = {
    "휴넷": "20693bdfd3ce81f29fb8000cd8572d21", 
    "멀티캠퍼스": "20693bdfd3ce8121bb98000c4c345514",
    "패스트캠퍼스": "20693bdfd3ce81e1b399000c88b117d4",
    "클래스101": "20693bdfd3ce8147bbc2000cd512ef61",
    "클라썸": "20693bdfd3ce81629e36000cb6e74580",
    "유데미": "20693bdfd3ce8196b214000c82a85065",
    "인프런": "20693bdfd3ce8131a77e000cbfc2ea33",
    "터치클래스": "20693bdfd3ce8198a1a6000c6df77ec2",
    "디지털 원격훈련 아카이브": "20693bdfd3ce8130aa5e000c23c5626a",
    "기업교육 AI": "20693bdfd3ce817e91d6000ca525d59b",
    "HRD 기업교육": "20693bdfd3ce817fae58000ce6e3b730"
}

# ✅ 뉴스 검색
def search_news(query, max_results=10):
    quoted_query = f'"{query}"'
    enc_query = urllib.parse.quote(quoted_query)
    url = f"https://openapi.naver.com/v1/search/news.json?query={enc_query}&display=30&sort=date"
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
    }
    res = requests.get(url, headers=headers)
    print(f"📡 [{query}] 뉴스 요청 결과: {res.status_code}")
    if res.status_code != 200:
        print(res.text)
        return []

    items = res.json().get("items", [])

    seen = set()
    unique_items = []
    for item in items:
        key = (item["title"], item["link"])
        if key not in seen:
            seen.add(key)
            unique_items.append(item)
        if len(unique_items) == max_results:
            break

    return unique_items

# ✅ Notion 업로드
def add_to_notion(title, url, keyword, summary, pub_date, database_id):
    notion_url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    data = {
        "parent": { "database_id": database_id },
        "properties": {
            "Title": { "title": [{ "text": { "content": title } }] },
            "Link": { "url": url },
            "Keyword": { "rich_text": [{ "text": { "content": keyword } }] },
            "Summary": { "rich_text": [{ "text": { "content": summary } }] },
            "Date": { "date": { "start": pub_date } }
        }
    }
    res = requests.post(notion_url, headers=headers, json=data)
    if res.status_code == 200:
        print(f"✅ Notion 업로드 성공: {title}")
    else:
        print(f"❌ Notion 업로드 실패: {res.status_code}")
        print(res.text)

# ✅ 메인 실행
def main():
    print("🔍 클리핑 스크립트 시작")
    for keyword, db_id in keywords.items():
        print(f"\n🔎 [{keyword}] 뉴스 검색 중...")
        news_items = search_news(keyword)
        if not news_items:
            print("📭 뉴스 없음")
            continue
        for news in news_items:
            title = clean_text(news["title"])
            summary = clean_text(news["description"])
            link = news["link"]
            pub_date = news.get("pubDate", "")[:16] 
            pub_date = datetime.strptime(pub_date, "%a, %d %b %Y %H:%M").strftime("%Y-%m-%d")
            add_to_notion(title, link, keyword, summary, pub_date, db_id)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"🔥 예외 발생: {e}")
