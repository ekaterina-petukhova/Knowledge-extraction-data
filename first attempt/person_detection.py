import pandas as pd
import re
from urllib.parse import quote

INPUT_FILE = "museum_exhibitions_combined.csv"

OUTPUT_FILE = "exhibitions_geo_people_classified.csv"
REVIEW_FILE = "exhibitions_manual_review.csv"
SUMMARY_FILE = "exhibitions_category_summary.csv"

def normalize(text):
    """
    Приводит текст к удобному виду:
    - нижний регистр
    - ё -> е
    - убирает кавычки и пунктуацию
    - схлопывает пробелы
    """

    text = str(text or "").lower()
    text = text.replace("ё", "е")
    text = text.replace("\xa0", " ")

    text = re.sub(r"[«»\"“”„,.;:!?()\[\]{}]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    return text


def compile_regex(pattern):
    return re.compile(pattern, re.IGNORECASE | re.UNICODE)

GEO_PATTERNS = [


    (
        r"\bросси[яийскуюае]+\b|\bрусск\w*\b|\bроссийск\w*\b",
        "Russia",
        "Russia",
        "geo_title"
    ),

    (
        r"\bмоскв\w*\b|\bмосковск\w*\b|\bпетербург\w*\b|"
        r"\bсанкт[- ]петербург\w*\b|\bленинград\w*\b|\bпетроград\w*\b",
        "Russia",
        "Russia",
        "geo_title"
    ),

    (
        r"\bновгород\w*\b|\bпсков\w*\b|\bсуздал\w*\b|"
        r"\bвладимиро[- ]суздальск\w*\b|\bвладимир\w*\b|"
        r"\bказан\w*\b|\bсамар\w*\b|\bвладивосток\w*\b|"
        r"\bперм\w*\b|\bчуваш\w*\b|\bтатарстан\w*\b|"
        r"\bурал\w*\b|\bсибир\w*\b|\bчукотк\w*\b|\bплес\w*\b",
        "Russia",
        "Russia",
        "geo_title"
    ),

    (
        r"\bзападноевроп\w*\b|\bзападн\w+ искусств\w*\b|"
        r"\bевропейск\w*\b|\bевроп\w*\b",
        "Europe",
        "West",
        "geo_title"
    ),


    (
        r"\bфранци\w*\b|\bфранцуз\w*\b|\bпариж\w*\b|"
        r"\bмонпарнас\w*\b|\bверсал\w*\b|\bлувр\w*\b|"
        r"\bруан\w*\b|\bпомпиду\b",
        "France",
        "West",
        "geo_title"
    ),

    (
        r"\bитал\w*\b|\bрим\w*\b|\bвенеци\w*\b|"
        r"\bфлоренц\w*\b|\bсиен\w*\b|\bтоскан\w*\b|"
        r"\bнеапол\w*\b|\bкаподимонте\w*\b|"
        r"\bренессанс\w*\b|\bвозрождени\w*\b|\bбарокко\b",
        "Italy",
        "West",
        "geo_title"
    ),


    (
        r"\bиспан\w*\b|\bиспания\w*\b|\bмадрид\w*\b|"
        r"\bбарселон\w*\b|\bкаталони\w*\b",
        "Spain",
        "West",
        "geo_title"
    ),

    (
        r"\bгермани\w*\b|\bнемец\w*\b|\bберлин\w*\b|"
        r"\bмюнхен\w*\b|\bдрезден\w*\b|\bпотсдам\w*\b",
        "Germany",
        "West",
        "geo_title"
    ),


    (
        r"\bавстри\w*\b|\bвен[аеы]\b|\bальбертин\w*\b",
        "Austria",
        "West",
        "geo_title"
    ),

    (
        r"\bангли\w*\b|\bбритан\w*\b|\bвеликобритани\w*\b|"
        r"\bлондон\w*\b|\bоксфорд\w*\b|\bкембридж\w*\b",
        "United Kingdom",
        "West",
        "geo_title"
    ),


    (
        r"\bнидерланд\w*\b|\bголланд\w*\b|\bамстердам\w*\b|"
        r"\bлейденск\w*\b",
        "Netherlands",
        "West",
        "geo_title"
    ),


    (
        r"\bбельги\w*\b|\bфламанд\w*\b|\bбрюссел\w*\b",
        "Belgium/Flanders",
        "West",
        "geo_title"
    ),

    (
        r"\bшвейцари\w*\b|\bцюрих\w*\b|\bженев\w*\b",
        "Switzerland",
        "West",
        "geo_title"
    ),


    (
        r"\bамерик\w*\b|\bсша\b|\bнью[- ]йорк\w*\b|"
        r"\bчикаго\w*\b|\bвашингтон\w*\b",
        "USA",
        "West",
        "geo_title"
    ),

    (
        r"\bпольш\w*\b|\bваршав\w*\b|\bчех\w*\b|\bпраг\w*\b|"
        r"\bвенгри\w*\b|\bбудапешт\w*\b|\bнорвеги\w*\b|"
        r"\bшвед\w*\b|\bдания\w*\b|\bдатск\w*\b|\bфинлянди\w*\b",
        "Europe",
        "West",
        "geo_title"
    ),


    (
        r"\bвосточн\w*\b|\bдальн\w+ восток\w*\b",
        "East",
        "East",
        "geo_title"
    ),


    (
        r"\bяпони\w*\b|\bяпон\w*\b|\bтокио\w*\b|"
        r"\bкиото\w*\b|\bосака\w*\b|\bэдо\b",
        "Japan",
        "East",
        "geo_title"
    ),

    (
        r"\bкита\w*\b|\bкитай\w*\b|\bпекин\w*\b|"
        r"\bшанха\w*\b|\bхань\b|\bмин\b|\bтан\b",
        "China",
        "East",
        "geo_title"
    ),


    (
        r"\bкоре\w*\b|\bсеул\w*\b",
        "Korea",
        "East",
        "geo_title"
    ),


    (
        r"\bинд\w*\b|\bдели\b|\bбомбей\b",
        "India",
        "East",
        "geo_title"
    ),


    (
        r"\bиран\w*\b|\bперси\w*\b|\bтегеран\w*\b",
        "Iran/Persia",
        "East",
        "geo_title"
    ),


    (
        r"\bказахстан\w*\b|\bузбекистан\w*\b|\bсамарканд\w*\b|"
        r"\bбухар\w*\b|\bкиргиз\w*\b|\bтаджикистан\w*\b|"
        r"\bтуркменистан\w*\b|\bмонголи\w*\b",
        "Central Asia",
        "East",
        "geo_title"
    ),


    (
        r"\bтибет\w*\b|\bнепал\w*\b|\bтаиланд\w*\b|"
        r"\bвьетнам\w*\b|\bкамбодж\w*\b|\bлаос\w*\b|"
        r"\bбирм\w*\b|\bмьянм\w*\b|\bшри[- ]ланк\w*\b",
        "Asia",
        "East",
        "geo_title"
    ),


    (
        r"\bегип\w*\b|\bдревнеегип\w*\b|\bмумии\b|"
        r"\bпапирус\w*\b|\bбибл\w*\b",
        "Egypt/Levant",
        "East",
        "geo_title"
    ),

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

PERSON_DICT = {
    "беатриса сандомирская": ("Russia", "Russia"),
    "сандомирская": ("Russia", "Russia"),

    "ефим харабет": ("Russia", "Russia"),
    "харабет": ("Russia", "Russia"),

    "александра лукашевкер": ("Russia", "Russia"),
    "лукашевкер": ("Russia", "Russia"),

    "марк шагал": ("Russia", "Russia"),
    "шагал": ("Russia", "Russia"),

    "марина бессонова": ("Russia", "Russia"),
    "бессонова": ("Russia", "Russia"),

    "щетинин": ("Russia", "Russia"),
    "крамской": ("Russia", "Russia"),
    "щуткин": ("Russia", "Russia"),
    "щукин": ("Russia", "Russia"),

    "варвара степанова": ("Russia", "Russia"),
    "степанова": ("Russia", "Russia"),

    "владимир вейсберг": ("Russia", "Russia"),
    "вейсберг": ("Russia", "Russia"),

    "святослав рихтер": ("Russia", "Russia"),
    "рихтер": ("Russia", "Russia"),

    "дмитрий краснопевцев": ("Russia", "Russia"),
    "краснопевцев": ("Russia", "Russia"),

    "наталья золотова": ("Russia", "Russia"),
    "золотова": ("Russia", "Russia"),

    "иван морозов": ("Russia", "Russia"),
    "михаил морозов": ("Russia", "Russia"),
    "морозов": ("Russia", "Russia"),

    "иван цветаев": ("Russia", "Russia"),
    "цветаев": ("Russia", "Russia"),

    "ирина затуловская": ("Russia", "Russia"),
    "затуловская": ("Russia", "Russia"),

    "александр фролов": ("Russia", "Russia"),
    "сергей прокофьев": ("Russia", "Russia"),

    "пушкин": ("Russia", "Russia"),
    "юсуповы": ("Russia", "Russia"),

    "родченко": ("Russia", "Russia"),
    "гончарова": ("Russia", "Russia"),

    "казимир малевич": ("Russia", "Russia"),
    "малевич": ("Russia", "Russia"),

    "кандинский": ("Russia", "Russia"),
    "кандинского": ("Russia", "Russia"),

    "верещагин": ("Russia", "Russia"),
    "репин": ("Russia", "Russia"),
    "суриков": ("Russia", "Russia"),
    "саврасов": ("Russia", "Russia"),
    "васнецов": ("Russia", "Russia"),
    "перов": ("Russia", "Russia"),
    "шишкин": ("Russia", "Russia"),
    "левитан": ("Russia", "Russia"),
    "серов": ("Russia", "Russia"),
    "врубель": ("Russia", "Russia"),
    "айвазовский": ("Russia", "Russia"),
    "иванов": ("Russia", "Russia"),
    "тропинин": ("Russia", "Russia"),
    "поленов": ("Russia", "Russia"),

    "пиросмани": ("Georgia", "East"),

    "рерих": ("Russia", "Russia"),
    "попков": ("Russia", "Russia"),
    "василий поленов": ("Russia", "Russia"),
    "сергей коненков": ("Russia", "Russia"),
    "малявин": ("Russia", "Russia"),
    "архипов": ("Russia", "Russia"),

    "алексей моргунов": ("Russia", "Russia"),
    "юрий ларин": ("Russia", "Russia"),
    "виктор иванов": ("Russia", "Russia"),
    "эдуард бояков": ("Russia", "Russia"),
    "михаил розанов": ("Russia", "Russia"),
    "владимир конашевич": ("Russia", "Russia"),
    "николай ульянов": ("Russia", "Russia"),
    "юрий злотников": ("Russia", "Russia"),
    "александр константинов": ("Russia", "Russia"),
    "александр пономарев": ("Russia", "Russia"),
    "николай милиоти": ("Russia", "Russia"),
    "сергей рахманинов": ("Russia", "Russia"),
    "алексей боголюбов": ("Russia", "Russia"),
    "виктор казарин": ("Russia", "Russia"),
    "илья кабаков": ("Russia", "Russia"),
    "эдуард браговский": ("Russia", "Russia"),
    "олег кудряшов": ("Russia", "Russia"),
    "александр рубцов": ("Russia", "Russia"),
    "владимир гаврилов": ("Russia", "Russia"),
    "игорь грабарь": ("Russia", "Russia"),
    "михаил шемякин": ("Russia", "Russia"),
    "николай вечтомов": ("Russia", "Russia"),
    "сергей кузнецов": ("Russia", "Russia"),
    "александр юликов": ("Russia", "Russia"),
    "юрий купер": ("Russia", "Russia"),
    "борис неменский": ("Russia", "Russia"),
    "коржовы": ("Russia", "Russia"),
    "ткачев": ("Russia", "Russia"),
    "алексей щусев": ("Russia", "Russia"),
    "шадр": ("Russia", "Russia"),
    "наталья эльконина": ("Russia", "Russia"),
    "лев кропивницкий": ("Russia", "Russia"),
    "велимир хлебников": ("Russia", "Russia"),
    "василий чекрыгин": ("Russia", "Russia"),
    "гурий захаров": ("Russia", "Russia"),
    "татьяна соколова": ("Russia", "Russia"),
    "петр великий": ("Russia", "Russia"),
    "виктор алимпиев": ("Russia", "Russia"),
    "илья репин": ("Russia", "Russia"),
    "манизеры": ("Russia", "Russia"),
    "николай андреев": ("Russia", "Russia"),
    "борис кочейшвили": ("Russia", "Russia"),
    "юрий пименов": ("Russia", "Russia"),
    "александр бенуа": ("Russia", "Russia"),
    "алла урбан": ("Russia", "Russia"),
    "мария якунчикова": ("Russia", "Russia"),
    "андрей красулин": ("Russia", "Russia"),
    "иван цветков": ("Russia", "Russia"),
    "анна голубкина": ("Russia", "Russia"),
    "сарра лебедева": ("Russia", "Russia"),
    "никоновы": ("Russia", "Russia"),
    "владимир смирнов": ("Russia", "Russia"),
    "константин сорокин": ("Russia", "Russia"),
    "александр рукавишников": ("Russia", "Russia"),
    "сергей сапожников": ("Russia", "Russia"),
    "иа крылов": ("Russia", "Russia"),
    "крылов": ("Russia", "Russia"),
    "игорь шелковский": ("Russia", "Russia"),
    "романович": ("Russia", "Russia"),
    "олег яхонт": ("Russia", "Russia"),
    "константин истомин": ("Russia", "Russia"),


    "гверчино": ("Italy", "West"),
    "брейгель": ("Netherlands/Flanders", "West"),
    "фрагонар": ("France", "West"),
    "франс снейдерс": ("Belgium/Flanders", "West"),
    "снейдерс": ("Belgium/Flanders", "West"),

    "матисс": ("France", "West"),
    "клод моне": ("France", "West"),
    "моне": ("France", "West"),

    "вазари": ("Italy", "West"),
    "медичи": ("Italy", "West"),
    "дидро": ("France", "West"),
    "шлиман": ("Germany", "West"),
    "герлен": ("France", "West"),

    "джанни маттиоли": ("Italy", "West"),
    "маттиоли": ("Italy", "West"),

    "ксения хауснер": ("Austria", "West"),
    "хауснер": ("Austria", "West"),

    "билл виола": ("USA", "West"),
    "виола": ("USA", "West"),

    "дюрер": ("Germany", "West"),

    "томас гейнсборо": ("United Kingdom", "West"),
    "гейнсборо": ("United Kingdom", "West"),

    "якоб йорданс": ("Belgium/Flanders", "West"),
    "йорданс": ("Belgium/Flanders", "West"),

    "тинторетто": ("Italy", "West"),

    "артемизия джентилески": ("Italy", "West"),
    "джентилески": ("Italy", "West"),

    "пикассо": ("Spain", "West"),

    "ольга хохлова": ("Russia", "Russia"),

    "руссо": ("France", "West"),
    "модильяни": ("Italy", "West"),
    "аполлинер": ("France", "West"),
    "сюрваж": ("Russia/France", "West"),
    "фера": ("France", "West"),

    "тьеполо": ("Italy", "West"),
    "каналетто": ("Italy", "West"),
    "гварди": ("Italy", "West"),
    "фабрицио плесси": ("Italy", "West"),
    "плесси": ("Italy", "West"),

    "рембрандт": ("Netherlands", "West"),
    "вермеер": ("Netherlands", "West"),

    "уильям генри фокс тальбот": ("United Kingdom", "West"),
    "тальбот": ("United Kingdom", "West"),

    "хаим сутин": ("France", "West"),
    "сутин": ("France", "West"),

    "густав климт": ("Austria", "West"),
    "климт": ("Austria", "West"),

    "эгон шиле": ("Austria", "West"),
    "шиле": ("Austria", "West"),

    "фрэнсис бэкон": ("United Kingdom", "West"),
    "бэкон": ("United Kingdom", "West"),

    "лючен фрейд": ("United Kingdom", "West"),
    "люсьен фрейд": ("United Kingdom", "West"),
    "фрейд": ("United Kingdom", "West"),

    "сальвадор дали": ("Spain", "West"),
    "дали": ("Spain", "West"),

    # ---------------- EAST ----------------

    "цаи гоцян": ("China", "East"),
    "цай гоцян": ("China", "East"),

    "тадаси кавамата": ("Japan", "East"),
    "кавамата": ("Japan", "East"),
    "кавалмата": ("Japan", "East"),
    "кавахмата": ("Japan", "East"),

    "хань юйчэнь": ("China", "East"),
    "юйчэнь": ("China", "East"),
}


def find_geo(title):
    """
    Ищет географические маркеры в названии выставки.
    Возвращает список совпадений.
    """

    text = normalize(title)
    matches = []

    for pattern, country, category, method in GEO_PATTERNS:
        match = compile_regex(pattern).search(text)

        if match:
            matches.append({
                "entity": match.group(0),
                "country": country,
                "category": category,
                "method": method
            })

    return matches


def find_person(title):
    """
    Ищет персоналии в названии выставки.
    Используется только если география не найдена.
    """

    text = normalize(title)
    matches = []

    for name in sorted(PERSON_DICT.keys(), key=len, reverse=True):
        pattern = r"(?<!\w)" + re.escape(name) + r"(?!\w)"

        if re.search(pattern, text):
            country, category = PERSON_DICT[name]

            matches.append({
                "entity": name,
                "country": country,
                "category": category,
                "method": "person_curated_wikipedia_lookup"
            })

    unique = []
    seen = set()

    for item in matches:
        key = (
            item["entity"],
            item["country"],
            item["category"]
        )

        if key not in seen:
            unique.append(item)
            seen.add(key)

    return unique


def choose_classification(matches):
    """
    Выбирает итоговую классификацию.

    Логика:
    - если нет совпадений -> Unknown
    - если есть West/East и Russia одновременно -> берем иностранный маркер
    - если есть только Russia -> Russia
    - если есть West и East одновременно -> Mixed_East_West
    """

    if not matches:
        return {
            "detected_entity": "",
            "detected_country": "",
            "category_final": "Unknown",
            "classification_method": "unknown",
            "all_matches": "",
            "confidence": "review"
        }

    non_russia = [
        item for item in matches
        if item["category"] in ["West", "East"]
    ]

    if non_russia:
        categories = sorted(set(item["category"] for item in non_russia))

        if len(categories) == 1:
            category_final = categories[0]
        else:
            category_final = "Mixed_East_West"

        detected_country = "; ".join(
            dict.fromkeys(item["country"] for item in non_russia)
        )

        detected_entity = "; ".join(
            dict.fromkeys(item["entity"] for item in non_russia)
        )

        method = "+".join(
            dict.fromkeys(item["method"] for item in non_russia)
        )

        used_matches = non_russia

    else:
        category_final = "Russia"

        detected_country = "; ".join(
            dict.fromkeys(item["country"] for item in matches)
        )

        detected_entity = "; ".join(
            dict.fromkeys(item["entity"] for item in matches)
        )

        method = "+".join(
            dict.fromkeys(item["method"] for item in matches)
        )

        used_matches = matches

    if any(item["method"] == "geo_title" for item in matches):
        confidence = "high"
    else:
        confidence = "medium"

    all_matches = " | ".join(
        f"{item['entity']} → {item['country']}/{item['category']} ({item['method']})"
        for item in matches
    )

    return {
        "detected_entity": detected_entity,
        "detected_country": detected_country,
        "category_final": category_final,
        "classification_method": method,
        "all_matches": all_matches,
        "confidence": confidence
    }

df = pd.read_csv(INPUT_FILE)

rows = []

for _, row in df.iterrows():

    title = row.get("title", "")
    geo_matches = find_geo(title)

    if geo_matches:
        person_matches = []
    else:
        person_matches = find_person(title)

    matches = geo_matches or person_matches

    classification = choose_classification(matches)

    new_row = row.to_dict()
    new_row.update(classification)

    new_row["wikipedia_check_needed"] = (
        new_row["category_final"] == "Unknown"
        or new_row["classification_method"] == "person_curated_wikipedia_lookup"
    )

    if new_row["category_final"] == "Unknown":
        new_row["wikipedia_search_url"] = (
            "https://ru.wikipedia.org/w/index.php?search="
            + quote(str(title))
        )
    else:
        new_row["wikipedia_search_url"] = ""

    rows.append(new_row)


out = pd.DataFrame(rows)



out.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)



review = out[
    (out["category_final"] == "Unknown")
    | (out["confidence"] == "medium")
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
    "wikipedia_search_url"
]

review[review_columns].to_csv(
    REVIEW_FILE,
    index=False,
    encoding="utf-8-sig"
)


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


print("Saved:", OUTPUT_FILE)
print("Rows:", out.shape)

print()
print("Category counts:")
print(out["category_final"].value_counts())

print()
print("By period:")
print(pd.crosstab(out["period"], out["category_final"]))

print()
print("Manual review rows:", len(review))