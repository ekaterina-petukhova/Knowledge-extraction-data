import pandas as pd
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import TfidfVectorizer

INPUT_FILE = 'pushkin_categorized.csv'
TEXT_COL = 'text_to_analyze'
MUSEUM_LABEL = 'Pushkin Museum'

df = pd.read_csv(INPUT_FILE)
df['year'] = pd.to_numeric(df['year'], errors='coerce')

before = df[df['year'] < 2022]
after = df[df['year'] >= 2022]

print(f"Всего записей: {len(df)}")
print(f"До 2022: {len(before)}  |  После 2022: {len(after)}\n")
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
    'музея', 'музей', 'музее', 'пушкинского', 'пушкинский', 'пушкина', 'гмии',
    'имени', 'государственный', 'государственного', 'государственных',
    'изобразительных', 'искусств', 'подробнее', 'представляет', 'выставку',
    'коллекции', 'коллекция', 'собрания', 'собрание', 'собраний',
    'согласен', 'нажимая', 'кнопку', 'подтверждаете',
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
    """TF-IDF по всему корпусу выборки -> {слово: средний вес на документ}."""
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

print("--- Топ слов ДО 2022 ---")
for w, s in top_before:
    print(f"{w}: {s:.4f}")
print("\n--- Топ слов ПОСЛЕ 2022 ---")
for w, s in top_after:
    print(f"{w}: {s:.4f}")

all_candidate_words = set(dict(top_before)) | set(dict(top_after))
combined_scores = {w: before_scores.get(w, 0) + after_scores.get(w, 0) for w in all_candidate_words}

TOP_N_KEYWORDS = 10
main_keywords = [w for w, _ in sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)[:TOP_N_KEYWORDS]]
print(f"\n=== Выбранные {TOP_N_KEYWORDS} главных ключевых слов ===")
print(main_keywords)

rows = []
for w in main_keywords:
    rows.append({'period': 'before_2022', 'word': w, 'tfidf_avg_score': round(float(before_scores.get(w, 0)), 4)})
for w in main_keywords:
    rows.append({'period': 'after_2022', 'word': w, 'tfidf_avg_score': round(float(after_scores.get(w, 0)), 4)})

keywords_df = pd.DataFrame(rows)
keywords_df.to_csv('pushkin_tfidf_keywords.csv', index=False)
print("\nСохранено: pushkin_tfidf_keywords.csv")

pivot_kw = keywords_df.pivot(index='word', columns='period', values='tfidf_avg_score')
pivot_kw['_sort'] = pivot_kw['before_2022'] + pivot_kw['after_2022']
pivot_kw = pivot_kw.sort_values('_sort', ascending=False).drop(columns='_sort')
pivot_kw = pivot_kw[['before_2022', 'after_2022']]

fig, ax = plt.subplots(figsize=(12, 6))
x = range(len(pivot_kw))
width = 0.38
ax.bar([i - width / 2 for i in x], pivot_kw['before_2022'], width, label='Before 2022', color='#2F6663')
ax.bar([i + width / 2 for i in x], pivot_kw['after_2022'], width, label='After 2022', color='#A06060')
ax.set_xticks(list(x))
ax.set_xticklabels(pivot_kw.index, rotation=0)
ax.set_ylabel('Mean TF-IDF Weight per Document', fontsize=11)
ax.set_title(f'{MUSEUM_LABEL}: Top Keywords, Before vs. After 2022', fontsize=15, pad=16)
ax.legend(fontsize=11)
plt.tight_layout()
plt.savefig('pushkin_tfidf_keywords.png', dpi=300, bbox_inches='tight')
print("Сохранено: pushkin_tfidf_keywords.png")