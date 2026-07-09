import asyncio
import pandas as pd
import re
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        results = []
        # Мы просто будем перебирать страницы от 1 до 140 (у вас было 139 страниц)
        for page_num in range(1, 140):
            url = f"https://rusmuseum.ru/exhibitions/archive/?PAGEN_1={page_num}"
            print(f"Загружаю: {url}")
            
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(2) # Пауза, чтобы данные подгрузились
                
                items = await page.query_selector_all('div.event-list__item')
                
                # Если на странице нет выставок, значит мы дошли до конца
                if not items:
                    print("Элементы не найдены, возможно, архив закончился.")
                    break
                
                for item in items:
                    title_el = await item.query_selector('h3.event-title-name')
                    title = await title_el.inner_text() if title_el else "н/д"
                    
                    date_div = await item.query_selector('div.event-date')
                    date_text = await date_div.inner_text() if date_div else ""
                    
                    desc_div = await item.query_selector('div.event-about-text')
                    desc_text = await desc_div.inner_text() if desc_div else ""

                    year_match = re.search(r'(19\d{2}|20[0-2]\d)', date_text + " " + desc_text)
                    year = year_match.group(1) if year_match else "0"
                    
                    link_el = await item.query_selector('a.building')
                    href = await link_el.get_attribute('href') if link_el else "#"
                    full_url = "https://rusmuseum.ru" + href

                    results.append({
                        "title": title.strip(),
                        "year": year,
                        "url": full_url,
                        "text_to_analyze": desc_text.strip().replace('\n', ' ')
                    })
                
                print(f"--- Страница {page_num}: добавлено {len(items)} записей ---")
                
            except Exception as e:
                print(f"Ошибка на странице {page_num}: {e}")
                break

        df = pd.DataFrame(results)
        df.to_csv("exhibitions_full_archive_v2.csv", index=False, encoding='utf-8-sig')
        print(f"Финиш! Всего собрано {len(df)} записей.")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
    