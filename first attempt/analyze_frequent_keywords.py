import pandas as pd
from collections import Counter
import re
import os

# Путь к файлу
file_path = 'final_analysis_fixed.csv'

if not os.path.exists(file_path):
    print(f"Ошибка: Файл {file_path} не найден.")
else:
    # 1. Загрузка
    df = pd.read_csv(file_path)
    all_titles = " ".join(df['title'].astype(str))

    # 2. Очистка (слова от 4 символов)
    words = re.findall(r'\w{4,}', all_titles.lower())

    # 3. Список стоп-слов (можно расширить, если увидите лишнее)
    stop_words = {'года', 'века', 'выставка', 'начало', 'собрание', 'музея', 'искусства', 'искусство'}
    filtered_words = [w for w in words if w not in stop_words]

    # 4. Считаем самые частые
    counts = Counter(filtered_words)
    most_common = counts.most_common(50)

    # 5. Сохраняем в файл
    output_filename = 'frequent_words_list.txt'
    with open(output_filename, 'w', encoding='utf-8') as f:
        f.write("Топ-50 самых частых слов в названиях:\n\n")
        for word, count in most_common:
            f.write(f"{word}: {count}\n")

    print(f"Готово! Топ-50 слов сохранен в файл: {output_filename}")
    # Выводим первые 10 в консоль для быстрого ознакомления
    for word, count in most_common[:10]:
        print(f"{word}: {count}")
        