import csv
import re

def clean_hermitage_universal(text):
    if not isinstance(text, str): return ""
    
    # 1. Удаляем все слова в капслоке (от 3 букв), так как весь интерфейс Эрмитажа — капс
    text = re.sub(r'\b[А-ЯЁA-Z]{3,}\b', '', text)
    
    # 2. Разбиваем на предложения
    sentences = re.split(r'\. (?=[А-ЯЁA-Z])', text)
    
    # 3. Фильтр: оставляем предложения, которые НЕ похожи на пункты меню
    # Мусорные блоки обычно содержат слова из интерфейса или очень короткие
    trash_words = ["цветовая", "палитра", "стандартная", "инверсия", "шрифт", "меню", "посетителям", "эрмитаж", "магазин"]
    
    cleaned_sentences = []
    for s in sentences:
        s = s.strip()
        # Пропускаем, если предложение слишком короткое (меню) или содержит мусорные слова
        if len(s) < 30: continue 
        if any(w in s.lower() for w in trash_words): continue
        
        cleaned_sentences.append(s)
        
    return ". ".join(cleaned_sentences).strip()

# Применение к файлу
def process_hermitage(input_path, output_path):
    with open(input_path, 'r', encoding='utf-8') as f_in, \
         open(output_path, 'w', encoding='utf-8', newline='') as f_out:
        
        reader = csv.DictReader(f_in)
        writer = csv.DictWriter(f_out, fieldnames=reader.fieldnames)
        writer.writeheader()
        
        for row in reader:
            if 'description' in row:
                row['description'] = clean_hermitage_universal(row['description'])
            writer.writerow(row)

process_hermitage('hermitage_exhibitions_2014_2026.csv', 'hermitage_FINAL_CLEANED.csv')
