#!/usr/bin/env python3
"""Run the same minutes prompt over every invented transcript, for each model, through Open WebUI.

Phase 1 step 4, and reused in Phase 3. Goes through Open WebUI's API (not straight to Ollama)
so the per-model settings in Open WebUI, such as the 32K context length, apply.

Usage:  python3 scripts/run_minutes.py MODEL [MODEL ...]
Writes: output/minutes/<model>__<transcript>.md and output/minutes/results.csv (appended)
"""
import csv
import json
import pathlib
import subprocess
import sys
import time
import urllib.error
import urllib.request

BASE = "http://localhost:3000"
ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "minutes"
PROMPT = (
    "Write minutes for the meeting transcript below. Give: attendees and apologies, "
    "a short summary, decisions, and an actions table with owner and due date. "
    "Use only what was said.\n\n"
)


def call(path, token=None, body=None, timeout=1200):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, headers=headers)
    return json.load(urllib.request.urlopen(req, timeout=timeout))


def main(models):
    OUT.mkdir(parents=True, exist_ok=True)
    # Sign-in is off in Phase 1, so an empty sign-in returns a token.
    token = call("/api/v1/auths/signin", body={"email": "", "password": ""})["token"]
    call("/api/models?refresh=true", token=token)  # pick up newly pulled models
    transcripts = sorted((ROOT / "transcripts" / "invented").glob("*.txt"))
    results = OUT / "results.csv"
    new_file = not results.exists()
    with results.open("a", newline="") as fh:
        writer = csv.writer(fh)
        if new_file:
            writer.writerow(["date", "model", "transcript", "wall_seconds", "input_tokens",
                             "output_tokens", "output_tokens_per_second", "load_seconds", "error"])
        for model in models:
            for path in transcripts:
                body = {"model": model, "stream": False,
                        "messages": [{"role": "user", "content": PROMPT + path.read_text()}]}
                start = time.time()
                try:
                    reply = call("/api/chat/completions", token=token, body=body)
                    error = ""
                except urllib.error.HTTPError as exc:
                    reply, error = {}, f"HTTP {exc.code}: {exc.read()[:200]!r}"
                except Exception as exc:  # timeouts, connection drops
                    reply, error = {}, repr(exc)
                wall = round(time.time() - start, 1)
                usage = reply.get("usage") or {}
                out_tokens = usage.get("completion_tokens") or usage.get("output_tokens") or ""
                # Ollama reports its own speed; for hosted models fall back to tokens / wall time.
                speed = usage.get("response_token/s") or (round(out_tokens / wall, 1) if out_tokens else "")
                load = round(usage["load_duration"] / 1e9, 1) if usage.get("load_duration") else ""
                if reply:
                    text = reply["choices"][0]["message"].get("content") or ""
                    name = f"{model.replace(':', '-').replace('/', '-')}__{path.stem}.md"
                    (OUT / name).write_text(text)
                writer.writerow([time.strftime("%Y-%m-%d"), model, path.stem, wall,
                                 usage.get("prompt_tokens", ""), out_tokens, speed, load, error])
                fh.flush()
                print(model, path.stem, wall, "s", speed, "tok/s", error, flush=True)
            # Keep one local model in memory at a time.
            subprocess.run(["ollama", "stop", model], capture_output=True)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    main(sys.argv[1:])
