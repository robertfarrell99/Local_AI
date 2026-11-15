"""The Word tool: does Markdown from a model become a proper Word document?"""
from conftest import load
from docx import Document

word = load("tools/export_word.py")

MINUTES = """# Decisions

- Go-live moves to **18 November**.
- Budget stays at 18,000.

## Next steps

1. Dan to deduplicate records.
2. Mei to confirm in writing.

---

| Action | Owner | Due |
| --- | --- | --- |
| Deduplicate records | **Dan** | 18 November |
| Written confirmation | Mei | |

Closing remark.
"""


def build():
    return Document(word._build("Steering group", MINUTES))


def test_title_and_headings_use_word_heading_styles():
    styles = [(p.style.name, p.text) for p in build().paragraphs if p.style.name.startswith(("Title", "Heading"))]
    assert styles == [("Title", "Steering group"), ("Heading 1", "Decisions"), ("Heading 2", "Next steps")]


def test_bullets_and_numbered_lists_become_real_lists():
    doc = build()
    assert [p.text for p in doc.paragraphs if p.style.name == "List Bullet"] == ["Go-live moves to 18 November.", "Budget stays at 18,000."]
    assert [p.text for p in doc.paragraphs if p.style.name == "List Number"] == ["Dan to deduplicate records.", "Mei to confirm in writing."]


def test_bold_markers_become_bold_text_not_asterisks():
    bullet = next(p for p in build().paragraphs if p.text.startswith("Go-live"))
    assert [(run.text, bool(run.bold)) for run in bullet.runs] == [("Go-live moves to ", False), ("18 November", True), (".", False)]


def test_table_keeps_every_cell_and_drops_the_divider_row():
    table = build().tables[0]
    rows = [[cell.text for cell in row.cells] for row in table.rows]
    assert rows == [["Action", "Owner", "Due"], ["Deduplicate records", "Dan", "18 November"], ["Written confirmation", "Mei", ""]]
    assert all(run.bold for cell in table.rows[0].cells for run in cell.paragraphs[0].runs)


def test_rule_lines_are_dropped_and_plain_text_is_kept():
    texts = [p.text for p in build().paragraphs]
    assert "---" not in texts
    assert "Closing remark." in texts


def test_uneven_table_rows_do_not_crash():
    doc = Document(word._build("T", "| a | b | c |\n| --- | --- | --- |\n| 1 | 2 |\n"))
    assert len(doc.tables[0].columns) == 3
