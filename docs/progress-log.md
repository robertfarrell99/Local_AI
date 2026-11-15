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
- Phase 1 step 5, knowledge base: three invented documents and seven questions with an answer key added in `knowledge/invented/`; knowledge base created in Open WebUI through its API (a few seconds, default indexing, no configuration); `scripts/run_knowledge.py` asks every model the same questions. 21 runs, no errors, about 20 minutes. Claude 7/7 right, Qwen 7/7, Mistral 6/7 with one partly right. No model invented an answer to the question that was not in the documents. Caveat: three short documents are too few to test the search itself. Details in [step5-knowledge-base.md](step5-knowledge-base.md).

## 2026-11-14

- Phase 1 step 6, Word and Excel tools: `tools/export_word.py` and `tools/export_excel.py` written, loaded with `scripts/install_tools.py`, and tested in the browser with all three models. All three called both tools correctly and returned working download links. Claude about 30 seconds per request, Qwen about 5 minutes, Mistral about 6 minutes; Mistral's files missed one of three actions. About an hour in total, most of it working out how a tool hands a file back. Details in [step6-word-excel-tools.md](step6-word-excel-tools.md).
- Checked whether giving Docker more memory would help (Rob's question). It would not: Open WebUI was using about 1 GB of its 4 GB limit, and the models run outside Docker. Left at 4 GB.
- Looked at extra models, not downloaded or tested (outside the Phase 1 plan). Coding: `devstral-small-2:24b` (15 GB) or `qwen3-coder:30b` (19 GB). Images: Open WebUI's local image engines are ComfyUI and AUTOMATIC1111; Ollama's own image generation is experimental and has no documented connection to Open WebUI. In ComfyUI, Z-Image Turbo and FLUX.2 klein 4B fit 32 GB and are Apache 2.0 licensed; FLUX.2 klein 9B and FLUX.2 dev are non-commercial. Sources checked 2026-11-14.
- Phase 1 step 7, write-up: Findings rows 1 and 5, time per step, what broke and the Phase 2 recommendation filled in [spike-plan.md](spike-plan.md), all from this log and the step write-ups. Under an hour. Row 1 (look and feel) is only partly answered: it records what was seen while the browser was driven for step 6 and is marked unverified until Rob has used Open WebUI himself. The Anthropic key prerequisite is now ticked (the Claude connection has worked since 13 November). Nothing broke.
- Image models downloaded at Rob's request (outside the Phase 1 plan; nothing tested yet). First batch: six files, 27 GB on disk, about 20 minutes, saved in `~/ComfyUI-models` (outside this repo) in the subfolders ComfyUI expects. All six matched the checksums published on Hugging Face. File names and links taken from the ComfyUI docs pages for each model, checked 2026-11-14. Both models are Apache 2.0 licensed.
  - Z-Image Turbo (text to image): `z_image_turbo_bf16.safetensors` 12.3 GB, `ae.safetensors` 0.3 GB.
  - FLUX.2 klein 4B (text to image and image editing): `flux-2-klein-4b-fp8.safetensors` 4.1 GB (fast version), `flux-2-klein-base-4b-fp8.safetensors` 4.1 GB (base version), `flux2-vae.safetensors` 0.3 GB.
  - `qwen_3_4b.safetensors` 8.0 GB: the text encoder (the part that reads the prompt), shared by both models.
  - Qwen-Image-Edit 2511 (image editing, Apache 2.0), added later the same day at Rob's request: `qwen_image_edit_2511_int8_convrot.safetensors` 20.5 GB, `qwen_2.5_vl_7b_fp8_scaled.safetensors` 9.4 GB (its text encoder), `Qwen-Image-Edit-2511-Lightning-4steps-V1.0-bf16.safetensors` 0.9 GB (an add-on that cuts an edit to 4 steps, goes in `loras`), `qwen_image_vae.safetensors` 0.3 GB. All four matched their checksums. The main file may be too heavy for a 32 GB Mac; untested. The folder now holds 56 GB in ten files, with 144 GB of disk free.
  - ComfyUI itself is not installed yet, so no image has been produced and nothing is connected to Open WebUI.
- ComfyUI installed and first image generated (at Rob's request; outside the Phase 1 plan). ComfyUI is a program that runs image models and shows them as a web page.
  - Install: version 0.45.3 copied from its GitHub repository into `~/ComfyUI`, with its Python packages in a private environment in that folder (2.1 GB). Manual install rather than the desktop app or Homebrew, because Homebrew commands are blocked in this Claude session. About 10 minutes. Python 3.14, PyTorch 2.15.0, Apple GPU (MPS) available.
  - Models linked through `~/ComfyUI/extra_model_paths.yaml`, which points at `~/ComfyUI-models`. Nothing was moved.
  - Start it with `cd ~/ComfyUI && .venv/bin/python main.py`, then open http://localhost:8188.
  - Test: one 1024 by 1024 image with Z-Image Turbo, 8 steps, settings taken from ComfyUI's official Z-Image Turbo template, sent through ComfyUI's API. Worked first time. **4 minutes 29 seconds** in total from a cold start: about 25 seconds per step (3 min 20 s for the 8 steps), the rest loading the model. The image matched the prompt, including the word REPAIRS spelled correctly on the van's sign. Saved as `output/images/z-image-turbo-test-01.png` (not tracked). One run only; a second image should be quicker because the model is already loaded.
  - Memory: Z-Image Turbo and its text encoder take about 19 GB while loaded, so it cannot be loaded at the same time as a local chat model. ComfyUI was told to unload after the test.
  - Not done: FLUX.2 klein and Qwen-Image-Edit are untested; ComfyUI is not connected to Open WebUI. Connecting it needs ComfyUI started with `--listen`, which also opens it to other devices on the same network.

## 2026-11-15

- Z-Image Turbo tested on people (Rob's request; outside the Phase 1 plan). Three 1024 by 1024 images of invented people, same settings as the first test, one run each. Saved in `output/images/` (not tracked). Judged by eye by Claude, not by Rob.

  | Image | Time | What came out |
  | --- | --- | --- |
  | Portrait: woman in her forties, grey hair, glasses, navy blazer, office | 4 min 31 s (model loading from cold) | Looks like a real photograph. Face, skin, glasses and hair all convincing; every detail asked for is there. |
  | Group: five colleagues at a meeting table, one man pointing at a whiteboard | 3 min 47 s | Faces and hands look natural, which is where image models usually fail. But seven people, not five; the pointing man is sitting, and two laptops face the wrong way. A real Apple logo appeared on a laptop unasked. |
  | Full length: repairs engineer with a toolbox in one hand and a tablet in the other, walking up to a front door | 3 min 46 s | Body, clothing and house look right. But he carries two toolboxes and no tablet, and is walking away from the door, not towards it. |

  Reading: people look realistic, and single portraits are strong. It is loose with exact instructions: counts of people, which object is in which hand, and direction of movement were all wrong. With the model already loaded an image takes about 3 min 45 s on this Mac.

**Still to do**

- Rob to spot-check a few step 4 outputs against the answer key (the scoring was done by Claude, which is also one of the models tested).
- Step 4 in the browser: upload a transcript file in Open WebUI and compare models side by side there.
- Rerun local speeds with other heavy apps closed.
- Knowledge base with a realistic set of documents in Word, PDF and PowerPoint (30 or more, non-sensitive), to test whether the right passage is found.
- Rob to open the step 6 files in `output/tools/` in Word and Excel, and to click a download link in his own browser.
- Rob to use Open WebUI for half an hour of ordinary work and record a view on look and feel (Findings row 1).

**What broke**

- Mistral Small ran slower per token than the larger Qwen model, the opposite of what the plan expected (see the 13 November table). Likely the different Ollama engines; not confirmed.
- Minor: on first launch Ollama took about 10 seconds before it answered requests; the first `ollama list` timed out. Fine on retry.
- A newly downloaded Ollama model was not usable through Open WebUI straight away: the first request failed with HTTP 400 until the model list was refreshed. In the browser, reloading the page does the same thing.
- Changing Docker Desktop's memory limit restarts Docker, and the Open WebUI container did not come back by itself (exited with code 137). `docker compose up -d` fixed it; no data lost.
- The Open WebUI docs do not say how a tool should give the user a file. The method used (its internal upload function) was found by reading the source code in the container, and could change in a later version.
- Tools are not run when a chat is sent through the plain API; the model's tool request comes back unexecuted. Tool tests had to go through the browser.
- A newly added tool did not appear in the chat's Tools menu until the page was reloaded.
- When one reply creates two files, only the last shows as an attachment above the reply. The links in the reply text both work.
- While driving the browser, a mistimed click on a suggested prompt started a stray chat ("Vocabulary Practice") with Claude. Harmless; it can be deleted from the sidebar.
