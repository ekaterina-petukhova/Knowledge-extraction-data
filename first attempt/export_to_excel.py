import pandas as pd

df = pd.read_csv('final_analysis_results.csv')
df.to_excel('my_data.xlsx', index=False)
print("Файл my_data.xlsx создан!")