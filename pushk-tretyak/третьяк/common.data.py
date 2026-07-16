import pandas as pd
from transformers import pipeline
print("Загрузка и объединение данных...")
df_tretyakov = pd.read_csv('tretyakov_exhibitions_2014_2026.csv')
df_pushkin = pd.read_csv('pushkin_exhibitions_raw.csv')

df_tretyakov = df_tretyakov.rename(columns={'description': 'text_to_analyze'})
df_pushkin = df_pushkin.rename(columns={'raw_text': 'text_to_analyze'})

df_combined = pd.concat([df_tretyakov, df_pushkin], ignore_index=True)
print(f"Объединено {len(df_combined)} записей.")

print("Инициализация модели (это может занять время)...")
classifier = pipeline("zero-shot-classification", model="MoritzLaurer/mDeBERTa-v3-base-mnli-xnli")
labels = ["западное искусство", "восточное искусство", "национальное российское искусство"]

print("Начинаю анализ содержания выставок...")
def get_category(text):
    text = str(text)[:512] 
    result = classifier(text, labels)
    return result['labels'][0]
categories = []
for i, row in df_combined.iterrows():
    if i % 10 == 0:
        print(f"Обработано {i} из {len(df_combined)}...")
    categories.append(get_category(row['text_to_analyze']))

df_combined['category'] = categories

df_combined.to_csv('final_analysis_results.csv', index=False)
print("Анализ завершен! Результаты сохранены в 'final_analysis_results.csv'.")

