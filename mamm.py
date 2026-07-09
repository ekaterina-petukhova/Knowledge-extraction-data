import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import pandas as pd
import re
import time


BASE_URL = "https://mamm-mdf.ru"
ARCHIVE_URL = "https://mamm-mdf.ru/en/exhibitions/{year}/"


def clean_text(text):
    if text is None:
        return ""
    return re.sub(r"\s+", " ", str(text)).strip()


def extract_year_from_text(text):
    years = re.findall(r"20\d{2}|19\d{2}", str(text))
    if years:
        return int(years[-1])
    return None


def assign_period(year):
    if year is None:
        return "unknown"
    elif 2014 <= year <= 2021:
        return "pre_2022"
    elif year == 2022:
        return "transition_2022"
    elif 2023 <= year <= 2026:
        return "post_2022"
    else:
        return "outside_scope"


def get_soup(url):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()

    return BeautifulSoup(response.text, "html.parser")


def collect_links_for_year(year):
    """
    Собирает ссылки на выставки MAMM за конкретный год.
    """
    url = ARCHIVE_URL.format(year=year)
    print(f"\nОткрываю архив за {year}: {url}")

    try:
        soup = get_soup(url)
    except Exception as e:
        print(f"Ошибка при открытии {year}:", e)
        return []

    items = []

    for a in soup.find_all("a"):
        href = a.get("href")
        text = clean_text(a.get_text(" "))

        if not href:
            continue

        href = urljoin(BASE_URL, href)
        href = href.split("?")[0].split("#")[0]

        if not href.startswith("https://mamm-mdf.ru/en/exhibitions/"):
            continue

        # Убираем саму годовую страницу
        if href.rstrip("/") == url.rstrip("/"):
            continue

        # Убираем общую страницу Exhibitions
        if href.rstrip("/") == "https://mamm-mdf.ru/en/exhibitions":
            continue

        # Нам нужны только страницы отдельных выставок:
        # https://mamm-mdf.ru/en/exhibitions/name/
        parts = href.replace("https://mamm-mdf.ru/en/exhibitions/", "").strip("/").split("/")

        if len(parts) != 1:
            continue

        slug = parts[0]

        # Годовые страницы типа /2025/ не берем
        if re.fullmatch(r"\d{4}", slug):
            continue

        if len(text) == 0:
            continue

        items.append({
            "museum": "Multimedia Art Museum Moscow",
            "archive_year": year,
            "raw_text": text,
            "url": href.rstrip("/")
        })

    print(f"Найдено ссылок за {year}:", len(items))
    return items


def collect_all_archive_links():
    all_items = []

    for year in range(2014, 2027):
        items = collect_links_for_year(year)
        all_items.extend(items)
        time.sleep(0.5)

    df_links = pd.DataFrame(all_items)

    if len(df_links) == 0:
        return df_links

    df_links = df_links.drop_duplicates(subset=["url"]).reset_index(drop=True)

    return df_links


def parse_exhibition_page(url):
    """
    Парсит отдельную страницу выставки MAMM.
    """
    try:
        soup = get_soup(url)

        page_text = clean_text(soup.get_text(" "))

        title = None
        h1 = soup.find("h1")
        if h1:
            title = clean_text(h1.get_text(" "))

        date_patterns = [
            r"\d{1,2}\.\d{1,2}\.20\d{2}\s*[—–-]\s*\d{1,2}\.\d{1,2}\.20\d{2}",
            r"\d{1,2}\s+[a-zA-Z]+\s+20\d{2}\s*[—–-]\s*\d{1,2}\s+[a-zA-Z]+\s+20\d{2}",
            r"\d{1,2}\s+[a-zA-Z]+\s*[—–-]\s*\d{1,2}\s+[a-zA-Z]+\s+20\d{2}",
            r"\d{1,2}\s+[a-zA-Z]+\s+20\d{2}",
            r"20\d{2}",
        ]

        date_range = None

        for pattern in date_patterns:
            date_match = re.search(pattern, page_text)
            if date_match:
                date_range = date_match.group(0)
                break

        if date_range:
            year = extract_year_from_text(date_range)
        else:
            year = extract_year_from_text(page_text)

        period = assign_period(year)

        return {
            "museum": "Multimedia Art Museum Moscow",
            "title": title,
            "date_range": date_range,
            "year": year,
            "period": period,
            "url": url,
            "description": page_text[:3000]
        }

    except Exception as e:
        print("Ошибка при парсинге страницы:", url, e)
        return None


def parse_all_exhibition_pages(df_links):
    rows = []

    urls = df_links["url"].dropna().drop_duplicates().tolist()

    for i, url in enumerate(urls):
        print(f"\nПарсинг выставки {i + 1}/{len(urls)}")
        print(url)

        item = parse_exhibition_page(url)

        if item:
            rows.append(item)

        time.sleep(0.5)

    return pd.DataFrame(rows)


def main():
    print("STEP 1: собираю ссылки MAMM")

    df_links = collect_all_archive_links()

    print("\nИтого уникальных ссылок:", len(df_links))

    if len(df_links) == 0:
        print("Ссылки не найдены.")
        return

    df_links.to_csv("mamm_archive_links_all_years.csv", index=False, encoding="utf-8-sig")
    print("Ссылки сохранены: mamm_archive_links_all_years.csv")

    print("\nSTEP 2: парсю каждую страницу выставки")

    df = parse_all_exhibition_pages(df_links)

    if len(df) == 0:
        print("Данные выставок не собраны.")
        return

    df = df[df["period"] != "outside_scope"]

    df.to_csv("mamm_exhibitions_2014_2026.csv", index=False, encoding="utf-8-sig")

    print("\nГотово!")
    print("Собрано выставок 2014–2026:", len(df))
    print("Файл сохранен: mamm_exhibitions_2014_2026.csv")

    print("\nПервые строки:")
    print(df[["title", "date_range", "year", "period", "url"]].head(30).to_string())

    print("\nРаспределение по периодам:")
    print(df["period"].value_counts())


if __name__ == "__main__":
    main()