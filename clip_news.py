import requests, urllib.parse, os, re
from html import unescape
from datetime import datetime, timedelta


def logger(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


class NewsClipper:
    def __init__(self):
        self.naver_client_id = os.getenv("NAVER_CLIENT_ID")
        self.naver_client_secret = os.getenv("NAVER_CLIENT_SECRET")
        self.notion_token = os.getenv("NOTION_TOKEN")
        self.notion_version = "2022-06-28"

        # 키워드별 Notion DB ID
        self.keywords = {
            "휴넷": "20693bdfd3ce810da9f9ea32a6f462cf", 
            "멀티캠퍼스": "20693bdfd3ce810faecede33064bbf5b",
            "패스트캠퍼스": "20693bdfd3ce81acba7bf37a59555636",
            "클래스101": "20693bdfd3ce819cb9ead103d34bbcfd",
            "클라썸": "20693bdfd3ce81938cc0cae3a8aeed36",
            "유데미": "20693bdfd3ce815e96d2ea36980f5d4b",
            "인프런": "20693bdfd3ce815db7c7cedd727958d0",
            "터치클래스": "20693bdfd3ce812fa96ce406fc3c3a10",
            "디지털 원격훈련 아카이브": "20693bdfd3ce81af971ddb0eeded978e",
            "기업교육 AI": "20693bdfd3ce817ea5e7d3260183b623",
            "HRD 기업교육": "20693bdfd3ce813ebf22d9e276ac6bd6"
        }

    @staticmethod
    def clean_text(text):
        return unescape(re.sub(r"<[^>]+>", "", text))

    @staticmethod
    def parse_pub_date(raw):
        for fmt in ("%a, %d %b %Y %H:%M", "%a, %d %b %Y"):
            try:
                return datetime.strptime(raw[:len(fmt)], fmt).strftime("%Y-%m-%d")
            except ValueError:
                continue
        logger(f"⚠️ 날짜 파싱 실패, 오늘로 대체: {raw}")
        return datetime.today().strftime("%Y-%m-%d")

    @staticmethod
    def generate_key(title, link):
        return f"{title}|{link}"

    def fetch_existing_keys(self, db_id):
        url = f"https://api.notion.com/v1/databases/{db_id}/query"
        headers = self._notion_headers()

        two_days_ago = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")
        payload = {
            "filter": {
                "property": "Date",
                "date": { "on_or_after": two_days_ago }
            }
        }

        res = requests.post(url, headers=headers, json=payload)
        if res.status_code != 200:
            logger(f"❌ Notion DB 조회 실패: {res.status_code}")
            return set()

        results = res.json().get("results", [])
        return {
            self.generate_key(
                r["properties"]["Title"]["title"][0]["plain_text"],
                r["properties"]["Link"]["url"]
            )
            for r in results if r["properties"]["Title"]["title"] and r["properties"]["Link"]["url"]
        }

    def search_news(self, keyword):
        enc_query = urllib.parse.quote(f'"{keyword}"')
        url = f"https://openapi.naver.com/v1/search/news.json?query={enc_query}&display=30&sort=date"
        headers = {
            "X-Naver-Client-Id": self.naver_client_id,
            "X-Naver-Client-Secret": self.naver_client_secret
        }

        res = requests.get(url, headers=headers)
        logger(f"🔍 [{keyword}] 뉴스 검색: {res.status_code}")
        if res.status_code != 200:
            logger(res.text)
            return []

        return res.json().get("items", [])

    def add_to_notion(self, title, link, keyword, summary, pub_date, db_id):
        url = "https://api.notion.com/v1/pages"
        headers = self._notion_headers()
        payload = {
            "parent": { "database_id": db_id },
            "properties": {
                "Title": { "title": [{ "text": { "content": title } }] },
                "Link": { "url": link },
                "Keyword": { "rich_text": [{ "text": { "content": keyword } }] },
                "Summary": { "rich_text": [{ "text": { "content": summary } }] },
                "Date": { "date": { "start": pub_date } }
            }
        }

        res = requests.post(url, headers=headers, json=payload)
        if res.status_code == 200:
            logger(f"✅ 업로드 성공: {title}")
        else:
            logger(f"❌ 업로드 실패: {res.status_code}\n{res.text}")

    def _notion_headers(self):
        return {
            "Authorization": f"Bearer {self.notion_token}",
            "Content-Type": "application/json",
            "Notion-Version": self.notion_version
        }

    def run(self):
        logger("🚀 뉴스 클리핑 시작")
        for keyword, db_id in self.keywords.items():
            logger(f"\n🔎 [{keyword}] 처리 중")
            existing_keys = self.fetch_existing_keys(db_id)
            news_items = self.search_news(keyword)

            if not news_items:
                logger("📭 뉴스 없음")
                continue

            for news in news_items:
                title = self.clean_text(news["title"])
                summary = self.clean_text(news["description"])
                link = news["link"]
                pub_date = self.parse_pub_date(news.get("pubDate", ""))
                key = self.generate_key(title, link)

                if key in existing_keys:
                    logger(f"🚫 중복 건너뜀: {title}")
                    continue

                self.add_to_notion(title, link, keyword, summary, pub_date, db_id)


if __name__ == "__main__":
    try:
        NewsClipper().run()
    except Exception as e:
        logger(f"🔥 예외 발생: {e}")
