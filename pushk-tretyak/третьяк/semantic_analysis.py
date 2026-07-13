import pandas as pd
from collections import Counter
import re

df = pd.read_csv('final_analysis_results_fixed.csv')
df['year'] = pd.to_numeric(df['year'], errors='coerce')
df['text'] = df['text_to_analyze'].fillna('').str.lower()

pattern = r'запад\w*'

def get_context_for_pattern(subset, pattern):
    all_context = []
    matches = subset[subset['text'].str.contains(pattern, na=False)]
    for text in matches['text']:
        words = re.findall(r'\w+', text)
        for i, word in enumerate(words):
            if re.match(pattern, word):
                all_context.extend(words[max(0, i-3):i] + words[i+1:i+4])
    return [w for w in all_context if len(w) > 4], len(matches)

print("--- СРАВНИТЕЛЬНЫЙ АНАЛИЗ СЛОВА 'ЗАПАД' ---")

for period_name, year_condition in [("ДО 2022", df['year'] < 2022), 
                                   ("ПОСЛЕ 2022", df['year'] >= 2022)]:
    
    subset = df[year_condition]
    context, count = get_context_for_pattern(subset, pattern)
    
    print(f"\nПериод: {period_name} (Записей с упоминанием: {count})")
    if count > 0:
        print(f"Самые частые соседи: {Counter(context).most_common(10)}")
    else:
        print("Упоминаний не найдено.")