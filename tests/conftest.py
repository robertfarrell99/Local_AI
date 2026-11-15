"""Shared test setup.

The tools and the delete function are written to run inside Open WebUI, so they import Open WebUI's own
code. That code is not available on GitHub's test machines, so stand-ins are put in its place here.
The tests therefore check our logic (what gets built, what gets selected), not Open WebUI itself.
"""
import importlib.util
import pathlib
import sys
import types

ROOT = pathlib.Path(__file__).resolve().parent.parent


def _stand_in(name, **contents):
    module = types.ModuleType(name)
    for key, value in contents.items():
        setattr(module, key, value)
    sys.modules[name] = module
    return module


class _Anything:
    """Placeholder for an Open WebUI object. Tests replace the parts they need."""


_stand_in("open_webui")
_stand_in("open_webui.models")
_stand_in("open_webui.models.users", Users=_Anything())
_stand_in("open_webui.models.chats", Chats=_Anything())
_stand_in("open_webui.models.files", Files=_Anything())
_stand_in("open_webui.routers")
_stand_in("open_webui.routers.files", upload_file_handler=None)
_stand_in("open_webui.storage")
_stand_in("open_webui.storage.provider", Storage=_Anything())
if "fastapi" not in sys.modules:
    _stand_in("fastapi", UploadFile=_Anything)


def load(relative_path):
    """Load one of our files (tools/..., functions/...) as a module."""
    path = ROOT / relative_path
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
