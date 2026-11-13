#!/usr/bin/env python3
"""Load the invented documents into an Open WebUI knowledge base and ask each model the same questions.

Phase 1 step 5. Goes through Open WebUI's API so its own document search (retrieval) is what gets tested.

Usage:  python3 scripts/run_knowledge.py MODEL [MODEL ...]
Writes: output/knowledge/<model>__<question id>.md and output/knowledge/results.csv (appended)
"""
import csv
import json
import pathlib
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid

BASE = "http://localhost:3000"
ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCS = ROOT / "knowledge" / "invented"
OUT = ROOT / "output" / "knowledge"
KB_NAME = "Meridian Programme (invented test documents)"


def call(path, token=None, body=None, method=None, timeout=1200):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    return json.load(urllib.request.urlopen(req, timeout=timeout))


def upload(path, token):
    """Upload one file as a multipart form, which is how the browser does it."""
    boundary = uuid.uuid4().hex
    body = (f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{path.name}"\r\n'
            f"Content-Type: text/markdown\r\n\r\n").encode() + path.read_bytes() + f"\r\n--{boundary}--\r\n".encode()
    req = urllib.request.Request(BASE + "/api/v1/files/", data=body, headers={
        "Authorization": "Bearer " + token, "Content-Type": f"multipart/form-data; boundary={boundary}"})
    return json.load(urllib.request.urlopen(req, timeout=600))


def knowledge_base(token):
    """Return the id of the test knowledge base, creating and filling it the first time."""
    existing = call("/api/v1/knowledge/", token=token)
    items = existing.get("items", existing) if isinstance(existing, dict) else existing
    for kb in items:
        if kb.get("name") == KB_NAME:
            return kb["id"]
    kb = call("/api/v1/knowledge/create", token=token,
              body={"name": KB_NAME, "description": "Invented documents for the Phase 1 step 5 test."})
    for doc in sorted(DOCS.glob("0*.md")):  # the numbered documents only, never the answer key
        file_id = upload(doc, token)["id"]
        call(f"/api/v1/knowledge/{kb['id']}/file/add", token=token, body={"file_id": file_id})
        print("added", doc.name, flush=True)
    return kb["id"]


def main(models):
    OUT.mkdir(parents=True, exist_ok=True)
    token = call("/api/v1/auths/signin", body={"email": "", "password": ""})["token"]
    kb_id = knowledge_base(token)
    questions = json.loads((DOCS / "questions.json").read_text())
    results = OUT / "results.csv"
    new_file = not results.exists()
    with results.open("a", newline="") as fh:
        writer = csv.writer(fh)
        if new_file:
            writer.writerow(["date", "model", "question", "wall_seconds", "input_tokens",
                             "output_tokens", "sources_cited", "error"])
        for model in models:
            for q in questions:
                body = {"model": model, "stream": False,
                        "messages": [{"role": "user", "content": q["question"]}],
                        "files": [{"type": "collection", "id": kb_id}]}
                start = time.time()
                try:
                    reply, error = call("/api/chat/completions", token=token, body=body), ""
                except urllib.error.HTTPError as exc:
                    reply, error = {}, f"HTTP {exc.code}: {exc.read()[:200]!r}"
                except Exception as exc:
                    reply, error = {}, repr(exc)
                wall = round(time.time() - start, 1)
                usage = reply.get("usage") or {}
                # Open WebUI returns the passages it retrieved alongside the answer.
                names = sorted({m.get("name") or m.get("source") or "?"
                                for s in reply.get("sources") or [] for m in s.get("metadata") or []})
                if reply:
                    text = reply["choices"][0]["message"].get("content") or ""
                    name = f"{model.replace(':', '-').replace('/', '-')}__{q['id']}.md"
                    (OUT / name).write_text(f"**Question ({q['kind']}):** {q['question']}\n\n"
                                            f"**Documents retrieved:** {', '.join(names) or 'none reported'}\n\n{text}\n")
                writer.writerow([time.strftime("%Y-%m-%d"), model, q["id"], wall, usage.get("prompt_tokens", ""),
                                 usage.get("completion_tokens") or usage.get("output_tokens") or "",
                                 "; ".join(names), error])
                fh.flush()
                print(model, q["id"], wall, "s", names, error, flush=True)
            subprocess.run(["ollama", "stop", model], capture_output=True)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    main(sys.argv[1:])
