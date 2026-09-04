import re
import json
from datetime import date

import requests
from bs4 import BeautifulSoup


SOURCES = [
    "vezuchiytakoi",
    "RafflesTelegram",
    "rozigrishi_telegrama",
    "vse_rozygryshi",
    "PrizeTech",
    "rozygrysh_live",
    "coffeesession",
    "dvigeq",
    "ra4lck73",
]

TODAY = date.today()

MONTHS = {
    "января": 1,
    "февраля": 2,
    "марта": 3,
    "апреля": 4,
    "мая": 5,
    "июня": 6,
    "июля": 7,
    "августа": 8,
    "сентября": 9,
    "октября": 10,
    "ноября": 11,
    "декабря": 12,
}

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

CATEGORY_KEYWORDS = {
    "money": [
        "₽", "руб", "рублей", "рубля", "рубль",
        "денеж", "деньг", "cash"
    ],
    "tech": [
        "iphone", "айфон", "ipad", "айпад", "macbook",
        "макбук", "airpods", "apple", "samsung",
        "xiaomi", "смартфон", "телефон", "ноутбук",
        "планшет", "телевизор", "монитор", "наушник",
        "пылесос", "фен", "стайлер", "фотоаппарат",
        "камера", "техника", "playstation", "ps5",
        "xbox", "приставка", "часы", "apple watch"
    ],
    "cosmetics": [
        "космет", "beauty", "бьюти", "парфюм",
        "духи", "аромат", "крем", "шампунь",
        "маска", "макияж", "помад", "тушь",
        "сыворот", "уход за кож", "уход за волос",
        "скраб", "гель для душа", "косметичк"
    ],
    "clothes": [
        "одежд", "плать", "костюм", "футболк",
        "рубашк", "куртк", "пальто", "джинс",
        "обув", "кроссовк", "ботинк", "сумк",
        "рюкзак", "аксессуар"
    ],
    "home": [
        "мебел", "посуда", "кухн", "постель",
        "декор", "интерьер", "светильник",
        "полотен", "подушк", "одеял",
        "товар для дома", "для дома"
    ],
    "games": [
        "игр", "gaming", "гейм", "steam",
        "playstation", "ps5", "xbox", "nintendo",
        "standoff", "roblox", "minecraft", "скин"
    ],
    "auto": [
        "автомобил", "машин", "авто", "шины",
        "колес", "запчаст", "бензин", "автосервис"
    ],
    "food": [
        "кофе", "еда", "ресторан", "кафе",
        "пицц", "бургер", "продукт", "продукты",
        "сладк", "торт", "доставк", "чай",
        "шоколад"
    ],
    "certificates": [
        "сертификат", "подарочная карта",
        "ozon", "озон", "wildberries",
        "баллы"
    ],
    "crypto": [
        "crypto", "крипт", "bitcoin", "биткоин",
        "usdt", "ton", "token", "токен",
        "nft", "airdrop"
    ],
}

CATEGORY_NAMES = {
    "money": "💰 Деньги",
    "tech": "📱 Техника",
    "cosmetics": "💄 Косметика",
    "clothes": "👗 Одежда",
    "home": "🏠 Дом",
    "games": "🎮 Игры",
    "auto": "🚗 Авто",
    "food": "🍔 Еда",
    "certificates": "🎟️ Сертификаты",
    "crypto": "🪙 Crypto",
    "other": "🎁 Другое",
}

RUSSIA_PHRASES = [
    "вся россия",
    "по россии",
    "по территории рф",
    "территории рф",
    "все города рф",
    "города рф",
    "жителей рф",
    "жители рф",
    "для жителей рф",
    "участвуют жители рф",
    "участвует вся россия",
    "доставка по рф",
    "доставка по россии",
    "отправка по рф",
    "отправляем по россии",
    "российской федерации",
]

FOREIGN_PHRASES = [
    "worldwide",
    "international",
    "usa",
    "united states",
    "canada only",
    "европа",
    "сша",
    "канада",
]

EXCLUDED_PHRASES = [
    "telegram stars",
    "telegram premium",
    "premium на месяц",
    "premium на 3 месяца",
    "premium на 6 месяцев",
    "premium на год",
    "звезд telegram",
    "звёзд telegram",
    "звезды telegram",
    "звёзды telegram",
]


def detect_category(text):
    text = text.lower()

    for category, words in CATEGORY_KEYWORDS.items():
        for word in words:
            if word in text:
                return category

    return "other"


def is_giveaway(text):
    text = text.lower()

    words = [
        "розыгрыш",
        "розыгрыша",
        "разыгрываем",
        "разыграть",
        "конкурс",
        "выиграй",
        "выиграть",
        "победитель",
        "победителей",
        "приз",
        "призы",
        "участвовать",
        "участвуй",
    ]

    return any(word in text for word in words)


def is_excluded(text):
    text = text.lower()

    return any(
        phrase in text
        for phrase in EXCLUDED_PHRASES
    )


def is_russia(text, source):
    text = text.lower()

    if any(word in text for word in FOREIGN_PHRASES):
        return False

    if any(phrase in text for phrase in RUSSIA_PHRASES):
        return True

    russian_sources = {
        "RafflesTelegram",
        "rozigrishi_telegrama",
        "vse_rozygryshi",
        "rozygrysh_live",
        "PrizeTech",
        "vezuchiytakoi",
        "dvigeq",
        "ra4lck73",
        "coffeesession",
    }

    return source in russian_sources


def parse_date(text):
    text = text.lower()

    word_dates = re.findall(
        r"(?<!\d)(\d{1,2})\s+"
        r"(января|февраля|марта|апреля|мая|июня|июля|августа|"
        r"сентября|октября|ноября|декабря)"
        r"(?:\s+(\d{4}))?",
        text
    )

    for day, month_name, year in word_dates:
        day = int(day)
        month = MONTHS[month_name]
        year = int(year) if year else TODAY.year

        try:
            result = date(year, month, day)
        except ValueError:
            continue

        if result >= TODAY:
            return result

    numeric_dates = re.findall(
        r"(?<!\d)(\d{1,2})[./-](\d{1,2})"
        r"(?:[./-](\d{4}))?(?!\d)",
        text
    )

    for day, month, year in numeric_dates:
        day = int(day)
        month = int(month)
        year = int(year) if year else TODAY.year

        try:
            result = date(year, month, day)
        except ValueError:
            continue

        if result >= TODAY:
            return result

    return None


def make_title(text):
    lines = []

    for line in text.splitlines():
        line = line.strip()

        if not line:
            continue

        if line.startswith("http"):
            continue

        lines.append(line)

        if len(" ".join(lines)) >= 120:
            break

    title = " ".join(lines)
    title = re.sub(r"\s+", " ", title)

    if len(title) > 140:
        title = title[:137] + "..."

    return title or "Розыгрыш"


def get_post_url(message):
    post_id = message.get("data-post")

    if post_id:
        return "https://t.me/" + post_id

    return None


def collect_channel(source):
    url = f"https://t.me/s/{source}"

    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=30
        )

        response.raise_for_status()

    except Exception as error:
        print(f"[ERROR] @{source}: {error}")
        return []

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    result = []

    messages = soup.select(
        ".tgme_widget_message"
    )

    for message in messages:
        text_node = message.select_one(
            ".tgme_widget_message_text"
        )

        if not text_node:
            continue

        text = text_node.get_text(
            "\n",
            strip=True
        )

        if not text:
            continue

        if not is_giveaway(text):
            continue

        if is_excluded(text):
            continue

        if not is_russia(text, source):
            continue

        end_date = parse_date(text)

        if not end_date:
            continue

        if end_date < TODAY:
            continue

        post_url = get_post_url(message)

        if not post_url:
            continue

        category = detect_category(text)

        result.append({
            "title": make_title(text),
            "category": category,
            "category_name": CATEGORY_NAMES.get(
                category,
                CATEGORY_NAMES["other"]
            ),
            "end_date": end_date.isoformat(),
            "source": "@" + source,
            "url": post_url,
        })

    return result


all_giveaways = []

for source in SOURCES:
    print(f"[INFO] Проверяем @{source}")

    items = collect_channel(source)

    print(
        f"[INFO] @{source}: найдено {len(items)}"
    )

    all_giveaways.extend(items)


unique = {}

for item in all_giveaways:
    unique[item["url"]] = item

all_giveaways = list(unique.values())

all_giveaways.sort(
    key=lambda item: item["end_date"]
)

with open(
    "giveaways.json",
    "w",
    encoding="utf-8"
) as file:
    json.dump(
        all_giveaways,
        file,
        ensure_ascii=False,
        indent=2
    )

print()
print(
    f"[DONE] Всего актуальных розыгрышей: "
    f"{len(all_giveaways)}"
)
