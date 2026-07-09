import pandas as pd
import requests

def get_tags(text):
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": "llama3",
        "prompt": f"Извлеки из описания выставки 3-5 существительных (ключевых тем), описывающих содержание (например: 'авангард', 'пейзаж', 'война'). Верни только эти слова через запятую. Описание: {text}",
        "stream": False
    }
    try:
        response = requests.post(url, json=payload)
        return response.json()['response'].strip()
    except:
        return ""

df = pd.read_csv('final_analysis_cleaned.csv')
print("Извлекаю теги (это превратит тексты в чистые ключевые слова)...")
df['tags'] = df['text_to_analyze'].apply(get_tags)
df.to_csv('final_analysis_with_tags.csv', index=False)
print("Готово! Файл final_analysis_with_tags.csv создан.")
