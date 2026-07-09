import pandas as pd

# 1. Загружаем основной файл
df = pd.read_csv('final_analysis_results.csv')

# 2. Список исправлений: { "часть названия": "правильная категория" }
# Используйте уникальные слова из названий выставок, где модель ошиблась
corrections = {
    "Название, которое было красным": "национальное российское искусство",
    "Другое ошибочное название": "национальное российское искусство",
    # ... добавьте сюда все 30 правок
}

# 3. Функция исправления
def apply_corrections(row):
    for title, correct_cat in corrections.items():
        if title in str(row['title']):
            return correct_cat
    return row['category']

# Применяем правки
df['category'] = df.apply(apply_corrections, axis=1)

# 4. Сохраняем "чистый" файл
df.to_csv('final_analysis_results_fixed.csv', index=False)
print("Все правки применены! Файл 'final_analysis_results_fixed.csv' готов.")
