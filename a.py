# step1_read_excel.py
# Goal: open the Excel file and SEE what is inside. Nothing is saved.

import pandas as pd

file_name = "MBBP26_Apr_V1.xlsx"

# ---- Part 1: which sheets are in the file? ----
excel_file = pd.ExcelFile(file_name)

print("Sheets in this file:")
for sheet in excel_file.sheet_names:
    print("  -", sheet)

# ---- Part 2: read the main sheet ----
sheet_name = "MBBP_2026_09Apr"
data = pd.read_excel(file_name, sheet_name=sheet_name)

print()
print("Number of rows:", len(data))
print("Number of columns:", len(data.columns))

# ---- Part 3: the exact column names ----
print()
print("Column names:")
for column in data.columns:
    print("  -", column)

# ---- Part 4: the first 5 rows ----
print()
print("First 5 rows:")
print(data.head())
