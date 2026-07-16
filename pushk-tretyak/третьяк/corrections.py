import pandas as pd

df = pd.read_csv('final_analysis_results.csv')

corrections = {
}
def apply_corrections(row):
    for title, correct_cat in corrections.items():
        if title in str(row['title']):
            return correct_cat
    return row['category']

df['category'] = df.apply(apply_corrections, axis=1)

df.to_csv('final_analysis_results_fixed.csv', index=False)
print("Все правки применены! Файл 'final_analysis_results_fixed.csv' готов.")
