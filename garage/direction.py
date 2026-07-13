import pandas as pd
from transformers import pipeline

# 1. Загрузка данных
df = pd.read_csv('garage_FINAL_CLEANED.csv')

# 2. Инициализация модели
classifier = pipeline("zero-shot-classification", model="MoritzLaurer/mDeBERTa-v3-base-mnli-xnli")

# 3. Русские метки (с пояснениями для точности)
labels = [
    "западное искусство (международные проекты, современное искусство, архитектура)",
    "восточное искусство (искусство стран Востока, Япония, архитектор Шигеру Бан)",
    "национальное российское искусство (российские художники, российские дизайнеры, культурная сцена России)"
]

def get_category(text):
    if not isinstance(text, str) or len(text.strip()) == 0:
        return "не определено"
    
    text_lower = text.lower()
    
    # ПРЕДОХРАНИТЕЛИ: 
    # Шигеру Бан — это Восточная архитектура (в рамках вашего деления)
    if any(word in text_lower for word in ["шигеру бан", "японский архитектор"]):
        return "восточное искусство"
    
    # Молодые российские художники/дизайнеры — это Россия
    if any(word in text_lower for word in ["российских молодых художников", "российских графических дизайнеров"]):
        return "национальное российское искусство"
    
    # Нейросетевой анализ
    try:
        result = classifier(text[:512], labels)
        best_label = result['labels'][0]
        
        # Приведение к чистому виду
        if "западное" in best_label: return "западное искусство"
        if "восточное" in best_label: return "восточное искусство"
        if "национальное" in best_label: return "национальное российское искусство"
        return best_label
    except:
        return "ошибка анализа"

# 4. Анализ
df['category'] = df['text_to_analyze'].apply(get_category)

# 5. Сохранение
df.to_csv('garage_categorized.csv', index=False, encoding='utf-8-sig')
print("Анализ 'Гаража' завершен! Файл: garage_categorized.csv")
