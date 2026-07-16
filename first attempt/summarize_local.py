import pandas as pd
import requests
import time

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
    input_file = 'final_analysis_cleaned.csv'
    output_file = 'final_analysis_summarized_test.csv'
    
    print("Загрузка данных...")
    df = pd.read_csv(input_file)
    
    df_test = df.head(20).copy()
    
    cols = ['museum', 'title', 'date_range', 'year', 'url', 'text_to_analyze', 'category']
    df_test = df_test[cols]
    
    print(f"Начинаю обработку 20 строк...")
    
    for index, row in df_test.iterrows():
        print(f"[{index + 1}/20] Обрабатываю выставку: {row['title']}...")
        
        summary = get_local_summary(row['text_to_analyze'])
        df_test.at[index, 'text_to_analyze'] = summary
        
        time.sleep(1) 

    df_test.to_csv(output_file, index=False)
    print(f"Тест завершен! Результаты сохранены в {output_file}")

if __name__ == "__main__":
    main()

    