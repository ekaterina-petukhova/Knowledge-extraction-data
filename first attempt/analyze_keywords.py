import pandas as pd
from collections import Counter
import re


df = pd.read_csv('final_analysis_fixed.csv')

all_titles = " ".join(df['title'].astype(str))

words = re.findall(r'\w{4,}', all_titles.lower())

stop_words = ['года', 'века', 'выставка', 'начало', 'собрание', 'творчестве', 'российской']
filtered_words = [w for w in words if w not in stop_words]

most_common = Counter(filtered_words).most_common(30)

print("Топ-30 ключевых слов в названиях:")
for word, count in most_common:
    print(f"{word}: {count}")
    