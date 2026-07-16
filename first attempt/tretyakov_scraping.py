from playwright.sync_api import sync_playwright
import pandas as pd
import re
import time


ARCHIVE_URL = "https://www.tretyakovgallery.ru/exhibitions/arkhiv-vystavok/"


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


def collect_links_on_current_page(page):
    links = page.locator("a").evaluate_all("elements => elements.map(el => ({ href: el.href, text: el.innerText }))"    
    )

    items = []

    for link in links:
        href = link.get("href", "")
        text = clean_text(link.get("text", ""))

        if href and "/exhibitions/o/" in href:
            items.append({
                "museum": "Tretyakov Gallery",
                "raw_text": text,
                "url": href.split("?")[0]
            })

    return items


def click_pagination_button(page, page_number):
    selector = f"button.pagination-btn:text-is('{page_number}')"

    button = page.locator(selector)

    if button.count() == 0:
        print(f"Кнопка страницы {page_number} не найдена.")
        return False

    try:
        button.first.scroll_into_view_if_needed()
        page.wait_for_timeout(500)

        button.first.click()
        page.wait_for_timeout(2500)

        return True

    except Exception as e:
        print(f"Не удалось нажать страницу {page_number}:", e)
        return False


def collect_all_archive_links():
    all_items = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page(viewport={"width": 1400, "height": 900})

        print("Открываю архив...")
        page.goto(ARCHIVE_URL, wait_until="domcontentloaded", timeout=90000)
        page.wait_for_timeout(5000)

        for text in ["Соглашаюсь", "Принять", "ОК", "OK"]:
            try:
                btn = page.locator(f"text={text}")
                if btn.count() > 0:
                    btn.first.click()
                    page.wait_for_timeout(1000)
                    print("Закрыт cookie banner:", text)
                    break
            except Exception:
                pass
        print("\nСобираю страницу 1")
        items = collect_links_on_current_page(page)
        print("Найдено ссылок на странице 1:", len(items))
        all_items.extend(items)

        for page_number in range(2, 19):
            print(f"\nПерехожу на страницу {page_number}")

            success = click_pagination_button(page, page_number)

            if not success:
                print(f"Пропускаю страницу {page_number}")
                continue

            items = collect_links_on_current_page(page)
            print(f"Найдено ссылок на странице {page_number}:", len(items))

            all_items.extend(items)

        browser.close()

    df_links = pd.DataFrame(all_items)

    if len(df_links) == 0:
        return df_links

    df_links = df_links.drop_duplicates(subset=["url"]).reset_index(drop=True)

    return df_links


def parse_exhibition_page(page, url):
    
    try:
        page.goto(url, wait_until="networkidle", timeout=90000)
        page.wait_for_timeout(3000)

        title = None
        if page.locator("h1").count() > 0:
            title = clean_text(page.locator("h1").first.inner_text())

        page_text = clean_text(page.locator("body").inner_text())

        date_pattern = r"\d{1,2}\s+[а-яё]+\s+20\d{2}\s*[—–-]\s*\d{1,2}\s+[а-яё]+\s+20\d{2}"
        date_match = re.search(date_pattern, page_text, re.IGNORECASE)
        date_range = date_match.group(0) if date_match else None

        if date_range:
            year = extract_year_from_text(date_range)
        else:
            year = extract_year_from_text(page_text)

        period = assign_period(year)

        return {
            "museum": "Tretyakov Gallery",
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
    print("STEP 1: собираю ссылки со всех страниц пагинации")
    df_links = collect_all_archive_links()

    print("\nИтого уникальных ссылок:", len(df_links))

    if len(df_links) == 0:
        print("Ссылки не найдены.")
        return

    df_links.to_csv("tretyakov_archive_links_all_pages.csv", index=False, encoding="utf-8-sig")
    print("Ссылки сохранены: tretyakov_archive_links_all_pages.csv")

    print("\nSTEP 2: парсю каждую страницу выставки")
    df = parse_all_exhibition_pages(df_links)

    if len(df) == 0:
        print("Данные выставок не собраны.")
        return

    df = df[df["period"] != "outside_scope"]

    df.to_csv("tretyakov_exhibitions_2014_2026.csv", index=False, encoding="utf-8-sig")

    print("\nГотово!")
    print("Собрано выставок 2014–2026:", len(df))
    print("Файл сохранен: tretyakov_exhibitions_2014_2026.csv")

    print("\nПервые строки:")
    print(df[["title", "date_range", "year", "period", "url"]].head(30).to_string())

    print("\nРаспределение по периодам:")
    print(df["period"].value_counts())


if __name__ == "__main__":
    main()