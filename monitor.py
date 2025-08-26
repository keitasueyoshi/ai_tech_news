import asyncio
from playwright.async_api import async_playwright
import re
import os
import requests
from datetime import datetime, timedelta

URL = "https://ai-info-aggregator.vercel.app/"
SLACK_WEBHOOK_URL = os.environ["SLACK_WEBHOOK_URL"]

# 実行時の現在時刻
NOW = datetime.now()
THRESHOLD = NOW - timedelta(minutes=90)

def parse_japanese_time(text: str, now: datetime) -> datetime | None:
    match = re.match(r"(\d{1,2})月(\d{1,2})日\s+(\d{1,2}):(\d{2})", text.strip())
    if not match:
        return None
    month, day, hour, minute = map(int, match.groups())
    return datetime(now.year, month, day, hour, minute)

async def fetch_recent_articles():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(URL)
        await page.wait_for_selector("div.article-card")

        cards = await page.query_selector_all("div.article-card")
        recent_articles = []

        for card in cards:
            # URL抽出
            onclick = await card.get_attribute("onclick")
            if not onclick:
                continue
            match = re.search(r"window\.open\('(.+?)'", onclick)
            if not match:
                continue
            url = match.group(1)

            # タイトル抽出
            h3 = await card.query_selector("h3")
            title = await h3.inner_text() if h3 else "タイトルなし"

            # 日付抽出（全 span の中から探す）
            spans = await card.query_selector_all("span")
            time_text = None
            for span in spans:
                text = await span.inner_text()
                if re.match(r"\d{1,2}月\d{1,2}日\s+\d{1,2}:\d{2}", text):
                    time_text = text
                    break
            if not time_text:
                print("⚠️ 日付が見つからない記事:", title)
                continue

            published = parse_japanese_time(time_text, NOW)
            if not published:
                print(f"⚠️ 日付パース失敗: {time_text}")
                continue

            # 90分以内の記事だけ追加
            if published >= THRESHOLD:
                recent_articles.append({
                    "title": title.strip(),
                    "url": url,
                    "time": time_text
                })

        await browser.close()
        return recent_articles

def send_slack_notification(article):
    message = f"🆕 新着記事: *{article['title']}*（{article['time']} 公開）\n🔗 {article['url']}"
    response = requests.post(SLACK_WEBHOOK_URL, json={"text": message})
    if response.status_code != 200:
        print("Slack送信エラー:", response.text)

async def main():
    articles = await fetch_recent_articles()
    if articles:
        for article in articles:
            send_slack_notification(article)
            print("通知:", article["title"])
    else:
        print("新着記事なし")

if __name__ == "__main__":
    asyncio.run(main())
