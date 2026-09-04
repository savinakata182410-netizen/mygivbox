import json
import requests
from bs4 import BeautifulSoup

URL = "https://telegramgiveaways.ru/ru"

response = requests.get(
    URL,
    timeout=30,
    headers={"User-Agent": "Mozilla/5.0"}
)
response.raise_for_status()

soup = BeautifulSoup(response.text, "html.parser")

giveaways = []

for link in soup.find_all("a", href=True):
    text = " ".join(link.stripped_strings)

    if not text:
        continue

    href = link["href"]

    if "t.me/" not in href:
        continue

    giveaways.append({
        "title": text[:150],
        "url": href
    })

# Убираем повторы
unique = {}
for item in giveaways:
    unique[item["url"]] = item

giveaways = list(unique.values())

with open("giveaways.json", "w", encoding="utf-8") as file:
    json.dump(giveaways, file, ensure_ascii=False, indent=2)

print(f"Найдено розыгрышей: {len(giveaways)}")
