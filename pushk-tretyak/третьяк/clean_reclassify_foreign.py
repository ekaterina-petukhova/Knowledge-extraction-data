import pandas as pd
import re


INPUT_FILE = "final_exhibitions_labeled.csv"
OUTPUT_FILE = "final_exhibitions_clean_reclassified.csv"


df = pd.read_csv(INPUT_FILE)

def clean_text(x):
    if pd.isna(x):
        return ""
    x = str(x)
    x = re.sub(r"\s+", " ", x)
    return x.strip()


def remove_site_noise(text):

    text = clean_text(text)

    noise_patterns = [
        r"РУС\s+РУС\s+ENG\s+ITA\s+GER\s+FRA\s+ESP\s+中文\s+日本",
        r"РУС\s+ENG\s+ITA\s+GER\s+FRA\s+ESP\s+中文\s+日本",
        r"ENG\s+ITA\s+GER\s+FRA\s+ESP\s+中文\s+日本",
        r"OK\s+VKontakte\s+TripAdviser\s+Telegram\s+Яндекс\s+Цзен\s+RuTube\s+Max",
        r"Обычная версия\s+Контрастная версия\s+Крупный шрифт.*?скрыть картинки",
        r"Рекомендации для посетителей с электронными билетами",
        r"поиск найти Билеты",
        r"Музей Посетителям Выставки и события Коллекции Медиа Наука и образование",
        r"Поделиться Музей в соцсетях.*?Max",
        r"© Государственный музей изобразительных искусств.*",
    ]

    for pattern in noise_patterns:
        text = re.sub(pattern, " ", text, flags=re.IGNORECASE)

    text = re.sub(r"\s+", " ", text)
    return text.strip()


def get_analysis_text(row):
    title = clean_text(row.get("title", ""))
    description = remove_site_noise(row.get("description", ""))

    markers = [
        "представляет выставку",
        "выставка посвящена",
        "экспозиция посвящена",
        "проект посвящен",
        "проект посвящён",
        "подробнее о выставке",
        "подробнее о проекте",
    ]

    desc_lower = description.lower()
    start_positions = [desc_lower.find(m) for m in markers if desc_lower.find(m) != -1]

    if start_positions:
        start = min(start_positions)
        description = description[start:start + 3500]
    else:
        description = description[:3500]

    return (title + ". " + description).lower()

RUSSIAN_INSTITUTION_WORDS = [
    "третьяков", "пушкин", "гмии", "российск", "русск", "москва", "московск",
    "санкт-петербург", "петербург", "эрмитаж", "русский музей", "гараж",
    "винзавод", "манеж", "музей москвы", "мультимедиа арт музей",
    "мамм", "музей архитектуры", "бахрушин", "музей востока",
    "музей современного искусства", "ммома", "рггу", "росизо",
    "министерство культуры российской федерации", "минкультуры",
    "государственный музей", "государственная галерея",
]

FOREIGN_PARTNER_KEYWORDS = {
    "France": [
        "fondation louis vuitton", "louis vuitton", "лувр", "louvre",
        "центр помпиду", "pompidou", "музей орсе", "orsay",
        "париж", "франция", "французск"
    ],
    "Italy": [
        "уффици", "uffizi", "ватикан", "рим", "венеция", "флоренция",
        "италия", "итальянск"
    ],
    "Germany": [
        "берлин", "германия", "немецк", "дрезден", "мюнхен",
        "staatliche", "kunstsammlungen"
    ],
    "United Kingdom": [
        "tate", "british museum", "national gallery", "victoria and albert",
        "лондон", "британия", "британск", "английск"
    ],
    "USA": [
        "metropolitan museum", "метрополитен", "moma", "guggenheim",
        "нью-йорк", "сша", "американск"
    ],
    "China": [
        "китай", "китайск", "пекин", "шанхай", "national museum of china"
    ],
    "Japan": [
        "япония", "японск", "токио"
    ],
    "India": [
        "индия", "индийск"
    ],
    "Iran": [
        "иран", "персия", "персидск"
    ],
    "Oman": [
        "оман", "национальный музей омана", "national museum of oman"
    ],
    "Central Asia": [
        "центральная азия", "центральной азии", "узбекистан", "казахстан",
        "киргиз", "таджикистан", "туркменистан"
    ],
    "Turkey": [
        "турция", "турецк", "стамбул"
    ],
}

COLLAB_CUES = [
    "совместно с",
    "в сотрудничестве с",
    "при участии",
    "при поддержке",
    "организована совместно",
    "подготовлена совместно",
    "партнер выставки",
    "партнёр выставки",
    "партнерами выставки",
    "партнёрами выставки",
    "предоставлены",
    "предоставил",
    "предоставила",
    "произведения из собрания",
    "работы из собрания",
    "из собрания",
    "из коллекции",
    "loan",
    "loans",
    "lent by",
    "in collaboration with",
]


def contains_any(text, words):
    return any(w.lower() in text for w in words)


def detect_countries(text):
    found = []

    for country, keywords in FOREIGN_PARTNER_KEYWORDS.items():
        if contains_any(text, keywords):
            found.append(country)

    return sorted(set(found))


def is_russian_partner(partner_text):
    p = partner_text.lower()
    return contains_any(p, RUSSIAN_INSTITUTION_WORDS)


def split_sentences(text):
    return re.split(r"(?<=[.!?])\s+|(?<=\.)\s+", text)


def sentence_has_collab_cue(sentence):
    return contains_any(sentence.lower(), COLLAB_CUES)


def sentence_has_foreign_signal(sentence):
    return len(detect_countries(sentence.lower())) > 0


def extract_partner_from_sentence(sentence):
    """
    Достаем партнера только из конкретного предложения.
    """
    patterns = [
        r"совместно с ([^.;:|]+)",
        r"в сотрудничестве с ([^.;:|]+)",
        r"при участии ([^.;:|]+)",
        r"при поддержке ([^.;:|]+)",
        r"партнер(?:ом|ы|ами)? выставки[:\s]+([^.;:|]+)",
        r"партнёр(?:ом|ы|ами)? выставки[:\s]+([^.;:|]+)",
        r"произведения из собрания ([^.;:|]+)",
        r"работы из собрания ([^.;:|]+)",
        r"из собрания ([^.;:|]+)",
        r"из коллекции ([^.;:|]+)",
        r"предоставлены ([^.;:|]+)",
        r"предоставил[аи]? ([^.;:|]+)",
        r"in collaboration with ([^.;:|]+)",
        r"lent by ([^.;:|]+)",
    ]

    for pattern in patterns:
        m = re.search(pattern, sentence, flags=re.IGNORECASE)
        if m:
            partner = clean_text(m.group(1))
            partner = re.sub(r"\s+", " ", partner)
            return partner[:250]

    return ""


def find_foreign_collaboration(row):

    text = get_analysis_text(row)
    sentences = split_sentences(text)

    contexts = []
    partners = []
    countries = []

    for sentence in sentences:
        s = clean_text(sentence.lower())

        if not sentence_has_collab_cue(s):
            continue

        if not sentence_has_foreign_signal(s):
            continue

        partner = extract_partner_from_sentence(s)

        if partner and is_russian_partner(partner):
            continue

        sent_countries = detect_countries(s)

        contexts.append(clean_text(sentence))
        countries.extend(sent_countries)

        if partner:
            partners.append(partner)

    if contexts:
        return pd.Series({
            "foreign_collaboration_clean": "yes",
            "foreign_countries_clean": "; ".join(sorted(set(countries))),
            "foreign_partner_clean": " | ".join(sorted(set(partners))),
            "foreign_context_clean": " | ".join(contexts[:3])
        })

    return pd.Series({
        "foreign_collaboration_clean": "no",
        "foreign_countries_clean": "",
        "foreign_partner_clean": "",
        "foreign_context_clean": ""
    })

WEST_TOPIC_KEYWORDS = [
    "франц", "париж", "лувр", "louvre", "итал", "рим", "венеци", "герман",
    "немец", "британ", "англи", "лондон", "европ", "сша", "американ",
    "пикассо", "матисс", "моне", "сезанн", "ван гог", "импрессионизм",
    "постимпрессионизм", "ренессанс"
]

EAST_TOPIC_KEYWORDS = [
    "восток", "китай", "китайск", "япони", "индия", "иран", "оман",
    "центральная азия", "центральной азии", "узбекистан", "казахстан",
    "кавказ", "визант", "ислам", "персия", "араб"
]

INTERNAL_TOPIC_KEYWORDS = [
    "из собрания гмии", "из собрания третьяковской", "из фондов",
    "фонды музея", "собрание музея", "коллекция музея",
    "новое поступление", "дар", "реставрац", "архив", "провенанс",
    "русск", "росси", "советск", "икон", "передвижник", "малевич",
    "репин", "суриков", "серов", "третьяков", "пушкинск"
]


def classify_orientation_clean(row):
    text = get_analysis_text(row)

    west = contains_any(text, WEST_TOPIC_KEYWORDS)
    east = contains_any(text, EAST_TOPIC_KEYWORDS)
    internal = contains_any(text, INTERNAL_TOPIC_KEYWORDS)

    signals = []
    if west:
        signals.append("west")
    if east:
        signals.append("east")
    if internal:
        signals.append("internal")

    if len(signals) == 0:
        return "unknown"
    if len(signals) > 1:
        return "mixed_" + "_".join(signals)

    if signals[0] == "west":
        return "west_oriented"
    if signals[0] == "east":
        return "east_oriented"
    if signals[0] == "internal":
        return "internal_russia_oriented"

    return "unknown"


def pivot_score_clean(row):
    text = get_analysis_text(row)

    score = 0

    if contains_any(text, WEST_TOPIC_KEYWORDS):
        score -= 1

    if contains_any(text, EAST_TOPIC_KEYWORDS):
        score += 1

    if contains_any(text, INTERNAL_TOPIC_KEYWORDS):
        score += 1

    foreign_status = row.get("foreign_collaboration_clean", "no")
    foreign_countries = clean_text(row.get("foreign_countries_clean", ""))

    if foreign_status == "yes":
        if any(c in foreign_countries for c in ["France", "Italy", "Germany", "United Kingdom", "USA"]):
            score -= 2
        if any(c in foreign_countries for c in ["China", "Japan", "India", "Iran", "Oman", "Central Asia", "Turkey"]):
            score += 2

    return score

print("Cleaning descriptions and reclassifying foreign collaborations...")

foreign_cols = df.apply(find_foreign_collaboration, axis=1)
df = pd.concat([df, foreign_cols], axis=1)

df["final_orientation_clean"] = df.apply(classify_orientation_clean, axis=1)
df["pivot_score_clean"] = df.apply(pivot_score_clean, axis=1)

df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")

print("Готово.")
print("Создан файл:", OUTPUT_FILE)

print("\nForeign collaboration clean:")
print(df["foreign_collaboration_clean"].value_counts())

print("\nOrientation clean:")
print(df["final_orientation_clean"].value_counts())

print("\nPivot score clean by period:")
print(df.groupby("period")["pivot_score_clean"].mean())

print("\nExamples of real foreign collaborations:")
cols = [
    "museum", "title", "year", "period",
    "foreign_collaboration_clean",
    "foreign_countries_clean",
    "foreign_partner_clean",
    "foreign_context_clean",
    "url"
]
print(df[df["foreign_collaboration_clean"] == "yes"][cols].head(30).to_string())
