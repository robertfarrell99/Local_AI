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

- `mistral-small3.2:24b` downloaded (15 GB). Context set to 32K the same way and confirmed with `ollama ps`. Same test, transcript 01, through Open WebUI:

  | Measure | `qwen3.8:27b` | `mistral-small3.2:24b` |
  | --- | --- | --- |
  | Output speed | 12.3 tokens per second | 6.9 tokens per second (7.1 on a second, short run) |
  | Input reading speed | 55 tokens per second | 45 tokens per second |
  | Total time | 3 min 21 s | 2 min 20 s |
  | Output length | 1,859 tokens including hidden reasoning | 526 tokens, no reasoning step |
  | Engine Ollama used | MLX (Apple's own) | llama.cpp |
  | Decisions found (of 3) | 3 | 2 (missed "no decision on vulnerability flags"; listed the pilot rerun as a decision instead) |
  | Actions found (of 7) | 7 | 6 (missed Dan's deduplication by 18 November) |
  | Invented detail | One due date | One due date ("as soon as possible") |
  | Left out | Nothing material | Budget figures, record counts, the rejected 14 December option |

  Mistral was slower per token than Qwen, the opposite of what the plan expected. The likely reason is that Ollama runs Qwen on its MLX engine and Mistral on llama.cpp, but that is a guess from the `ollama ps` output and is not confirmed. Mistral still finished sooner because it writes a much shorter answer and does not reason first. Its minutes were correct in what they said but thinner.

  **Caveat on all speed figures:** the Mac was short of memory during these runs (12% free, 12.9 GB of swap in use, other apps open). Rerun with other heavy apps closed before treating the numbers as final.

- Phase 1 step 4 run: same minutes prompt, three transcripts, three models (Claude Fable 5.2, `qwen3.8:27b`, `mistral-small3.2:24b`), nine runs, no errors, about 25 minutes. Full write-up in [step4-minutes-comparison.md](step4-minutes-comparison.md). Headline: Claude 10/10 decisions and 19/19 actions with nothing invented, about 20 seconds each; Qwen 10/10 and 19/19 with three small errors, 3–4 minutes each; Mistral 9/10 and 17/19 with seven invented or wrong details and thin summaries, 1.5–2.5 minutes each.
- Added `scripts/run_minutes.py` so the same test can be rerun in Phase 3.
- Long transcript test: added `04-long-programme-board.txt` (invented one-hour meeting, 9,037 words, about 15,500 tokens) and its answer key, and ran it on all three models. No errors or timeouts. The 32K context held: both local models kept the decision from the first three minutes. Claude 7/7 decisions and 15/15 actions in 48 seconds; Qwen 7/7 and 14/15 in 12 min 36 s; Mistral 6/7 and 9/15 in 8 min 55 s. Details in [step4-minutes-comparison.md](step4-minutes-comparison.md).

**Still to do**

- Rob to spot-check a few step 4 outputs against the answer key (the scoring was done by Claude, which is also one of the models tested).
- Step 4 in the browser: upload a transcript file in Open WebUI and compare models side by side there.
- Rerun local speeds with other heavy apps closed.

**What broke**

- Minor: on first launch Ollama took about 10 seconds before it answered requests; the first `ollama list` timed out. Fine on retry.
- A newly downloaded Ollama model was not usable through Open WebUI straight away: the first request failed with HTTP 400 until the model list was refreshed. In the browser, reloading the page does the same thing.
- Changing Docker Desktop's memory limit restarts Docker, and the Open WebUI container did not come back by itself (exited with code 137). `docker compose up -d` fixed it; no data lost.
