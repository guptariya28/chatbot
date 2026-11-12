// ============================================================
// app.js - everything that happens in the browser
//   1. get the data from Flask   (/api/demands)
//   2. fill the filter dropdowns
//   3. draw the KPI cards and the table
//   4. redraw when a filter changes
// ============================================================


// ---------- Settings ----------

// Which Excel columns to show in the table, and the short title to show.
// "key" must be EXACTLY the Excel column name.
const COLUMNS = [
  { key: "SI NO", label: "SI No" },
  { key: "Requirement/CR/New Demand Item", label: "Requirement" },
  { key: "JIRA ID", label: "JIRA ID" },
  { key: "Topic Group", label: "Topic Group" },
  { key: "Module.1", label: "Tech Module" },
  { key: "IO Lead", label: "IO Lead" },
  { key: "Business E4 manager", label: "Business E4 Manager" },
  { key: "Business Confirmation", label: "Business Confirmation" },
  { key: "Total Effort (Man-Days)", label: "Total Effort" },
  { key: "Actual Date/ Planned Del. Date", label: "Delivery Date" }
];

// The filter dropdowns: which Excel column, which <select> on the page,
// and the text of the first option.
const FILTERS = [
  { key: "IO Lead", selectId: "filter-io-lead", allText: "All IO Leads" },
  { key: "Business E4 manager", selectId: "filter-e4-manager", allText: "All E4 Managers" },
  { key: "Module.1", selectId: "filter-tech-module", allText: "All Tech Modules" },
  { key: "Business Confirmation", selectId: "filter-confirmation", allText: "All Confirmations" }
];

// Excel column names used by the KPI cards
const EFFORT_COLUMN = "Total Effort (Man-Days)";
const CONFIRMATION_COLUMN = "Business Confirmation";
const PACKAGE_COLUMN = "Can this Object be delivered as Inhouse or can it be deliverd as MS/MT PKG?";


// ---------- Data ----------
let allDemands = [];   // all 301 rows from Flask


// ============================================================
// 1. Get the data from Flask
// ============================================================
async function loadData() {
  const response = await fetch("/api/demands");
  allDemands = await response.json();

  fillFilterDropdowns();
  showPage();
}


// ============================================================
// 2. Fill every filter dropdown with the values found in the data
// ============================================================
function fillFilterDropdowns() {
  for (let i = 0; i < FILTERS.length; i++) {
    const filter = FILTERS[i];
    const values = getUniqueValues(filter.key);

    let html = '<option value="">' + filter.allText + "</option>";
    for (let j = 0; j < values.length; j++) {
      const value = escapeHtml(values[j]);
      html = html + '<option value="' + value + '">' + value + "</option>";
    }

    document.getElementById(filter.selectId).innerHTML = html;
  }
}


// All different values of one column, sorted A to Z (empty values left out)
function getUniqueValues(columnKey) {
  const values = [];

  for (let i = 0; i < allDemands.length; i++) {
    const value = String(allDemands[i][columnKey]).trim();
    if (value !== "" && values.includes(value) === false) {
      values.push(value);
    }
  }

  values.sort();
  return values;
}


// ============================================================
// 3. Which rows match the search box and the filters?
// ============================================================
function getFilteredDemands() {
  const searchText = document.getElementById("search-box").value.toLowerCase().trim();
  const result = [];

  for (let i = 0; i < allDemands.length; i++) {
    const row = allDemands[i];

    if (matchesFilters(row) && matchesSearch(row, searchText)) {
      result.push(row);
    }
  }

  return result;
}


// true if the row matches every chosen dropdown
function matchesFilters(row) {
  for (let i = 0; i < FILTERS.length; i++) {
    const filter = FILTERS[i];
    const chosenValue = document.getElementById(filter.selectId).value;

    if (chosenValue === "") {
      continue; // "All ..." is chosen, so this filter does nothing
    }

    const rowValue = String(row[filter.key]).trim();
    if (rowValue !== chosenValue) {
      return false;
    }
  }
  return true;
}


// true if the search text is found in any of the shown columns
function matchesSearch(row, searchText) {
  if (searchText === "") {
    return true;
  }

  for (let i = 0; i < COLUMNS.length; i++) {
    const value = String(row[COLUMNS[i].key]).toLowerCase();
    if (value.includes(searchText)) {
      return true;
    }
  }
  return false;
}


// ============================================================
// 4. Draw the page: KPI cards + table
// ============================================================
function showPage() {
  const rows = getFilteredDemands();

  showKpis(rows);
  showTable(rows);
}


function showKpis(rows) {
  let totalEffort = 0;
  let mustCount = 0;
  let packageCount = 0;

  for (let i = 0; i < rows.length; i++) {
    const row = rows[i];

    totalEffort = totalEffort + (Number(row[EFFORT_COLUMN]) || 0);

    const confirmation = String(row[CONFIRMATION_COLUMN]).toLowerCase().trim();
    if (confirmation === "must to have") {
      mustCount = mustCount + 1;
    }

    const deliveryMode = String(row[PACKAGE_COLUMN]).trim();
    if (deliveryMode === "MS/MT PKG") {
      packageCount = packageCount + 1;
    }
  }

  document.getElementById("kpi-items").textContent = rows.length;
  document.getElementById("kpi-effort").textContent = totalEffort.toLocaleString("en-IN");
  document.getElementById("kpi-must").textContent = mustCount;
  document.getElementById("kpi-package").textContent = packageCount;
}


function showTable(rows) {
  // Header row
  let headHtml = "<tr>";
  for (let i = 0; i < COLUMNS.length; i++) {
    headHtml = headHtml + "<th>" + COLUMNS[i].label + "</th>";
  }
  headHtml = headHtml + "</tr>";
  document.getElementById("table-head").innerHTML = headHtml;

  // One table row per item
  let bodyHtml = "";
  for (let i = 0; i < rows.length; i++) {
    bodyHtml = bodyHtml + "<tr>";
    for (let j = 0; j < COLUMNS.length; j++) {
      bodyHtml = bodyHtml + buildCell(rows[i], COLUMNS[j].key);
    }
    bodyHtml = bodyHtml + "</tr>";
  }

  if (rows.length === 0) {
    bodyHtml = '<tr><td colspan="' + COLUMNS.length + '">No items match these filters.</td></tr>';
  }

  document.getElementById("table-body").innerHTML = bodyHtml;
  document.getElementById("table-info").textContent =
    "Showing " + rows.length + " of " + allDemands.length + " items";
}


// One table cell. Some columns get a special look.
function buildCell(row, columnKey) {
  const value = row[columnKey];
  const text = escapeHtml(value);

  if (columnKey === "Requirement/CR/New Demand Item") {
    return '<td class="wide-cell">' + text + "</td>";
  }

  if (columnKey === EFFORT_COLUMN) {
    return '<td class="number-cell">' + text + "</td>";
  }

  if (columnKey === CONFIRMATION_COLUMN && text !== "") {
    return '<td><span class="badge ' + getBadgeClass(text) + '">' + text + "</span></td>";
  }

  return "<td>" + text + "</td>";
}


// Color of the Business Confirmation label
function getBadgeClass(value) {
  const lower = value.toLowerCase().trim();

  if (lower === "must to have") {
    return "badge-must";
  }
  if (lower === "good to have") {
    return "badge-good";
  }
  if (lower === "not required") {
    return "badge-not";
  }
  return "badge-other";
}


// ============================================================
// 5. Buttons and helpers
// ============================================================
function clearFilters() {
  document.getElementById("search-box").value = "";
  for (let i = 0; i < FILTERS.length; i++) {
    document.getElementById(FILTERS[i].selectId).value = "";
  }
  showPage();
}


// Makes text safe to put inside HTML (so "<" or "&" don't break the page)
function escapeHtml(value) {
  let text = String(value);
  text = text.replaceAll("&", "&amp;");
  text = text.replaceAll("<", "&lt;");
  text = text.replaceAll(">", "&gt;");
  text = text.replaceAll('"', "&quot;");
  return text;
}


// ---------- Start ----------
loadData();
