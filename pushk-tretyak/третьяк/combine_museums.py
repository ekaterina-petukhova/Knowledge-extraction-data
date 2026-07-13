import pandas as pd

pushkin = pd.read_csv("pushkin_exhibitions_raw.csv")
tretyakov = pd.read_csv("tretyakov_exhibitions_2014_2026.csv")

combined = pd.concat([pushkin, tretyakov], ignore_index=True)

combined.to_csv("museum_exhibitions_combined.csv", index=False, encoding="utf-8-sig")

print("Создан файл: museum_exhibitions_combined.csv")
print("Всего строк:", len(combined))
print(combined.head().to_string())