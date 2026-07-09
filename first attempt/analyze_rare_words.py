import pandas as pd
from collections import Counter
import re
import os

# Путь к файлу
file_path = 'final_analysis_fixed.csv'

# Проверяем, есть ли файл
if not os.path.exists(file_path):
    print(f"Ошибка: Файл {file_path} не найден в текущей папке.")
else:
    # 1. Загрузка данных
    df = pd.read_csv(file_path)

    # 2. Объединяем названия в один текст
    all_titles = " ".join(df['title'].astype(str))

    # 3. Очистка: берем только слова от 5 символов (чтобы убрать союзы/предлоги)
    # Используем нижний регистр
    words = re.findall(r'\w{5,}', all_titles.lower())

    # 4. Считаем частоту всех слов
    counts = Counter(words)

    # 5. Отбираем редкие слова (встречаются <= 2 раз)
    # Исключаем очень частые слова, которые могли проскочить
    rare_words = [word for word, count in counts.items() if count <= 2]

    # 6. Сохраняем результат в файл
    output_filename = 'rare_words_list.txt'
    with open(output_filename, 'w', encoding='utf-8') as f:
        # Пишем в алфавитном порядке для удобства
        for word in sorted(rare_words):
            f.write(word + '\n')

    print(f"Готово! Найдено {len(rare_words)} уникальных (редких) слов.")
    print(f"Полный список сохранен в файл: {output_filename}")
    print("Теперь открой этот файл и посмотри, какие редкие темы там скрыты.")
    