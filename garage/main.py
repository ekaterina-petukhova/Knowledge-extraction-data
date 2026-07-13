import asyncio
import pandas as pd
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        # Запускаем браузер в режиме, который Playwright контролирует сам
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print("Открываю Русский музей...")
        await page.goto("https://rusmuseum.ru/exhibitions/", wait_until="networkidle")

        # Нажимаем "Показать еще", пока кнопка существует
        while True:
            try:
                # Ищем кнопку по селектору
                load_more = await page.query_selector('button.redline-button')
                if load_more and await load_more.is_visible():
                    await load_more.click()
                    print("Подгружаю список...")
                    await asyncio.sleep(2)
                else:
                    print("Все выставки загружены.")
                    break
            except:
                break

        # Собираем данные
        items = await page.query_selector_all('div.event-list__item')
        results = []

        for item in items:
            title = await item.query_selector('h3.event-title-name')
            title_text = await title.inner_text() if title else "н/д"
            
            date_div = await item.query_selector('div.event-date')
            date_text = await date_div.inner_text() if date_div else "0"
            year = date_text.strip()[-4:] if len(date_text) >= 4 else "0"
            
            link_el = await item.query_selector('a.building')
            href = await link_el.get_attribute('href') if link_el else "#"
            full_url = "https://rusmuseum.ru" + href
            
            desc_div = await item.query_selector('div.event-about-text')
            desc_text = await desc_div.inner_text() if desc_div else ""

            results.append({
                "title": title_text.strip(),
                "year": year,
                "url": full_url,
                "text_to_analyze": desc_text.strip().replace('\n', ' ')
            })

        # Обработка данных
        df = pd.DataFrame(results)
        df['year_numeric'] = pd.to_numeric(df['year'], errors='coerce').fillna(0)
        df = df.sort_values(by='year_numeric', ascending=True).drop(columns=['year_numeric'])
        
        df.to_csv("exhibitions_final.csv", index=False, encoding='utf-8-sig')
        print(f"Готово! Собрано {len(df)} выставок. Файл 'exhibitions_final.csv' готов.")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
    