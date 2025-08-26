import asyncio
from playwright.async_api import async_playwright
import re
import os
import json
import requests

URL = "https://ai-info-aggregator.vercel.app/"
DATA_FILE = "notified_urls.json"
SLACK_WEBHOOK_URL = os.environ["SLACK_WEBHOOK_URL"]

async def fetch_articles():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(URL)
        await page.wait_for_selector("div.article-card")  # JSレンダリング待ち

        cards = await page.query_selector_all("div.article-card")

        articles = []
        for card in cards:
            onclick = await card.get_attribute("onclick")
            if not onclick:
                continue
            match = re.search(r"window\.open\('(.+?)'", onclick)
            if not match:
                continue
            url = match.group(1)

            h3 = await card.query_selector("h3")
            title = await h3.inner_text() if h3 else "タイトルなし"

            articles.append({"title": title.strip(), "url": url})

        await browser.close()
        return articles

def load_notified_urls():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()

def save_notified_urls(urls):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(list(urls), f, ensure_ascii=False, indent=2)

def send_slack_notification(message):
    requests.post(SLACK_WEBHOOK_URL, json={"text": message})

async def main():
    articles = await fetch_articles()
    notified_urls = load_notified_urls()

    new_articles = [a for a in articles if a["url"] not in notified_urls]

    if new_articles:
        for article in new_articles:
            message = f"🆕 新着記事: *{article['title']}*\n🔗 {article['url']}"
            send_slack_notification(message)
            print("通知:", message)
    else:
        print("新着記事なし")

    # 取得したすべてのURLを上書き保存
    notified_urls = set(a["url"] for a in articles)
    save_notified_urls(notified_urls)

if __name__ == "__main__":
    asyncio.run(main())
