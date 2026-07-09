import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import pandas as pd
import re
import time


BASE_URL = "https://artguide.ru"
START_URL = "https://artguide.ru/events?full_name=&city=Moscow&start_date=&end_date=&kind=past"


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


def make_page_url(page_number):
    if page_number == 1:
        return START_URL

    return (
        "https://artguide.ru/events"
        f"?full_name=&city=Moscow&start_date=&end_date=&kind=past&page={page_number}"
    )


def is_event_link(href):
    if not href:
        return False

    href = href.split("?")[0].split("#")[0]

    bad_parts = [
        "/events",
        "/addresses",
        "/news",
        "/articles",
        "/process",
        "/practice",
        "/theory",
        "/community",
        "/about",
        "/subscribe",
    ]

    if href.startswith("http") and not href.startswith(BASE_URL):
        return False

    if any(bad in href for bad in bad_parts):
        return False

    # У Artguide события чаще всего лежат отдельными короткими URL.
    # Берём ссылки, которые не похожи на меню/разделы.
    return True


def collect_events_from_page(page_number):
    url = make_page_url(page_number)

    print(f"\nОткрываю страницу {page_number}: {url}")

    try:
        soup = get_soup(url)
    except Exception as e:
        print("Ошибка при открытии страницы:", e)
        return []

    page_text = clean_text(soup.get_text(" "))

    # Берём только часть страницы после фильтров событий.
    # До этого на странице могут быть новости, меню и футер.
    marker = "Все Закрываются Открываются Эти выходные Прошедшие"
    if marker in page_text:
        events_text = page_text.split(marker, 1)[1]
    else:
        events_text = page_text

    # Разбиваем по датам формата 06.03-06.06.2026
    date_pattern = r"\d{2}\.\d{2}\s*[—–-]\s*\d{2}\.\d{2}\.\d{4}"
    chunks = re.split(f"({date_pattern})", events_text)

    rows = []

    for i in range(1, len(chunks), 2):
        date_range = clean_text(chunks[i])
        chunk = clean_text(chunks[i + 1]) if i + 1 < len(chunks) else ""

        if not chunk:
            continue

        # Обычно после даты идёт:
        # название выставки / площадка / Выставки
        parts = chunk.split(" Выставки ")

        before_type = parts[0]
        tokens = before_type.split(" ")

        # Это грубый способ, но для Artguide работает как первичный сбор:
        # название и площадку потом можно поправить вручную/допарсингом страницы.
        title = None
        venue = None

        # Берём до ближайшего длинного разделителя/служебных слов
        stop_words = [
            "Лекции",
            "Аукционы",
            "Фестивали",
            "Другое",
            "Ярмарки",
            "Загрузить еще",
            "Загрузить ещё",
        ]

        for stop in stop_words:
            if stop in before_type:
                before_type = before_type.split(stop)[0]

        # В тексте карточки чаще всего сначала название, потом площадка.
        # Поэтому оставляем весь блок как raw_text, а ниже парсим детальную страницу.
        year = extract_year_from_text(date_range)
        period = assign_period(year)

        rows.append({
            "source": "Artguide",
            "city": "Moscow",
            "date_range": date_range,
            "year": year,
            "period": period,
            "raw_text": before_type,
            "url": url
        })

    print("Найдено событий на странице:", len(rows))
    return rows


def collect_links_from_page(page_number):
    """
    Отдельно собирает ссылки на страницы событий.
    """
    url = make_page_url(page_number)

    try:
        soup = get_soup(url)
    except Exception:
        return []

    links = []

    for a in soup.find_all("a"):
        text = clean_text(a.get_text(" "))
        href = a.get("href")

        if not href:
            continue

        full_url = urljoin(BASE_URL, href)
        full_url = full_url.split("?")[0].split("#")[0].rstrip("/")

        if not text:
            continue

        # Отсекаем очевидное меню
        menu_words = [
            "Новости", "Открытия", "Практика", "Процесс", "Теория",
            "События", "Адреса", "Арт-сообщество", "Об Артгиде",
            "Выставки", "Москва", "Россия", "Санкт-Петербург",
            "Загрузить еще", "Загрузить ещё"
        ]

        if text in menu_words:
            continue

        if not full_url.startswith(BASE_URL):
            continue

        if "/events" in full_url:
            continue

        links.append({
            "page_number": page_number,
            "link_text": text,
            "event_url": full_url
        })

    return links


def parse_event_page(url):
    """
    Парсит отдельную страницу события, если ссылка открывается.
    """
    try:
        soup = get_soup(url)
        text = clean_text(soup.get_text(" "))

        title = None
        h1 = soup.find("h1")
        if h1:
            title = clean_text(h1.get_text(" "))

        date_patterns = [
            r"\d{2}\.\d{2}\s*[—–-]\s*\d{2}\.\d{2}\.\d{4}",
            r"\d{2}\.\d{2}\.\d{4}\s*[—–-]\s*\d{2}\.\d{2}\.\d{4}",
            r"\d{1,2}\s+[а-яёА-ЯЁ]+\s+20\d{2}\s*[—–-]\s*\d{1,2}\s+[а-яёА-ЯЁ]+\s+20\d{2}",
            r"20\d{2}",
        ]

        date_range = None
        for pattern in date_patterns:
            m = re.search(pattern, text)
            if m:
                date_range = m.group(0)
                break

        year = extract_year_from_text(date_range or text)
        period = assign_period(year)

        return {
            "detail_title": title,
            "detail_date_range": date_range,
            "detail_year": year,
            "detail_period": period,
            "detail_text": text[:3000],
        }

    except Exception as e:
        print("Ошибка при парсинге detail page:", url, e)
        return {
            "detail_title": None,
            "detail_date_range": None,
            "detail_year": None,
            "detail_period": None,
            "detail_text": None,
        }


def main():
    print("STEP 1: собираю события Artguide")

    all_rows = []
    all_links = []

    # Сначала попробуем 20 страниц.
    # Если будет мало — увеличим до 50.
    for page_number in range(1, 21):
        rows = collect_events_from_page(page_number)
        links = collect_links_from_page(page_number)

        all_rows.extend(rows)
        all_links.extend(links)

        if len(rows) == 0 and page_number > 3:
            print("Похоже, страницы закончились.")
            break

        time.sleep(0.5)

    df_events = pd.DataFrame(all_rows)
    df_links = pd.DataFrame(all_links)

    if len(df_events) == 0:
        print("События не найдены.")
        return

    if len(df_links) > 0:
        df_links = df_links.drop_duplicates(subset=["event_url"]).reset_index(drop=True)
        df_links.to_csv("artguide_event_links.csv", index=False, encoding="utf-8-sig")
        print("Ссылки сохранены: artguide_event_links.csv")
    else:
        print("Ссылки на отдельные события не собраны, но карточки событий есть.")

    df_events = df_events.drop_duplicates(subset=["date_range", "raw_text"]).reset_index(drop=True)

    df_events.to_csv("artguide_events_moscow_raw.csv", index=False, encoding="utf-8-sig")
    print("Сырые события сохранены: artguide_events_moscow_raw.csv")

    print("\nSTEP 2: фильтрую только нужные годы 2014–2026")

    df_filtered = df_events[df_events["period"] != "outside_scope"].copy()

    df_filtered.to_csv("artguide_events_moscow_2014_2026.csv", index=False, encoding="utf-8-sig")

    print("\nГотово!")
    print("Всего сырых событий:", len(df_events))
    print("Событий 2014–2026:", len(df_filtered))
    print("Файл сохранен: artguide_events_moscow_2014_2026.csv")

    print("\nПервые строки:")
    print(df_filtered.head(30).to_string())


if __name__ == "__main__":
    main()