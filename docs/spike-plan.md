# Spike plan: Open WebUI as an in-house assistant front end

> **Status:** draft, 2026-11-13
> **Owner:** Rob Farrell
> **Context:** see `in-house-llm-direction.md` for the direction and reasoning.
> **Goal:** see Open WebUI in action and judge its look and feel, then establish how to put it in front of a self-hosted open model.

## Questions the spike answers

1. What does Open WebUI look and feel like for a consultant doing everyday work?
2. Can it take a transcript upload and produce usable minutes?
3. Can we switch between models and compare them on the same input?
4. Can a tool generate a Word or Excel document from the output?
5. How much setup effort is it, and what breaks?

## Out of scope for Phase 1

Entra sign-in, multi-user behaviour, performance under load, data isolation, cost modelling, CRM capture integration.

## Phase 1: local on Rob's Mac

**Before starting**

- [x] Mac spec confirmed 2026-11-13: M1 Pro, 32 GB memory, 285 GB disk free. Enough for a 24B–27B model at 4-bit, one loaded at a time.
- [x] Docker Desktop installed, with its memory limit set to about 4 GB so the model keeps the rest.
- [x] Ollama installed as the native Mac app, not inside Docker, so it can use the Mac's GPU.
- [ ] An Anthropic API key for the comparison model.
- [x] Two or three non-sensitive test transcripts. Phase 1 can send text to an external API, so nothing real. *(Three invented ones in `transcripts/invented/`.)*

**Steps**

1. Run Open WebUI as a single Docker container and open it on localhost. Take the run command from the current Open WebUI README.
2. Pull the local models with Ollama and confirm they appear in Open WebUI. Confirm the exact tags on ollama.com first; names below are from November 2026 guides.
   - Primary: Qwen 3.8 27B at 4-bit (about 18 GB). Reported as the strongest general model that fits 32 GB.
   - Second: Mistral Small 24B (about 14–15 GB). Faster, native tool calling, and a likely candidate for the Azure deployment.
   - Load one at a time. Close other heavy apps while testing.
   - Raise the context length to about 32K in the model settings. Ollama's default is too short for a meeting transcript, and the model will silently drop the start of the text.
   - Expect noticeably slower output than Claude on an M1 Pro. Record tokens per second.
3. Add Claude as a second model: an OpenAI-compatible connection to the Anthropic API in the admin connection settings, or an Open WebUI function if that connection does not work. Check current docs for which is supported.
4. Upload a test transcript and run the same minutes prompt against both models. Note quality, speed and formatting.
5. Try the knowledge base with two or three documents and ask questions across them.
6. Add one custom Python tool that turns the model's output into a .docx, then an .xlsx.
7. Write up the findings below.

**Done when** questions 1–5 have written answers and the model comparison has been run on at least three transcripts.

## Phase 2: shared deployment in Azure (after Phase 1)

1. Move the same container to a small VM in Alchemmy's Azure subscription, UK South.
2. Add Entra sign-in (OIDC) and two or three test users with different roles.
3. Check the audit and usage logging against what an ISO 27001 auditor would ask for.
4. Check the Open WebUI licence terms on branding for Alchemmy's size.

## Phase 3: self-hosted open model (after Phase 2)

1. Choose the model and GPU size together; they set the cost.
2. Serve the model on a GPU VM in UK South through an OpenAI-compatible endpoint, and point Open WebUI at it.
3. Rerun the Phase 1 transcripts and compare against the Claude results.
4. Schedule the GPU for office hours and measure real cost for a month.
5. Decide: go, change the model, or stop.

## Findings (fill in during the spike)

| Question | Finding | Evidence |
| --- | --- | --- |
| 1. Look and feel | | |
| 2. Transcript to minutes | Provisional: yes. On four invented transcripts (three short, one of an hour) Claude was complete and accurate. Qwen 3.8 27B was close behind with a few small errors. Mistral Small 3.2 was correct but thin and lost a third of the actions on the long meeting. The 32K context setting was enough for a one-hour meeting. Tested through the API; file upload in the browser not yet tested. | `docs/step4-minutes-comparison.md`, 12 runs on 2026-11-13 |
| 3. Model switching and comparison | Provisional: local and Claude models sit in the same picker and take the same prompt. On this Mac a one-hour transcript takes 9–13 minutes on a local model against under a minute for Claude; a short one takes 1.5–4 minutes against about 20 seconds. Side-by-side view in the browser not yet tried. | `docs/step4-minutes-comparison.md`; `output/minutes/results.csv` |
| 4. Word and Excel output | Yes. Two small Python tools (about 100 lines each) produce a Word file and an Excel file from the model's output, with a download link in the chat. Claude, Qwen and Mistral all used both tools correctly in the browser. The file is only as complete as the model's minutes: Mistral's missed one of three actions. Plain formatting only, no house template. The docs do not cover returning a file, so the method relies on Open WebUI internals and may need fixing after an update. Not yet opened in Word or Excel by a person. | `docs/step6-word-excel-tools.md`; files in `output/tools/`, 2026-11-14 |
| 5. Setup effort and problems | | |

**Time taken per step:**

**What broke:**

**Recommendation for Phase 2:**
