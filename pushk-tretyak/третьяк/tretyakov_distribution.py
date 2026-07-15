import pandas as pd
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import TfidfVectorizer

INPUT_FILE = 'tretyakov_categorized.csv'
TEXT_COL = 'text_to_analyze'
MUSEUM_LABEL = 'Tretyakov Gallery'

df = pd.read_csv(INPUT_FILE)
df['year'] = pd.to_numeric(df['year'], errors='coerce')

before = df[df['year'] < 2022]
after = df[df['year'] >= 2022]

print(f"Всего записей: {len(df)}")
print(f"До 2022: {len(before)}  |  После 2022: {len(after)}\n")


# =====================================================================
# 1. РАСПРЕДЕЛЕНИЕ ПО ГОДАМ
# =====================================================================

distribution = df['year'].value_counts().sort_index()
print("=== Распределение по годам ===")
print(distribution)

dist_df = distribution.reset_index()
dist_df.columns = ['year', 'count']
dist_df.to_csv('tretyakov_year_distribution.csv', index=False)
print("\nСохранено: tretyakov_year_distribution.csv\n")

# график по годам, с разбивкой по категориям (в штуках, как в plot_results_fixed.py)
pivot = df.groupby(['year', 'category']).size().unstack(fill_value=0)
categories_order = ["восточное искусство", "западное искусство", "национальное российское искусство"]
pivot = pivot.reindex(columns=categories_order, fill_value=0)

english_labels = {
    "восточное искусство": "Eastern Art",
    "западное искусство": "Western Art",
    "национальное российское искусство": "National Russian Art"
}
pivot_plot = pivot.rename(columns=english_labels)
pivot_plot.to_csv('tretyakov_category_by_year.csv')
print("Сохранено: tretyakov_category_by_year.csv\n")

plt.style.use('seaborn-v0_8-whitegrid')
colors = ['#440154', '#21908c', '#fde725']
ax = pivot_plot.plot(kind='bar', stacked=True, figsize=(12, 7), color=colors, width=0.8)
ax.set_title(f'Dynamics of Exhibition Cultural Focus — {MUSEUM_LABEL}', fontsize=16, pad=20)
ax.set_xlabel('Year', fontsize=12)
ax.set_ylabel('Number of Exhibitions', fontsize=12)
ax.legend(title='Category', fontsize=11, loc='upper left', bbox_to_anchor=(1.02, 1))
plt.tight_layout()
plt.savefig('tretyakov_trends.png', dpi=300, bbox_inches='tight')
print("Сохранено: tretyakov_trends.png\n")





# =====================================================================
# 2. NATIONAL COMPONENT SHARE (до/после 2022, по колонке category)
# =====================================================================

NATIONAL_LABEL = "национальное российское искусство"

n_before_total = len(before)
n_after_total = len(after)
n_before_national = (before['category'] == NATIONAL_LABEL).sum()
n_after_national = (after['category'] == NATIONAL_LABEL).sum()

pct_before = n_before_national / n_before_total * 100
pct_after = n_after_national / n_after_total * 100

national_share_df = pd.DataFrame([
    {'period': 'before_2022', 'total_records': n_before_total,
     'national_records': int(n_before_national), 'percent': round(pct_before, 1)},
    {'period': 'after_2022', 'total_records': n_after_total,
     'national_records': int(n_after_national), 'percent': round(pct_after, 1)},
])

national_share_df.to_csv('tretyakov_national_share.csv', index=False)
print("=== National Component Share ===")
print(national_share_df.to_string(index=False))
print("Сохранено: tretyakov_national_share.csv\n")

fig, ax = plt.subplots(figsize=(6, 7))
colors_share = ['#2F6663', '#A06060']
counts_plot = [n_before_national, n_after_national]
bars = ax.bar(['Before 2022', 'After 2022'], counts_plot, color=colors_share, width=0.55)
for bar, count, total in zip(bars, counts_plot, [n_before_total, n_after_total]):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
            f"{count} of {total}", ha='center', fontsize=12, fontweight='bold', color='#C9A84C')
ax.set_ylim(0, max(counts_plot) * 1.3)
ax.set_ylabel('Number of Exhibitions', fontsize=11)
ax.set_title(f'{MUSEUM_LABEL}: National Component Count', fontsize=15, pad=16)
plt.tight_layout()
plt.savefig('tretyakov_national_share.png', dpi=300, bbox_inches='tight')
print("Сохранено: tretyakov_national_share.png\n")