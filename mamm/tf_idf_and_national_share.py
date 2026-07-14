import re
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import TfidfVectorizer, ENGLISH_STOP_WORDS

INPUT_FILE = 'mamm_categorized.csv'
TEXT_COL = 'text_to_analyze'

df = pd.read_csv(INPUT_FILE)
df['year'] = pd.to_numeric(df['year'], errors='coerce')

# =====================================================================
# 0. ЧИСТКА ВСТРОЕННОГО МУСОРА
#    В отличие от Эрмитажа (там было 15 ЦЕЛИКОМ мусорных записей),
#    у MAMM один и тот же блок (контакты музея, часы работы,
#    cookie-баннер, "Buy a ticket" и т.д.) вклеен ВНУТРЬ примерно
#    45% записей вперемешку с реальным текстом. Точное совпадение
#    тут не сработает — вырезаем блоки по устойчивым якорным фразам.
# =====================================================================

JUNK_ANCHORS = [
    r"MULTIMEDIA ART MUSEUM, MOSCOW.*?priemnaja@culture\.mos\.ru",
    r"Version for the visually impaired.*?I agree",
    r"We use cookies.*?I agree",
    r"Buy a ticket",
    r"Share with friends",
]

def strip_junk(text):
    if not isinstance(text, str):
        return ""
    for pattern in JUNK_ANCHORS:
        text = re.sub(pattern, " ", text, flags=re.DOTALL)
    return re.sub(r"\s+", " ", text).strip()

df[TEXT_COL] = df[TEXT_COL].apply(strip_junk)

before = df[df['year'] < 2022]
after = df[df['year'] >= 2022]

print(f"Всего записей: {len(df)}")
print(f"До 2022: {len(before)}  |  После 2022: {len(after)}\n")


# =====================================================================
# 1. NATIONAL COMPONENT SHARE
#    ВАЖНО: у MAMM категории на английском ("national Russian art",
#    "western art", "eastern art"), а не на русском — старое сравнение
#    с "национальное российское искусство" никогда бы не совпало.
# =====================================================================

NATIONAL_LABEL = "national Russian art"

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

national_share_df.to_csv('mamm_national_share.csv', index=False)
print("=== National Component Share ===")
print(national_share_df.to_string(index=False))
print("Сохранено: mamm_national_share.csv\n")

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
ax.set_title('MAMM: National Component Share', fontsize=15, pad=16)
plt.tight_layout()
plt.savefig('mamm_national_share.png', dpi=300, bbox_inches='tight')
print("Сохранено: mamm_national_share.png\n")


# =====================================================================
# 2. TOP TF-IDF KEYWORDS
#    Данные на английском -> английские стоп-слова (sklearn built-in)
#    + расширенный список мусорных/шаблонных слов сайта MAMM (то, что
#    просочилось бы даже после вырезания блоков выше).
# =====================================================================

mamm_domain_stop = [
    'moscow', 'museum', 'mamm', 'multimedia', 'exhibition', 'exhibitions',
    'close', 'video', 'press', 'ticket', 'tickets', 'email', 'mail',
    'inquiry', 'office', 'department', 'event', 'organization',
    'photobiennale', 'auditorium', 'events', 'rus', 'plan',
    'culture', 'mos', 'cookies', 'agree', 'read', 'ostozhenka',
    'monday', 'curator', 'curators', 'collection', 'collections',
    'hours', 'closed', 'information', 'visitors', 'disabilities',
    'impaired', 'version', 'visually', 'day', 'days', 'com', 'www',
    'org', 'tel', 'phone', 'strategic', 'partner', 'partners', 'official',
    'media', 'sponsor', 'friends', 'buy', 'use', 'ul', 'street', 'st',
    'photography', 'fashion', 'style', 'school', 'books', 'book',
    'biennales', 'rodchenko', 'anna', 'alexander', 'zaitseva', 'olga', 'sviblova', 'maria', 'lavrova'
]

all_stop = list(ENGLISH_STOP_WORDS) + mamm_domain_stop


def get_all_keyword_scores(text_series):
    """
    Считает TF-IDF по всему корпусу выборки, возвращает словарь
    {слово: средний вес НА ДОКУМЕНТ} = sum(tfidf) / n_documents.
    Среднее, а не сырая сумма, чтобы периоды разного размера
    (before/after) были сравнимы.
    """
    vec = TfidfVectorizer(
        stop_words=all_stop,
        max_features=1500,
        token_pattern=r'(?u)\b[^\d\W]{3,}\b'
    )
    tfidf = vec.fit_transform(text_series.fillna('').astype(str))
    words = vec.get_feature_names_out()
    sums = tfidf.sum(axis=0)
    n_docs = tfidf.shape[0]
    return {words[i]: sums[0, i] / n_docs for i in range(len(words))}


def top_n(scores_dict, n=15):
    return sorted(scores_dict.items(), key=lambda x: x[1], reverse=True)[:n]


before_scores = get_all_keyword_scores(before[TEXT_COL])
after_scores = get_all_keyword_scores(after[TEXT_COL])

top_before = top_n(before_scores, n=15)
top_after = top_n(after_scores, n=15)

print("--- Топ слов ДО 2022 (для отбора) ---")
for w, s in top_before:
    print(f"{w}: {s:.4f}")
print("\n--- Топ слов ПОСЛЕ 2022 (для отбора) ---")
for w, s in top_after:
    print(f"{w}: {s:.4f}")

# Выбираем 10 главных слов: объединяем топ-слова обоих периодов
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

# Вес каждого из этих слов в каждой выборке — из полнокорпусных словарей
rows = []
for w in main_keywords:
    rows.append({'period': 'before_2022', 'word': w, 'tfidf_avg_score': round(float(before_scores.get(w, 0)), 4)})
for w in main_keywords:
    rows.append({'period': 'after_2022', 'word': w, 'tfidf_avg_score': round(float(after_scores.get(w, 0)), 4)})

keywords_df = pd.DataFrame(rows)
keywords_df.to_csv('mamm_tfidf_keywords.csv', index=False)
print("\nСохранено: mamm_tfidf_keywords.csv")
print(keywords_df.to_string(index=False))

# --- график: Top Keywords (Mean TF-IDF per Document) ---
pivot = keywords_df.pivot(index='word', columns='period', values='tfidf_avg_score')
pivot['_sort'] = pivot['before_2022'] + pivot['after_2022']
pivot = pivot.sort_values('_sort', ascending=False).drop(columns='_sort')
pivot = pivot[['before_2022', 'after_2022']]

fig, ax = plt.subplots(figsize=(12, 6))
x = range(len(pivot))
width = 0.38

ax.bar([i - width / 2 for i in x], pivot['before_2022'], width, label='Before 2022', color='#2F6663')
ax.bar([i + width / 2 for i in x], pivot['after_2022'], width, label='After 2022', color='#A06060')

ax.set_xticks(list(x))
ax.set_xticklabels(pivot.index, rotation=0)
ax.set_ylabel('Mean TF-IDF Weight per Document', fontsize=11)
ax.set_title('MAMM: Top Keywords (Mean TF-IDF per Document), Before vs. After 2022', fontsize=15, pad=16)
ax.legend(fontsize=11)

plt.tight_layout()
plt.savefig('mamm_tfidf_keywords.png', dpi=300, bbox_inches='tight')
print("\nСохранено: mamm_tfidf_keywords.png")