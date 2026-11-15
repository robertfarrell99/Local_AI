"""
title: Delete images
author: Local_AI spike
version: 0.2.0
description: Four buttons under each reply that delete chats and images - this chat, chats between two dates, every chat with an image, or everything - along with ComfyUI's saved copies.
"""

# Not part of the Phase 1 plan; added at Rob's request. Load it with scripts/install_tools.py.
# Needs ComfyUI's data folder shared with the container (see docker-compose.yml and scripts/start_comfyui.sh).
# Relies on Open WebUI internals (checked on 0.13.3), so recheck after an upgrade.

import asyncio
import datetime
import hashlib
import json
import pathlib
import re

import aiohttp
from open_webui.models.chats import Chats
from open_webui.models.files import Files
from open_webui.storage.provider import Storage
from pydantic import BaseModel, Field

KEEP = {"_output_images_will_be_put_here", "example.png"}  # files that ship with ComfyUI


def _icon(emoji):
    return f"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Ctext x='12' y='18' font-size='17' text-anchor='middle'%3E{emoji}%3C/text%3E%3C/svg%3E"


OPTIONS = {
    "this": ("Delete this chat and its images", _icon("🗑")),
    "dates": ("Delete chats and images between two dates", _icon("📅")),
    "images": ("Delete all images and their chats", _icon("🖼")),
    "everything": ("Delete all images and ALL chats", _icon("⚠")),
}


def _is_image(file):
    return ((file.meta or {}).get("content_type") or "").startswith("image/")


def _sha(path):
    try:
        return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()
    except Exception:
        return None


def _parse_dates(text):
    """'2026-11-01 to 2026-11-14' or '1/11/2026 - 14/11/2026' or one date. Returns (start, end) as timestamps, end inclusive of its whole day."""
    days = []
    for y, m, d in re.findall(r"(\d{4})-(\d{1,2})-(\d{1,2})", text or ""):
        days.append(datetime.datetime(int(y), int(m), int(d)))
    if not days:
        for d, m, y in re.findall(r"(\d{1,2})/(\d{1,2})/(\d{4})", text or ""):
            days.append(datetime.datetime(int(y), int(m), int(d)))
    if not days or len(days) > 2:
        raise ValueError("no date found")
    start, end = min(days), max(days) + datetime.timedelta(days=1)
    return start.timestamp(), end.timestamp(), f"{start:%d %B %Y} to {max(days):%d %B %Y}"


class Action:
    class Valves(BaseModel):
        comfyui_url: str = Field(default="http://host.docker.internal:8188", description="Address of ComfyUI as seen from Open WebUI.")
        comfyui_folder: str = Field(default="/comfyui", description="ComfyUI's data folder (output, input, temp) as shared with the container.")
        dry_run: bool = Field(default=False, description="Count what would be deleted, but delete nothing.")

    def __init__(self):
        self.valves = self.Valves()
        self.actions = [{"id": key, "name": name, "icon_url": icon} for key, (name, icon) in OPTIONS.items()]

    def _folder_files(self):
        """Every file in ComfyUI's shared data folder, or None if the folder is not shared."""
        path = pathlib.Path(self.valves.comfyui_folder)
        if not path.is_dir():
            return None
        return [p for p in path.rglob("*") if p.is_file() and p.name not in KEEP]

    async def _comfyui(self, method, path, body=None):
        """Call ComfyUI. Returns the reply, or None if ComfyUI is not running."""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as session:
                async with session.request(method, self.valves.comfyui_url + path, json=body) as response:
                    return await response.json() if method == "GET" else True
        except Exception:
            return None

    async def _plan(self, option, chat_id, start=None, end=None):
        """Work out what the chosen option covers: chats, Open WebUI images, ComfyUI files and ComfyUI jobs."""
        all_images = [f for f in await Files.get_files() if _is_image(f)]
        all_chats = await Chats.get_chats()
        folder = self._folder_files()
        dumps = {c.id: json.dumps(c.chat) for c in all_chats}

        if option == "everything":
            chats, images = all_chats, all_images
        elif option == "images":
            images = all_images
            chats = [c for c in all_chats if any(f.id in dumps[c.id] for f in images)]
        else:
            if option == "this":
                chats = [c for c in all_chats if c.id == chat_id]
                images = []
            else:  # dates
                chats = [c for c in all_chats if start <= c.created_at < end]
                images = [f for f in all_images if start <= (f.created_at or 0) < end]
            text = " ".join(dumps[c.id] for c in chats)
            images += [f for f in all_images if f.id in text and f not in images]

        if option in ("everything", "images"):
            files = folder or []
        else:
            # ComfyUI keeps its own copy of each picture; find it by matching the file's contents exactly.
            wanted = {_sha(f.path) for f in images if f.path} - {None}
            files = [p for p in (folder or []) if _sha(p) in wanted]
            if option == "dates":
                files += [p for p in (folder or []) if start <= p.stat().st_mtime < end and p not in files]

        history = await self._comfyui("GET", "/history")
        if history is None:
            jobs = None
        elif option in ("everything", "images"):
            jobs = list(history)
        else:
            names = {p.name for p in files}
            jobs = [
                job_id
                for job_id, job in history.items()
                if any(image.get("filename") in names for output in (job.get("outputs") or {}).values() for image in output.get("images", []))
            ]
        return {"chats": chats, "images": images, "files": files, "jobs": jobs, "folder_shared": folder is not None}

    @staticmethod
    def _describe(plan):
        jobs = "ComfyUI not running" if plan["jobs"] is None else f"{len(plan['jobs'])} job(s) in ComfyUI's list"
        return f"{len(plan['chats'])} chat(s) and {len(plan['images'])} image(s) in Open WebUI, {len(plan['files'])} file(s) in ComfyUI's folder, {jobs}"

    async def action(self, body: dict, __user__=None, __id__=None, __event_emitter__=None, __event_call__=None):
        async def tell(kind, text):
            if __event_emitter__:
                await __event_emitter__({"type": "notification", "data": {"type": kind, "content": text}})

        if (__user__ or {}).get("role") != "admin":
            return await tell("error", "Only an administrator can delete chats and images.")
        if __id__ not in OPTIONS:
            return await tell("error", f"Unknown option: {__id__}")
        title = OPTIONS[__id__][0]

        start = end = None
        scope = {"this": "this chat and its images", "images": "every image and every chat that contains one", "everything": "EVERY chat and every image"}.get(__id__)
        if __id__ == "dates":
            typed = await __event_call__(
                {"type": "input", "data": {"title": title, "message": "Type the first and last day, for example 2026-11-01 to 2026-11-14. One date means that day only. Nothing is deleted until you confirm on the next screen.", "placeholder": "2026-11-01 to 2026-11-14"}}
            )
            if not isinstance(typed, str) or not typed.strip():
                return await tell("info", "Nothing was deleted.")
            try:
                start, end, label = _parse_dates(typed)
            except ValueError:
                return await tell("error", f"Could not read dates from '{typed}'. Nothing was deleted.")
            scope = f"every chat started and every image made from {label}"

        plan = await self._plan(__id__, body.get("chat_id"), start, end)
        found = self._describe(plan)
        if self.valves.dry_run:
            titles = ", ".join(f"'{c.title}'" for c in plan["chats"][:8]) or "none"
            return await tell("info", f"Dry run, nothing deleted. Would delete {scope}. Found: {found}. Chats: {titles}.")
        if not (plan["chats"] or plan["images"] or plan["files"] or plan["jobs"]):
            return await tell("info", f"Nothing found to delete for {scope}.")

        answer = await __event_call__(
            {"type": "confirmation", "data": {"title": title, "message": f"This deletes {scope}, with ComfyUI's saved copies. Found: {found}. This cannot be undone."}}
        )
        if answer is not True:  # False, or an error dict when the browser did not answer
            return await tell("info", "Nothing was deleted.")

        problems = []
        for chat in plan["chats"]:
            if not await Chats.delete_chat_by_id(chat.id):
                problems.append(f"chat {chat.id}")
        for file in plan["images"]:
            try:
                if await Files.delete_file_by_id(file.id) and file.path:
                    await asyncio.to_thread(Storage.delete_file, file.path)
            except Exception as exc:
                problems.append(f"image {file.id}: {exc!r}")
        for path in plan["files"]:
            try:
                path.unlink()
            except Exception as exc:
                problems.append(f"{path}: {exc!r}")
        if plan["jobs"]:
            if __id__ in ("everything", "images"):
                await self._comfyui("POST", "/queue", {"clear": True})
                await self._comfyui("POST", "/history", {"clear": True})
            else:
                await self._comfyui("POST", "/history", {"delete": plan["jobs"]})

        # Look again, so the report says what is really left.
        chat_ids = {c.id for c in await Chats.get_chats()}
        file_ids = {f.id for f in await Files.get_files()}
        history = await self._comfyui("GET", "/history")
        left = {
            "chat(s)": sum(1 for c in plan["chats"] if c.id in chat_ids),
            "image(s)": sum(1 for f in plan["images"] if f.id in file_ids),
            "ComfyUI file(s)": sum(1 for p in plan["files"] if p.exists()),
            "ComfyUI job(s)": sum(1 for j in plan["jobs"] or [] if j in (history or {})),
        }
        report = f"Deleted {scope}: {found}. Left behind: " + ", ".join(f"{n} {what}" for what, n in left.items()) + "."
        if plan["jobs"] is None:
            report += " ComfyUI was not running, so its job list was not checked (it clears when ComfyUI next starts)."
        if not plan["folder_shared"]:
            report += f" NOT CHECKED: ComfyUI's folder {self.valves.comfyui_folder} is not shared with Open WebUI."
        if problems:
            report += f" Could not delete: {'; '.join(problems[:5])}."
        clean = not any(left.values()) and plan["folder_shared"] and not problems
        await tell("success" if clean else "warning", report + (" Reload the page to refresh the chat list." if clean else ""))
