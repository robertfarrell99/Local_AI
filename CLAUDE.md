# Local_AI — project guidance

A spike, not a product. The goal is to judge Open WebUI as an in-house assistant front end and learn how to put it in front of a self-hosted open model. The deliverable is written findings, not polished code.

## Where things are

- `docs/spike-plan.md` — the plan, phases, and the Findings table. This is the source of truth for scope and order of work.
- `docs/progress-log.md` — dated record of what was done, time taken, and what broke.
- `docker-compose.yml` — Open WebUI for Phase 1 (http://localhost:3000, sign-in off, localhost only).
- `tools/` — custom Open WebUI tools (Python). One file per tool.
- `transcripts/invented/` — three made-up test transcripts and `answer-key.md` for scoring minutes. Tracked in Git so Phase 3 can rerun them.
- `transcripts/` (anything else), `output/` — other test inputs and generated documents. Ignored by Git.

## How to work here

- **Follow the plan's order.** Work through the Phase 1 steps in sequence. Do not start Phase 2 or 3 work, or anything listed as out of scope for Phase 1, unless Rob asks.
- **Record as you go.** After each step, add to `docs/progress-log.md`: what was done, roughly how long it took, and anything that broke, including small annoyances. Setup effort and breakage are spike questions in their own right. Tick the checkbox in the plan when a prerequisite or step is complete.
- **Findings need evidence.** Fill the Findings table only from things actually observed (a run, a screenshot, a measured tokens-per-second figure). Mark anything unverified as unverified.
- **Check current docs before relying on names.** Open WebUI settings paths, Ollama model tags and Anthropic model IDs change often. Confirm against openwebui.com docs, ollama.com and Anthropic's docs rather than memory, and note the date checked.
- **Keep it simple.** Prefer configuration through the Open WebUI admin screens and one compose file over extra services or scripts. No tests, CI or abstractions unless a step needs them.
- **Plain English in the docs.** Rob will share findings with non-technical colleagues. Explain terms on first use.

## Hard rules

- **This GitHub repo is public.** Never commit API keys, `.env` files, real transcripts, client names or client material. Secrets go in the Open WebUI admin screens or a local `.env` (ignored by Git).
- **No real or sensitive data in Phase 1.** Text may be sent to an external API (Anthropic). Use invented or already-public transcripts only.
- **Ollama runs natively on the Mac**, never in Docker, so it can use the GPU. Open WebUI reaches it at `http://host.docker.internal:11434`.
- **One local model loaded at a time.** The Mac has 32 GB of memory; a 27B model takes about 18 GB.
- **Set context length to about 32K** (`num_ctx` 32768) on every local model before testing with transcripts. The default silently drops the start of long input and would make the model comparison unfair.
- **Do not delete the `open-webui` Docker volume** without asking. It holds all chats, settings and connections. `docker compose down` is safe; `docker compose down -v` is not.

## Common commands

```bash
docker compose up -d          # start Open WebUI
docker compose logs -f        # watch its logs
docker compose pull && docker compose up -d   # update to the latest image
ollama list                   # models downloaded
ollama ps                     # model currently loaded, and memory used
ollama run <model> --verbose  # prints tokens per second after each reply
```

## Git

- Work on a branch per phase or step (`spike/…`), commit small, and say what step of the plan the commit covers.
- Ask before pushing; the repo is public.
