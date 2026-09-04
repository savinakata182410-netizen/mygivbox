```python
import re
import json
from datetime import datetime, date
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


# Каналы, которые ты прислала
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
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 Chrome/140 Safari/537.36"
}


# -----------------------------
# Категории
# -----------------------------

CATEGORY_KEYWORDS = {
    "money": [
        "₽", "руб", "рублей", "рубля", "рубль",
        "денеж", "деньг", "наличн", "cash"
    ],

    "tech": [
        "iphone", "айфон", "ipad", "айпад", "macbook",
        "макбук", "airpods", "эпл", "apple",
        "samsung", "xiaomi", "смартфон", "телефон",
        "ноутбук", "планшет", "телевизор", "монитор",
        "наушник", "пылесос", "робот-пылесос",
        "фен", "стайлер", "фотоаппарат", "камера",
        "электрон", "техник", "playstation", "ps5",
        "xbox", "приставк", "часы", "apple watch"
    ],

    "cosmetics": [
        "космет", "beauty", "бьюти", "парфюм",
        "духи", "аромат", "крем", "шампунь",
        "маск", "макияж", "помад", "тушь",
        "сыворот", "уход за кож", "уход за волос",
        "скраб", "гель для душа", "косметичк"
    ],

    "clothes": [
        "одежд", "плать", "костюм", "футболк",
        "рубашк", "куртк", "пальто", "джинс",
        "обув", "кроссовк", "ботинк", "сумк",
        "рюкзак", "аксессуар", "модн"
    ],

    "home": [
        "дом", "мебел", "посуда", "кухн",
        "постель", "декор", "интерьер", "светильник",
        "полотен", "подушк", "одеял", "товар для дома",
        "для дома"
    ],

    "games": [
        "игр", "gaming", "гейм", "steam",
        "playstation", "ps5", "xbox", "nintendo",
        "standoff", "roblox", "minecraft",
        "скин", "game"
    ],

    "auto": [
        "автомобил", "машин", "авто", "шины",
        "колес", "запчаст", "бензин", "автотовар",
        "автосервис", "мото"
    ],

    "food": [
        "кофе", "еда", "ресторан", "кафе",
        "пицц", "бургер", "продукт", "продукты",
        "сладк", "торт", "доставк", "чай",
        "дрип", "шоколад"
    ],

    "certificates": [
        "сертификат", "подарочная карта",
        "промокод", "ozon", "озон",
        "wildberries", "вб", "баллы"
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


# -----------------------------
# Россия
# -----------------------------

RUSSIA_PHRASES = [
    "вся россия",
    "по россии",
    "по территории рф",
    "территории рф",
    "территории российской федерации",
    "все города рф",
    "города рф",
    "жителей рф",
    "жители рф",
    "для жителей рф",
    "только для жителей рф",
    "участвуют жители рф",
    "участвует вся россия",
    "доставка по рф",
    "доставка по россии",
    "отправка по рф",
    "отправляем по россии",
    "отправим по рф",
    "российской федерации",
    "россии",
]


FOREIGN_PHRASES = [
    "worldwide",
    "international",
    "usa",
    "united states",
    "uk only",
    "canada only",
    "европа",
    "европе",
    "сша",
    "канада",
    "украина",
    "казахстан",
]


# Эти призы нам не нужны
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


# -----------------------------
# Определение категории
# -----------------------------

def detect_category(text):
    text = text.lower()

    # Сначала проверяем конкретные категории
    for category, words in CATEGORY_KEYWORDS.items():
        for word in words:
            if word in text:
                return category

    return "other"


# -----------------------------
# Проверка, что это розыгрыш
# -----------------------------

def is_giveaway(text):
    text = text.lower()

    giveaway_words = [
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
        "участвую",
    ]

    return any(word in text for word in giveaway_words)


# -----------------------------
# Россия-only
# -----------------------------

def is_russia(text, source):
    text_lower = text.lower()

    # Зарубежные признаки — сразу исключаем
    if any(word in text_lower for word in FOREIGN_PHRASES):
        return False

    # Канал "vse_rozygryshi" и остальные не считаем
    # автоматически российскими.
    # Если в публикации прямо указана РФ — пропускаем.
    if any(phrase in text_lower for phrase in RUSSIA_PHRASES):
        return True

    # Для явно российских каналов разрешаем публикации,
    # если нет признаков зарубежного розыгрыша.
    trusted_russian_sources = {
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

    return source in trusted_russian_sources


# -----------------------------
# Исключение Stars / Premium
# -----------------------------

def is_excluded(text):
    text_lower = text.lower()

    return any(
        phrase in text_lower
        for phrase in EXCLUDED_PHRASES
    )


# -----------------------------
# Дата окончания
# -----------------------------

def parse_date(text):
    text_lower = text.lower()

    # 8 сентября / 8 сентября 2026
    pattern_words = re.findall(
        r"(?<!\d)(\d{1,2})\s+"
        r"(января|февраля|марта|апреля|мая|июня|июля|августа|"
        r"сентября|октября|ноября|декабря)"
        r"(?:\s+(\d{4}))?",
        text_lower
    )

    for day, month_name, year in pattern_words:
        month = MONTHS[month_name]

        if year:
            year = int(year)
        else:
            year = TODAY.year

        try:
            result = date(year, month, int(day))

            # Если дата без года уже прошла,
            # допускаем следующий год.
            if not year or result < TODAY:
                if not year:
                    result = date(year + 1, month, int(day))

            return result

        except ValueError:
            continue

    # 08.09.2026 / 08.09
    pattern_numeric = re.findall(
        r"(?<!\d)(\d{1,2})[./-](\d{1,2})"
        r"(?:[./-](\d{4}))?(?!\d)",
        text_lower
    )

    for day, month, year in pattern_numeric:
        day = int(day)
        month = int(month)

        if year:
            year = int(year)
        else:
            year = TODAY.year

        try:
            result = date(year, month, day)

            if result >= TODAY:
                return result

        except ValueError:
            continue

    return None


# -----------------------------
# Заголовок
# -----------------------------

def make_title(text):
    lines = []

    for line in text.splitlines():
        line = line.strip()

        if not line:
            continue

        # Убираем служебные строки
        if line.startswith("http"):
            continue

        lines.append(line)

        if len(" ".join(lines)) >= 140:
            break

    title = " ".join(lines)

    title = re.sub(r"\s+", " ", title)

    if len(title) > 140:
        title = title[:137] + "..."

    return title or "Розыгрыш"


# -----------------------------
# Ссылка на пост
# -----------------------------

def get_post_url(message):
    post_id = message.get("data-post")

    if post_id:
        return "https://t.me/" + post_id

    return None


# -----------------------------
# Получение канала
# -----------------------------

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
        print(f"[ERROR] {source}: {error}")
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

        # Только розыгрыши
        if not is_giveaway(text):
            continue

        # Stars / Premium исключаем
        if is_excluded(text):
            continue

        # Только Россия
        if not is_russia(text, source):
            continue

        # Должна быть дата окончания
        end_date = parse_date(text)

        if not end_date:
            continue

        # Завершённые не показываем
        if end_date < TODAY:
            continue

        post_url = get_post_url(message)

        if not post_url:
            continue

        category = detect_category(text)

        title = make_title(text)

        result.append({
            "title": title,
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


# -----------------------------
# Сбор
# -----------------------------

all_giveaways = []

for source in SOURCES:
    print(f"[INFO] Проверяем @{source}")

    items = collect_channel(source)

    print(
        f"[INFO] @{source}: найдено {len(items)}"
    )

    all_giveaways.extend(items)


# -----------------------------
# Удаляем дубликаты
# -----------------------------

unique = {}

for item in all_giveaways:
    unique[item["url"]] = item

all_giveaways = list(unique.values())


# -----------------------------
# Сортировка
# -----------------------------

all_giveaways.sort(
    key=lambda item: item["end_date"]
)


# -----------------------------
# Сохраняем
# -----------------------------

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
```
