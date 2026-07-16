import pandas as pd

df = pd.read_csv('final_analysis_cleaned.csv')


distribution = df['year'].value_counts().sort_index()
print("Распределение выставок по годам:")
print(distribution)

before_2022 = df[df['year'] < 2022].shape[0]
after_2022 = df[df['year'] >= 2022].shape[0]

print(f"\nВыставок до 2022: {before_2022}")
print(f"Выставок после 2022: {after_2022}")