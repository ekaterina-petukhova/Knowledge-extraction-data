import pandas as pd

# Читаем файл с учетом точки с запятой (sep=';') и убираем лишние символы
df = pd.read_csv('garage_categorized.csv', sep=';', encoding='utf-8-sig', on_bad_lines='skip')

# Очищаем имена колонок от пробелов и лишнего мусора
df.columns = df.columns.str.strip().str.replace('\ufeff', '', regex=True)

# Оставляем только нужные колонки (избавляемся от пустых)
df = df[['year', 'category']]

# Приводим год к числу
df['year'] = pd.to_numeric(df['year'], errors='coerce')

# Считаем
before = df[df['year'] < 2022]
after = df[df['year'] >= 2022]

stats_before = before['category'].value_counts(normalize=True) * 100
stats_after = after['category'].value_counts(normalize=True) * 100

# Вывод
print(f"{'Категория':<25} | {'До 2022 (%)':<15} | {'После 2022 (%)':<15}")
print("-" * 60)

all_cats = set(stats_before.index).union(set(stats_after.index))

for cat in all_cats:
    print(f"{str(cat):<25} | {stats_before.get(cat, 0):>12.1f}% | {stats_after.get(cat, 0):>13.1f}%")