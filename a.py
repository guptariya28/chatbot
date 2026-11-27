import pandas as pd

# 1. Update these names to match your file
file = 'your_file.xlsx'
master = pd.read_excel(file, sheet_name='alice_user')
keywords = pd.read_excel(file, sheet_name='keywords')

# 2. Grab all text from the master sheet
all_text = str(master.values).lower()

# 3. Check each keyword (assumes keywords are in the first column)
for word in keywords.iloc[:, 0].dropna():
    if str(word).lower() in all_text:
        print(f"{word} -> Found")
    else:
        print(f"{word} -> Not Found")
