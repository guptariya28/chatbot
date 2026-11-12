# app.py
# The website. Every page is one function ("route").
# The math is in calculations.py, reading Excel is in excel_reader.py.

import io
from datetime import datetime
from urllib.parse import urlencode

import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, session, send_file

from excel_reader import load_demands
import calculations as calc


app = Flask(__name__)
app.secret_key = "change-this-later"   # needed to remember "Viewing as" (the session)


# ============================================================
# Data in memory (read once when the app starts)
# Edits stay only while the app runs. Use "Download Excel" to keep them.
# ============================================================
demands = load_demands()
change_log = []
settings = calc.make_default_settings(demands)

# The Functional Effort column has a line break in its name, so we find it
FUNC_COLUMN = calc.find_column(demands[0], "Funtional Effort")


# Fields you can change on the Edit page.
# type "choice" = a box where you pick an existing value or type a new one
EDIT_FIELDS = [
    {"column": calc.REQUIREMENT_COLUMN, "label": "Requirement", "type": "text"},
    {"column": calc.JIRA_COLUMN, "label": "JIRA ID", "type": "text"},
    {"column": calc.AOP_COLUMN, "label": "AOP / Non-AOP", "type": "choice"},
    {"column": calc.TOPIC_COLUMN, "label": "Topic Group", "type": "choice"},
    {"column": calc.MODULE_COLUMN, "label": "Tech Module", "type": "choice"},
    {"column": calc.IO_LEAD_COLUMN, "label": "IO Lead", "type": "choice"},
    {"column": calc.E4_COLUMN, "label": "Business E4 Manager", "type": "choice"},
    {"column": calc.CONFIRMATION_COLUMN, "label": "Business Confirmation", "type": "choice"},
    {"column": "Priority", "label": "Priority", "type": "choice"},
    {"column": calc.DEV_COLUMN, "label": "Development (Man-Days)", "type": "number"},
    {"column": FUNC_COLUMN, "label": "Functional (Man-Days)", "type": "number"},
    {"column": calc.DELIVERY_COLUMN, "label": "Actual / Planned Delivery Date", "type": "choice"},
    {"column": calc.MODE_COLUMN, "label": "In-house or MS/MT PKG", "type": "choice"},
    {"column": "Comments", "label": "Comments", "type": "text"},
]

# Columns shown in the Register table
REGISTER_COLUMNS = [
    {"column": calc.SI_NO_COLUMN, "label": "SI No"},
    {"column": calc.REQUIREMENT_COLUMN, "label": "Requirement"},
    {"column": calc.JIRA_COLUMN, "label": "JIRA ID"},
    {"column": calc.AOP_COLUMN, "label": "AOP"},
    {"column": calc.MODULE_COLUMN, "label": "Tech Module"},
    {"column": calc.IO_LEAD_COLUMN, "label": "IO Lead"},
    {"column": calc.E4_COLUMN, "label": "E4 Manager"},
    {"column": calc.CONFIRMATION_COLUMN, "label": "Confirmation"},
    {"column": calc.EFFORT_COLUMN, "label": "Total Effort"},
    {"column": calc.DELIVERY_COLUMN, "label": "Delivery Date"},
]

ROLES = [
    {"value": "admin", "label": "PMO Admin"},
    {"value": "io_lead", "label": "IO Lead"},
    {"value": "business", "label": "Business User"},
    {"value": "viewer", "label": "Viewer"},
]


# ============================================================
# Who is using the portal? (no login yet - picked in the top bar)
# ============================================================
def get_current_user():
    role = session.get("role", "admin")
    name = session.get("name", "PMO Admin")
    return {"role": role, "name": name}


# admin -> can edit everything.  IO Lead -> only items where they are the IO Lead.
def can_edit(user, row):
    if user["role"] == "admin":
        return True
    if user["role"] == "io_lead" and calc.same_text(row.get(calc.IO_LEAD_COLUMN, ""), user["name"]):
        return True
    return False


def can_raise_request(user):
    return user["role"] == "admin" or user["role"] == "business"


def find_demand(demand_id):
    for row in demands:
        if row["id"] == demand_id:
            return row
    return None


def add_log(user, row, text):
    entry = {
        "time": datetime.now().strftime("%d %b %Y, %H:%M"),
        "user": user["name"],
        "item": row,
        "text": text,
    }
    change_log.insert(0, entry)   # newest first


def count_pending_requests():
    count = 0
    for row in demands:
        if row.get(calc.REQUEST_STATUS_COLUMN, "") == "Pending review":
            count = count + 1
    return count


# Builds one "chart card" (bars + table) for a page
def make_card(card_id, title, rows, column, measure, filter_name):
    per_fte = settings["man_days_per_fte"]
    groups = calc.group_rows(rows, column, per_fte, measure)

    # Clicking a bar opens the Register filtered on that value
    for group in groups:
        group["link"] = ""
        if filter_name != "" and group["label"] != "(blank)":
            group["link"] = "/register?" + urlencode({filter_name: group["label"]})

    card = {
        "id": card_id,
        "title": title,
        "groups": groups,
        "totals": calc.get_totals(groups, per_fte),
    }
    return card


# These values are available in EVERY page (the top bar needs them)
@app.context_processor
def add_common_values():
    return {
        "user": get_current_user(),
        "roles": ROLES,
        "io_lead_names": calc.get_unique_values(demands, calc.IO_LEAD_COLUMN),
        "pending_count": count_pending_requests(),
    }


# ============================================================
# Page 1: Dashboard
# ============================================================
@app.route("/")
def dashboard():
    chosen = calc.read_filters(request.args)
    rows = calc.apply_filters(demands, chosen)
    per_fte = settings["man_days_per_fte"]

    # KPI cards
    total_man_days = 0
    must_count = 0
    package_count = 0
    non_aop_count = 0
    for row in rows:
        total_man_days = total_man_days + calc.get_effort(row)
        if calc.is_must_have(row):
            must_count = must_count + 1
        if calc.is_package(row):
            package_count = package_count + 1
        if calc.same_text(row.get(calc.AOP_COLUMN, ""), "NON-AOP"):
            non_aop_count = non_aop_count + 1

    kpis = {
        "item_count": len(rows),
        "man_days": total_man_days,
        "fte": round(total_man_days / per_fte, 2),
        "must": must_count,
        "packages": package_count,
        "non_aop": non_aop_count,
    }

    # Chart cards
    cards = [
        make_card("module", "Effort by Tech Module (man-days)", rows, calc.MODULE_COLUMN, "man_days", "tech_module"),
        make_card("e4", "FTE by Business E4 Manager", rows, calc.E4_COLUMN, "fte", "e4_manager"),
        make_card("iolead", "Items by IO Lead", rows, calc.IO_LEAD_COLUMN, "count", "io_lead"),
        make_card("confirmation", "Items by Business Confirmation", rows, calc.CONFIRMATION_COLUMN, "count", "confirmation"),
        make_card("mode", "In-house vs MS/MT Package", rows, calc.MODE_COLUMN, "count", ""),
        make_card("delivery", "Items by Delivery Date", rows, calc.DELIVERY_COLUMN, "count", ""),
    ]

    # 5 biggest items
    biggest_items = sorted(rows, key=calc.get_effort, reverse=True)[:5]

    return render_template(
        "dashboard.html",
        page="dashboard",
        chosen=chosen,
        filters=calc.FILTERS,
        filter_options=calc.get_filter_options(demands),
        kpis=kpis,
        cards=cards,
        biggest_items=biggest_items,
    )


# ============================================================
# Page 2: Demand Register (the table)
# ============================================================
@app.route("/register")
def register():
    chosen = calc.read_filters(request.args)
    rows = calc.apply_filters(demands, chosen)
    user = get_current_user()

    # Which rows can this user edit?
    editable_ids = []
    for row in rows:
        if can_edit(user, row):
            editable_ids.append(row["id"])

    return render_template(
        "register.html",
        page="register",
        chosen=chosen,
        filters=calc.FILTERS,
        filter_options=calc.get_filter_options(demands),
        rows=rows,
        total_count=len(demands),
        columns=REGISTER_COLUMNS,
        editable_ids=editable_ids,
        can_raise=can_raise_request(user),
    )


# ============================================================
# Page 3: Edit one item
# GET  = show the form,  POST = save the form
# ============================================================
@app.route("/edit/<int:demand_id>", methods=["GET", "POST"])
def edit(demand_id):
    row = find_demand(demand_id)
    user = get_current_user()

    if row is None:
        return "Item not found", 404

    # Everyone can VIEW an item. Only some users can change it.
    editable = can_edit(user, row)

    if request.method == "POST":
        if not editable:
            return "You are not allowed to edit this item", 403

        effort_changed = False

        for number in range(len(EDIT_FIELDS)):
            field = EDIT_FIELDS[number]
            column = field["column"]
            old_value = row.get(column, "")
            new_value = request.form.get("field_" + str(number), "").strip()

            if field["type"] == "number":
                if calc.to_number(old_value) == calc.to_number(new_value):
                    continue
                new_value = calc.to_number(new_value)
                effort_changed = True
            else:
                if calc.clean_text(old_value) == new_value:
                    continue

            row[column] = new_value
            add_log(user, row, field["label"] + ': "' + str(old_value) + '" -> "' + str(new_value) + '"')

        # Same formulas as the Excel:
        # Total Effort = Development + Functional
        if effort_changed:
            row[calc.EFFORT_COLUMN] = calc.to_number(row[calc.DEV_COLUMN]) + calc.to_number(row[FUNC_COLUMN])
        # IS PACKAGE = 1 when the item can be delivered as MS/MT PKG
        if calc.is_package(row):
            row[calc.PACKAGE_COLUMN] = 1
        else:
            row[calc.PACKAGE_COLUMN] = 0

        return redirect(url_for("edit", demand_id=demand_id, saved=1))

    # The choices for every "choice" box
    options = {}
    for field in EDIT_FIELDS:
        if field["type"] == "choice":
            options[field["column"]] = calc.get_unique_values(demands, field["column"])

    # This item's history
    history = []
    for entry in change_log:
        if entry["item"]["id"] == demand_id:
            history.append(entry)

    return render_template(
        "edit.html",
        page="register",
        row=row,
        editable=editable,
        fields=EDIT_FIELDS,
        options=options,
        history=history,
        saved=request.args.get("saved"),
    )


# ============================================================
# Page 4: Raise a new Non-AOP request
# ============================================================
@app.route("/new-request", methods=["GET", "POST"])
def new_request():
    user = get_current_user()
    if not can_raise_request(user):
        return "Only Business users or PMO can raise a request", 403

    if request.method == "POST":
        # A new row with every column empty
        new_row = {}
        for column in demands[0]:
            new_row[column] = ""

        biggest_id = 0
        for row in demands:
            if row["id"] > biggest_id:
                biggest_id = row["id"]

        new_row["id"] = biggest_id + 1
        new_row[calc.AOP_COLUMN] = "NON-AOP"
        new_row[calc.REQUEST_STATUS_COLUMN] = "Pending review"
        new_row[calc.REQUIREMENT_COLUMN] = request.form.get("requirement", "").strip()
        new_row[calc.TOPIC_COLUMN] = request.form.get("topic", "").strip()
        new_row[calc.MODULE_COLUMN] = request.form.get("module", "").strip()
        new_row[calc.IO_LEAD_COLUMN] = request.form.get("io_lead", "").strip()
        new_row[calc.E4_COLUMN] = request.form.get("e4_manager", "").strip()
        new_row[calc.CONFIRMATION_COLUMN] = request.form.get("confirmation", "").strip()
        new_row["Reporter"] = request.form.get("reporter", "").strip()
        new_row[calc.DELIVERY_COLUMN] = request.form.get("delivery", "").strip()
        new_row["Comments"] = request.form.get("comments", "").strip()
        new_row[calc.DEV_COLUMN] = calc.to_number(request.form.get("dev_days", ""))
        new_row[FUNC_COLUMN] = calc.to_number(request.form.get("func_days", ""))
        new_row[calc.EFFORT_COLUMN] = new_row[calc.DEV_COLUMN] + new_row[FUNC_COLUMN]

        demands.append(new_row)
        add_log(user, new_row, "raised a new Non-AOP request")

        return redirect(url_for("requests_page"))

    options = {
        "topic": calc.get_unique_values(demands, calc.TOPIC_COLUMN),
        "module": calc.get_unique_values(demands, calc.MODULE_COLUMN),
        "io_lead": calc.get_unique_values(demands, calc.IO_LEAD_COLUMN),
        "e4_manager": calc.get_unique_values(demands, calc.E4_COLUMN),
        "confirmation": calc.get_unique_values(demands, calc.CONFIRMATION_COLUMN),
    }
    return render_template("new_request.html", page="requests", options=options)


# ============================================================
# Page 5: Non-AOP requests (PMO approves or rejects)
# ============================================================
@app.route("/requests")
def requests_page():
    request_rows = []
    for row in demands:
        if row.get(calc.REQUEST_STATUS_COLUMN, "") != "":
            request_rows.append(row)

    user = get_current_user()
    return render_template(
        "requests.html",
        page="requests",
        rows=request_rows,
        can_raise=can_raise_request(user),
    )


@app.route("/approve/<int:demand_id>", methods=["POST"])
def approve(demand_id):
    user = get_current_user()
    row = find_demand(demand_id)
    if user["role"] == "admin" and row is not None:
        row[calc.REQUEST_STATUS_COLUMN] = "Approved"
        add_log(user, row, "approved the request")
    return redirect(url_for("requests_page"))


@app.route("/reject/<int:demand_id>", methods=["POST"])
def reject(demand_id):
    user = get_current_user()
    row = find_demand(demand_id)
    if user["role"] == "admin" and row is not None:
        row[calc.REQUEST_STATUS_COLUMN] = "Rejected"
        add_log(user, row, "rejected the request")
    return redirect(url_for("requests_page"))


# ============================================================
# Page 6: FTE Summary (the MBBP_Summary sheet)
# ============================================================
@app.route("/summary")
def summary():
    result = calc.calculate_summary(demands, settings)

    cards = [
        make_card("sum-e4", "Required FTE by Business E4 Manager", result["scope_rows"], calc.E4_COLUMN, "fte", "e4_manager"),
        make_card("sum-pkg", "Packaging possible (MS/MT PKG) by E4 Manager", result["package_rows"], calc.E4_COLUMN, "fte", "e4_manager"),
        make_card("sum-module", "Required FTE by Tech Module", result["scope_rows"], calc.MODULE_COLUMN, "fte", "tech_module"),
    ]

    return render_template(
        "summary.html",
        page="summary",
        result=result,
        settings=settings,
        cards=cards,
    )


@app.route("/summary/settings", methods=["POST"])
def save_settings():
    user = get_current_user()
    if user["role"] != "admin":
        return "Only PMO can change the settings", 403

    per_fte = calc.to_number(request.form.get("man_days_per_fte", ""))
    if per_fte > 0:
        settings["man_days_per_fte"] = per_fte

    settings["available_man_days"] = calc.to_number(request.form.get("available_man_days", ""))
    settings["included_modules"] = request.form.getlist("modules")
    settings["included_deliveries"] = request.form.getlist("deliveries")

    return redirect(url_for("summary"))


# ============================================================
# Page 7: Change log
# ============================================================
@app.route("/log")
def log():
    return render_template("log.html", page="log", change_log=change_log)


# ============================================================
# Top bar: "Viewing as"  and  "Download Excel"
# ============================================================
@app.route("/set-role", methods=["POST"])
def set_role():
    role = request.form.get("role", "admin")
    session["role"] = role

    if role == "admin":
        session["name"] = "PMO Admin"
    if role == "io_lead":
        session["name"] = request.form.get("io_lead_name", "")
    if role == "business":
        session["name"] = "Business User"
    if role == "viewer":
        session["name"] = "Viewer"

    # go back to the page you were on
    return redirect(request.referrer or url_for("dashboard"))


@app.route("/download")
def download():
    table = pd.DataFrame(demands)
    file = io.BytesIO()                       # a file in memory, not on disk
    table.to_excel(file, index=False, sheet_name="MBBP_2026_09Apr")
    file.seek(0)                              # go back to the start of the file
    return send_file(file, as_attachment=True, download_name="MBBP_portal_export.xlsx")


if __name__ == "__main__":
    app.run(debug=True)
