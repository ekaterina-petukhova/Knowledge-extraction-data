import re
import time

import pandas as pd
import requests
from bs4 import BeautifulSoup

INPUT_FILE = "pushkin_exhibitions_raw.csv"
OUTPUT_FILE = "pushkin_exhibitions_with_descriptions.csv"
ERRORS_FILE = "pushkin_description_errors.csv"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
}


def clean_text(text):
    if text is None:
        return ""
    return re.sub(r"\s+", " ", str(text)).strip()


def fetch_description(url):
    """
    Заходит на страницу конкретной выставки и забирает весь текст <body>.
    Дальше это потребует отдельной чистки (как cleaner.py для Эрмитажа) —
    на странице очень много меню/навигации вокруг самого текста описания.
    """
    try:
        response = requests.get(url, headers=HEADERS, timeout=40)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        body = soup.find("body")
        if not body:
            return None

        text = clean_text(body.get_text(" "))
        return text[:5000]

    except Exception as e:
        print(f"Ошибка при загрузке {url}: {e}")
        return None


def main():
    df = pd.read_csv(INPUT_FILE)
    print(f"Загружено выставок: {len(df)}")

    descriptions = []
    errors = []

    for i, row in df.iterrows():
        url = row.get("url")
        title = row.get("title", "")

        print(f"\n[{i + 1}/{len(df)}] {title}")

        if not isinstance(url, str) or not url.strip():
            print("  Нет URL, пропускаю.")
            descriptions.append(None)
            errors.append({"index": i, "title": title, "url": url, "error": "no url"})
            continue

        desc = fetch_description(url)

        if desc is None:
            errors.append({"index": i, "title": title, "url": url, "error": "fetch failed"})

        descriptions.append(desc)
        time.sleep(1.0)

    df["description"] = descriptions

    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
    print(f"\nСохранено: {OUTPUT_FILE}")

    if errors:
        pd.DataFrame(errors).to_csv(ERRORS_FILE, index=False, encoding="utf-8-sig")
        print(f"Ошибок при сборе: {len(errors)}. Записаны в {ERRORS_FILE}")

    empty_count = df["description"].isna().sum()
    print(f"\nВсего записей: {len(df)}")
    print(f"Без описания: {empty_count}")
    print(f"С описанием: {len(df) - empty_count}")


if __name__ == "__main__":
    main()