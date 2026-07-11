import csv
import re

def clean_mamm_description(text):
    if not isinstance(text, str): return ""
    
    # 1. Убираем навигационный блок в начале (всё до первого упоминания названия выставки или начала основного текста)
    # Ищем блок до фразы "1 2 3 4 5 6 7" или аналогичных счетчиков, которые есть в начале
    # Также убираем служебные заголовки сайта
    pattern_start = r'.*?(1 2 3 4 5 6 7)'
    text = re.sub(pattern_start, '', text, flags=re.IGNORECASE | re.DOTALL)
    
    # 2. Убираем "хвост" — всё, что идет после описания. 
    # Обычно описание заканчивается перед фразой "Idea: Olga Sviblova" или "Exhibition schedule"
    pattern_end = r'(Idea:.*|Exhibition schedule.*|Supported by.*)'
    text = re.sub(pattern_end, '', text, flags=re.IGNORECASE | re.DOTALL)
    
    # 3. Чистка от мусора (архивные подписи, лишние пробелы)
    text = re.sub(r'Ogoniok archive', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

# Применение
# Замените этот блок в вашем файле cleaner.py:
with open('mamm_exhibitions_2014_2026.csv', 'r', encoding='utf-8') as f_in, \
     open('mamm_FINAL_CLEANED.csv', 'w', encoding='utf-8', newline='') as f_out:
    
    reader = csv.DictReader(f_in)
    writer = csv.DictWriter(f_out, fieldnames=reader.fieldnames)
    writer.writeheader()
    
    for row in reader:
        if 'description' in row:
            row['description'] = clean_mamm_description(row['description'])
        writer.writerow(row)

print("Данные МАММ очищены! Сохранены в 'mamm_FINAL_CLEANED.csv'.")

