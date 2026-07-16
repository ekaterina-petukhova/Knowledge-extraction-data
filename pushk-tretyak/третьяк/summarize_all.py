import pandas as pd
import requests
import time
import os

def get_local_summary(text):
    if not isinstance(text, str) or len(text) < 10:
        return text
    
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": "llama3",
        "prompt": f"Проанализируй описание выставки и напиши суть в 1-2 предложениях. Только результат, без лишних слов. Описание: {text}",
        "stream": False
    }
    
    try:
        response = requests.post(url, json=payload)
        return response.json()['response'].strip()
    except Exception as e:
        print(f"Ошибка при обращении к модели: {e}")
        return text

def main():
    file_path = 'final_analysis_cleaned.csv'
    temp_file = 'final_analysis_processing.csv'
    
    print("Загрузка данных...")
    df = pd.read_csv(file_path)
    
    total = len(df)
    print(f"Начинаю обработку {total} строк. Результат будет сохранен в {file_path}...")
    
    for index, row in df.iterrows():
        print(f"[{index + 1}/{total}] Обрабатываю: {row['title'][:30]}...")
        
        summary = get_local_summary(row['text_to_analyze'])
        df.at[index, 'text_to_analyze'] = summary

        if (index + 1) % 5 == 0:
            df.to_csv(temp_file, index=False)
        
        time.sleep(1) 

    df.to_csv(file_path, index=False)
    
    if os.path.exists(temp_file):
        os.remove(temp_file)
        
    print(f"Готово! Все изменения записаны в {file_path}")

if __name__ == "__main__":
    main()
    