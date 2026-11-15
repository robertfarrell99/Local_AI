"""The Delete images buttons: does each button pick exactly the right things, and delete only after a yes?

Open WebUI and ComfyUI are replaced by stand-ins holding three chats, three images and four files.
These tests cannot show that deletion works against a real Open WebUI; that needs a person to press the button.
"""
import asyncio
import datetime
import os
import types

import pytest
from conftest import load

mod = load("functions/delete_images.py")


def day(n, hour=12):
    return datetime.datetime(2026, 11, n, hour).timestamp()


class World:
    """A pretend Open WebUI and ComfyUI.

    Chat c1 (1 Nov) shows image img1. Chat c2 (2 Nov) has no image. Chat c3 (3 Nov) shows img2.
    Image img3 (2 Nov) is in no chat. ComfyUI holds a copy of img1 (a.png) and img2 (b.png),
    plus other.png made on 2 Nov, plus one file that ships with ComfyUI and must never be deleted.
    """

    def __init__(self, tmp_path, monkeypatch, comfyui_running=True, folder_shared=True):
        uploads, comfy = tmp_path / "uploads", tmp_path / "comfyui"
        uploads.mkdir()
        (comfy / "output").mkdir(parents=True)
        self.comfy = comfy

        def image(name, content, created):
            path = uploads / name
            path.write_bytes(content)
            return types.SimpleNamespace(id=name, meta={"content_type": "image/png"}, path=str(path), created_at=created)

        self.files = [
            image("img1", b"picture one", day(1)),
            image("img2", b"picture two", day(3)),
            image("img3", b"picture three", day(2)),
            types.SimpleNamespace(id="doc1", meta={"content_type": "text/markdown"}, path=None, created_at=day(1)),
        ]

        def chat(id, created, text):
            return types.SimpleNamespace(id=id, title=id, chat={"messages": text}, created_at=created)

        self.chats = [chat("c1", day(1), "see /api/v1/files/img1/content"), chat("c2", day(2), "just words"), chat("c3", day(3), "see img2")]

        for name, content, made in (("a.png", b"picture one", 1), ("b.png", b"picture two", 3), ("other.png", b"made in ComfyUI", 2)):
            (comfy / "output" / name).write_bytes(content)
            os.utime(comfy / "output" / name, (day(made), day(made)))
        (comfy / "output" / "_output_images_will_be_put_here").write_bytes(b"")

        self.history = {job: {"outputs": {"10": {"images": [{"filename": name}]}}} for job, name in (("job1", "a.png"), ("job2", "b.png"), ("job3", "other.png"))}
        self.comfyui_running = comfyui_running

        async def get_files():
            return list(self.files)

        async def get_chats():
            return list(self.chats)

        async def delete_chat(id):
            self.chats = [c for c in self.chats if c.id != id]
            return True

        async def delete_file(id):
            self.files = [f for f in self.files if f.id != id]
            return True

        monkeypatch.setattr(mod, "Files", types.SimpleNamespace(get_files=get_files, delete_file_by_id=delete_file))
        monkeypatch.setattr(mod, "Chats", types.SimpleNamespace(get_chats=get_chats, delete_chat_by_id=delete_chat))
        monkeypatch.setattr(mod, "Storage", types.SimpleNamespace(delete_file=lambda path: os.remove(path)))

        self.action = mod.Action()
        self.action.valves.comfyui_folder = str(comfy if folder_shared else tmp_path / "not-there")

        async def comfyui(method, path, body=None):
            if not self.comfyui_running:
                return None
            if method == "GET":
                return dict(self.history)
            if path == "/history" and body.get("clear"):
                self.history = {}
            for job in (body or {}).get("delete", []):
                self.history.pop(job, None)
            return True

        self.action._comfyui = comfyui
        self.messages, self.questions = [], []

    def plan(self, option, chat_id=None, start=None, end=None):
        plan = asyncio.run(self.action._plan(option, chat_id, start, end))
        return {
            "chats": sorted(c.id for c in plan["chats"]),
            "images": sorted(f.id for f in plan["images"]),
            "files": sorted(p.name for p in plan["files"]),
            "jobs": None if plan["jobs"] is None else sorted(plan["jobs"]),
        }

    def press(self, option, chat_id="c1", answers=(), role="admin"):
        """Press a button. `answers` are what the person replies to each box that pops up."""
        answers = list(answers)

        async def emit(event):
            self.messages.append((event["data"]["type"], event["data"]["content"]))

        async def ask(event):
            self.questions.append(event["type"])
            return answers.pop(0)

        asyncio.run(self.action.action({"chat_id": chat_id}, __user__={"role": role}, __id__=option, __event_emitter__=emit, __event_call__=ask))
        return self.messages[-1]

    def left(self):
        return {
            "chats": sorted(c.id for c in self.chats),
            "files": sorted(f.id for f in self.files),
            "comfyui": sorted(p.name for p in (self.comfy / "output").iterdir()),
            "jobs": sorted(self.history),
        }


@pytest.fixture
def world(tmp_path, monkeypatch):
    return World(tmp_path, monkeypatch)


EVERYTHING = {
    "chats": ["c1", "c2", "c3"],
    "files": ["doc1", "img1", "img2", "img3"],
    "comfyui": ["_output_images_will_be_put_here", "a.png", "b.png", "other.png"],
    "jobs": ["job1", "job2", "job3"],
}


# --- reading the dates a person types -------------------------------------------------------------


def test_date_range_covers_the_whole_last_day():
    start, end, label = mod._parse_dates("2026-11-01 to 2026-11-14")
    assert start == datetime.datetime(2026, 11, 1).timestamp()
    assert end == datetime.datetime(2026, 11, 15).timestamp()
    assert label == "01 November 2026 to 14 November 2026"


def test_one_date_means_that_day_only():
    start, end, _ = mod._parse_dates("2026-11-14")
    assert end - start == 24 * 3600


def test_british_dates_and_reversed_order_are_understood():
    assert mod._parse_dates("14/11/2026 - 1/11/2026")[:2] == mod._parse_dates("2026-11-01 to 2026-11-14")[:2]


@pytest.mark.parametrize("typed", ["", "last week", "2026-11-01, 2026-11-02, 2026-11-03", None])
def test_unreadable_dates_are_refused(typed):
    with pytest.raises(ValueError):
        mod._parse_dates(typed)


# --- what each button selects ---------------------------------------------------------------------


def test_this_chat_selects_only_that_chat_its_image_and_the_matching_comfyui_copy(world):
    assert world.plan("this", chat_id="c1") == {"chats": ["c1"], "images": ["img1"], "files": ["a.png"], "jobs": ["job1"]}


def test_this_chat_with_no_image_selects_just_the_chat(world):
    assert world.plan("this", chat_id="c2") == {"chats": ["c2"], "images": [], "files": [], "jobs": []}


def test_between_dates_selects_chats_images_and_comfyui_files_from_those_days(world):
    start, end, _ = mod._parse_dates("2026-11-02")
    assert world.plan("dates", start=start, end=end) == {"chats": ["c2"], "images": ["img3"], "files": ["other.png"], "jobs": ["job3"]}


def test_between_dates_also_takes_images_shown_in_the_selected_chats(world):
    start, end, _ = mod._parse_dates("2026-11-01")
    assert world.plan("dates", start=start, end=end) == {"chats": ["c1"], "images": ["img1"], "files": ["a.png"], "jobs": ["job1"]}


def test_all_images_selects_every_image_but_leaves_the_chat_without_one(world):
    assert world.plan("images") == {"chats": ["c1", "c3"], "images": ["img1", "img2", "img3"], "files": ["a.png", "b.png", "other.png"], "jobs": ["job1", "job2", "job3"]}


def test_everything_selects_every_chat(world):
    assert world.plan("everything")["chats"] == ["c1", "c2", "c3"]


def test_documents_that_are_not_images_are_never_selected(world):
    assert "doc1" not in world.plan("everything")["images"]


def test_comfyui_not_running_is_reported_not_guessed(tmp_path, monkeypatch):
    assert World(tmp_path, monkeypatch, comfyui_running=False).plan("images")["jobs"] is None


# --- pressing the buttons -------------------------------------------------------------------------


def test_only_an_administrator_can_delete(world):
    kind, _ = world.press("everything", answers=[True], role="user")
    assert kind == "error" and world.left() == EVERYTHING


def test_dry_run_deletes_nothing_and_asks_nothing(world):
    world.action.valves.dry_run = True
    kind, text = world.press("everything")
    assert kind == "info" and text.startswith("Dry run, nothing deleted")
    assert world.questions == [] and world.left() == EVERYTHING


@pytest.mark.parametrize("answer", [False, None, {"error": "browser did not answer"}])
def test_anything_other_than_a_clear_yes_deletes_nothing(world, answer):
    kind, text = world.press("everything", answers=[answer])
    assert text == "Nothing was deleted." and world.left() == EVERYTHING


def test_unreadable_dates_delete_nothing(world):
    kind, _ = world.press("dates", answers=["sometime last week"])
    assert kind == "error" and world.questions == ["input"] and world.left() == EVERYTHING


def test_confirming_this_chat_deletes_only_that_chat_and_its_copies(world):
    kind, _ = world.press("this", chat_id="c1", answers=[True])
    assert kind == "success"
    assert world.left() == {
        "chats": ["c2", "c3"],
        "files": ["doc1", "img2", "img3"],
        "comfyui": ["_output_images_will_be_put_here", "b.png", "other.png"],
        "jobs": ["job2", "job3"],
    }


def test_confirming_between_dates_asks_for_dates_then_a_yes(world):
    kind, _ = world.press("dates", answers=["2026-11-02 to 2026-11-03", True])
    assert kind == "success" and world.questions == ["input", "confirmation"]
    assert world.left() == {"chats": ["c1"], "files": ["doc1", "img1"], "comfyui": ["_output_images_will_be_put_here", "a.png"], "jobs": ["job1"]}


def test_confirming_everything_leaves_only_documents_and_comfyui_own_file(world):
    kind, _ = world.press("everything", answers=[True])
    assert kind == "success"
    assert world.left() == {"chats": [], "files": ["doc1"], "comfyui": ["_output_images_will_be_put_here"], "jobs": []}


def test_a_folder_that_is_not_shared_is_flagged_as_a_warning(tmp_path, monkeypatch):
    world = World(tmp_path, monkeypatch, folder_shared=False)
    kind, text = world.press("everything", answers=[True])
    assert kind == "warning" and "NOT CHECKED" in text
    assert world.left()["comfyui"] == EVERYTHING["comfyui"]


def test_something_that_will_not_delete_is_reported(world, monkeypatch):
    async def refuse(id):
        return False

    monkeypatch.setattr(mod.Chats, "delete_chat_by_id", refuse)
    kind, text = world.press("this", chat_id="c1", answers=[True])
    assert kind == "warning" and "Could not delete: chat c1" in text and "1 chat(s)" in text
