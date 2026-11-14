#!/usr/bin/env python3
"""Load every tool in tools/ into Open WebUI, creating it or updating it if it is already there.

Phase 1 step 6. The same thing can be done by hand: Workspace > Tools > +, then paste the file.

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
    existing = {t["id"] for t in call("/api/v1/tools/", token=token)}
    for path in sorted((ROOT / "tools").glob("*.py")):
        source = path.read_text()
        title = re.search(r"^title:\s*(.+)$", source, re.M).group(1).strip()
        description = re.search(r"^description:\s*(.+)$", source, re.M).group(1).strip()
        body = {"id": path.stem, "name": title, "content": source, "meta": {"description": description}}
        route = f"/api/v1/tools/id/{path.stem}/update" if path.stem in existing else "/api/v1/tools/create"
        try:
            call(route, token=token, body=body)
            print("updated" if path.stem in existing else "created", path.stem)
        except urllib.error.HTTPError as exc:
            print("FAILED", path.stem, exc.code, exc.read()[:400])


if __name__ == "__main__":
    main()
