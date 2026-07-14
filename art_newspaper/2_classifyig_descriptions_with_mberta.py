import pandas as pd
from transformers import pipeline

# 1. Загрузка данных
df_rm = pd.read_csv('art_newspaper_exhibitions_2014_2026.csv')

# 2. Инициализация классификатора
# Используем модель, которая лучше работает с логикой
classifier = pipeline("zero-shot-classification", model="MoritzLaurer/mDeBERTa-v3-base-mnli-xnli")
labels = ["западное искусство", "восточное искусство", "национальное российское искусство"]

# 3. Функция классификации с отладкой
def get_category(text):
    text_snippet = str(text)[:512]
    # Используем шаблон гипотезы, чтобы модель "лучше соображала"
    result = classifier(
        text_snippet, 
        labels, 
        multi_label=False, 
        hypothesis_template="Это искусство относится к категории: {}"
    )
    
    # ОТЛАДКА: Если вы видите, что всё "национальное", посмотрите на это в терминале
    # print(f"Текст: {text_snippet[:30]} | Лучшая метка: {result['labels'][0]} ({result['scores'][0]:.2f})")
    
    return result['labels'][0]

# 4. Анализ
print(f"Начинаю классификацию {len(df_rm)} записей...")

categories = []
for i, text in enumerate(df_rm['description']):
    categories.append(get_category(text))
    if (i + 1) % 20 == 0:
        print(f"Обработано {i + 1} из {len(df_rm)}...")

df_rm['category'] = categories

# 5. Сохранение
df_rm.to_csv('art_newspaper_classified.csv', index=False)
print("Готово! Результаты в 'art_newspaper_classified.csv'.")