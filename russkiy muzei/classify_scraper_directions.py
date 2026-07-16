import pandas as pd
from transformers import pipeline

df_rm = pd.read_csv('russkiy muzei/russian_museum_exhibitions_2014_2026_updated_ordered.csv')

classifier = pipeline("zero-shot-classification", model="MoritzLaurer/mDeBERTa-v3-base-mnli-xnli")
labels = ["западное искусство", "восточное искусство", "национальное российское искусство"]

def get_category(text):
    text_snippet = str(text)[:512]
    result = classifier(
        text_snippet, 
        labels, 
        multi_label=False, 
        hypothesis_template="Это искусство относится к категории: {}"
    )
    
    return result['labels'][0]

print(f"Начинаю классификацию {len(df_rm)} записей...")

categories = []
for i, text in enumerate(df_rm['description']):
    categories.append(get_category(text))
    if (i + 1) % 20 == 0:
        print(f"Обработано {i + 1} из {len(df_rm)}...")

df_rm['category'] = categories

df_rm.to_csv('russkiy_muzei_classified_final.csv', index=False)
print("Готово! Результаты в 'russkiy_muzei_classified_final.csv'.")