import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

# 1. Загрузка данных
df = pd.read_csv('russkiy muzei/russkiy_muzei_classified_final.csv')

# 2. Подготовка данных
pivot_df = df.groupby(['year', 'category']).size().unstack(fill_value=0)
categories_order = ["восточное искусство", "западное искусство", "национальное российское искусство"]
pivot_df = pivot_df.reindex(columns=categories_order, fill_value=0)


# 3. Настройка перевода (Labels)
english_labels = {
    "восточное искусство": "Eastern Art",
    "западное искусство": "Western Art (corrected)",
    "национальное российское искусство": "National Russian Art (+fixes)"
}
pivot_df = pivot_df.rename(columns=english_labels)
pivot_df.to_csv("category_by_year.csv")

# 4. Построение графика
plt.style.use('seaborn-v0_8-whitegrid')
colors = ['#440154', '#21908c', '#fde725']

ax = pivot_df.plot(kind='bar', stacked=True, figsize=(12, 7), color=colors, width=0.8)

# Заголовки на английском
ax.set_title('Dynamics of Exhibition Cultural Focus (2014–2026)', fontsize=16, pad=20)
ax.set_xlabel('Year', fontsize=12)
ax.set_ylabel('Number of Exhibitions', fontsize=12)

# Легенда
ax.legend(title='Category', fontsize=11, loc='upper left', bbox_to_anchor=(1.02, 1))

# 5. КРИТИЧЕСКИЙ ШАГ: исправляем обрезку
plt.tight_layout() 

# Сохранение
plt.savefig('museum_trends_english.png', dpi=300, bbox_inches='tight')
print("График сохранен как 'museum_trends_english.png' с исправленными полями.")
