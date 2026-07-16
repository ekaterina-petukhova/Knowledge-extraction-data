import pandas as pd
from collections import Counter
import re
import os

file_path = 'final_analysis_fixed.csv'

if not os.path.exists(file_path):
    print(f"Ошибка: Файл {file_path} не найден.")
else:

    df = pd.read_csv(file_path)
    all_titles = " ".join(df['title'].astype(str))


    words = re.findall(r'\w{4,}', all_titles.lower())


    stop_words = {'года', 'века', 'выставка', 'начало', 'собрание', 'музея', 'искусства', 'искусство'}
    filtered_words = [w for w in words if w not in stop_words]

  
    counts = Counter(filtered_words)
    most_common = counts.most_common(50)

    output_filename = 'frequent_words_list.txt'
    with open(output_filename, 'w', encoding='utf-8') as f:
        f.write("Топ-50 самых частых слов в названиях:\n\n")
        for word, count in most_common:
            f.write(f"{word}: {count}\n")

    print(f"Готово! Топ-50 слов сохранен в файл: {output_filename}")
    for word, count in most_common[:10]:
        print(f"{word}: {count}")
        