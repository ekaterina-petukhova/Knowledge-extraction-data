import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import time


INPUT_FILE = "museum_exhibitions_combined.csv"
OUTPUT_FILE = "museum_exhibitions_enriched.csv"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


foreign_words = [
    "франция", "француз", "париж", "fondation louis vuitton", "louis vuitton",
    "лувр", "louvre", "помпиду", "pompidou",
    "италия", "итальян", "уффици", "uffizi", "рим", "венеция",
    "германия", "берлин", "немец",
    "британия", "лондон", "tate", "british museum", "national gallery",
    "сша", "америк", "metropolitan", "moma", "guggenheim", "new york",
    "китай", "китайск", "пекин",
    "япония", "япон", "токио",
    "индия", "иран", "оман", "национальный музей омана",
    "центральная азия", "узбекистан", "казахстан"
]

collab_words = [
    "совместно с",
    "в сотрудничестве с",
    "при участии",
    "при поддержке",
    "совместный проект",
    "партнер",
    "партнёр",
    "организована совместно",
    "подготовлена совместно",
    "из собрания",
    "из коллекции",
    "предоставлены",
    "предоставил",
    "предоставила",
    "loan",
    "loans",
    "lent by",
    "in collaboration with"
]


def clean_text(text):
    if pd.isna(text):
        return ""
    text = str(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def get_page_description(url):
    if pd.isna(url) or not str(url).startswith("http"):
        return ""

    try:
        response = requests.get(url, headers=HEADERS, timeout=20)

        if response.status_code != 200:
            print("Не открылась страница:", response.status_code, url)
            return ""

        soup = BeautifulSoup(response.text, "html.parser")

        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()

        text = soup.get_text(" ", strip=True)
        text = clean_text(text)

        return text[:5000]

    except Exception as e:
        print("Ошибка:", url, e)
        return ""


def has_foreign_word(text):
    text = text.lower()
    return any(word in text for word in foreign_words)


def has_collab_word(text):
    text = text.lower()
    return any(word in text for word in collab_words)


def split_sentences(text):
    return re.split(r"(?<=[.!?])\s+", text)


def extract_collaboration_context(text):
    text = clean_text(text)
    sentences = split_sentences(text)

    contexts = []

    for sentence in sentences:
        s = sentence.lower()

        if has_foreign_word(s) and has_collab_word(s):
            contexts.append(sentence.strip())

    return " | ".join(contexts[:3])


def detect_foreign_collaboration(row):
    full_text = (
        clean_text(row.get("title", "")) + " " +
        clean_text(row.get("description", ""))
    ).lower()

    if has_foreign_word(full_text) and has_collab_word(full_text):
        return "yes"

    return "no"


def detect_country_or_region(text):
    text = text.lower()

    countries = []

    country_dict = {
        "France": ["франция", "француз", "париж", "louis vuitton", "лувр", "louvre", "помпиду", "pompidou"],
        "Italy": ["италия", "итальян", "уффици", "uffizi", "рим", "венеция"],
        "Germany": ["германия", "немец", "берлин"],
        "United Kingdom": ["британия", "британ", "англи", "лондон", "tate", "british museum"],
        "USA": ["сша", "америк", "metropolitan", "moma", "guggenheim", "new york"],
        "China": ["китай", "китайск", "пекин"],
        "Japan": ["япония", "япон", "токио"],
        "India": ["индия", "индий"],
        "Iran": ["иран", "персия", "персид"],
        "Oman": ["оман", "национальный музей омана"],
        "Central Asia": ["центральная азия", "узбекистан", "казахстан", "киргиз", "таджикистан", "туркменистан"]
    }

    for country, keywords in country_dict.items():
        if any(keyword in text for keyword in keywords):
            countries.append(country)

    return "; ".join(countries)


def extract_possible_partner(context):
    if not context:
        return ""

    patterns = [
        r"совместно с ([^.;|]+)",
        r"в сотрудничестве с ([^.;|]+)",
        r"при участии ([^.;|]+)",
        r"при поддержке ([^.;|]+)",
        r"из собрания ([^.;|]+)",
        r"из коллекции ([^.;|]+)",
        r"предоставлены ([^.;|]+)",
        r"предоставил[аи]? ([^.;|]+)"
    ]

    for pattern in patterns:
        match = re.search(pattern, context, re.IGNORECASE)
        if match:
            return clean_text(match.group(1))[:250]

    return ""


df = pd.read_csv(INPUT_FILE)

if "description" not in df.columns:
    df["description"] = ""

for i, row in df.iterrows():
    if not clean_text(row.get("description", "")):
        url = row.get("url", "")
        print(f"{i + 1}/{len(df)} Парсю описание:", url)
        df.at[i, "description"] = get_page_description(url)
        time.sleep(0.7)

df["foreign_collaboration"] = df.apply(detect_foreign_collaboration, axis=1)

df["collaboration_context"] = df.apply(
    lambda row: extract_collaboration_context(
        clean_text(row.get("title", "")) + " " + clean_text(row.get("description", ""))
    ),
    axis=1
)

df["country_or_region"] = df["collaboration_context"].apply(detect_country_or_region)
df["foreign_partner"] = df["collaboration_context"].apply(extract_possible_partner)

df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")

print("Готово.")
print("Создан файл:", OUTPUT_FILE)
print(df["foreign_collaboration"].value_counts())

print("\nНайденные foreign collaborations:")
cols = ["museum", "title", "year", "foreign_collaboration", "country_or_region", "foreign_partner", "collaboration_context", "url"]
existing_cols = [c for c in cols if c in df.columns]

print(df[df["foreign_collaboration"] == "yes"][existing_cols].head(30).to_string())