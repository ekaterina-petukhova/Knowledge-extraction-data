import pandas as pd
from collections import Counter
import re
import os

file_path = 'final_analysis_fixed.csv'

if not os.path.exists(file_path):
    print(f"Ошибка: Файл {file_path} не найден в текущей папке.")
else:

    df = pd.read_csv(file_path)

    all_titles = " ".join(df['title'].astype(str))

    words = re.findall(r'\w{5,}', all_titles.lower())

    counts = Counter(words)
    rare_words = [word for word, count in counts.items() if count <= 2]

    output_filename = 'rare_words_list.txt'
    with open(output_filename, 'w', encoding='utf-8') as f:
        for word in sorted(rare_words):
            f.write(word + '\n')

    print(f"Готово! Найдено {len(rare_words)} уникальных (редких) слов.")
    print(f"Полный список сохранен в файл: {output_filename}")
    print("Теперь открой этот файл и посмотри, какие редкие темы там скрыты.")
    