import pandas as pd
import re
import requests
import time
from urllib.parse import quote

from natasha import Segmenter, NewsEmbedding, NewsNERTagger, Doc
import pymorphy3


# ==========================================================
# INPUT / OUTPUT
# ==========================================================

INPUT_FILE = "museum_exhibitions_combined.csv"

OUTPUT_FILE = "exhibitions_geo_people_classified.csv"
REVIEW_FILE = "exhibitions_manual_review.csv"
SUMMARY_FILE = "exhibitions_category_summary.csv"


# ==========================================================
# WIKIPEDIA SETTINGS
# ==========================================================

WIKI_HEADERS = {
    "User-Agent": "MuseumExhibitionsResearch/1.0 (student research; contact: ekaterina.petukhova03@gmail.com)",
    "Accept": "application/json,text/html,*/*",
    "Accept-Language": "ru,en;q=0.9"
}

WIKI_SESSION = requests.Session()
WIKI_SESSION.headers.update(WIKI_HEADERS)

WIKI_CACHE = {}


# ==========================================================
# NATASHA NER SETTINGS
# ==========================================================

segmenter = Segmenter()
emb = NewsEmbedding()
ner_tagger = NewsNERTagger(emb)


# ==========================================================
# MORPHOLOGY SETTINGS
# ==========================================================

morph = pymorphy3.MorphAnalyzer()


# ==========================================================
# TEXT NORMALIZATION
# ==========================================================

def normalize(text):
    text = str(text or "").lower()
    text = text.replace("ё", "е")
    text = text.replace("\xa0", " ")
    text = re.sub(r"[«»\"“”„,.;:!?()\[\]{}]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def compile_regex(pattern):
    return re.compile(pattern, re.IGNORECASE | re.UNICODE)


def remove_institutional_noise(text):
    """
    Удаляет музейные/институциональные фразы,
    чтобы слово 'Пушкина' не относило выставку к России
    только из-за названия ГМИИ им. А.С. Пушкина.
    """

    text = str(text or "")

    patterns = [
        r"ГМИИ\s+им\.?\s*А\.?\s*С\.?\s*Пушкина",
        r"ГМИИ\s+им\.?\s*Пушкина",
        r"Государственн\w*\s+музе\w*\s+изобразительн\w*\s+искусств\w*\s+им\.?\s*А\.?\s*С\.?\s*Пушкина",
        r"Пушкинск\w*\s+музе\w*",
        r"музе\w*\s+им\.?\s*А\.?\s*С\.?\s*Пушкина",
    ]

    for pattern in patterns:
        text = re.sub(pattern, " ", text, flags=re.IGNORECASE | re.UNICODE)

    text = re.sub(r"\s+", " ", text).strip()

    return text


# ==========================================================
# GEO PATTERNS
# Сначала ищем страны, города, регионы, культурные маркеры
# ==========================================================

GEO_PATTERNS = [

    # ---------------- RUSSIA ----------------

    (
        r"\bросси[яийскуюае]+\b|\bрусск\w*\b|\bроссийск\w*\b",
        "Russia",
        "Russia",
        "geo_title"
    ),

    (
        r"\bмоскв\w*\b|\bмосковск\w*\b|\bпетербург\w*\b|"
        r"\bсанкт[- ]петербург\w*\b|\bленинград\w*\b|\bпетроград\w*\b|"
        r"\bлаврушинск\w*\b",
        "Russia",
        "Russia",
        "geo_title"
    ),

    (
        r"\bновгород\w*\b|\bпсков\w*\b|\bсуздал\w*\b|"
        r"\bвладимиро[- ]суздальск\w*\b|\bвладимир\w*\b|"
        r"\bказан\w*\b|\bсамар\w*\b|\bвладивосток\w*\b|"
        r"\bперм\w*\b|\bчуваш\w*\b|\bтатарстан\w*\b|"
        r"\bурал\w*\b|\bсибир\w*\b|\bчукотк\w*\b|\bплес\w*\b|"
        r"\bарктик\w*\b",
        "Russia",
        "Russia",
        "geo_title"
    ),

    # ---------------- RUSSIA EXTRA ----------------

    (
        r"\bпушкин\w*\b|\bпушкинск\w*\b|"
        r"\bцветаев\w*\b|\bцветаевск\w*\b|"
        r"\bюсупов\w*\b|\bкняз\w*\b|\bкняж\w*\b|"
        r"\bроманов\w*\b|\bцарск\w*\b|\bимператорск\w*\b|"
        r"\bвсесоюзн\w*\b|\bсоветск\w*\b|\bссср\b|"
        r"\bдревнерусск\w*\b|\bправослав\w*\b|"
        r"\bлаврушинск\w*\b|\bтретьяков\w*\b",
        "Russia",
        "Russia",
        "geo_title"
    ),

    # ---------------- WEST GENERAL ----------------

    (
        r"\bзападноевроп\w*\b|\bзападн\w+ искусств\w*\b|"
        r"\bевропейск\w*\b|\bевроп\w*\b",
        "Europe",
        "West",
        "geo_title"
    ),

    # ---------------- GREECE / ANTIQUITY ----------------

    (
        r"\bгрец\w*\b|\bгреческ\w*\b|\bэллад\w*\b|"
        r"\bантичн\w*\b|\bантичности\b|\bантик\w*\b|"
        r"\bафин\w*\b|\bспарт\w*\b|\bолимп\w*\b|"
        r"\bэллин\w*\b",
        "Greece / Antiquity",
        "West",
        "geo_title"
    ),

    # ---------------- FRANCE ----------------

    (
        r"\bфранци\w*\b|\bфранцуз\w*\b|\bпариж\w*\b|"
        r"\bмонпарнас\w*\b|\bверсал\w*\b|\bлувр\w*\b|"
        r"\bруан\w*\b|\bпомпиду\b|\bрококо\b",
        "France",
        "West",
        "geo_title"
    ),

    # ---------------- ITALY ----------------

    (
        r"\bитал\w*\b|\bрим\w*\b|\bвенеци\w*\b|"
        r"\bфлоренц\w*\b|\bфлорентийск\w*\b|\bмедичи\b|"
        r"\bсиен\w*\b|\bтоскан\w*\b|"
        r"\bнеапол\w*\b|\bкаподимонте\w*\b|"
        r"\bренессанс\w*\b|\bвозрождени\w*\b|\bбарокко\b",
        "Italy",
        "West",
        "geo_title"
    ),

    # ---------------- SPAIN / PORTUGAL ----------------

    (
        r"\bиспан\w*\b|\bиспания\w*\b|\bмадрид\w*\b|"
        r"\bбарселон\w*\b|\bкаталони\w*\b",
        "Spain",
        "West",
        "geo_title"
    ),

    # ---------------- GERMANY ----------------

    (
        r"\bгермани\w*\b|\bнемец\w*\b|\bберлин\w*\b|"
        r"\bмюнхен\w*\b|\bдрезден\w*\b|\bпотсдам\w*\b",
        "Germany",
        "West",
        "geo_title"
    ),

    # ---------------- AUSTRIA ----------------

    (
        r"\bавстри\w*\b|\bвен[аеы]\b|\bальбертин\w*\b",
        "Austria",
        "West",
        "geo_title"
    ),

    # ---------------- UNITED KINGDOM ----------------

    (
        r"\bангли\w*\b|\bбритан\w*\b|\bвеликобритани\w*\b|"
        r"\bлондон\w*\b|\bоксфорд\w*\b|\bкембридж\w*\b",
        "United Kingdom",
        "West",
        "geo_title"
    ),

    # ---------------- NETHERLANDS ----------------

    (
        r"\bнидерланд\w*\b|\bголланд\w*\b|\bамстердам\w*\b|"
        r"\bлейденск\w*\b",
        "Netherlands",
        "West",
        "geo_title"
    ),

    # ---------------- BELGIUM / FLANDERS ----------------

    (
        r"\bбельги\w*\b|\bфламанд\w*\b|\bбрюссел\w*\b",
        "Belgium/Flanders",
        "West",
        "geo_title"
    ),

    # ---------------- SWITZERLAND ----------------

    (
        r"\bшвейцари\w*\b|\bцюрих\w*\b|\bженев\w*\b",
        "Switzerland",
        "West",
        "geo_title"
    ),

    # ---------------- USA ----------------

    (
        r"\bамерик\w*\b|\bсша\b|\bнью[- ]йорк\w*\b|"
        r"\bчикаго\w*\b|\bвашингтон\w*\b",
        "USA",
        "West",
        "geo_title"
    ),

    # ---------------- OTHER EUROPE ----------------

    (
        r"\bпольш\w*\b|\bваршав\w*\b|\bчех\w*\b|\bпраг\w*\b|"
        r"\bвенгри\w*\b|\bбудапешт\w*\b|\bнорвеги\w*\b|"
        r"\bшвед\w*\b|\bдания\w*\b|\bдатск\w*\b|\bфинлянди\w*\b|"
        r"\bисланд\w*\b|\bирланд\w*\b|\bшотланд\w*\b",
        "Europe",
        "West",
        "geo_title"
    ),

    # ---------------- EAST GENERAL ----------------

    (
        r"\bвосточн\w*\b|\bдальн\w+ восток\w*\b",
        "East",
        "East",
        "geo_title"
    ),

    # ---------------- JAPAN ----------------

    (
        r"\bяпони\w*\b|\bяпон\w*\b|\bтокио\w*\b|"
        r"\bкиото\w*\b|\bосака\w*\b|\bэдо\b|\bраку\b",
        "Japan",
        "East",
        "geo_title"
    ),

    # ---------------- CHINA ----------------

    (
        r"\bкита\w*\b|\bкитай\w*\b|\bпекин\w*\b|"
        r"\bшанха\w*\b|\bхань\b|\bмин\b|\bтан\b|\bхубэй\w*\b",
        "China",
        "East",
        "geo_title"
    ),

    # ---------------- KOREA ----------------

    (
        r"\bкоре\w*\b|\bсеул\w*\b",
        "Korea",
        "East",
        "geo_title"
    ),

    # ---------------- INDIA ----------------

    (
        r"\bинд\w*\b|\bдели\b|\bбомбей\b",
        "India",
        "East",
        "geo_title"
    ),

    # ---------------- IRAN / PERSIA ----------------

    (
        r"\bиран\w*\b|\bперси\w*\b|\bтегеран\w*\b",
        "Iran/Persia",
        "East",
        "geo_title"
    ),

    # ---------------- CENTRAL ASIA ----------------

    (
        r"\bказахстан\w*\b|\bузбекистан\w*\b|\bсамарканд\w*\b|"
        r"\bбухар\w*\b|\bкиргиз\w*\b|\bкыргыз\w*\b|\bтаджикистан\w*\b|"
        r"\bтуркменистан\w*\b|\bмонголи\w*\b",
        "Central Asia",
        "East",
        "geo_title"
    ),

    # ---------------- OTHER ASIA ----------------

    (
        r"\bтибет\w*\b|\bнепал\w*\b|\bтаиланд\w*\b|"
        r"\bвьетнам\w*\b|\bкамбодж\w*\b|\bлаос\w*\b|"
        r"\bбирм\w*\b|\bмьянм\w*\b|\bшри[- ]ланк\w*\b",
        "Asia",
        "East",
        "geo_title"
    ),

    # ---------------- ANCIENT EGYPT ----------------

    (
        r"\bегип\w*\b|\bегипетск\w*\b|\bдревнеегип\w*\b|\bмумии\b|"
        r"\bпапирус\w*\b|\bнильск\w*\b|\bсаркофаг\w*\b|"
        r"\bаменемхет\w*\b|\bфараон\w*\b|\bсредн\w+ царств\w*\b|"
        r"\bдревн\w+ царств\w*\b|\bнов\w+ царств\w*\b",
        "Ancient Egypt",
        "East",
        "geo_title"
    ),

    # ---------------- ASSYRIA / MESOPOTAMIA ----------------

    (
        r"\bашшур\w*\b|\bашшурнацирапал\w*\b|\bассири\w*\b|"
        r"\bмесопотами\w*\b|\bвавилон\w*\b|\bшумер\w*\b|"
        r"\bаккад\w*\b|\bниневи\w*\b",
        "Ancient Near East",
        "East",
        "geo_title"
    ),

    # ---------------- ANCIENT EAST / CAUCASUS ----------------

    (
        r"\bвизанти\w*\b|\bурарту\w*\b|\bармени\w*\b|"
        r"\bереван\w*\b|\bтроя\w*\b|\bкарфаген\w*\b|"
        r"\bсармат\w*\b|\bбоспорск\w*\b|\bпантикапей\w*\b|"
        r"\bфанагори\w*\b",
        "Ancient East / Caucasus",
        "East",
        "geo_title"
    ),

    (
        r"\bгрузи\w*\b|\bгрузин\w*\b",
        "Georgia",
        "East",
        "geo_title"
    ),
]


# ==========================================================
# WIKIPEDIA CLASSIFICATION DICTIONARIES
# ==========================================================

COUNTRY_TO_CATEGORY = {
    # Russia
    "россия": "Russia",
    "российская империя": "Russia",
    "ссср": "Russia",
    "советский союз": "Russia",

    # West
    "франция": "West",
    "италия": "West",
    "испания": "West",
    "германия": "West",
    "австрия": "West",
    "великобритания": "West",
    "англия": "West",
    "нидерланды": "West",
    "голландия": "West",
    "бельгия": "West",
    "швейцария": "West",
    "сша": "West",
    "соединенные штаты": "West",
    "соединённые штаты": "West",
    "польша": "West",
    "чехия": "West",
    "венгрия": "West",
    "норвегия": "West",
    "швеция": "West",
    "дания": "West",
    "финляндия": "West",
    "исландия": "West",
    "ирландия": "West",
    "греция": "West",

    # East
    "япония": "East",
    "китай": "East",
    "корея": "East",
    "индия": "East",
    "иран": "East",
    "персия": "East",
    "казахстан": "East",
    "узбекистан": "East",
    "киргизия": "East",
    "кыргызстан": "East",
    "таджикистан": "East",
    "туркменистан": "East",
    "монголия": "East",
    "грузия": "East",
    "армения": "East",
    "египет": "East",
    "турция": "East",
}


NATIONALITY_TO_CATEGORY = {
    # Russia
    "русский": "Russia",
    "русская": "Russia",
    "российский": "Russia",
    "российская": "Russia",
    "советский": "Russia",
    "советская": "Russia",

    # West
    "французский": "West",
    "французская": "West",
    "итальянский": "West",
    "итальянская": "West",
    "испанский": "West",
    "испанская": "West",
    "немецкий": "West",
    "немецкая": "West",
    "германский": "West",
    "германская": "West",
    "австрийский": "West",
    "австрийская": "West",
    "британский": "West",
    "британская": "West",
    "английский": "West",
    "английская": "West",
    "нидерландский": "West",
    "нидерландская": "West",
    "голландский": "West",
    "голландская": "West",
    "бельгийский": "West",
    "бельгийская": "West",
    "швейцарский": "West",
    "швейцарская": "West",
    "американский": "West",
    "американская": "West",
    "польский": "West",
    "польская": "West",
    "чешский": "West",
    "чешская": "West",
    "венгерский": "West",
    "венгерская": "West",
    "норвежский": "West",
    "норвежская": "West",
    "шведский": "West",
    "шведская": "West",
    "датский": "West",
    "датская": "West",
    "финский": "West",
    "финская": "West",
    "исландский": "West",
    "исландская": "West",
    "ирландский": "West",
    "ирландская": "West",
    "греческий": "West",
    "греческая": "West",

    # East
    "японский": "East",
    "японская": "East",
    "китайский": "East",
    "китайская": "East",
    "корейский": "East",
    "корейская": "East",
    "индийский": "East",
    "индийская": "East",
    "иранский": "East",
    "иранская": "East",
    "персидский": "East",
    "персидская": "East",
    "казахский": "East",
    "казахская": "East",
    "узбекский": "East",
    "узбекская": "East",
    "киргизский": "East",
    "киргизская": "East",
    "кыргызский": "East",
    "кыргызская": "East",
    "таджикский": "East",
    "таджикская": "East",
    "туркменский": "East",
    "туркменская": "East",
    "монгольский": "East",
    "монгольская": "East",
    "грузинский": "East",
    "грузинская": "East",
    "армянский": "East",
    "армянская": "East",
    "турецкий": "East",
    "турецкая": "East",
    "египетский": "East",
    "египетская": "East",
}


# ==========================================================
# GEOGRAPHY DETECTION
# ==========================================================

def find_geo(title):
    clean_title = remove_institutional_noise(title)
    text = normalize(clean_title)
    matches = []

    for pattern, country, category, method in GEO_PATTERNS:
        match = compile_regex(pattern).search(text)

        if match:
            matches.append({
                "entity": match.group(0),
                "country": country,
                "category": category,
                "method": method,
                "wiki_title": "",
                "wiki_url": ""
            })

    return matches


# ==========================================================
# PERSON EXTRACTION FROM TITLE WITH NATASHA
# ==========================================================

def extract_possible_people_from_title(title):
    """
    Извлекает имена людей из названия выставки через Natasha NER.
    Возвращает только сущности типа PER.
    """

    title = str(title or "")

    clean_title = remove_institutional_noise(title)

    # Удаляем инициалы типа А.С., А.Н., К.А.
    clean_title = re.sub(r"\b[А-ЯЁ]\.\s*[А-ЯЁ]\.", " ", clean_title)
    clean_title = re.sub(r"\b[А-ЯЁ]\.", " ", clean_title)

    doc = Doc(clean_title)
    doc.segment(segmenter)
    doc.tag_ner(ner_tagger)

    people = []

    for span in doc.spans:
        if span.type == "PER":
            person = span.text.strip()

            if len(person) >= 4:
                people.append(person)

    people = list(dict.fromkeys(people))

    return people


# ==========================================================
# MANUAL PERSON OVERRIDES
# Для редких музейных персон, которых Wikipedia/API может не найти
# ==========================================================

MANUAL_PERSON_OVERRIDES = {
    # Russia
    "беатриса сандомирская": {
        "country": "Russia",
        "category": "Russia",
        "method": "manual_person_override"
    },
    "ефим харабет": {
        "country": "Russia",
        "category": "Russia",
        "method": "manual_person_override"
    },
    "иван похитонов": {
        "country": "Russia",
        "category": "Russia",
        "method": "manual_person_override"
    },
    "сергей романович": {
        "country": "Russia",
        "category": "Russia",
        "method": "manual_person_override"
    },
    "петр великий": {
        "country": "Russia",
        "category": "Russia",
        "method": "manual_person_override"
    },
    "пётр великий": {
        "country": "Russia",
        "category": "Russia",
        "method": "manual_person_override"
    },
    "олег яхонт": {
        "country": "Russia",
        "category": "Russia",
        "method": "manual_person_override"
    },
    "василий кандинский": {
        "country": "Russia",
        "category": "Russia",
        "method": "manual_person_override"
    },

    # West
    "пабло пикассо": {
        "country": "Spain/France",
        "category": "West",
        "method": "manual_person_override"
    },
    "анри матисс": {
        "country": "France",
        "category": "West",
        "method": "manual_person_override"
    },
    "альбрехт дюрер": {
        "country": "Germany",
        "category": "West",
        "method": "manual_person_override"
    },
}


def normalize_person_name(person_name):
    """
    Приводит имя к нормальной форме:
    'Ефима Харабета' -> 'ефим харабет'
    'Сергея Романовича' -> 'сергей романович'
    'Ивана Похитонова' -> 'иван похитонов'
    """

    text = str(person_name or "").lower()
    text = text.replace("ё", "е")
    text = re.sub(r"[^а-яa-z\s-]", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text).strip()

    normalized_words = []

    for word in text.split():
        parsed = morph.parse(word)[0]
        normalized_words.append(parsed.normal_form)

    return " ".join(normalized_words)


# ==========================================================
# WIKIPEDIA API FUNCTIONS
# ==========================================================

def wiki_search_ru(query):
    """
    Ищет страницу в русской Википедии.
    Если Wikipedia отвечает 403 или зависает, возвращает None.
    """

    query = str(query).strip()

    if not query:
        return None

    cache_key = "search::" + query.lower()

    if cache_key in WIKI_CACHE:
        return WIKI_CACHE[cache_key]

    url = "https://ru.wikipedia.org/w/api.php"

    params = {
        "action": "query",
        "list": "search",
        "srsearch": query,
        "format": "json",
        "utf8": 1,
        "srlimit": 1
    }

    try:
        response = WIKI_SESSION.get(
            url,
            params=params,
            timeout=(5, 10)
        )

        if response.status_code == 403:
            print("Wikipedia 403, skip:", query)
            WIKI_CACHE[cache_key] = None
            return None

        response.raise_for_status()

        data = response.json()
        results = data.get("query", {}).get("search", [])

        if results:
            page_title = results[0]["title"]
            WIKI_CACHE[cache_key] = page_title
            return page_title

    except Exception as e:
        print("Wikipedia search error:", query, e)

    WIKI_CACHE[cache_key] = None
    return None


def wiki_get_page_text_ru(title):
    """
    Загружает текст страницы из русской Википедии.
    Если Wikipedia отвечает 403 или зависает, возвращает пустую строку.
    """

    title = str(title).strip()

    if not title:
        return ""

    cache_key = "page::" + title.lower()

    if cache_key in WIKI_CACHE:
        return WIKI_CACHE[cache_key]

    url = "https://ru.wikipedia.org/w/api.php"

    params = {
        "action": "query",
        "prop": "extracts",
        "explaintext": 1,
        "titles": title,
        "format": "json",
        "utf8": 1
    }

    try:
        response = WIKI_SESSION.get(
            url,
            params=params,
            timeout=(5, 10)
        )

        if response.status_code == 403:
            print("Wikipedia 403 page, skip:", title)
            WIKI_CACHE[cache_key] = ""
            return ""

        response.raise_for_status()

        data = response.json()
        pages = data.get("query", {}).get("pages", {})

        for _, page in pages.items():
            text = page.get("extract", "")
            WIKI_CACHE[cache_key] = text
            return text

    except Exception as e:
        print("Wikipedia page error:", title, e)

    WIKI_CACHE[cache_key] = ""
    return ""


def classify_person_by_wikipedia(person_name):
    """
    Проверяет человека сначала через ручные исключения,
    потом через Wikipedia.
    """

    person_key = normalize_person_name(person_name)

    if person_key in MANUAL_PERSON_OVERRIDES:
        item = MANUAL_PERSON_OVERRIDES[person_key]

        return {
            "entity": person_name,
            "country": item["country"],
            "category": item["category"],
            "method": item["method"],
            "wiki_title": "",
            "wiki_url": ""
        }

    page_title = wiki_search_ru(person_key)

    if page_title is None:
        return {
            "entity": person_name,
            "country": "",
            "category": "Unknown",
            "method": "wikipedia_not_found_or_blocked",
            "wiki_title": "",
            "wiki_url": ""
        }

    page_text = wiki_get_page_text_ru(page_title)

    if not page_text:
        return {
            "entity": person_name,
            "country": "",
            "category": "Unknown",
            "method": "wikipedia_page_empty_or_blocked",
            "wiki_title": page_title,
            "wiki_url": "https://ru.wikipedia.org/wiki/" + page_title.replace(" ", "_")
        }

    intro = page_text[:1500].lower()
    intro = intro.replace("ё", "е")

    # 1. Проверяем национальности
    for word, category in NATIONALITY_TO_CATEGORY.items():
        word_norm = word.replace("ё", "е")

        if re.search(r"\b" + re.escape(word_norm) + r"\b", intro):
            return {
                "entity": person_name,
                "country": word,
                "category": category,
                "method": "wikipedia_person_nationality",
                "wiki_title": page_title,
                "wiki_url": "https://ru.wikipedia.org/wiki/" + page_title.replace(" ", "_")
            }

    # 2. Проверяем страны
    for country, category in COUNTRY_TO_CATEGORY.items():
        country_norm = country.replace("ё", "е")

        if re.search(r"\b" + re.escape(country_norm) + r"\b", intro):
            return {
                "entity": person_name,
                "country": country,
                "category": category,
                "method": "wikipedia_person_country",
                "wiki_title": page_title,
                "wiki_url": "https://ru.wikipedia.org/wiki/" + page_title.replace(" ", "_")
            }

    return {
        "entity": person_name,
        "country": "",
        "category": "Unknown",
        "method": "wikipedia_no_country_detected",
        "wiki_title": page_title,
        "wiki_url": "https://ru.wikipedia.org/wiki/" + page_title.replace(" ", "_")
    }


def find_person_via_wikipedia(title):
    """
    Если география в названии не найдена:
    - извлекаем людей через Natasha
    - нормализуем падежи через pymorphy3
    - проверяем максимум 3 кандидата через manual overrides + Wikipedia
    """

    people = extract_possible_people_from_title(title)

    people = [
        person for person in people
        if len(person) >= 4
    ]

    people = people[:3]

    matches = []

    for person in people:
        result = classify_person_by_wikipedia(person)
        matches.append(result)

        time.sleep(1.0)

        if result["category"] != "Unknown":
            return [result]

    return matches


# ==========================================================
# FINAL CLASSIFICATION
# ==========================================================

def choose_classification(matches):
    """
    Выбирает итоговую классификацию.

    Логика:
    - если нет совпадений -> No_geo_no_person_in_title
    - если есть West/East и Russia одновременно -> берем иностранный маркер
    - если есть только Russia -> Russia
    - если есть West и East одновременно -> Mixed_East_West
    """

    if not matches:
        return {
            "detected_entity": "",
            "detected_country": "",
            "category_final": "No_geo_no_person_in_title",
            "classification_method": "no_geo_no_person_in_title",
            "all_matches": "",
            "confidence": "not_applicable",
            "wiki_title": "",
            "wiki_url": ""
        }

    known_matches = [
        item for item in matches
        if item.get("category") != "Unknown"
    ]

    if not known_matches:
        all_matches = " | ".join(
            f"{item.get('entity', '')} → Unknown ({item.get('method', '')})"
            for item in matches
        )

        wiki_title = "; ".join(
            dict.fromkeys(item.get("wiki_title", "") for item in matches if item.get("wiki_title"))
        )

        wiki_url = "; ".join(
            dict.fromkeys(item.get("wiki_url", "") for item in matches if item.get("wiki_url"))
        )

        return {
            "detected_entity": "; ".join(
                dict.fromkeys(item.get("entity", "") for item in matches)
            ),
            "detected_country": "",
            "category_final": "Unknown",
            "classification_method": "+".join(
                dict.fromkeys(item.get("method", "") for item in matches)
            ),
            "all_matches": all_matches,
            "confidence": "review",
            "wiki_title": wiki_title,
            "wiki_url": wiki_url
        }

    non_russia = [
        item for item in known_matches
        if item["category"] in ["West", "East"]
    ]

    if non_russia:
        categories = sorted(set(item["category"] for item in non_russia))

        if len(categories) == 1:
            category_final = categories[0]
        else:
            category_final = "Mixed_East_West"

        used_matches = non_russia

    else:
        category_final = "Russia"
        used_matches = known_matches

    detected_country = "; ".join(
        dict.fromkeys(item.get("country", "") for item in used_matches)
    )

    detected_entity = "; ".join(
        dict.fromkeys(item.get("entity", "") for item in used_matches)
    )

    method = "+".join(
        dict.fromkeys(item.get("method", "") for item in used_matches)
    )

    wiki_title = "; ".join(
        dict.fromkeys(item.get("wiki_title", "") for item in used_matches if item.get("wiki_title"))
    )

    wiki_url = "; ".join(
        dict.fromkeys(item.get("wiki_url", "") for item in used_matches if item.get("wiki_url"))
    )

    if any(item.get("method") == "geo_title" for item in used_matches):
        confidence = "high"
    elif any("wikipedia" in item.get("method", "") for item in used_matches):
        confidence = "medium"
    elif any("manual_person_override" in item.get("method", "") for item in used_matches):
        confidence = "manual_high"
    else:
        confidence = "review"

    all_matches = " | ".join(
        f"{item.get('entity', '')} → {item.get('country', '')}/{item.get('category', '')} ({item.get('method', '')})"
        for item in matches
    )

    return {
        "detected_entity": detected_entity,
        "detected_country": detected_country,
        "category_final": category_final,
        "classification_method": method,
        "all_matches": all_matches,
        "confidence": confidence,
        "wiki_title": wiki_title,
        "wiki_url": wiki_url
    }


# ==========================================================
# MAIN
# ==========================================================

df = pd.read_csv(INPUT_FILE)

rows = []

for i, row in df.iterrows():

    title = row.get("title", "")

    print(f"\n{i + 1}/{len(df)}: {title}")

    # 1. Сначала ищем географию в заголовке
    geo_matches = find_geo(title)

    # 2. Если география не найдена, ищем людей через Natasha + manual overrides + Wikipedia
    if geo_matches:
        person_matches = []
    else:
        person_matches = find_person_via_wikipedia(title)

    matches = geo_matches or person_matches

    classification = choose_classification(matches)

    new_row = row.to_dict()
    new_row.update(classification)

    # Ручная проверка нужна только если Natasha/Wikipedia нашла человека,
    # но не смогла определить страну/категорию.
    new_row["wikipedia_check_needed"] = (
        new_row["category_final"] == "Unknown"
    )

    if new_row["category_final"] == "Unknown":
        new_row["wikipedia_search_url"] = (
            "https://ru.wikipedia.org/w/index.php?search="
            + quote(str(title))
        )
    else:
        new_row["wikipedia_search_url"] = new_row.get("wiki_url", "")

    rows.append(new_row)


out = pd.DataFrame(rows)


# ==========================================================
# SAVE FULL CLASSIFIED DATA
# ==========================================================

out.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)


# ==========================================================
# SAVE MANUAL REVIEW TABLE
# ==========================================================

review = out[
    out["category_final"] == "Unknown"
].copy()

review_columns = [
    "museum",
    "year",
    "period",
    "title",
    "detected_entity",
    "detected_country",
    "category_final",
    "classification_method",
    "wiki_title",
    "wiki_url",
    "wikipedia_search_url"
]

existing_review_columns = [
    col for col in review_columns
    if col in review.columns
]

review[existing_review_columns].to_csv(
    REVIEW_FILE,
    index=False,
    encoding="utf-8-sig"
)


# ==========================================================
# SAVE SUMMARY TABLE
# ==========================================================

summary = (
    out
    .groupby(["period", "category_final"])
    .size()
    .reset_index(name="n")
)

summary["period_total"] = summary.groupby("period")["n"].transform("sum")
summary["share"] = summary["n"] / summary["period_total"]

summary.to_csv(
    SUMMARY_FILE,
    index=False,
    encoding="utf-8-sig"
)


# ==========================================================
# SAVE ANALYSIS-READY SUMMARY
# Без No_geo_no_person_in_title и Unknown
# ==========================================================

analysis = out[
    out["category_final"].isin(["Russia", "West", "East", "Mixed_East_West"])
].copy()

analysis_summary = (
    analysis
    .groupby(["period", "category_final"])
    .size()
    .reset_index(name="n")
)

analysis_summary["period_total_classified"] = analysis_summary.groupby("period")["n"].transform("sum")
analysis_summary["share_classified_only"] = (
    analysis_summary["n"] / analysis_summary["period_total_classified"]
)

analysis_summary.to_csv(
    "exhibitions_analysis_summary_classified_only.csv",
    index=False,
    encoding="utf-8-sig"
)


# ==========================================================
# PRINT RESULTS
# ==========================================================

print("\nГотово!")
print("Saved:", OUTPUT_FILE)
print("Rows:", out.shape)

print("\nCategory counts:")
print(out["category_final"].value_counts())

print("\nBy period:")
print(pd.crosstab(out["period"], out["category_final"]))

print("\nManual review rows:", len(review))
print("Manual review saved:", REVIEW_FILE)
print("Summary saved:", SUMMARY_FILE)
print("Analysis-ready summary saved: exhibitions_analysis_summary_classified_only.csv")