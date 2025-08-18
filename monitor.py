import requests
from bs4 import BeautifulSoup
import hashlib
import os

URL = "https://ai-info-aggregator.vercel.app/"
SLACK_WEBHOOK_URL = os.environ["SLACK_WEBHOOK_URL"]
HASH_FILE = "last_hash.txt"

def get_site_hash():
    response = requests.get(URL)
    soup = BeautifulSoup(response.text, 'html.parser')
    content = soup.get_text()
    return hashlib.md5(content.encode("utf-8")).hexdigest()

def send_slack_notification(message):
    requests.post(SLACK_WEBHOOK_URL, json={"text": message})

def load_last_hash():
    if os.path.exists(HASH_FILE):
        with open(HASH_FILE, "r") as f:
            return f.read().strip()
    return ""

def save_hash(hash_value):
    with open(HASH_FILE, "w") as f:
        f.write(hash_value)

def main():
    new_hash = get_site_hash()
    old_hash = load_last_hash()

    if new_hash != old_hash:
        send_slack_notification(f"🔔 Webサイトが更新されました: {URL}")
        save_hash(new_hash)
        print("更新検知 → Slack通知")
    else:
        print("変更なし")

if __name__ == "__main__":
    main()
