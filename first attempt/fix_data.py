import asyncio
import pandas as pd
from playwright.async_api import async_playwright

async def run():
    df = pd.read_csv('final_data_v5.csv')
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        for index, row in df.iterrows():
            if pd.notna(row['title']) and row['title'] != 'н/д':
                continue
                
            link = row['url']
            print(f"Исправляю {index}: {link}")
            try:
                await page.goto(link, wait_until="networkidle") 
                
                data = await page.evaluate('''() => {
                    return {
                        title: document.querySelector('h1')?.innerText || 'н/д',
                        date: document.querySelector('span[data-v-606ff2bd]')?.innerText || 'н/д'
                    }
                }''')
                
                df.at[index, 'title'] = data['title']
                df.at[index, 'date'] = data['date']
                
                if index % 10 == 0:
                    df.to_csv('final_data_fixed.csv', index=False, encoding='utf-8-sig')
            except Exception as e:
                print(f"Ошибка на {link}: {e}")

        df.to_csv('final_data_fixed.csv', index=False, encoding='utf-8-sig')
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
    