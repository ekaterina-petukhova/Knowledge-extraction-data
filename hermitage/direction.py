import pandas as pd
from transformers import pipeline
import os

print("--- Скрипт запущен ---")

# 1. Проверка файла
file_path = 'hermitage_FINAL_CLEANED.csv'
if not os.path.exists(file_path):
    print(f"ОШИБКА: Файл {file_path} не найден в папке {os.getcwd()}")
    exit()
else:
    print(f"Файл {file_path} найден, читаю...")

df = pd.read_csv(file_path)
print(f"Загружено строк: {len(df)}")

if 'description' in df.columns:
    df = df.rename(columns={'description': 'text_to_analyze'})

# 2. Инициализация (самый долгий этап)
print("Инициализирую модель (подождите)...")
classifier = pipeline("zero-shot-classification", model="MoritzLaurer/mDeBERTa-v3-base-mnli-xnli")
print("Модель загружена!")

# 3. Функция с "предохранителем"
def get_category(text):
    if not isinstance(text, str) or len(text.strip()) == 0:
        return "не определено"
    
    text_lower = text.lower()
    
    # Жесткая привязка
    if "пушкин" in text_lower or "митрохин" in text_lower:
        return "национальное российское искусство"
    
    # Нейросеть
    labels = [
        "западное искусство",
        "восточное искусство",
        "национальное российское искусство"
    ]
    
    result = classifier(text[:512], labels)
    return result['labels'][0]

# 4. Анализ
print("Начинаю цикл обработки...")
df['category'] = df['text_to_analyze'].apply(get_category)

# 5. Сохранение
df.to_csv('hermitage_categorized.csv', index=False, encoding='utf-8-sig')
print("УРА! Файл 'hermitage_categorized.csv' сохранен.")