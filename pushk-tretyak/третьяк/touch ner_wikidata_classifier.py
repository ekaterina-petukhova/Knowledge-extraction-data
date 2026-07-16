import pandas as pd
import requests
import time
import re

from natasha import (
    Segmenter,
    NewsEmbedding,
    NewsNERTagger,
    Doc
)


INPUT_FILE = "museum_exhibitions_enriched.csv"
OUTPUT_ENTITIES = "entities_extracted.csv"
OUTPUT_CLASSIFIED = "entities_classified_wikidata.csv"
OUTPUT_EXHIBITIONS = "exhibitions_with_geo_orientation.csv"

WEST_COUNTRIES = {
    "France", "Italy", "Germany", "United Kingdom", "United States of America",
    "Spain", "Portugal", "Netherlands", "Belgium", "Austria", "Switzerland",
    "Sweden", "Norway", "Denmark", "Finland", "Poland", "Czech Republic",
    "Greece", "Ireland", "Canada", "Australia"
}

EAST_COUNTRIES = {
    "China", "Japan", "India", "Iran", "Turkey", "Oman", "Uzbekistan",
    "Kazakhstan", "Kyrgyzstan", "Tajikistan", "Turkmenistan", "Armenia",
    "Azerbaijan", "Georgia", "Mongolia", "Vietnam", "Korea", "South Korea",
    "North Korea", "Egypt", "Iraq", "Syria", "Saudi Arabia"
}

RUSSIA_NAMES = {
    "Russia", "Russian Empire", "Soviet Union", "Russian Federation"
}

segmenter = Segmenter()
emb = NewsEmbedding()
ner_tagger = NewsNERTagger(emb)


def clean_text(text):
    if pd.isna(text):
        return ""
    return re.sub(r"\s+", " ", str(text)).strip()


def extract_entities_natasha(text):
    """
    Natasha достает PER, ORG, LOC.
    Для нас важны ORG и LOC, но PER тоже можно оставить.
    """
    text = clean_text(text)

    if not text:
        return []

    doc = Doc(text[:5000])
    doc.segment(segmenter)
    doc.tag_ner(ner_tagger)

    entities = []

    for span in doc.spans:
        entities.append({
            "entity": span.text,
            "entity_type": span.type
        })

    return entities

def wikidata_search(entity):
    """
    Ищет entity в Wikidata.
    Возвращает QID и label.
    """
    url = "https://www.wikidata.org/w/api.php"

    params = {
        "action": "wbsearchentities",
        "search": entity,
        "language": "ru",
        "format": "json",
        "limit": 1
    }

    try:
        r = requests.get(url, params=params, timeout=20)
        data = r.json()

        if data.get("search"):
            item = data["search"][0]
            return {
                "qid": item.get("id"),
                "wikidata_label": item.get("label"),
                "wikidata_description": item.get("description")
            }

    except Exception as e:
        print("Wikidata search error:", entity, e)

    return {
        "qid": None,
        "wikidata_label": None,
        "wikidata_description": None
    }


def wikidata_get_claims(qid):
    """
    Получает claims объекта Wikidata.
    Нам нужны:
    P17 = country
    P27 = country of citizenship
    P495 = country of origin
    P131 = located in administrative territorial entity
    """
    if not qid:
        return {}

    url = "https://www.wikidata.org/wiki/Special:EntityData/{}.json".format(qid)

    try:
        r = requests.get(url, timeout=20)
        data = r.json()
        entity = data["entities"][qid]
        return entity.get("claims", {})

    except Exception as e:
        print("Wikidata claims error:", qid, e)
        return {}


def extract_qids_from_claims(claims, properties):
    qids = []

    for prop in properties:
        if prop not in claims:
            continue

        for claim in claims[prop]:
            try:
                value = claim["mainsnak"]["datavalue"]["value"]
                qid_num = value["numeric-id"]
                qids.append("Q" + str(qid_num))
            except Exception:
                pass

    return list(set(qids))


def wikidata_get_label(qid, lang="en"):
    if not qid:
        return None

    url = "https://www.wikidata.org/wiki/Special:EntityData/{}.json".format(qid)

    try:
        r = requests.get(url, timeout=20)
        data = r.json()
        entity = data["entities"][qid]
        labels = entity.get("labels", {})

        if lang in labels:
            return labels[lang]["value"]

        if "en" in labels:
            return labels["en"]["value"]

    except Exception:
        return None

    return None


def classify_country_name(country_name):
    if not country_name:
        return "unknown"

    if country_name in RUSSIA_NAMES:
        return "internal_russia"

    if country_name in WEST_COUNTRIES:
        return "west"

    if country_name in EAST_COUNTRIES:
        return "east"

    return "unknown"


def classify_entity_with_wikidata(entity):
    """
    1. Ищем entity в Wikidata
    2. Достаем связанные страны
    3. Классифицируем West/East/Internal Russia
    """
    search = wikidata_search(entity)
    qid = search["qid"]

    if not qid:
        return {
            "entity": entity,
            "qid": None,
            "wikidata_label": None,
            "wikidata_description": None,
            "country": None,
            "geo_orientation": "unknown"
        }

    claims = wikidata_get_claims(qid)

    country_qids = extract_qids_from_claims(claims, ["P17", "P27", "P495"])

    countries = []

    for cqid in country_qids:
        label = wikidata_get_label(cqid, lang="en")
        if label:
            countries.append(label)

    countries = list(set(countries))

    orientations = [classify_country_name(c) for c in countries]
    orientations = [o for o in orientations if o != "unknown"]

    if "internal_russia" in orientations:
        orientation = "internal_russia"
    elif "east" in orientations:
        orientation = "east"
    elif "west" in orientations:
        orientation = "west"
    else:
        orientation = "unknown"

    return {
        "entity": entity,
        "qid": qid,
        "wikidata_label": search["wikidata_label"],
        "wikidata_description": search["wikidata_description"],
        "country": "; ".join(countries),
        "geo_orientation": orientation
    }


def classify_exhibition(entity_rows):
    """
    Логика:
    - если есть west → exhibition has west signal
    - если есть east → exhibition has east signal
    - если есть internal_russia → internal signal
    Потом можно дать итоговый label.
    """
    orientations = entity_rows["geo_orientation"].dropna().tolist()

    west_count = orientations.count("west")
    east_count = orientations.count("east")
    internal_count = orientations.count("internal_russia")

    if west_count > east_count and west_count > internal_count:
        return "west_oriented"
    elif east_count > west_count and east_count > internal_count:
        return "east_oriented"
    elif internal_count > west_count and internal_count > east_count:
        return "internal_russia_oriented"
    elif west_count == 0 and east_count == 0 and internal_count == 0:
        return "unknown"
    else:
        return "mixed"


def main():
    df = pd.read_csv(INPUT_FILE)

    if "description" not in df.columns:
        raise ValueError("Нужна колонка description. Сначала допарси описания выставок.")

    entity_rows = []

    print("STEP 1: extracting entities with Natasha...")

    for i, row in df.iterrows():
        text = clean_text(row.get("title", "")) + ". " + clean_text(row.get("description", ""))

        print(f"{i + 1}/{len(df)} {row.get('title', '')}")

        entities = extract_entities_natasha(text)

        for ent in entities:
            entity_rows.append({
                "museum": row.get("museum", ""),
                "exhibition_title": row.get("title", ""),
                "exhibition_year": row.get("year", ""),
                "exhibition_period": row.get("period", ""),
                "exhibition_url": row.get("url", ""),
                "entity": ent["entity"],
                "entity_type": ent["entity_type"]
            })

    df_entities = pd.DataFrame(entity_rows)
    df_entities = df_entities.drop_duplicates()

    df_entities.to_csv(OUTPUT_ENTITIES, index=False, encoding="utf-8-sig")
    print("Saved:", OUTPUT_ENTITIES)

    print("\nSTEP 2: classifying entities with Wikidata...")

    unique_entities = df_entities["entity"].dropna().drop_duplicates().tolist()

    classified_cache = {}

    for i, entity in enumerate(unique_entities):
        print(f"{i + 1}/{len(unique_entities)} {entity}")

        result = classify_entity_with_wikidata(entity)
        classified_cache[entity] = result

        time.sleep(0.3)

    classified_rows = []

    for _, row in df_entities.iterrows():
        entity = row["entity"]
        classification = classified_cache.get(entity, {})

        out = row.to_dict()
        out.update(classification)
        classified_rows.append(out)

    df_classified = pd.DataFrame(classified_rows)
    df_classified.to_csv(OUTPUT_CLASSIFIED, index=False, encoding="utf-8-sig")
    print("Saved:", OUTPUT_CLASSIFIED)

    print("\nSTEP 3: aggregating exhibition orientation...")

    exhibition_labels = []

    for title, group in df_classified.groupby("exhibition_title"):
        label = classify_exhibition(group)

        west_count = (group["geo_orientation"] == "west").sum()
        east_count = (group["geo_orientation"] == "east").sum()
        internal_count = (group["geo_orientation"] == "internal_russia").sum()

        exhibition_labels.append({
            "exhibition_title": title,
            "entity_west_count": west_count,
            "entity_east_count": east_count,
            "entity_internal_russia_count": internal_count,
            "ner_geo_orientation": label
        })

    df_labels = pd.DataFrame(exhibition_labels)

    df_final = df.merge(
        df_labels,
        left_on="title",
        right_on="exhibition_title",
        how="left"
    )

    df_final.to_csv(OUTPUT_EXHIBITIONS, index=False, encoding="utf-8-sig")

    print("Saved:", OUTPUT_EXHIBITIONS)

    print("\nSummary:")
    print(df_final["ner_geo_orientation"].value_counts(dropna=False))

    print("\nExamples:")
    cols = [
        "museum",
        "title",
        "year",
        "period",
        "entity_west_count",
        "entity_east_count",
        "entity_internal_russia_count",
        "ner_geo_orientation"
    ]
    print(df_final[cols].head(30).to_string())


if __name__ == "__main__":
    main()