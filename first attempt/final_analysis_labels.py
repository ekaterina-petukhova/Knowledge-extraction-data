import pandas as pd
import re


INPUT_FILE = "exhibitions_with_geo_orientation.csv"
OUTPUT_FILE = "final_exhibitions_labeled.csv"


df = pd.read_csv(INPUT_FILE)


def clean_text(x):
    if pd.isna(x):
        return ""
    x = str(x).lower()
    x = re.sub(r"\s+", " ", x)
    return x.strip()


def get_text(row):
    return clean_text(row.get("title", "")) + " " + clean_text(row.get("description", ""))


west_keywords = [
    "франц", "париж", "louis vuitton", "fondation", "лувр", "louvre",
    "помпиду", "pompidou", "итал", "рим", "венеци", "уффици",
    "герман", "немец", "берлин", "британ", "англи", "лондон",
    "tate", "british museum", "national gallery", "сша", "америк",
    "new york", "moma", "metropolitan", "guggenheim", "европ",
    "пикассо", "матисс", "моне", "сезанн", "ван гог", "импрессионизм",
    "постимпрессионизм", "ренессанс"
]

east_keywords = [
    "восток", "китай", "китайск", "япони", "индия", "иран", "оман",
    "турци", "центральная азия", "центральной азии", "узбекистан",
    "казахстан", "киргиз", "таджикистан", "туркменистан", "кавказ",
    "визант", "ислам", "персия", "араб"
]

internal_keywords = [
    "русск", "росси", "советск", "третьяков", "пушкинск", "гмии",
    "из собрания гмии", "из собрания третьяковской", "из фондов",
    "фонды музея", "собрание музея", "коллекция музея", "отдел",
    "дар", "поступление", "реставрац", "архив", "провенанс",
    "икон", "передвижник", "малевич", "репин", "суриков", "серов"
]

collab_cues = [
    "совместно с", "в сотрудничестве с", "при участии", "при поддержке",
    "организована совместно", "подготовлена совместно", "партнер",
    "партнёр", "предоставлены", "предоставил", "предоставила",
    "из собрания", "из коллекции"
]


def has_any(text, keywords):
    return any(k in text for k in keywords)


def classify_orientation(row):
    text = get_text(row)

    west = has_any(text, west_keywords)
    east = has_any(text, east_keywords)
    internal = has_any(text, internal_keywords)

    if west and not east and not internal:
        return "west_oriented"
    if east and not west:
        return "east_oriented"
    if internal and not west and not east:
        return "internal_russia_oriented"
    if west and east:
        return "mixed_west_east"
    if west and internal:
        return "mixed_west_internal"
    if east and internal:
        return "mixed_east_internal"

    return "unknown"


def calculate_pivot_score(row):
    text = get_text(row)

    score = 0

    if has_any(text, west_keywords):
        score -= 2

    if has_any(text, east_keywords):
        score += 2

    if has_any(text, internal_keywords):
        score += 1

    return score


def detect_foreign_collaboration(row):
    text = get_text(row)

    has_collab = has_any(text, collab_cues)
    has_foreign = has_any(text, west_keywords) or has_any(text, east_keywords)

    if has_collab and has_foreign:
        return "possible_yes"

    return "no"


def extract_context(row):
    text = get_text(row)
    sentences = re.split(r"(?<=[.!?])\s+", text)

    contexts = []

    for s in sentences:
        if has_any(s, collab_cues) and (has_any(s, west_keywords) or has_any(s, east_keywords)):
            contexts.append(s.strip())

    return " | ".join(contexts[:3])


df["final_orientation"] = df.apply(classify_orientation, axis=1)
df["pivot_score"] = df.apply(calculate_pivot_score, axis=1)
df["foreign_collaboration_recheck"] = df.apply(detect_foreign_collaboration, axis=1)
df["foreign_collaboration_context_recheck"] = df.apply(extract_context, axis=1)

df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")

print("Создан файл:", OUTPUT_FILE)

print("\nПо периодам:")
print(df["period"].value_counts())

print("\nФинальная ориентация:")
print(df["final_orientation"].value_counts())

print("\nСредний pivot_score по периодам:")
print(df.groupby("period")["pivot_score"].mean())

print("\nСредний pivot_score по музеям и периодам:")
print(df.groupby(["museum", "period"])["pivot_score"].mean())

print("\nВозможные иностранные коллаборации:")
cols = [
    "museum", "title", "year", "period",
    "foreign_collaboration_recheck",
    "foreign_collaboration_context_recheck",
    "url"
]
print(df[df["foreign_collaboration_recheck"] == "possible_yes"][cols].head(30).to_string())