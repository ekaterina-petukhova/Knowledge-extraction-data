import csv
import os
import re
import time
from urllib.parse import urljoin
import bs4
import pandas as pd
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://rusmuseum.ru"
ARCHIVE_URL = "https://rusmuseum.ru/exhibitions/archive"

# Файлы вывода
OUTPUT_FILE = "russian_museum_exhibitions_2014_2026_updated.csv"
PAGE_ERRORS_FILE = "page_parsing_errors.csv"
EXHIBITION_ERRORS_FILE = "exhibition_parsing_errors.csv"

START_PAGE = 1
END_PAGE = 74

MONTHS_RU = {
    "января": "01",
    "февраля": "02",
    "марта": "03",
    "апреля": "04",
    "мая": "05",
    "июня": "06",
    "июля": "07",
    "августа": "08",
    "сентября": "09",
    "октября": "10",
    "ноября": "11",
    "декабря": "12",
}


def clean_text(text):
    if text is None:
        return ""
    return re.sub(r"\s+", " ", str(text)).strip()


def log_error_to_csv(file_path, fieldnames, row_dict):
    """Записывает ошибку или предупреждение парсинга в нужный CSV файл."""
    file_exists = os.path.exists(file_path)
    with open(file_path, mode="a", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row_dict)


def extract_years_from_ru_text(text):
    """Находит все 4-значные года в тексте."""
    return [int(y) for y in re.findall(r"20\d{2}|19\d{2}", str(text))]


def get_period_from_years(years):
    """Распределяет выставку по периодам исходя из найденных лет."""
    if not years:
        return "unknown", None

    start_year = min(years)
    end_year = max(years)

    if end_year < 2014:
        return "outside_scope", end_year
    if start_year > 2026:
        return "outside_scope", start_year
    if start_year <= 2022 <= end_year:
        return "transition_2022", 2022
    if 2014 <= end_year <= 2021:
        return "pre_2022", end_year
    if 2023 <= start_year <= 2026:
        return "post_2022", start_year

    return "outside_scope", end_year


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
    return f"{ARCHIVE_URL}?page={page_number}&set_filter=y&arrFilter_375_MAX=31.12.2026&arrFilter_376_MIN=01.01.2014"


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

    card_items = soup.find_all(class_="event-list__item")
    if not card_items:
        card_items = soup.find_all(class_="tile card")

    rows = []

    for index, item in enumerate(card_items, start=1):
        try:
            # 1. Название выставки (парсим в начале)
            title_tag = item.find(class_="event-title-name") or item.find("h3")
            title = clean_text(title_tag.get_text()) if title_tag else None
            if not title:
                title = clean_text(item.get("aria-label"))

            if not title:
                raise ValueError("Не удалось извлечь название выставки")

            # 2. Ссылка на выставку (с логированием отсутствия, но без падения)
            link_tag = item.find("a", href=True)
            if link_tag:
                href = link_tag.get("href")
                exhibition_url = urljoin(BASE_URL, href).split("?")[0].split("#")[0].rstrip("/")
            else:
                exhibition_url = None
                # Принудительно логируем карточку без ссылки в CSV для ошибок
                item_html = str(item)[:500] + "..." if item else "None"
                log_error_to_csv(
                    EXHIBITION_ERRORS_FILE,
                    ["page_number", "card_index", "error", "html_snippet"],
                    {
                        "page_number": page_number,
                        "card_index": index,
                        "error": "Отсутствует тег ссылки <a> (карточка сохранена без URL)",
                        "html_snippet": item_html,
                    },
                )
                print(f"   [!] Карточка #{index} на стр. {page_number} ('{title}') не имеет ссылки. Записано в лог ошибок.")

            # 3. Диапазон дат
            date_tag = item.find(class_="event-date")
            if not date_tag:
                raise ValueError("Не найден контейнер даты '.event-date'")

            date_range = clean_text(date_tag.get_text(" "))

            # Вычисляем года для фильтрации / проставления периода
            years = extract_years_from_text_or_ru(date_range)
            period, year = get_period_from_years(years)

            # 4. Описание (краткий анонс карточки)
            desc_tag = item.find(class_="event-about-text") or item.find(
                class_="paragraph"
            )
            description = clean_text(desc_tag.get_text()) if desc_tag else ""

            # 5. Место проведения (Дворец / Филиал)
            place_tag = item.find("a", class_="building")
            place = (
                clean_text(place_tag.get_text())
                if place_tag
                else "Русский музей"
            )

            rows.append(
                {
                    "museum": "Русский музей",
                    "place": place,
                    "title": title,
                    "date_range": date_range,
                    "year": year,
                    "period": period,
                    "url": exhibition_url,
                    "description": description[:3000],
                }
            )

        except Exception as e:
            # Сюда скрипт попадет только при критических ошибках (например, если нет названия или блока дат)
            error_msg = f"Критическая ошибка парсинга карточки #{index} на странице {page_number}: {e}"
            print(error_msg)
            item_html = str(item)[:500] + "..." if item else "None"
            log_error_to_csv(
                EXHIBITION_ERRORS_FILE,
                ["page_number", "card_index", "error", "html_snippet"],
                {
                    "page_number": page_number,
                    "card_index": index,
                    "error": str(e),
                    "html_snippet": item_html,
                },
            )

    # Локальное удаление дубликатов на странице
    unique = {}
    for row in rows:
        key = row["url"] if row["url"] else f"no_url_{row['title']}"
        unique[key] = row

    print(f"Успешно собрано выставок на странице: {len(unique)}")
    return list(unique.values())


def extract_years_from_text_or_ru(text):
    """Ищет года как стандартным regex, так и проверяя текстовые упоминания."""
    years = extract_years_from_text(text)
    if years:
        return years
    return []


def extract_years_from_text(text):
    return [int(y) for y in re.findall(r"20\d{2}|19\d{2}", str(text))]


def main():
    print("СТАРТ: Сбор архива Русского музея с rusmuseum.ru (2014-2026)")

    all_rows = []

    for page_number in range(START_PAGE, END_PAGE + 1):
        page_rows = collect_exhibitions_from_archive_page(page_number)
        all_rows.extend(page_rows)

        time.sleep(1.0)

    df = pd.DataFrame(all_rows)

    if len(df) == 0:
        print("\n[!] Данные не были собраны. Проверьте файлы ошибок.")
        return

    # Финальная очистка от дубликатов по комбинации названия и URL
    df = df.drop_duplicates(subset=["title", "url"]).reset_index(drop=True)

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

    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")

    print("\n" + "=" * 50)
    print("Парсинг успешно завершен!")
    print(f"Всего уникальных выставок сохранено: {len(df)}")
    print(f"Основной файл: {OUTPUT_FILE}")
    print(f"Журнал ошибок страниц: {PAGE_ERRORS_FILE}")
    print(f"Журнал ошибок карточек: {EXHIBITION_ERRORS_FILE}")
    print("=" * 50)


if __name__ == "__main__":
    main()