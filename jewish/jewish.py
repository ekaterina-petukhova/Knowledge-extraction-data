from playwright.sync_api import sync_playwright
import pandas as pd
import re
import time


ARCHIVE_URL = "https://www.jewish-museum.ru/archive/exhibitions/?year={year}"


def clean_text(text):
    if text is None:
        return ""
    return re.sub(r"\s+", " ", str(text)).strip()


def extract_year_from_text(text):
    years = re.findall(r"20\d{2}|19\d{2}", str(text))
    if years:
        return int(years[0])
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


def collect_links_on_current_page(page, archive_year):
    """
    Собирает ссылки на выставки с текущей страницы архива.
    """
    links = page.locator("a").evaluate_all(
        """
        elements => elements.map(a => ({
            text: a.innerText,
            href: a.href
        }))
        """
    )

    items = []

    for link in links:
        href = link.get("href", "")
        text = clean_text(link.get("text", ""))

        if not href:
            continue

        href = href.split("?")[0].split("#")[0]

        if (
            href.startswith("https://www.jewish-museum.ru/exhibitions/")
            and href != "https://www.jewish-museum.ru/exhibitions/"
            and len(text) > 0
        ):
            items.append({
                "museum": "Jewish Museum and Tolerance Center",
                "archive_year": archive_year,
                "raw_text": text,
                "url": href
            })

    return items


def collect_all_archive_links():
    all_items = []

    years = list(range(2014, 2027))

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page(viewport={"width": 1400, "height": 900})

        for year in years:
            url = ARCHIVE_URL.format(year=year)

            print(f"\nОткрываю архив за {year}: {url}")

            try:
                page.goto(url, wait_until="domcontentloaded", timeout=90000)
                page.wait_for_timeout(4000)

                # Закрываем cookie banner, если есть
                for text in ["Хорошо", "Соглашаюсь", "Принять", "ОК", "OK"]:
                    try:
                        btn = page.locator(f"text={text}")
                        if btn.count() > 0:
                            btn.first.click()
                            page.wait_for_timeout(1000)
                            print("Закрыт cookie banner:", text)
                            break
                    except Exception:
                        pass

                items = collect_links_on_current_page(page, year)
                print(f"Найдено ссылок за {year}:", len(items))

                all_items.extend(items)

            except Exception as e:
                print(f"Ошибка при сборе архива за {year}:", e)
                continue

            time.sleep(0.5)

        browser.close()

    df_links = pd.DataFrame(all_items)

    if len(df_links) == 0:
        return df_links

    df_links = df_links.drop_duplicates(subset=["url"]).reset_index(drop=True)

    return df_links


def parse_exhibition_page(page, url):
    """
    Парсит отдельную страницу выставки.
    """
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=90000)
        page.wait_for_timeout(3000)

        title = None
        if page.locator("h1").count() > 0:
            title = clean_text(page.locator("h1").first.inner_text())

        page_text = clean_text(page.locator("body").inner_text())

        date_patterns = [
            r"\d{1,2}\s+[а-яё]+\s+20\d{2}\s*[—–-]\s*\d{1,2}\s+[а-яё]+\s+20\d{2}",
            r"\d{1,2}\.\d{1,2}\.\d{4}\s*[—–-]\s*\d{1,2}\.\d{1,2}\.\d{4}",
            r"\d{1,2}\s+[а-яё]+\s+20\d{2}",
        ]

        date_range = None

        for pattern in date_patterns:
            date_match = re.search(pattern, page_text, re.IGNORECASE)
            if date_match:
                date_range = date_match.group(0)
                break

        if date_range:
            year = extract_year_from_text(date_range)
        else:
            year = extract_year_from_text(page_text)

        period = assign_period(year)

        return {
            "museum": "Jewish Museum and Tolerance Center",
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

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page(viewport={"width": 1400, "height": 900})

        for i, url in enumerate(urls):
            print(f"\nПарсинг выставки {i + 1}/{len(urls)}")
            print(url)

            item = parse_exhibition_page(page, url)

            if item:
                rows.append(item)

            time.sleep(0.5)

        browser.close()

    return pd.DataFrame(rows)


def main():
    print("STEP 1: собираю ссылки из архива Еврейского музея")
    df_links = collect_all_archive_links()

    print("\nИтого уникальных ссылок:", len(df_links))

    if len(df_links) == 0:
        print("Ссылки не найдены.")
        return

    df_links.to_csv("jewish_museum_archive_links_all_years.csv", index=False, encoding="utf-8-sig")
    print("Ссылки сохранены: jewish_museum_archive_links_all_years.csv")

    print("\nSTEP 2: парсю каждую страницу выставки")
    df = parse_all_exhibition_pages(df_links)

    if len(df) == 0:
        print("Данные выставок не собраны.")
        return

    # Оставляем только нужный период 2014–2026
    df = df[df["period"] != "outside_scope"]

    df.to_csv("jewish_museum_exhibitions_2014_2026.csv", index=False, encoding="utf-8-sig")

    print("\nГотово!")
    print("Собрано выставок 2014–2026:", len(df))
    print("Файл сохранен: jewish_museum_exhibitions_2014_2026.csv")

    print("\nПервые строки:")
    print(df[["title", "date_range", "year", "period", "url"]].head(30).to_string())

    print("\nРаспределение по периодам:")
    print(df["period"].value_counts())


if __name__ == "__main__":
    main()