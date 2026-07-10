import csv
import re

input_file = 'jewish_museum_exhibitions_2014_2026.csv'
output_file = 'jewish_museum_cleaned_description.csv'

def remove_caps(text):
    if not text: return ""
    # Удаляем слова капсом (2 и более буквы)
    # Используем re.sub для замены
    text = re.sub(r'\b[А-ЯЁA-Z]{2,}\b', '', text)
    # Удаляем лишние пробелы, которые остались после удаления слов
    return " ".join(text.split())

with open(input_file, 'r', encoding='utf-8') as f_in, \
     open(output_file, 'w', encoding='utf-8', newline='') as f_out:
    
    reader = csv.DictReader(f_in)
    # Создаем writer с теми же колонками
    writer = csv.DictWriter(f_out, fieldnames=reader.fieldnames)
    writer.writeheader()
    
    for row in reader:
        # Пытаемся почистить колонку 'description'
        if 'description' in row:
            row['description'] = remove_caps(row['description'])
        # Если колонка называется иначе, посмотрите в заголовке файла
        # и замените 'description' на нужное имя
        writer.writerow(row)

print("Готово. Файл сохранен в 'jewish_museum_cleaned_description.csv'")
