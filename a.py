# step1_read_excel.py
# STEP 1: Read the Excel file and understand the data.
# Nothing is changed or saved. We only LOOK.

import warnings
import pandas as pd
from openpyxl.utils import get_column_letter

# Hide the harmless "Data Validation" warning
warnings.filterwarnings("ignore")

file_name = "MBBP26_Apr_V1.xlsx"
sheet_name = "MBBP_2026_09Apr"


# ============================================================
# Part 1: Which sheets are in the file?
# ============================================================
excel_file = pd.ExcelFile(file_name)

print("Sheets in this file:")
for sheet in excel_file.sheet_names:
    print("  -", sheet)


# ============================================================
# Part 2: Read the main sheet
# header=3 -> the column names are in Excel row 4
# ============================================================
data = pd.read_excel(file_name, sheet_name=sheet_name, header=3)

print()
print("Rows read:", len(data))
print("Columns read:", len(data.columns))


# ============================================================
# Part 3: Every column with its position and Excel letter
# position starts at 0, Excel letter starts at A
# ============================================================
print()
print("Columns (position, letter, name):")
position = 0
for column in data.columns:
    letter = get_column_letter(position + 1)
    print("  ", position, letter, "-", column)
    position = position + 1


# ============================================================
# Part 4: Columns whose names are hard to type -> use position
# ============================================================
functional_column = data.columns[22]       # W  Funtional Effort (Man-Days)
functional_old_column = data.columns[25]   # Z  Funtional Effort (Man-Days).1
delivery_date_column = data.columns[27]    # AB Actual Date/ Planned Del. Date
delivery_mode_column = data.columns[30]    # AE Can this Object be delivered as ... MS/MT PKG?


# ============================================================
# Part 5: Keep only real items (rows that have an SI NO)
# ============================================================
data = data[data["SI NO"].notna()]

print()
print("Items with an SI NO:", len(data))
print("Duplicate SI NO:", data["SI NO"].duplicated().sum())


# ============================================================
# Part 6: Are the second effort columns (Y, Z, AA) used?
# ============================================================
print()
print("Filled cells in Y  Development (Man-Days).1:", data["Development (Man-Days).1"].notna().sum())
print("Filled cells in Z  Functional Effort .1:    ", data[functional_old_column].notna().sum())
print("Filled cells in AA Total Effort (Man-Days).1:", data["Total Effort (Man-Days).1"].notna().sum())


# ============================================================
# Part 7: Is Total (X) always Development (V) + Functional (W)?
# ============================================================
dev = pd.to_numeric(data["Development (Man-Days)"], errors="coerce").fillna(0)
func = pd.to_numeric(data[functional_column], errors="coerce").fillna(0)
total = pd.to_numeric(data["Total Effort (Man-Days)"], errors="coerce").fillna(0)

wrong_rows = data[dev + func != total]

print()
print("Rows where Development + Functional is NOT equal to Total:", len(wrong_rows))
print(wrong_rows[["SI NO", "Development (Man-Days)", functional_column, "Total Effort (Man-Days)"]])


# ============================================================
# Part 8: What values are inside the important columns?
# ============================================================
columns_to_check = [
    "AOP/NON-AOP",                    # F
    "AOP/NON-AOP.1",                  # AG
    "Business Confirmation",          # AC
    "Mandatory Grouping (IO View)",   # U
    "Module.1",                       # T  (tech module)
    delivery_mode_column,             # AE
    "IS PACKAGE(Y/N)",                # AF
    "Business E4 manager",            # N
    "IO Lead",                        # K
    delivery_date_column,             # AB
]

for column in columns_to_check:
    print()
    print("========", column, "========")
    print(data[column].value_counts(dropna=False))
