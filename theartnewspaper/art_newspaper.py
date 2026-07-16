import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import pandas as pd
import re
import time


BASE_URL = "https://www.theartnewspaper.ru"
FIRST_PAGE_URL = "https://www.theartnewspaper.ru/sections/shows/"


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
        ),
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    }

    response = requests.get(url, headers=headers, timeout=40)
    response.raise_for_status()

    return BeautifulSoup(response.text, "html.parser")


def make_section_page_url(page_number):
    if page_number == 1:
        return FIRST_PAGE_URL

    return f"https://www.theartnewspaper.ru/posts/?section=shows&page={page_number}"


def normalize_article_url(href):
    if not href:
        return None

    href = urljoin(BASE_URL, href)
    href = href.split("?")[0].split("#")[0].rstrip("/")

    if not href.startswith(BASE_URL):
        return None

    if "/posts/" not in href:
        return None

    return href


def collect_articles_from_section_page(page_number):
    url = make_section_page_url(page_number)

    print(f"\nОткрываю страницу {page_number}: {url}")

    try:
        soup = get_soup(url)
    except Exception as e:
        print("Ошибка при открытии страницы:", e)
        return []

    items = []

    for a in soup.find_all("a"):
        href = a.get("href")
        text = clean_text(a.get_text(" "))

        article_url = normalize_article_url(href)

        if not article_url:
            continue

        if len(text) < 15:
            continue

        if "Выставки" not in text and "выстав" not in text.lower():
            continue

        items.append({
            "source": "The Art Newspaper Russia",
            "section": "shows",
            "raw_title": text,
            "url": article_url,
        })

    df = pd.DataFrame(items)

    if len(df) == 0:
        print("Статей на странице не найдено.")
        return []

    df = df.drop_duplicates(subset=["url"]).reset_index(drop=True)

    print("Найдено статей на странице:", len(df))

    return df.to_dict("records")


def parse_article_page(url):
    try:
        soup = get_soup(url)

        page_text = clean_text(soup.get_text(" "))

        title = None
        h1 = soup.find("h1")
        if h1:
            title = clean_text(h1.get_text(" "))

        date_patterns = [
            r"\d{2}\.\d{2}\.20\d{2}",
            r"\d{1,2}\s+[а-яёА-ЯЁ]+\s+20\d{2}",
            r"20\d{2}",
        ]

        publication_date = None

        for pattern in date_patterns:
            m = re.search(pattern, page_text)
            if m:
                publication_date = m.group(0)
                break

        year = extract_year_from_text(publication_date or page_text)
        period = assign_period(year)

        museum_keywords = [
            "Эрмитаж",
            "Третьяков",
            "Третьяковская галерея",
            "Русский музей",
            "Пушкинский музей",
            "ГМИИ",
            "Garage",
            "Гараж",
            "ГЭС-2",
            "MAMM",
            "Мультимедиа Арт Музей",
            "Еврейский музей",
            "Музей Москвы",
            "Музей русского импрессионизма",
            "Новая Третьяковка",
            "Манеж",
            "Музей Анны Ахматовой",
            "Музей Фаберже",
            "Дом русского зарубежья",
            "Новый Иерусалим",
            "Пакгауз",
            "Фабрика",
        ]

        foreign_keywords = [
            "международ",
            "зарубеж",
            "иностран",
            "Франц",
            "Герм",
            "Итал",
            "США",
            "Америка",
            "Китай",
            "Япон",
            "Инд",
            "Брит",
            "Лондон",
            "Париж",
            "Берлин",
            "Венециан",
            "Афины",
            "Европ",
            "Баухаус",
            "MoMA",
            "МоМА",
            "Tate",
            "Centre Pompidou",
            "Британский музей",
            "Токио",
        ]

        mentioned_museums = [
            keyword for keyword in museum_keywords
            if keyword.lower() in page_text.lower()
        ]

        foreign_entities = [
            keyword for keyword in foreign_keywords
            if keyword.lower() in page_text.lower()
        ]

        return {
            "source": "The Art Newspaper Russia",
            "title": title,
            "publication_date": publication_date,
            "year": year,
            "period": period,
            "url": url,
            "mentioned_museums": "; ".join(mentioned_museums),
            "foreign_entities": "; ".join(foreign_entities),
            "text": page_text[:5000],
        }

    except Exception as e:
        print("Ошибка при парсинге статьи:", url, e)
        return None


def main():
    print("STEP 1: собираю ссылки на статьи The Art Newspaper Russia")

    all_links = []

    for page_number in range(1, 81):
        items = collect_articles_from_section_page(page_number)

        if len(items) == 0 and page_number > 3:
            print("Похоже, страницы закончились.")
            break

        all_links.extend(items)
        time.sleep(0.5)

    df_links = pd.DataFrame(all_links)

    if len(df_links) == 0:
        print("Ссылки на статьи не найдены.")
        return

    df_links = df_links.drop_duplicates(subset=["url"]).reset_index(drop=True)

    df_links.to_csv("tanr_shows_article_links.csv", index=False, encoding="utf-8-sig")

    print("\nИтого уникальных ссылок:", len(df_links))
    print("Ссылки сохранены: tanr_shows_article_links.csv")

    print("\nSTEP 2: парсю статьи")

    rows = []

    urls = df_links["url"].dropna().drop_duplicates().tolist()

    for i, url in enumerate(urls):
        print(f"\nПарсинг статьи {i + 1}/{len(urls)}")
        print(url)

        item = parse_article_page(url)

        if item:
            rows.append(item)

        time.sleep(0.5)

    df = pd.DataFrame(rows)

    if len(df) == 0:
        print("Статьи не распарсились.")
        return

    df = df[df["period"] != "outside_scope"]

    df.to_csv("tanr_shows_articles_2014_2026.csv", index=False, encoding="utf-8-sig")

    print("\nГотово!")
    print("Собрано статей 2014–2026:", len(df))
    print("Файл сохранен: tanr_shows_articles_2014_2026.csv")

    print("\nПервые строки:")
    print(
        df[
            [
                "title",
                "publication_date",
                "year",
                "period",
                "mentioned_museums",
                "foreign_entities",
                "url",
            ]
        ].head(40).to_string()
    )

    print("\nРаспределение по периодам:")
    print(df["period"].value_counts())


if __name__ == "__main__":
    main()