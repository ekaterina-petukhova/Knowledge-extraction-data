import pandas as pd
from transformers import pipeline
import os

print("--- Скрипт запущен: классификация Пушкинского музея ---")

file_path = 'pushkin_cleaned.csv'
if not os.path.exists(file_path):
    print(f"ОШИБКА: Файл {file_path} не найден в папке {os.getcwd()}")
    exit()

df = pd.read_csv(file_path)
print(f"Загружено строк: {len(df)}")

if 'description' in df.columns:
    df = df.rename(columns={'description': 'text_to_analyze'})

print("Инициализирую модель (подождите, может занять пару минут)...")
classifier = pipeline("zero-shot-classification", model="MoritzLaurer/mDeBERTa-v3-base-mnli-xnli")
print("Модель загружена!")

labels = [
    "западное искусство",
    "восточное искусство",
    "национальное российское искусство",
]


def get_category(text):
    if not isinstance(text, str) or len(text.strip()) == 0:
        return "не определено"
    result = classifier(text[:512], labels)
    return result['labels'][0]


print("Начинаю цикл обработки...")
categories = []
for i, row in df.iterrows():
    if (i + 1) % 20 == 0:
        print(f"Обработано {i + 1} из {len(df)}...")
    categories.append(get_category(row['text_to_analyze']))

df['category'] = categories

df.to_csv('pushkin_categorized.csv', index=False, encoding='utf-8-sig')
print("\nГотово! Файл 'pushkin_categorized.csv' сохранен.")
print(df['category'].value_counts())