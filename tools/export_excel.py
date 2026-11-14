"""
title: Export to Excel
author: Local_AI spike
version: 0.1.0
description: Turns one or more tables the model has written (an actions list, a comparison) into an Excel .xlsx file the user can download.
"""

# Phase 1 step 6. Paste this file into Open WebUI under Workspace > Tools, or load it with the API.
# openpyxl is already part of the Open WebUI image (checked on 0.13.3), so no "requirements:" line is needed.

import io
import re

from fastapi import UploadFile
from open_webui.models.users import Users
from open_webui.routers.files import upload_file_handler
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font

XLSX_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _value(text):
    """Plain numbers become real numbers so Excel can add them up. Everything else, dates included, stays as text."""
    text = text.replace("**", "").strip()
    if re.fullmatch(r"-?\d{1,3}(,\d{3})+(\.\d+)?|-?\d+(\.\d+)?", text):
        number = float(text.replace(",", ""))
        return int(number) if number.is_integer() else number
    return text


def _tables(content):
    """Find each Markdown table. Returns a list of (name, rows); the name is the nearest heading above the table."""
    found, heading, rows = [], "", []
    for line in content.splitlines() + [""]:
        stripped = line.strip()
        if stripped.startswith("|"):
            if not re.fullmatch(r"[|\s:-]+", stripped):  # skip the |---|---| divider row
                rows.append([_value(c) for c in stripped.strip("|").split("|")])
            continue
        if rows:
            found.append((heading, rows))
            rows = []
        if stripped.startswith("#"):
            heading = stripped.lstrip("#").strip().replace("**", "")
    return found


def _build(content):
    tables = _tables(content)
    if not tables:
        raise ValueError("no Markdown table found in the content")
    book = Workbook()
    book.remove(book.active)
    for number, (heading, rows) in enumerate(tables, start=1):
        # Excel sheet names: 31 characters at most, and none of []:*?/\
        name = re.sub(r"[\[\]:*?/\\]", "", heading).strip()[:31] or f"Table {number}"
        if name in book.sheetnames:
            name = f"{name[:27]} ({number})"
        sheet = book.create_sheet(name)
        for row in rows:
            sheet.append(row)
        for cell in sheet[1]:
            cell.font = Font(bold=True)
        sheet.freeze_panes = "A2"
        for column in sheet.columns:
            longest = max(len(str(cell.value or "")) for cell in column)
            sheet.column_dimensions[column[0].column_letter].width = min(max(longest + 2, 8), 60)
            for cell in column:
                cell.alignment = Alignment(wrap_text=True, vertical="top")
    buffer = io.BytesIO()
    book.save(buffer)
    buffer.seek(0)
    return buffer, len(tables)


class Tools:
    def __init__(self):
        pass

    async def export_to_excel(
        self,
        title: str,
        content: str,
        __request__=None,
        __user__: dict = None,
        __event_emitter__=None,
    ) -> str:
        """
        Create an Excel (.xlsx) workbook from tables and give the user a download link. Use this when the user asks for an Excel file, a spreadsheet or an .xlsx file.

        :param title: Used as the file name. For example "Steering group actions 3 November".
        :param content: One or more Markdown tables (rows starting with |). Each table becomes its own sheet, named after the Markdown heading (#) above it. The first row of each table is the header.
        """
        try:
            buffer, count = _build(content)
            name = (re.sub(r"[^A-Za-z0-9 _-]", "", title).strip() or "workbook")[:80] + ".xlsx"
            user = await Users.get_user_by_id(__user__["id"])
            # Save through Open WebUI's own file store so the download is tied to this user.
            saved = await upload_file_handler(
                __request__,
                file=UploadFile(file=buffer, filename=name, headers={"content-type": XLSX_TYPE}),
                metadata=None,
                process=False,  # do not index the file for search
                user=user,
            )
        except Exception as exc:
            return f"The Excel file could not be created: {exc!r}"
        url = f"/api/v1/files/{saved.id}/content"
        if __event_emitter__:
            await __event_emitter__({"type": "files", "data": {"files": [{"type": "file", "name": name, "url": url}]}})
        return f"Excel workbook created with {count} sheet(s). Give the user this download link exactly as written: [{name}]({url})"
