import csv
import os
import re
import time
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.theartnewspaper.ru"
ARCHIVE_URL = "https://www.theartnewspaper.ru/posts/"
SECTION = "shows"

# Файлы вывода
OUTPUT_FILE = "art_newspaper_exhibitions_2014_2026.csv"
PAGE_ERRORS_FILE = "art_newspaper_page_errors.csv"

START_PAGE = 1
END_PAGE = 264


def clean_text(text):
    if text is None:
        return ""
    return re.sub(r"\s+", " ", str(text)).strip()


def log_error_to_csv(file_path, fieldnames, row_dict):
    file_exists = os.path.exists(file_path)
    with open(file_path, mode="a", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row_dict)


def get_period_from_year(year):
    """Та же логика периодов, что и в остальных скраперах проекта."""
    if year is None:
        return "unknown"
    if year < 2014:
        return "outside_scope"
    if year > 2026:
        return "outside_scope"
    if year == 2022:
        return "transition_2022"
    if 2014 <= year <= 2021:
        return "pre_2022"
    if 2023 <= year <= 2026:
        return "post_2022"
    return "outside_scope"


def get_soup(url):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    }
    response = requests.get(url, headers=headers, timeout=40)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")


def make_archive_page_url(page_number):
    return f"{ARCHIVE_URL}?page={page_number}&section={SECTION}"


def collect_exhibitions_from_archive_page(page_number):
    url = make_archive_page_url(page_number)
    print(f"\n[Страница {page_number}/{END_PAGE}] Загружаю: {url}")

    try:
        soup = get_soup(url)
    except Exception as e:
        print(f"Ошибка загрузки страницы {page_number}: {e}")
        log_error_to_csv(
            PAGE_ERRORS_FILE,
            ["page_number", "url", "error"],
            {"page_number": page_number, "url": url, "error": str(e)},
        )
        return []

    rows = []

    card_items = soup.find_all("a", class_="postPreviewsItem", href=True)

    for item in card_items:
        try:
            href = item["href"]
            full_url = urljoin(BASE_URL, href).split("?")[0].rstrip("/")

            title = clean_text(item.get("title"))
            if not title:
                title_tag = item.find(class_="postPreviewsItemTitle")
                title = clean_text(title_tag.get_text()) if title_tag else None
            if not title:
                raise ValueError("Не удалось извлечь название статьи")

            section_tag = item.find(class_="postPreviewsItemSection")
            section = clean_text(section_tag.get_text()) if section_tag else ""

            desc_tag = item.find(class_="postPreviewsItemTitle2")
            description = clean_text(desc_tag.get_text()) if desc_tag else ""

            date_tag = item.find(class_="postPreviewsItemDate")
            date_range = clean_text(date_tag.get_text()) if date_tag else None

            year = None
            if date_range:
                date_match = re.search(r"(\d{2})\.(\d{2})\.(\d{4})", date_range)
                if date_match:
                    year = int(date_match.group(3))

            period = get_period_from_year(year)

            rows.append(
                {
                    "museum": "The Art Newspaper Russia",
                    "place": section,  
                    "title": title,
                    "date_range": date_range,
                    "year": year,
                    "period": period,
                    "url": full_url,
                    "description": description[:3000],
                }
            )

        except Exception as e:
            print(f"Ошибка парсинга карточки на странице {page_number}: {e}")
            item_html = str(item)[:500] + "..." if item else "None"
            log_error_to_csv(
                "art_newspaper_card_errors.csv",
                ["page_number", "error", "html_snippet"],
                {"page_number": page_number, "error": str(e), "html_snippet": item_html},
            )
    unique = {}
    for row in rows:
        key = row["url"] if row["url"] else f"no_url_{row['title']}"
        unique[key] = row

    print(f"Успешно собрано статей на странице: {len(unique)}")
    return list(unique.values())


def main():
    print("СТАРТ: Сбор архива The Art Newspaper Russia, раздел 'Выставки' (2013-2026)")

    all_rows = []

    for page_number in range(START_PAGE, END_PAGE + 1):
        page_rows = collect_exhibitions_from_archive_page(page_number)
        all_rows.extend(page_rows)

        time.sleep(1.0)

    df = pd.DataFrame(all_rows)

    if len(df) == 0:
        print("\n[!] Данные не были собраны. Проверьте файл ошибок.")
        return


    df = df.drop_duplicates(subset=["url"]).reset_index(drop=True)


    df = df[df["period"] != "outside_scope"]

    df = df[
        [
            "museum",
            "place",
            "title",
            "date_range",
            "year",
            "period",
            "url",
            "description",
        ]
    ]

    df = df.sort_values(by="year", ascending=True).reset_index(drop=True)

    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")

    print("\n" + "=" * 50)
    print("Парсинг успешно завершен!")
    print(f"Всего уникальных статей сохранено: {len(df)}")
    print(f"Основной файл: {OUTPUT_FILE}")
    print(f"Журнал ошибок страниц: {PAGE_ERRORS_FILE}")
    print("=" * 50)

    print("\nРаспределение по периодам:")
    print(df["period"].value_counts())


if __name__ == "__main__":
    main()