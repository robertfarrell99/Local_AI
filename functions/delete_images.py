"""
title: Delete images
author: Local_AI spike
version: 0.1.0
description: Two buttons under each reply. One deletes every generated or uploaded image and the chats that contain them; the other deletes every chat as well. Both also empty ComfyUI's image folders and its job list.
"""

# Not part of the Phase 1 plan; added at Rob's request. Load it with scripts/install_tools.py.
# Needs ComfyUI's data folder shared with the container (see docker-compose.yml and scripts/start_comfyui.sh).
# Relies on Open WebUI internals (checked on 0.13.3), so recheck after an upgrade.

import asyncio
import json
import pathlib

import aiohttp
from open_webui.models.chats import Chats
from open_webui.models.files import Files
from open_webui.storage.provider import Storage
from pydantic import BaseModel, Field

KEEP = {"_output_images_will_be_put_here", "example.png"}  # files that ship with ComfyUI

OPTIONS = {
    "images": "Delete images and their chats",
    "everything": "Delete images and ALL chats",
}


def _is_image(file):
    return ((file.meta or {}).get("content_type") or "").startswith("image/")


class Action:
    class Valves(BaseModel):
        comfyui_url: str = Field(default="http://host.docker.internal:8188", description="Address of ComfyUI as seen from Open WebUI.")
        comfyui_folder: str = Field(default="/comfyui", description="ComfyUI's data folder (output, input, temp) as shared with the container.")
        dry_run: bool = Field(default=False, description="Count what would be deleted, but delete nothing.")

    def __init__(self):
        self.valves = self.Valves()
        self.actions = [{"id": key, "name": name} for key, name in OPTIONS.items()]

    def _folder_files(self):
        """Every file in ComfyUI's shared data folder. Returns (files, folders that are not shared)."""
        path = pathlib.Path(self.valves.comfyui_folder)
        if not path.is_dir():
            return [], [self.valves.comfyui_folder]
        return [p for p in path.rglob("*") if p.is_file() and p.name not in KEEP], []

    async def _comfyui_history(self, clear):
        """Number of jobs in ComfyUI's list (which holds prompts), clearing it first if asked. None if ComfyUI is not running."""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as session:
                if clear:
                    for path in ("/queue", "/history"):
                        await session.post(self.valves.comfyui_url + path, json={"clear": True})
                async with session.get(self.valves.comfyui_url + "/history") as response:
                    return len(await response.json())
        except Exception:
            return None

    async def _find(self, everything):
        """Image files in Open WebUI, and the chats to delete."""
        images = [f for f in await Files.get_files() if _is_image(f)]
        chats = await Chats.get_chats()
        if not everything:
            ids = [f.id for f in images]
            chats = [c for c in chats if any(i in json.dumps(c.chat) for i in ids)]
        return images, chats

    async def action(self, body: dict, __user__=None, __id__=None, __event_emitter__=None, __event_call__=None):
        async def tell(kind, text):
            if __event_emitter__:
                await __event_emitter__({"type": "notification", "data": {"type": kind, "content": text}})

        if (__user__ or {}).get("role") != "admin":
            return await tell("error", "Only an administrator can delete images.")
        if __id__ not in OPTIONS:
            return await tell("error", f"Unknown option: {__id__}")
        everything = __id__ == "everything"

        images, chats = await self._find(everything)
        folder_files, missing = self._folder_files()
        jobs = await self._comfyui_history(clear=False)
        found = (
            f"{len(images)} image(s) and {len(chats)} chat(s) in Open WebUI, {len(folder_files)} file(s) in ComfyUI's folders, "
            + ("ComfyUI not running" if jobs is None else f"{jobs} job(s) in ComfyUI's list")
        )
        if self.valves.dry_run:
            return await tell("info", f"Dry run, nothing deleted. Found: {found}.")

        question = "This deletes " + ("EVERY chat, " if everything else "every chat that contains an image, ") + "every image, and ComfyUI's saved images and job list."
        answer = await __event_call__({"type": "confirmation", "data": {"title": OPTIONS[__id__], "message": f"{question} Found: {found}. This cannot be undone."}})
        if answer is not True:  # False, or an error dict when the browser did not answer
            return await tell("info", "Nothing was deleted.")

        problems = []
        for chat in chats:
            if not await Chats.delete_chat_by_id(chat.id):
                problems.append(f"chat {chat.id}")
        for file in images:
            try:
                if await Files.delete_file_by_id(file.id) and file.path:
                    await asyncio.to_thread(Storage.delete_file, file.path)
            except Exception as exc:
                problems.append(f"image {file.id}: {exc!r}")
        for path in folder_files:
            try:
                path.unlink()
            except Exception as exc:
                problems.append(f"{path}: {exc!r}")
        jobs_left = await self._comfyui_history(clear=True)

        # Look again in every place, so the report says what is really left.
        images_left, chats_left = await self._find(everything)
        files_left, _ = self._folder_files()
        left = len(images_left) + len(chats_left) + len(files_left) + (jobs_left or 0)
        report = (
            f"Deleted {len(images)} image(s), {len(chats)} chat(s) and {len(folder_files)} ComfyUI file(s). "
            f"Left: {len(images_left)} image(s), {len(chats_left)} chat(s), {len(files_left)} ComfyUI file(s), "
            + ("ComfyUI not running, so its job list was not cleared (it clears when ComfyUI next starts)." if jobs_left is None else f"{jobs_left} job(s) in ComfyUI's list.")
        )
        if missing:
            report += f" NOT CHECKED, folder not shared with Open WebUI: {', '.join(missing)}."
        if problems:
            report += f" Could not delete: {'; '.join(problems[:5])}."
        clean = left == 0 and not missing and not problems
        await tell("success" if clean else "warning", report + (" Reload the page to refresh the chat list." if clean else ""))
