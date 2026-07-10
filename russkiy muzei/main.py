import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def scrape_all_exhibitions():
    # Настройка драйвера через webdriver-manager (этот метод самый надежный)
    service = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless") # Уберите комментарий, если всё заработает
    
    driver = webdriver.Chrome(service=service, options=options)
    driver.get('https://rusmuseum.ru/exhibitions/')

    print("Загрузка сайта...")
    while True:
        try:
            # Находим кнопку "Показать еще"
            btn = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.redline-button"))
            )
            driver.execute_script("arguments[0].click();", btn)
            time.sleep(3)
        except:
            break

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    items = soup.find_all('div', class_='event-list__item')
    
    data = [{'title': i.find('h3', class_='event-title-name').text.strip() if i.find('h3') else "н/д",
             'year': i.find('div', class_='event-date').text.strip()[-4:] if i.find('div', class_='event-date') else "0",
             'url': "https://rusmuseum.ru" + i.find('a', class_='building')['href'] if i.find('a', class_='building') else "н/д",
             'text_to_analyze': i.find('div', class_='event-about-text').text.strip() if i.find('div', class_='event-about-text') else ""}
            for i in items]

    driver.quit()
    df = pd.DataFrame(data)
    df['year_numeric'] = pd.to_numeric(df['year'], errors='coerce').fillna(0)
    df = df.sort_values(by='year_numeric', ascending=True).drop(columns=['year_numeric'])
    df.to_csv('exhibitions_all.csv', index=False, encoding='utf-8-sig')
    print(f"Готово! Сохранено {len(df)} выставок.")

if __name__ == "__main__":
    scrape_all_exhibitions()
    