import pandas as pd
from collections import Counter
import pymorphy3

morph = pymorphy3.MorphAnalyzer()

file_path = '/Users/mariagriga/Desktop/скрапинг/Knowledge-extraction-data/russkiy muzei/russkiy_muzei_classified_final.csv'
df = pd.read_csv(file_path)

target_cities = [
    'москва', 'санкт-петербург', 'новосибирск', 'екатеринбург', 'казань', 
    'нижний новгород', 'челябинск', 'самара', 'омск', 'ростов', 'ростов-на-дону',
    'уфа', 'красноярск', 'пермь', 'волгоград', 'воронеж', 'саратов', 
    'рязань', 'звенигород', 'владимир', 'тула', 'ярославль', 'ижевск'
]

df['combined'] = df['title'].fillna('') + ' ' + df['description'].fillna('')

def extract_cities(text):
    if not isinstance(text, str): return []
    words = text.split()
    found = []
    for word in words:
        clean_word = word.strip('.,:;"()«»').lower()
        lemma = morph.parse(clean_word)[0].normal_form
        if lemma in target_cities:
            found.append(lemma)
    return found

df_before = df[df['year'] < 2022]
df_after = df[df['year'] >= 2022]

before_list = [c for sublist in df_before['combined'].apply(extract_cities) for c in sublist]
after_list = [c for sublist in df_after['combined'].apply(extract_cities) for c in sublist]

print("\n--- Топ городов ДО 2022 ---")
print(Counter(before_list).most_common(20))

print("\n--- Топ городов ПОСЛЕ 2022 ---")
print(Counter(after_list).most_common(20))