import pandas as pd
from bertopic import BERTopic
from sklearn.feature_extraction.text import CountVectorizer

# 1. Загрузка
df = pd.read_csv('final_analysis_cleaned.csv')
docs = df['text_to_analyze'].fillna("").astype(str).tolist()

# 2. Убираем английский шум (стоп-слова)
# Добавляем стандартные английские стоп-слова в список игнорирования
vectorizer_model = CountVectorizer(stop_words="english")

# 3. Обучаем с учетом того, что это русскоязычные тексты (язык можно указать явно)
topic_model = BERTopic(vectorizer_model=vectorizer_model, language="multilingual")

print("Анализирую данные (уже без английского шума)...")
topics, probs = topic_model.fit_transform(docs)

# 4. Вывод
print(topic_model.get_topic_info())
print(topic_model.get_topic(0))

