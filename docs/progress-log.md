# Progress log

Running record of the spike: what was done, how long it took, what broke. Newest entry first. This feeds the Findings table in [spike-plan.md](spike-plan.md).

## 2026-11-13

**Done**

- Repo cloned, branch `spike/open-webui-phase-1` created.
- Phase 1 step 1: Open WebUI running from `docker-compose.yml` on http://localhost:3000 (image `ghcr.io/open-webui/open-webui:main`, sign-in off, bound to localhost only). Version 0.13.3; container healthy and page returns HTTP 200. About 10 minutes including the image download. Not yet looked at in a browser.
- Docs checked for steps 2 and 3:
  - Ollama tags, confirmed on the ollama.com tags pages 2026-11-13:
    - `qwen3.8:27b` — 18 GB, 256K context, text and image input, tools. Use this as the primary.
    - `mistral-small3.2:24b` — 15 GB, 128K context, text and image input, tools, improved function calling. Use this as the second model instead of the older one below.
    - `mistral-small:24b` — 14 GB, but only 32K context, text only, last updated about a year ago. Superseded by 3.2.
    - The pages do not label the default tags' quantization (compression level); the sizes match the 4-bit builds.
  - Claude: Open WebUI docs describe a direct OpenAI-compatible connection to the Anthropic API (Admin → Connections → OpenAI). Anthropic describes that endpoint as for evaluation and testing, which fits a spike. A pipe function is the fallback and the route to native features.

**Still to do before step 2**

- Install Ollama (native Mac app). Rob to do this by hand: download from https://ollama.com/download/mac, or `brew install --cask ollama-app`.
- Lower Docker Desktop memory limit from about 12.6 GB to about 4 GB.
- Anthropic API key.
- Two or three non-sensitive test transcripts in `transcripts/`.

**What broke**

- Nothing so far.
