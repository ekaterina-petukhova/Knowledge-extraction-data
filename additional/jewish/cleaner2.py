import csv
import re

def is_meaningful(block):
    """
    Проверяет, является ли блок текста осмысленным описанием выставки.
    """
    block = block.strip()
    
    # 1. Список слов-маркеров "мусора" (навигация, часы работы, контакты)
    bad_markers = [
        "часы работы", "понедельник", "вторник", "среда", "четверг", 
        "пятница", "суббота", "воскресенье", "кассы до", "выходные", 
        "контакты", "как проехать", "улица", "дом", "строение",
        "телефон", "информация", "билеты", "экспозиция", "музей онлайн"
    ]
    
    # 2. Если блок слишком короткий (менее 60 символов) — это вряд ли описание
    if len(block) < 60: 
        return False
    
    # 3. Если в блоке есть хоть один маркер мусора — удаляем
    if any(marker in block.lower() for marker in bad_markers):
        return False
        
    # 4. Если блок начинается с цифр (часто время или адреса) — удаляем
    if re.match(r'^\d', block):
        return False
        
    # 5. Если в предложении мало слов — это не описание
    if len(block.split()) < 8:
        return False
        
    return True

def process_file(input_path, output_path):
    with open(input_path, 'r', encoding='utf-8') as f_in, \
         open(output_path, 'w', encoding='utf-8', newline='') as f_out:
        
        reader = csv.DictReader(f_in)
        writer = csv.DictWriter(f_out, fieldnames=reader.fieldnames)
        writer.writeheader()
        
        for row in reader:
            text = row.get('description', '')
            if not text:
                continue
            
            # Разбиваем текст на предложения. 
            # Регулярка учитывает точку с пробелом, после которой идет заглавная буква
            sentences = re.split(r'\. (?=[А-ЯЁA-Z])', text)
            
            # Оставляем только те предложения, которые прошли все проверки
            filtered = [s for s in sentences if is_meaningful(s)]
            
            # Собираем обратно
            row['description'] = ". ".join(filtered)
            writer.writerow(row)

# Запуск обработки
if __name__ == "__main__":
    input_file = 'jewish_museum_cleaned_description.csv'
    output_file = 'jewish_museum_FINAL_CLEANED.csv'
    
    process_file(input_file, output_file)
    print(f"Готово! Очищенный файл сохранен как '{output_file}'.")

    