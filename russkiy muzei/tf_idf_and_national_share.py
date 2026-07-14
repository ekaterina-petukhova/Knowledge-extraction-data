import pandas as pd
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import TfidfVectorizer

INPUT_FILE = 'russkiy_muzei_classified_final.csv'

df = pd.read_csv(INPUT_FILE)
df['year'] = pd.to_numeric(df['year'], errors='coerce')

before = df[df['year'] < 2022]
after = df[df['year'] >= 2022]

print(f"Всего записей: {len(df)}")
print(f"До 2022: {len(before)}  |  После 2022: {len(after)}\n")


# =====================================================================
# 1. NATIONAL COMPONENT SHARE
#    Доля записей с category == "национальное российское искусство"
#    в каждой из двух выборок (year<2022 vs year>=2022)
# =====================================================================

NATIONAL_LABEL = "национальное российское искусство"

n_before_total = len(before)
n_after_total = len(after)
n_before_national = (before['category'] == NATIONAL_LABEL).sum()
n_after_national = (after['category'] == NATIONAL_LABEL).sum()

pct_before = n_before_national / n_before_total * 100
pct_after = n_after_national / n_after_total * 100

national_share_df = pd.DataFrame([
    {
        'period': 'before_2022',
        'total_records': n_before_total,
        'national_records': int(n_before_national),
        'percent': round(pct_before, 1),
    },
    {
        'period': 'after_2022',
        'total_records': n_after_total,
        'national_records': int(n_after_national),
        'percent': round(pct_after, 1),
    },
])

national_share_df.to_csv('russian_museum_national_share.csv', index=False)
print("=== National Component Share ===")
print(national_share_df.to_string(index=False))
print("Сохранено: russian_museum_national_share.csv\n")

# --- график: National Component Share ---
plt.style.use('seaborn-v0_8-whitegrid')
fig, ax = plt.subplots(figsize=(6, 7))
colors_share = ['#2F6663', '#A06060']
bars = ax.bar(['Before 2022', 'After 2022'], [pct_before, pct_after], color=colors_share, width=0.55)

for bar, pct in zip(bars, [pct_before, pct_after]):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1,
            f"{pct:.1f}%", ha='center', fontsize=12, fontweight='bold', color='#C9A84C')

ax.set_ylim(0, max(pct_before, pct_after) * 1.3)
ax.set_ylabel('Share of Exhibitions (%)', fontsize=11)
ax.set_title('National Component Share', fontsize=15, pad=16)
plt.tight_layout()
plt.savefig('russian_museum_national_share.png', dpi=300, bbox_inches='tight')
print("Сохранено: russian_museum_national_share.png\n")


# =====================================================================
# 2. TOP TF-IDF KEYWORDS
#    Считаем TF-IDF отдельно для before/after, находим топ-слова
#    по каждому периоду, объединяем в единый список 8-10 главных слов,
#    затем считаем вес (tfidf_score) КАЖДОГО из этих слов в ОБЕИХ выборках
# =====================================================================

RUSSIAN_STOPWORDS = [
    "и","в","во","не","что","он","на","я","с","со","как","а","то","все","она",
    "так","его","но","да","ты","к","у","же","вы","за","бы","по","только","ее",
    "мне","было","вот","от","меня","еще","нет","о","из","ему","теперь","когда",
    "даже","ну","вдруг","ли","если","уже","или","ни","быть","был","него","до",
    "вас","нибудь","опять","уж","вам","ведь","там","потом","себя","ничего","ей",
    "может","они","тут","где","есть","надо","ней","для","мы","тебя","их","чем",
    "была","сам","чтоб","без","будто","чего","раз","тоже","себе","под","будет",
    "ж","тогда","кто","этот","того","потому","этого","какой","совсем","ним",
    "здесь","этом","один","почти","мой","тем","чтобы","нее","сейчас","были",
    "куда","зачем","всех","никогда","можно","при","наконец","два","об","другой",
    "хоть","после","над","больше","тот","через","эти","нас","про","всего",
    "них","какая","много","разве","три","эту","моя","впрочем","хорошо","свою",
    "этой","перед","иногда","лучше","чуть","том","нельзя","такой","им","более",
    "всегда","конечно","всю","между",
]

domain_generic = [
    'год', 'году', 'года', 'лет', 'век', 'века', 'веке', 'время', 'времени',
    'работы', 'работ', 'работа', 'произведения', 'произведение', 'произведений',
    'истории', 'история', 'жизни', 'жизнь',
    'экспозиции', 'экспозиция', 'представлены', 'представлена', 'представлен',
    'музея', 'музей', 'музее', 'русский', 'русского', 'русском', 'русским',
    'коллекции', 'коллекция', 'собрания', 'собрание',
    'зал', 'залы', 'залах', 'зале',
    'картина', 'картины', 'картин',
    'художник', 'художника', 'художников', 'художники',
    'выставка', 'выставки', 'выставке', 'выставок',
    'который', 'которые', 'которых', 'которой', 'которым',
    'это', 'её', 'также', 'один', 'одной', 'одного',
]

en_stop = [
    'the','of','and','to','is','in','from','are','with','this','by','his',
    'that','their','through','show','on','for','as','it','was','at',
]

all_stop = RUSSIAN_STOPWORDS + domain_generic + en_stop


def get_all_keyword_scores(text_series):
    """Считает TF-IDF по всему корпусу выборки, возвращает словарь {слово: суммарный вес}."""
    vec = TfidfVectorizer(
        stop_words=all_stop,
        max_features=1500,
        token_pattern=r'(?u)\b[^\d\W]{3,}\b'
    )
    tfidf = vec.fit_transform(text_series.fillna('').astype(str))
    words = vec.get_feature_names_out()
    sums = tfidf.sum(axis=0)
    return {words[i]: sums[0, i] for i in range(len(words))}


def top_n(scores_dict, n=15):
    return sorted(scores_dict.items(), key=lambda x: x[1], reverse=True)[:n]


before_scores = get_all_keyword_scores(before['description'])
after_scores = get_all_keyword_scores(after['description'])

top_before = top_n(before_scores, n=15)
top_after = top_n(after_scores, n=15)

print("--- Топ слов ДО 2022 (для отбора) ---")
for w, s in top_before:
    print(f"{w}: {s:.4f}")
print("\n--- Топ слов ПОСЛЕ 2022 (для отбора) ---")
for w, s in top_after:
    print(f"{w}: {s:.4f}")

# Выбираем 8-10 главных слов: объединяем топ-слова обоих периодов
# по сумме их веса в before+after, берём самые значимые
all_candidate_words = set(dict(top_before)) | set(dict(top_after))

combined_scores = {
    w: before_scores.get(w, 0) + after_scores.get(w, 0)
    for w in all_candidate_words
}

TOP_N_KEYWORDS = 10
main_keywords = [w for w, _ in sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)[:TOP_N_KEYWORDS]]

print(f"\n=== Выбранные {TOP_N_KEYWORDS} главных ключевых слов ===")
print(main_keywords)

# Вес каждого из этих слов в каждой выборке берём из уже посчитанных
# полнокорпусных TF-IDF словарей (before_scores / after_scores) —
# так веса остаются сопоставимы и посчитаны в одинаковой системе координат.
rows = []
for w in main_keywords:
    rows.append({'period': 'before_2022', 'word': w, 'tfidf_score': round(float(before_scores.get(w, 0)), 4)})
for w in main_keywords:
    rows.append({'period': 'after_2022', 'word': w, 'tfidf_score': round(float(after_scores.get(w, 0)), 4)})

keywords_df = pd.DataFrame(rows)
keywords_df.to_csv('russian_museum_tfidf_keywords.csv', index=False)
print("\nСохранено: russian_museum_tfidf_keywords.csv")
print(keywords_df.to_string(index=False))

# --- график: Top Keywords (TF-IDF Weight), сгруппированные столбцы ---
pivot = keywords_df.pivot(index='word', columns='period', values='tfidf_score')
# сортируем по убыванию суммарного веса, чтобы самые весомые слова были слева
pivot['_sort'] = pivot['before_2022'] + pivot['after_2022']
pivot = pivot.sort_values('_sort', ascending=False).drop(columns='_sort')
pivot = pivot[['before_2022', 'after_2022']]

fig, ax = plt.subplots(figsize=(12, 6))
x = range(len(pivot))
width = 0.38

bars1 = ax.bar([i - width / 2 for i in x], pivot['before_2022'], width, label='Before 2022', color='#2F6663')
bars2 = ax.bar([i + width / 2 for i in x], pivot['after_2022'], width, label='After 2022', color='#A06060')

ax.set_xticks(list(x))
ax.set_xticklabels(pivot.index, rotation=0)
ax.set_ylabel('TF-IDF Weight', fontsize=11)
ax.set_title('Top Keywords (TF-IDF Weight): Before vs. After 2022', fontsize=15, pad=16)
ax.legend(fontsize=11)

plt.tight_layout()
plt.savefig('russian_museum_tfidf_keywords.png', dpi=300, bbox_inches='tight')
print("\nСохранено: russian_museum_tfidf_keywords.png")