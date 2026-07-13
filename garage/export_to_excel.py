import pandas as pd

# Загружаем ваш файл
df = pd.read_csv('garage_categorized.csv')

# Сохраняем в Excel (xlsx)
# encoding 'utf-8-sig' гарантирует, что Excel правильно поймет русский язык
df.to_excel('garage_data_for_edit.xlsx', index=False)

print("Файл 'garage_data_for_edit.xlsx' успешно создан!")
