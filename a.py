# excel_reader.py
# STEP 1: Read the demand list from Excel and give it to the portal.

import warnings
import pandas as pd

# Hide the harmless "Data Validation" warning from openpyxl
warnings.filterwarnings("ignore")

EXCEL_FILE = "MBBP26_Apr_V1.xlsx"
SHEET_NAME = "MBBP_2026_09Apr"
HEADER_ROW = 3          # column names are in Excel row 4 (pandas counts from 0)


def load_demands():
    # 1. Read the sheet
    data = pd.read_excel(EXCEL_FILE, sheet_name=SHEET_NAME, header=HEADER_ROW)

    # 2. Keep only real items (rows that have an SI NO)
    data = data[data["SI NO"].notna()]

    # 3. Show SI NO as 1, 2, 3 instead of 1.0, 2.0, 3.0
    data["SI NO"] = data["SI NO"].astype(int)

    # 4. Add our own unique id (SI NO repeats, so we can't use it)
    data.insert(0, "id", range(1, len(data) + 1))

    # 5. Empty cells: NaN -> "" (empty text)
    data = data.fillna("")

    # 6. Turn the table into a list of rows
    rows = data.to_dict(orient="records")

    return rows


# ------------------------------------------------------------
# This part runs ONLY when you run this file directly:
#     python excel_reader.py
# When Flask uses this file later, this part is skipped.
# ------------------------------------------------------------
if __name__ == "__main__":
    demands = load_demands()

    print("Items loaded:", len(demands))
    print("Columns per item:", len(demands[0]))

    print()
    print("First item:")
    first_item = demands[0]
    for column in first_item:
        print("  ", column, ":", first_item[column])
