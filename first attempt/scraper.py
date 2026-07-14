import asyncio
import pandas as pd
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        await page.goto("https://rusmuseum.ru/exhibitions/archive/", wait_until="networkidle")
        
        all_links = []
        
        for i in range(1, 150): # Пробуем пройти 150 страниц
            print(f"--- Страница {i} ---")
            
            # Ждем появления карточек
            try:
                await page.wait_for_selector('.tile.card', timeout=10000)
            except:
                print("Карточки не найдены, возможно, дошли до конца.")
                break
                
            # Собираем ссылки
            new_links = await page.evaluate('''() => {
                return Array.from(document.querySelectorAll('a.building')).map(a => a.href);
            }''')
            
            found = 0
            for link in new_links:
                if link not in all_links:
                    all_links.append(link)
                    found += 1
            print(f"Добавлено {found} новых ссылок. Всего: {len(all_links)}")

            # Пытаемся найти кнопку пагинации любым доступным способом
            # Часто это просто ссылка с классом, содержащим 'next'
            next_btn = await page.query_selector('a[aria-label="Следующая"]') or \
                       await page.query_selector('.pagination-nav__arrow.__next') or \
                       await page.query_selector('a:has-text("Вперед")')
            
            if next_btn:
                await next_btn.click()
                await asyncio.sleep(4) # Увеличили паузу
            else:
                # ХИТРОСТЬ: Если кнопка не найдена, пробуем перейти по URL вручную
                next_url = f"https://rusmuseum.ru/exhibitions/archive/?PAGEN_1={i+1}"
                print(f"Кнопка не найдена, пробуем переход по URL: {next_url}")
                await page.goto(next_url, wait_until="networkidle")
                await asyncio.sleep(4)
                
                # Если после перехода по URL те же 9 карточек - значит, дальше пусто
                current_cards = await page.query_selector_all('.tile.card')
                if len(current_cards) == 0:
                    print("Данных больше нет.")
                    break

        # Сбор контента (упрощенный)
        results = []
        for link in all_links:
            try:
                await page.goto(link, wait_until="domcontentloaded")
                title = await page.inner_text('h1') if await page.query_selector('h1') else "н/д"
                date = await page.inner_text('span[data-v-606ff2bd]') if await page.query_selector('span[data-v-606ff2bd]') else "н/д"
                results.append({"title": title, "date": date, "url": link})
            except: pass
            
        pd.DataFrame(results).to_csv("final_data_v5.csv")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
    