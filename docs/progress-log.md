# Progress log

Running record of the spike: what was done, how long it took, what broke. Newest entry first. This feeds the Findings table in [spike-plan.md](spike-plan.md).

## 2026-11-13

**Done**

- Repo cloned, branch `spike/open-webui-phase-1` created.
- Phase 1 step 1: Open WebUI running from `docker-compose.yml` on http://localhost:3000 (image `ghcr.io/open-webui/open-webui:main`, sign-in off, bound to localhost only). Version 0.13.3; container healthy and page returns HTTP 200. About 10 minutes including the image download. Not yet looked at in a browser.
- Docs checked for steps 2 and 3:
  - Ollama tags: `qwen3.8:27b` (18 GB) and `mistral-small:24b` (14 GB). Seen in search snippets of ollama.com; confirm on the tags pages before pulling.
  - Claude: Open WebUI docs describe a direct OpenAI-compatible connection to the Anthropic API (Admin → Connections → OpenAI). Anthropic describes that endpoint as for evaluation and testing, which fits a spike. A pipe function is the fallback and the route to native features.

**Still to do before step 2**

- Install Ollama (native Mac app).
- Lower Docker Desktop memory limit from about 12.6 GB to about 4 GB.
- Anthropic API key.
- Two or three non-sensitive test transcripts in `transcripts/`.

**What broke**

- Nothing so far.
