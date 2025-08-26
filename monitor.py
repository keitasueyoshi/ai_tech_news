import requests
from bs4 import BeautifulSoup
import hashlib
import os
import json
import re

URL = "https://ai-info-aggregator.vercel.app/"
SLACK_WEBHOOK_URL = os.environ["SLACK_WEBHOOK_URL"]
DATA_FILE = "articles.json"

def fetch_articles():
    response = requests.get(URL)
    soup = BeautifulSoup(response.text, 'html.parser')
    articles = []

    for card in soup.select("div.article-card"):
        # onclick属性からURLを抽出
        onclick = card.get("onclick", "")
        match = re.search(r"window\.open\('(.+?)'", onclick)
        if not match:
            continue
        url = match.group(1)

        # タイトルをh3から抽出
        title_tag = card.find("h3")
        if not title_tag:
            continue
        title = title_tag.get_text(strip=True)

        articles.append({"title": title, "url": url})

    return articles

def load_saved_articles():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return []

def save_articles(articles):
    with open(DATA_FILE, "w") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)

def send_slack_notification(message):
    requests.post(SLACK_WEBHOOK_URL, json={"text": message})

def main():
    current_articles = fetch_articles()
    saved_articles = load_saved_articles()

    saved_urls = {a["url"] for a in saved_articles}
    new_articles = [a for a in current_articles if a["url"] not in saved_urls]

    if new_articles:
        for article in new_articles:
            message = f"🆕 新着記事: *{article['title']}*\n🔗 {article['url']}"
            send_slack_notification(message)
            print("通知:", message)
        save_articles(current_articles)
    else:
        print("新着記事なし")

if __name__ == "__main__":
    main()
    
