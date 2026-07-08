import pandas as pd

df = pd.read_csv('final_analysis_cleaned.csv')
df['year'] = pd.to_numeric(df['year'], errors='coerce')

# Регулярка: ищем 'рус' или 'росс' (case=False игнорирует регистр)
# Это поймает: русский, русская, российское, России, russia, russian и т.д.
pattern = r'рус|росс|russ'

before_2022 = df[(df['year'] < 2022) & (df['text_to_analyze'].str.contains(pattern, case=False, na=False))]
after_2022 = df[(df['year'] >= 2022) & (df['text_to_analyze'].str.contains(pattern, case=False, na=False))]

print(f"--- Результаты с учетом 'рус' и 'росс' ---")
print(f"Всего записей ДО 2022: {len(df[df['year'] < 2022])}")
print(f"Записей с нац. компонентом ДО 2022: {len(before_2022)}")
print(f"Процент ДО 2022: {(len(before_2022)/len(df[df['year'] < 2022])*100):.1f}%")

print(f"\nВсего записей ПОСЛЕ 2022: {len(df[df['year'] >= 2022])}")
print(f"Записей с нац. компонентом ПОСЛЕ 2022: {len(after_2022)}")
print(f"Процент ПОСЛЕ 2022: {(len(after_2022)/len(df[df['year'] >= 2022])*100):.1f}%")
