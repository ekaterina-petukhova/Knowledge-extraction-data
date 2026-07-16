import pandas as pd
from transformers import pipeline

# 1. Загрузка вашего очищенного файла
print("Загрузка данных...")
df = pd.read_csv('jewish_museum_FINAL_CLEANED.csv')

# Убедимся, что колонка называется как нужно для анализа
# Если в файле колонка называется иначе, замените 'description'
df = df.rename(columns={'description': 'text_to_analyze'})

# 2. Инициализация классификатора
print("Инициализация модели (это может занять время)...")
# Модель mDeBERTa отлично работает с русским языком
classifier = pipeline("zero-shot-classification", model="MoritzLaurer/mDeBERTa-v3-base-mnli-xnli")

# Список направлений
labels = ["западное искусство", "восточное искусство", "национальное российское искусство"]

# 3. Классификация
print(f"Начинаю анализ {len(df)} выставок...")

def get_category(text):
    if not isinstance(text, str) or len(text.strip()) == 0:
        return "не определено"
    # Берем первые 512 символов
    text = text[:512]
    result = classifier(text, labels)
    return result['labels'][0]

categories = []
for i, row in df.iterrows():
    if i % 5 == 0:
        print(f"Обработано {i} из {len(df)}...")
    categories.append(get_category(row['text_to_analyze']))

df['category'] = categories

# 4. Сохранение результата
df.to_csv('jewish_museum_categorized.csv', index=False)
print("Анализ завершен! Результаты сохранены в 'jewish_museum_categorized.csv'.")
