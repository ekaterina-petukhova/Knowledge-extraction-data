import pandas as pd
from transformers import pipeline

# 1. Загрузка данных
print("Загрузка данных МАММ...")
df = pd.read_csv('mamm_FINAL_CLEANED.csv')

# Переименовываем колонку, если нужно
if 'description' in df.columns:
    df = df.rename(columns={'description': 'text_to_analyze'})

# 2. Инициализация классификатора
print("Инициализация модели (это может занять время)...")
classifier = pipeline("zero-shot-classification", model="MoritzLaurer/mDeBERTa-v3-base-mnli-xnli")

# Список направлений
labels = [
    "western art (European artists, photography, contemporary western art)",
    "eastern art (art from Asia, the Middle East, oriental photography)",
    "national Russian art (Russian photography, Soviet history, Russian culture, Russian artists)"
]

# 3. Функция классификации
def get_category(text):
    if not isinstance(text, str) or len(text.strip()) == 0:
        return "не определено"
    
    text_lower = text.lower()
    
    # ПРЕОДОХРАНИТЕЛЬ: только для слов, которые точно указывают на категорию
    # Мы убрали "moscow", так как оно есть в каждом футере сайта
    russian_keywords = ["soviet", "lenin", "ogoniok", "russian history", "ussr", "russian avant-garde"]
    if any(keyword in text_lower for keyword in russian_keywords):
        return "national Russian art"
    
    # Нейросетевая классификация
    text_short = text[:512]
    try:
        result = classifier(text_short, labels)
        best_label = result['labels'][0]
        
        # Очистка названий
        if "western" in best_label: return "western art"
        if "eastern" in best_label: return "eastern art"
        if "national" in best_label: return "national Russian art"
        return best_label
    except:
        return "error"

# 4. Анализ
print(f"Начинаю анализ {len(df)} выставок...")
df['category'] = df['text_to_analyze'].apply(get_category)

# 5. Сохранение
output_filename = 'mamm_categorized.csv'
df.to_csv(output_filename, index=False, encoding='utf-8-sig')
print(f"Анализ завершен! Результаты сохранены в '{output_filename}'.")
