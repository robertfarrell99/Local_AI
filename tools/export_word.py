"""
title: Export to Word
author: Local_AI spike
version: 0.1.0
description: Turns text the model has written (minutes, a summary, a report) into a Word .docx file the user can download.
"""

# Phase 1 step 6. Paste this file into Open WebUI under Workspace > Tools, or load it with the API.
# python-docx is already part of the Open WebUI image (checked on 0.13.3), so no "requirements:" line is needed.

import io
import re

from docx import Document
from fastapi import UploadFile
from open_webui.models.users import Users
from open_webui.routers.files import upload_file_handler

DOCX_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def _add_text(paragraph, text):
    """Add text to a paragraph, turning **bold** into real bold."""
    for i, part in enumerate(re.split(r"\*\*(.+?)\*\*", text)):
        if part:
            paragraph.add_run(part).bold = i % 2 == 1


def _cells(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def _build(title, content):
    """Convert simple Markdown (headings, bullets, numbered lists, tables, bold) into a Word document."""
    doc = Document()
    doc.add_heading(title, level=0)
    lines = content.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        stripped = line.strip()
        if not stripped or re.fullmatch(r"[-*_]{3,}", stripped):
            i += 1
        elif stripped.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                if not re.fullmatch(r"[|\s:-]+", lines[i].strip()):  # skip the |---|---| divider row
                    rows.append(_cells(lines[i]))
                i += 1
            width = max(len(r) for r in rows)
            table = doc.add_table(rows=len(rows), cols=width)
            table.style = "Table Grid"
            for r, row in enumerate(rows):
                for c, value in enumerate(row):
                    paragraph = table.cell(r, c).paragraphs[0]
                    _add_text(paragraph, value)
                    if r == 0:
                        for run in paragraph.runs:
                            run.bold = True
            doc.add_paragraph()
        elif stripped.startswith("#"):
            level = min(len(stripped) - len(stripped.lstrip("#")), 4)
            doc.add_heading(stripped.lstrip("#").strip().replace("**", ""), level=level)
            i += 1
        elif re.match(r"[-*•]\s+", stripped):
            _add_text(doc.add_paragraph(style="List Bullet"), re.sub(r"^[-*•]\s+", "", stripped))
            i += 1
        elif re.match(r"\d+[.)]\s+", stripped):
            _add_text(doc.add_paragraph(style="List Number"), re.sub(r"^\d+[.)]\s+", "", stripped))
            i += 1
        else:
            _add_text(doc.add_paragraph(), stripped)
            i += 1
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer


class Tools:
    def __init__(self):
        pass

    async def export_to_word(
        self,
        title: str,
        content: str,
        __request__=None,
        __user__: dict = None,
        __event_emitter__=None,
    ) -> str:
        """
        Create a Word (.docx) document and give the user a download link. Use this when the user asks for a Word document or a .docx file.

        :param title: Document title, also used as the file name. For example "Steering group minutes 12 March".
        :param content: The full text of the document in Markdown. Headings (#), bullet lists, numbered lists, tables and **bold** are kept.
        """
        try:
            buffer = _build(title, content)
            name = (re.sub(r"[^A-Za-z0-9 _-]", "", title).strip() or "document")[:80] + ".docx"
            user = await Users.get_user_by_id(__user__["id"])
            # Save through Open WebUI's own file store so the download is tied to this user.
            saved = await upload_file_handler(
                __request__,
                file=UploadFile(file=buffer, filename=name, headers={"content-type": DOCX_TYPE}),
                metadata=None,
                process=False,  # do not index the file for search
                user=user,
            )
        except Exception as exc:
            return f"The Word document could not be created: {exc!r}"
        url = f"/api/v1/files/{saved.id}/content"
        if __event_emitter__:
            await __event_emitter__({"type": "files", "data": {"files": [{"type": "file", "name": name, "url": url}]}})
        return f"Word document created. Give the user this download link exactly as written: [{name}]({url})"
