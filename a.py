# sheet_extraction.py
# Goal: read the main sheet with the CORRECT header row and list every column.

import warnings
import pandas as pd
from openpyxl.utils import get_column_letter

# Hide the harmless "Data Validation" warning
warnings.filterwarnings("ignore")

file_name = "MBBP26_Apr_V1.xlsx"
sheet_name = "MBBP_2026_09Apr"

# header=3  ->  use Excel row 4 as the column names
data = pd.read_excel(file_name, sheet_name=sheet_name, header=3)

print("Number of rows:", len(data))
print("Number of columns:", len(data.columns))

# ---- Every column, with its Excel letter (A, B, C...) ----
print()
print("Column names:")
number = 1
for column in data.columns:
    letter = get_column_letter(number)
    print("  ", letter, "-", column)
    number = number + 1

# ---- How many rows are real items (they have an SI NO)? ----
print()
print("Rows with an SI NO:", data["SI NO"].notna().sum())

# ---- The first item, shown top to bottom (easier to read) ----
print()
print("First item:")
print(data.iloc[0])
