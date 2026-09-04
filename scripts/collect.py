import json
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime

SOURCES = [
    {
        "name": "Worldwide Giveaways",
        "url": "https://t.me/s/wwgiveaways"
    },
    {
        "name": "Giveaway Drop",
        "url": "https://t.me/s/worldgiveawayscom"
    }
]

KEYWORDS = {
    "money": [
        "cash", "money", "paypal", "usd", "$", "€", "euro",
        "руб", "рублей", "₽", "деньги"
    ],
    "tech": [
        "iphone", "ipad", "macbook", "airpods", "smartphone",
        "phone", "laptop", "tablet", "ps5", "nintendo",
        "xbox", "computer", "gaming pc", "техника", "айфон"
    ],
    "games": [
        "steam", "game", "gaming", "playstation", "xbox",
        "nintendo", "game pc", "игр", "игров"
    ],
    "crypto": [
        "crypto", "bitcoin", "ethereum", "usdt", "ton",
        "solana", "nft", "token", "крипт"
    ]
}


def get_category(text):
    text = text.lower()

    for category, words in KEYWORDS.items():
        for word in words:
            if word in text:
                return category

    return None


def extract_date(text):
    patterns = [
        r"End Date\s*:\s*([A-Za-z]{3}\s+\d{1,2},\s+\d{4})",
        r"Deadline\s*:\s*([A-Za-z]{3,9}\s+\d{1,2},\s+\d{4})",
        r"до\s+(\d{1,2}\.\d{1,2}\.\d{4})",
        r"до\s+(\d{1,2}/\d{1,2}/\d{4})"
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            value = match.group(1)

            for fmt in (
                "%b %d, %Y",
                "%B %d, %Y",
                "%d.%m.%Y",
                "%d/%m/%Y"
            ):
                try:
                    return datetime.strptime(value, fmt).isoformat()
                except ValueError:
                    pass

    return None


giveaways = []

for source in SOURCES:
    try:
        response = requests.get(
            source["url"],
            timeout=30,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        for post in soup.select(".tgme_widget_message"):
            text = " ".join(post.stripped_strings)

            category = get_category(text)

            if category is None:
                continue

            date = extract_date(text)

            links = post.select("a[href]")
            telegram_url = None

            for link in links:
                href = link.get("href", "")

                if "t.me/" in href:
                    telegram_url = href
                    break

            if not telegram_url:
                continue

            title = text.split("------------------------------------------------------------")[0]
            title = title.strip()

            giveaways.append({
                "title": title[:180],
                "url": telegram_url,
                "category": category,
                "end_date": date,
                "source": source["name"]
            })

    except Exception as error:
        print(f"Ошибка источника {source['name']}: {error}")


# Удаляем дубликаты
unique = {}

for item in giveaways:
    unique[item["url"]] = item

giveaways = list(unique.values())


# Сначала розыгрыши с ближайшей датой окончания
giveaways.sort(
    key=lambda item: item["end_date"] or "9999-12-31"
)


with open(
    "giveaways.json",
    "w",
    encoding="utf-8"
) as file:
    json.dump(
        giveaways,
        file,
        ensure_ascii=False,
        indent=2
    )


print(f"Найдено розыгрышей: {len(giveaways)}")
