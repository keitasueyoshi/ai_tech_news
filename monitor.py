import asyncio
from playwright.async_api import async_playwright
import re
import os
import json
import requests

URL = "https://ai-info-aggregator.vercel.app/"
DATA_FILE = "articles.json"
SLACK_WEBHOOK_URL = os.environ["SLACK_WEBHOOK_URL"]

async def fetch_articles():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(URL)

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

def load_saved_articles():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_articles(all_articles):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(all_articles, f, ensure_ascii=False, indent=2)

def send_slack_notification(message):
    requests.post(SLACK_WEBHOOK_URL, json={"text": message})

async def main():
    current_articles = await fetch_articles()
    saved_articles = load_saved_articles()

    saved_urls = {a["url"] for a in saved_articles}
    new_articles = [a for a in current_articles if a["url"] not in saved_urls]

    if new_articles:
        for article in new_articles:
            message = f"🆕 新着記事: *{article['title']}*\n🔗 {article['url']}"
            send_slack_notification(message)
            print("通知:", message)

        # ✅ 既存の通知済み記事に追加して保存する（上書きしない）
        updated_articles = saved_articles + new_articles
        save_articles(updated_articles)
    else:
        print("新着記事なし")

if __name__ == "__main__":
    asyncio.run(main())
