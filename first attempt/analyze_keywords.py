import pandas as pd
from collections import Counter
import re

# 1. Загрузка данных
df = pd.read_csv('final_analysis_fixed.csv')

# 2. Объединяем все названия в один текст
all_titles = " ".join(df['title'].astype(str))

# 3. Очистка: берем слова длиннее 3 символов
words = re.findall(r'\w{4,}', all_titles.lower())

# 4. Стоп-слова (можно дополнить своими, если увидите "мусор")
stop_words = ['года', 'века', 'выставка', 'начало', 'собрание', 'творчестве', 'российской']
filtered_words = [w for w in words if w not in stop_words]

# 5. Считаем частоту
most_common = Counter(filtered_words).most_common(30)

print("Топ-30 ключевых слов в названиях:")
for word, count in most_common:
    print(f"{word}: {count}")
    