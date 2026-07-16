import csv
import re

def clean_garage_description(text):
    if not isinstance(text, str): return ""
    
    text = re.sub(r'Ежедневно, 11:00–22:00.*$', '', text, flags=re.DOTALL)
    
    text = re.sub(r'Скачать пресс-релиз \(pdf\)', '', text, flags=re.IGNORECASE)
    
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

with open('garage_news_final.csv', 'r', encoding='utf-8') as f_in, \
     open('garage_FINAL_CLEANED.csv', 'w', encoding='utf-8', newline='') as f_out:
    
    reader = csv.DictReader(f_in)
    writer = csv.DictWriter(f_out, fieldnames=reader.fieldnames)
    writer.writeheader()
    
    for row in reader:
        if 'text_to_analyze' in row:
            row['text_to_analyze'] = clean_garage_description(row['text_to_analyze'])
        writer.writerow(row)

print("Данные 'Гаража' очищены!")
