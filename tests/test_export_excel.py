"""The Excel tool: do Markdown tables become a proper workbook?"""
import pytest
from conftest import load
from openpyxl import load_workbook

excel = load("tools/export_excel.py")

TABLES = """## Actions

| Action | Owner | Due |
| --- | --- | --- |
| Deduplicate records | **Dan** | 2026-11-18 |
| Written confirmation | Mei | |

## Budget

| Item | Cost |
|:---|---:|
| Data migration | 18,000 |
| Training | 2500.50 |
"""


def build(content=TABLES):
    buffer, count = excel._build(content)
    return load_workbook(buffer), count


def test_one_sheet_per_table_named_after_its_heading():
    book, count = build()
    assert count == 2
    assert book.sheetnames == ["Actions", "Budget"]


def test_cells_are_kept_and_divider_rows_dropped():
    sheet = build()[0]["Actions"]
    assert [[c.value for c in row] for row in sheet.iter_rows()] == [
        ["Action", "Owner", "Due"],
        ["Deduplicate records", "Dan", "2026-11-18"],
        ["Written confirmation", "Mei", None],
    ]


def test_numbers_are_stored_as_numbers_and_dates_stay_text():
    book = build()[0]
    assert book["Budget"]["B2"].value == 18000 and isinstance(book["Budget"]["B2"].value, int)
    assert book["Budget"]["B3"].value == 2500.5
    assert book["Actions"]["C2"].value == "2026-11-18"


def test_header_row_is_bold_and_frozen():
    sheet = build()[0]["Actions"]
    assert all(cell.font.bold for cell in sheet[1])
    assert sheet.freeze_panes == "A2"


def test_sheet_names_are_made_valid_for_excel():
    long_heading = "# Actions / owners: a very long heading that goes past the limit\n\n| a |\n| - |\n| 1 |\n"
    name = build(long_heading)[0].sheetnames[0]
    assert len(name) <= 31 and not set(name) & set("[]:*?/\\")


def test_tables_with_no_heading_or_the_same_heading_get_distinct_names():
    book, _ = build("| a |\n| - |\n| 1 |\n\ntext\n\n| b |\n| - |\n| 2 |\n")
    assert book.sheetnames == ["Table 1", "Table 2"]
    book, _ = build("# Same\n\n| a |\n| - |\n| 1 |\n\ntext\n\n| b |\n| - |\n| 2 |\n")
    assert len(set(book.sheetnames)) == 2


def test_content_with_no_table_is_refused():
    with pytest.raises(ValueError):
        excel._build("Just some text, no table.")
