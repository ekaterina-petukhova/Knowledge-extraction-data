import pandas as pd
from bertopic import BERTopic
from sklearn.feature_extraction.text import CountVectorizer

df = pd.read_csv('final_analysis_cleaned.csv')
docs = df['text_to_analyze'].fillna("").astype(str).tolist()

vectorizer_model = CountVectorizer(stop_words="english")

topic_model = BERTopic(vectorizer_model=vectorizer_model, language="multilingual")

print("Анализирую данные (уже без английского шума)...")
topics, probs = topic_model.fit_transform(docs)

print(topic_model.get_topic_info())
print(topic_model.get_topic(0))

