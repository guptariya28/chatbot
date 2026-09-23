def format_location(metadata: dict) -> str:
    """Helper function to format source location for the frontend UI."""
    file_type = metadata.get("file_type", "").lower()
    if file_type in ["xlsx", "xls"]:
        row = metadata.get("row_index", "")
        sheet = metadata.get("sheet_name", "Sheet1")
        return f"Sheet: {sheet}, Row: {row}" if row else f"Sheet: {sheet}"
    elif file_type == "pdf":
        page = metadata.get("page", 0)
        return f"Page: {page + 1}"
    else:
        return "Document Section"