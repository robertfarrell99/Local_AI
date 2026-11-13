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

- Ollama 0.40.16 installed as the native Mac app (`brew install --cask ollama-app`, 229 MB, a couple of minutes). Responds on port 11434 and is reachable from inside the Open WebUI container with no extra configuration.
- Phase 1 step 2 started: pulling `qwen3.8:27b` then `mistral-small3.2:24b`.
- Docker Desktop memory limit lowered to 4 GB. Three invented test transcripts (about 1,100 words each: structured steering group, unedited client call captions, messy retrospective) and an answer key added in `transcripts/invented/`.

- Phase 1 step 3: Claude added by Rob as an OpenAI-compatible connection (`https://api.anthropic.com/v1`). Worked first time; 15 Claude models listed in Open WebUI. No function needed.
- `qwen3.8:27b` downloaded (18 GB) and appeared in Open WebUI with no further setup. Context length set to 32K as a per-model setting in Open WebUI (`num_ctx` 32768), and confirmed with `ollama ps`, which showed CONTEXT 32768 while the model was loaded through Open WebUI.
- First speed and quality run, `qwen3.8:27b` on transcript 01, sent through Open WebUI (output saved in `output/`, not tracked):

  | Measure | Result |
  | --- | --- |
  | Output speed | 12.3 tokens per second |
  | Input reading speed | 55 tokens per second (2,060 tokens, 38 seconds) |
  | Model load time | 12 seconds |
  | Total time | 3 minutes 21 seconds |
  | Output length | 1,859 tokens, which includes the model's hidden reasoning before the answer |
  | Processor | 100% GPU, 18 GB |

  Quality against the answer key: all 3 decisions, all 7 actions with the right owners, and every trap avoided (18 November not the 13th, 14 December shown as rejected, £18k shown as an unapproved estimate, Karen under apologies). One small invention: it gave "before go-live" as the due date for Mei's written confirmation, where none was stated. It also added two reasonable extra actions for Tom. One run only, so treat as indicative.

**Still to do**

- `mistral-small3.2:24b` download to finish, then the same context setting and speed run.

**What broke**

- Minor: on first launch Ollama took about 10 seconds before it answered requests; the first `ollama list` timed out. Fine on retry.
- Changing Docker Desktop's memory limit restarts Docker, and the Open WebUI container did not come back by itself (exited with code 137). `docker compose up -d` fixed it; no data lost.
