#!/usr/bin/env python3
"""Load every tool in tools/ and every function in functions/ into Open WebUI, creating or updating each.

Phase 1 step 6. The same thing can be done by hand: Workspace > Tools > +, or Admin Panel > Functions > +,
then paste the file. Functions are also switched on, and switched on for every model.

Usage:  python3 scripts/install_tools.py
"""
import json
import pathlib
import re
import urllib.error
import urllib.request

BASE = "http://localhost:3000"
ROOT = pathlib.Path(__file__).resolve().parent.parent


def call(path, token=None, body=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    data = json.dumps(body).encode() if body is not None else None
    return json.load(urllib.request.urlopen(urllib.request.Request(BASE + path, data=data, headers=headers), timeout=300))


def main():
    token = call("/api/v1/auths/signin", body={"email": "", "password": ""})["token"]
    for kind in ("tools", "functions"):
        existing = {t["id"]: t for t in call(f"/api/v1/{kind}/", token=token)}
        for path in sorted((ROOT / kind).glob("*.py")):
            source = path.read_text()
            title = re.search(r"^title:\s*(.+)$", source, re.M).group(1).strip()
            description = re.search(r"^description:\s*(.+)$", source, re.M).group(1).strip()
            body = {"id": path.stem, "name": title, "content": source, "meta": {"description": description}}
            route = f"/api/v1/{kind}/id/{path.stem}/update" if path.stem in existing else f"/api/v1/{kind}/create"
            try:
                saved = call(route, token=token, body=body)
                print("updated" if path.stem in existing else "created", kind, path.stem)
                if kind == "functions":  # a function does nothing until it is active, and shows nowhere until it is global
                    for switch, field in (("toggle", "is_active"), ("toggle/global", "is_global")):
                        if not saved.get(field):
                            saved = call(f"/api/v1/functions/id/{path.stem}/{switch}", token=token, body={})
                    print("  active:", saved.get("is_active"), " on every model:", saved.get("is_global"))
            except urllib.error.HTTPError as exc:
                print("FAILED", path.stem, exc.code, exc.read()[:400])


if __name__ == "__main__":
    main()
