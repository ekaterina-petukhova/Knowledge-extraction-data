import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
from urllib.parse import urljoin

url = "https://pushkinmuseum.art/site/exhibitions/exhibitions_year.php?lang=ru"

headers = {
    "User-Agent": "Mozilla/5.0"
}

response = requests.get(url, headers=headers)
print("Status code:", response.status_code)

soup = BeautifulSoup(response.text, "html.parser")
links = soup.find_all("a")

months = [
    "января", "февраля", "марта", "апреля", "мая", "июня",
    "июля", "августа", "сентября", "октября", "ноября", "декабря",
    "ЯНВ", "ФЕВ", "МАР", "АПР", "МАЙ", "ИЮН",
    "ИЮЛ", "АВГ", "СЕН", "ОКТ", "НОЯ", "ДЕК"
]

data = []

for link in links:
    text = link.get_text(" ", strip=True)
    href = link.get("href")

    if not text:
        continue

    has_month = any(month in text for month in months)

    if has_month:
        full_url = urljoin(url, href)

        data.append({
            "museum": "Pushkin Museum",
            "raw_text": text,
            "url": full_url
        })

df = pd.DataFrame(data)

def extract_year(text):
    years = re.findall(r"20\d{2}", text)
    if years:
        return int(years[-1])
    return None

df["year"] = df["raw_text"].apply(extract_year)

def assign_period(year):
    if year is None:
        return "unknown"
    elif year <= 2021:
        return "pre_2022"
    elif year == 2022:
        return "transition_2022"
    elif year >= 2023:
        return "post_2022"
    else:
        return "unknown"

df["period"] = df["year"].apply(assign_period)

date_pattern = r"\d{1,2}\s+(января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря|ЯНВ|ФЕВ|МАР|АПР|МАЙ|ИЮН|ИЮЛ|АВГ|СЕН|ОКТ|НОЯ|ДЕК)"

def extract_title(text):
    match = re.search(date_pattern, text)
    if match:
        return text[:match.start()].strip()
    return text.strip()

df["title"] = df["raw_text"].apply(extract_title)

df = df[[
    "museum",
    "title",
    "raw_text",
    "year",
    "period",
    "url"
]]

print("Собрано выставок:", len(df))

print(df.head(20))

df.to_csv("pushkin_exhibitions_raw.csv", index=False, encoding="utf-8-sig")