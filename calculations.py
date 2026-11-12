# calculations.py
# All the filtering and math of the portal.
# Plain Python only - no Flask in this file.


# ============================================================
# Excel column names we use (exactly as they are in the Excel)
# ============================================================
SI_NO_COLUMN = "SI NO"
REQUIREMENT_COLUMN = "Requirement/CR/New Demand Item"
JIRA_COLUMN = "JIRA ID"
TOPIC_COLUMN = "Topic Group"
AOP_COLUMN = "AOP/NON-AOP"
IO_LEAD_COLUMN = "IO Lead"
E4_COLUMN = "Business E4 manager"
MODULE_COLUMN = "Module.1"                          # tech module (FICO, LOGISTICS...)
CONFIRMATION_COLUMN = "Business Confirmation"
DEV_COLUMN = "Development (Man-Days)"
EFFORT_COLUMN = "Total Effort (Man-Days)"
DELIVERY_COLUMN = "Actual Date/ Planned Del. Date"
MODE_COLUMN = "Can this Object be delivered as Inhouse or can it be deliverd as MS/MT PKG?"
PACKAGE_COLUMN = "IS PACKAGE(Y/N)"

# Our own column, only for Non-AOP requests raised in the portal
REQUEST_STATUS_COLUMN = "Request Status"


# The filter dropdowns used on the Dashboard and the Register.
# "name" is the name in the web address, e.g. /register?io_lead=Ravi S
FILTERS = [
    {"name": "io_lead", "column": IO_LEAD_COLUMN, "all_text": "All IO Leads"},
    {"name": "e4_manager", "column": E4_COLUMN, "all_text": "All E4 Managers"},
    {"name": "tech_module", "column": MODULE_COLUMN, "all_text": "All Tech Modules"},
    {"name": "confirmation", "column": CONFIRMATION_COLUMN, "all_text": "All Confirmations"},
]


# ============================================================
# Small helpers
# ============================================================

# "20" -> 20.0,   "" -> 0,   "TBD" -> 0
def to_number(value):
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0


# Any value -> text without spaces at the start and end
def clean_text(value):
    return str(value).strip()


# True if two texts are the same, ignoring capitals and extra spaces.
# "Must to have " and "Must to Have" -> True   (Excel pivots work like this)
def same_text(first, second):
    return clean_text(first).lower() == clean_text(second).lower()


# Finds a column whose name starts with some text.
# Used for "Funtional Effort \n(Man-Days)" which has a line break in its name.
def find_column(row, starts_with):
    for column in row:
        if column.startswith(starts_with) and not column.endswith(".1"):
            return column
    return ""


# All different values of one column, A to Z.
# "Must to Have" and "Must to have" count as ONE value.
def get_unique_values(rows, column):
    values = []
    seen = []
    for row in rows:
        value = clean_text(row.get(column, ""))
        if value == "":
            continue
        if value.lower() in seen:
            continue
        seen.append(value.lower())
        values.append(value)
    values.sort()
    return values


def is_package(row):
    return clean_text(row.get(MODE_COLUMN, "")).upper() == "MS/MT PKG"


def is_must_have(row):
    return same_text(row.get(CONFIRMATION_COLUMN, ""), "Must to Have")


# Non-AOP requests that are waiting or rejected don't count anywhere
def is_not_approved(row):
    status = row.get(REQUEST_STATUS_COLUMN, "")
    return status == "Pending review" or status == "Rejected"


# The delivery date text, or "(blank)" when empty
def get_delivery_value(row):
    value = clean_text(row.get(DELIVERY_COLUMN, ""))
    if value == "":
        return "(blank)"
    return value


# The tech module text, or "(blank)" when empty
def get_module_value(row):
    value = clean_text(row.get(MODULE_COLUMN, ""))
    if value == "":
        return "(blank)"
    return value


# Used to sort rows by effort (biggest first)
def get_effort(row):
    return to_number(row.get(EFFORT_COLUMN, ""))


# ============================================================
# Filters (Dashboard + Register)
# ============================================================

# Reads the chosen filters from the web address.
# /register?io_lead=Ravi S&search=PR  ->  {"io_lead": "Ravi S", ..., "search": "PR"}
def read_filters(args):
    chosen = {}
    for filter_info in FILTERS:
        chosen[filter_info["name"]] = args.get(filter_info["name"], "")
    chosen["search"] = args.get("search", "")
    return chosen


# Keeps only the rows that match the chosen filters and search text
def apply_filters(rows, chosen):
    search_text = chosen["search"].lower().strip()
    result = []

    for row in rows:
        keep = True

        for filter_info in FILTERS:
            chosen_value = chosen[filter_info["name"]]
            if chosen_value != "":
                if not same_text(row.get(filter_info["column"], ""), chosen_value):
                    keep = False

        if search_text != "":
            row_text = (
                str(row.get(REQUIREMENT_COLUMN, "")) + " "
                + str(row.get(JIRA_COLUMN, "")) + " "
                + str(row.get(TOPIC_COLUMN, "")) + " "
                + str(row.get(SI_NO_COLUMN, ""))
            ).lower()
            if search_text not in row_text:
                keep = False

        if keep:
            result.append(row)

    return result


# The options for every filter dropdown
def get_filter_options(rows):
    options = {}
    for filter_info in FILTERS:
        options[filter_info["name"]] = get_unique_values(rows, filter_info["column"])
    return options


# ============================================================
# Grouping (like an Excel pivot table)
# ============================================================

# Groups rows by one column and adds them up.
# measure = what the bar shows: "count", "man_days" or "fte"
#
# Result, one item per group, biggest first:
#   {"label": "Ravi S", "count": 70, "jira_count": 52, "man_days": 1530,
#    "packages": 13, "fte": 9.0, "value": 70, "value_text": "70", "percent": 100}
def group_rows(rows, column, man_days_per_fte, measure):
    groups = {}   # key = label in small letters, so "Must to have" and "Must to Have" join

    for row in rows:
        label = clean_text(row.get(column, ""))
        if label == "":
            label = "(blank)"
        key = label.lower()

        if key not in groups:
            groups[key] = {"label": label, "count": 0, "jira_count": 0, "man_days": 0, "packages": 0}

        group = groups[key]
        group["count"] = group["count"] + 1
        group["man_days"] = group["man_days"] + get_effort(row)
        if clean_text(row.get(JIRA_COLUMN, "")) != "":
            group["jira_count"] = group["jira_count"] + 1
        if is_package(row):
            group["packages"] = group["packages"] + 1

    group_list = list(groups.values())

    # FTE and the value for the bar
    for group in group_list:
        group["fte"] = round(group["man_days"] / man_days_per_fte, 2)
        group["value"] = group[measure]
        if measure == "fte":
            group["value_text"] = "{:.2f}".format(group["value"])
        else:
            group["value_text"] = "{:,.0f}".format(group["value"])

    group_list.sort(key=get_group_value, reverse=True)

    # Bar length in % (the biggest group = 100%)
    biggest = 0
    if len(group_list) > 0:
        biggest = group_list[0]["value"]
    for group in group_list:
        if biggest > 0:
            group["percent"] = round(group["value"] / biggest * 100)
        else:
            group["percent"] = 0

    return group_list


def get_group_value(group):
    return group["value"]


# Adds up a list of groups (for the "Grand Total" row)
def get_totals(groups, man_days_per_fte):
    totals = {"count": 0, "jira_count": 0, "man_days": 0, "packages": 0}
    for group in groups:
        totals["count"] = totals["count"] + group["count"]
        totals["jira_count"] = totals["jira_count"] + group["jira_count"]
        totals["man_days"] = totals["man_days"] + group["man_days"]
        totals["packages"] = totals["packages"] + group["packages"]
    totals["fte"] = round(totals["man_days"] / man_days_per_fte, 2)
    return totals


# ============================================================
# FTE Summary (the MBBP_Summary sheet)
# ============================================================

# Delivery dates BEFORE the plan period (Apr-Dec 2026):
# anything in 2025, and Jan / Feb / Mar 2026.
# "Mar' 26" -> True,  "Dec' 25" -> True,  "Aug'26" -> False,  "Q3 2026" -> False
def is_before_period(text):
    short = text.lower().replace(" ", "").replace("'", "")
    if "25" in short:
        return True
    if short.startswith("jan") and "26" in short:
        return True
    if short.startswith("feb") and "26" in short:
        return True
    if short.startswith("mar") and "26" in short:
        return True
    return False


# The first settings when the app starts.
# These are the same choices as the ticks in the Excel pivot filters.
def make_default_settings(rows):
    all_modules = []
    all_deliveries = []
    for row in rows:
        module = get_module_value(row)
        if module not in all_modules:
            all_modules.append(module)
        delivery = get_delivery_value(row)
        if delivery not in all_deliveries:
            all_deliveries.append(delivery)
    all_modules.sort()
    all_deliveries.sort()

    # Modules: everything except TRAVEL, SAC and empty
    included_modules = []
    for module in all_modules:
        if module.upper() not in ["TRAVEL", "SAC", "(BLANK)"]:
            included_modules.append(module)

    # Delivery dates: everything except "Drop" and dates before April 2026
    included_deliveries = []
    for delivery in all_deliveries:
        if delivery.lower() == "drop":
            continue
        if is_before_period(delivery):
            continue
        included_deliveries.append(delivery)

    settings = {
        "man_days_per_fte": 170,
        "available_man_days": 0,
        "all_modules": all_modules,
        "included_modules": included_modules,
        "all_deliveries": all_deliveries,
        "included_deliveries": included_deliveries,
    }
    return settings


# Is this row counted as "required work"?  (= the Excel pivot filters)
def is_in_scope(row, settings):
    if not is_must_have(row):
        return False
    if is_not_approved(row):
        return False
    if get_module_value(row) not in settings["included_modules"]:
        return False
    if get_delivery_value(row) not in settings["included_deliveries"]:
        return False
    return True


def calculate_summary(rows, settings):
    per_fte = settings["man_days_per_fte"]

    scope_rows = []        # required work
    package_rows = []      # required work that MS/MT can deliver
    before_rows = []       # Must to Have, delivered before April 2026
    dropped_rows = []      # Must to Have, marked "Drop"

    for row in rows:
        if is_in_scope(row, settings):
            scope_rows.append(row)
            if is_package(row):
                package_rows.append(row)

        if is_must_have(row) and get_module_value(row) in settings["included_modules"]:
            delivery = get_delivery_value(row)
            if is_before_period(delivery):
                before_rows.append(row)
            if delivery.lower() == "drop":
                dropped_rows.append(row)

    required_man_days = 0
    for row in scope_rows:
        required_man_days = required_man_days + get_effort(row)

    package_man_days = 0
    for row in package_rows:
        package_man_days = package_man_days + get_effort(row)

    before_man_days = 0
    for row in before_rows:
        before_man_days = before_man_days + get_effort(row)

    dropped_man_days = 0
    for row in dropped_rows:
        dropped_man_days = dropped_man_days + get_effort(row)

    available_man_days = settings["available_man_days"]

    summary = {
        "per_fte": per_fte,
        "scope_count": len(scope_rows),

        "required_man_days": required_man_days,
        "required_fte": round(required_man_days / per_fte, 2),

        "available_man_days": available_man_days,
        "available_fte": round(available_man_days / per_fte, 2),

        "deficit_man_days": available_man_days - required_man_days,
        "deficit_fte": round((available_man_days - required_man_days) / per_fte, 2),

        "package_count": len(package_rows),
        "package_man_days": package_man_days,
        "package_fte": round(package_man_days / per_fte, 2),

        "before_count": len(before_rows),
        "before_man_days": before_man_days,
        "before_fte": round(before_man_days / per_fte, 2),

        "dropped_count": len(dropped_rows),
        "dropped_man_days": dropped_man_days,
        "dropped_fte": round(dropped_man_days / per_fte, 2),

        "scope_rows": scope_rows,
        "package_rows": package_rows,
    }

    summary["deficit_after_package_fte"] = round(summary["deficit_fte"] + summary["package_fte"], 2)

    return summary
