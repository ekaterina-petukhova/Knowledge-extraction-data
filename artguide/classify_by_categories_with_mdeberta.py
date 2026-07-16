import pandas as pd
from transformers import pipeline


df_rm = pd.read_csv('artguide_events_moscow_2014_2026.csv')

classifier = pipeline("zero-shot-classification", model="MoritzLaurer/mDeBERTa-v3-base-mnli-xnli")
labels = ["западное искусство", "восточное искусство", "национальное российское искусство"]


def get_category(text):
    text_snippet = str(text)[:512]
    # Используем шаблон гипотезы, чтобы модель "лучше соображала"
    result = classifier(
        text_snippet, 
        labels, 
        multi_label=False, 
        hypothesis_template="Это искусство относится к категории: {}"
    )

    
    return result['labels'][0]


print(f"Начинаю классификацию {len(df_rm)} записей...")

categories = []
for i, text in enumerate(df_rm['raw_text']):
    categories.append(get_category(text))
    if (i + 1) % 20 == 0:
        print(f"Обработано {i + 1} из {len(df_rm)}...")

df_rm['category'] = categories


df_rm.to_csv('artguide_classified.csv', index=False)
print("Готово! Результаты в 'artguide_classified.csv'.")