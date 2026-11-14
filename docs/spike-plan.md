# Spike plan: Open WebUI as an in-house assistant front end

> **Status:** Phase 1 steps 1–7 run, findings written 2026-11-14. Rob's own hands-on checks are still open (listed under Findings).
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
- [x] An Anthropic API key for the comparison model. *(Entered by Rob in the Open WebUI admin screen on 2026-11-13; not stored in this repo.)*
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

Written up 2026-11-14. Read these with three limits in mind: every test was run once; the scoring was done by Claude, which is also one of the models tested; and all test material was invented, short and tidy compared with real client work.

| Question | Finding | Evidence |
| --- | --- | --- |
| 1. Look and feel | Partly answered; Rob's own judgement is still needed. What was seen while the browser was driven for step 6: it works like a familiar chat assistant. One picker at the top holds the local models and Claude together. A + button beside the message box switches tools on. Replies show formatted minutes, tables and download links. A web link can open a new chat with the model and tools already chosen. Rough edges: new models and tools need a page reload before they appear, and on this Mac a local model takes minutes to reply, which will shape how it feels more than the screen design does. Not yet done: a consultant using it for everyday work, uploading a file by hand, and the side-by-side model view. | Step 6 browser session, 2026-11-14 (no screenshots kept). Unverified by Rob. |
| 2. Transcript to minutes | Provisional: yes. On four invented transcripts (three short, one of an hour) Claude was complete and accurate. Qwen 3.8 27B was close behind with a few small errors. Mistral Small 3.2 was correct but thin and lost a third of the actions on the long meeting. The 32K context setting was enough for a one-hour meeting. Tested through the API; file upload in the browser not yet tested. | `docs/step4-minutes-comparison.md`, 12 runs on 2026-11-13 |
| 3. Model switching and comparison | Provisional: local and Claude models sit in the same picker and take the same prompt. On this Mac a one-hour transcript takes 9–13 minutes on a local model against under a minute for Claude; a short one takes 1.5–4 minutes against about 20 seconds. Side-by-side view in the browser not yet tried. | `docs/step4-minutes-comparison.md`; `output/minutes/results.csv` |
| 4. Word and Excel output | Yes. Two small Python tools (about 100 lines each) produce a Word file and an Excel file from the model's output, with a download link in the chat. Claude, Qwen and Mistral all used both tools correctly in the browser. The file is only as complete as the model's minutes: Mistral's missed one of three actions. Plain formatting only, no house template. The docs do not cover returning a file, so the method relies on Open WebUI internals and may need fixing after an update. Not yet opened in Word or Excel by a person. | `docs/step6-word-excel-tools.md`; files in `output/tools/`, 2026-11-14 |
| 5. Setup effort and problems | Low effort, no showstoppers. From nothing to three models answering in one browser screen took part of one day, most of it waiting for 33 GB of model downloads. It needed one Docker file, the Ollama Mac app and a few settings in the admin screens; the Claude connection worked first time. Eight small problems came up, each fixed in minutes (listed below). Three things need care rather than fixing: the context length must be raised on every local model or long transcripts are silently cut; a 32 GB Mac only just holds one 27B model alongside normal apps; and the Word and Excel tools rely on undocumented Open WebUI internals. | `docs/progress-log.md`, 2026-11-13 and 2026-11-14 |

**Also tested, outside the five questions:** the knowledge base (step 5). With three invented documents and seven questions, Claude and Qwen got 7 of 7 right and Mistral 6 of 7, and no model invented an answer to the question the documents did not cover. Three short documents are too few to test whether the search finds the right passage in a realistic library. See `docs/step5-knowledge-base.md`.

**Time taken per step:**

Times are from the progress log. Where no time was noted at the point of doing the work, it says so.

| Step | Time | Notes |
| --- | --- | --- |
| 1. Open WebUI running | About 10 minutes | Including the image download. |
| 2. Local models | A couple of minutes to install Ollama; download time for 18 GB and 15 GB not recorded | Setting the context length took a minute per model. |
| 3. Claude connection | Not recorded; worked first time | Done by Rob in the admin screen. |
| 4. Minutes comparison | About 25 minutes for nine runs, plus about 22 minutes for the one-hour transcript on three models | Writing the invented transcripts and answer keys is not included and was not timed. |
| 5. Knowledge base | About 20 minutes for 21 runs | Creating the knowledge base itself took seconds. |
| 6. Word and Excel tools | About an hour | Most of it finding out how a tool hands a file back. |
| 7. Write-up | Under an hour | |

All seven steps were done across two days, 13 and 14 November 2026.

**What broke:**

Nothing stopped the work. In the order they happened:

1. Ollama took about 10 seconds to answer after its first launch; the first command timed out and worked on retry.
2. A newly downloaded model failed on its first request through Open WebUI until the model list was refreshed (in the browser, a page reload).
3. Changing Docker's memory limit restarted Docker, and the Open WebUI container did not come back by itself. One command restarted it; no data was lost.
4. Mistral Small ran slower per word than the larger Qwen model, the opposite of what the plan expected. The likely cause is that Ollama runs the two on different engines; this is not confirmed.
5. The Open WebUI documentation does not say how a tool should give the user a file. The working method came from reading its source code and could break in a later version.
6. Tools do not run when a chat is sent through the plain API, so tool tests had to go through the browser.
7. A newly added tool did not appear in the Tools menu until the page was reloaded.
8. When one reply creates two files, only the last shows as an attachment. Both links in the reply text work.

**Still open before Phase 1 is fully closed** (all need Rob at the keyboard):

- Use Open WebUI for half an hour of ordinary work and record a view on look and feel (question 1).
- Upload a transcript file by hand and try the side-by-side model view.
- Open the step 6 files in Word and Excel, and click a download link.
- Spot-check a few step 4 outputs against the answer key, since Claude did the scoring.
- Rerun the local speed figures with other heavy apps closed; the Mac was short of memory during the first runs.

**Recommendation for Phase 2:**

Go ahead to Phase 2, once Rob has done the hands-on look-and-feel check above. Nothing found in Phase 1 argues against Open WebUI as the front end: it was quick to set up, put local and Claude models behind one screen, produced usable minutes and generated Word and Excel files.

Carry these points into Phase 2 and 3:

- **Fix the Open WebUI version.** Phase 1 ran whatever version was newest (0.13.3). For a shared deployment, pin a version and test the export tools before each upgrade, because they rely on internals.
- **Restrict who can add or edit tools.** A tool runs with full access inside the Open WebUI container. Limit this to administrators and check it is logged, alongside the audit check already in Phase 2.
- **Revisit how Claude is connected.** The direct connection used here is described by Anthropic as for evaluation and testing. Check current guidance before relying on it for a team; an Open WebUI function is the alternative.
- **Do not judge local model speed from this Mac.** Minutes took 1.5 to 13 minutes on a local model against 20 to 50 seconds for Claude. That is the laptop, not the model; Phase 3 on a proper GPU is where speed gets a fair test.
- **Question Mistral Small as the Azure candidate.** It was the weakest of the three on every test: thinner minutes, a third of the actions lost on the one-hour meeting, one action missed in the exported files. Qwen 3.8 27B was close to Claude on quality. Decide the Phase 3 model on that evidence and on GPU cost together.
- **Test the knowledge base properly.** Use 30 or more non-sensitive documents in Word, PDF and PowerPoint before telling anyone it works.
- **Add a house template to the Word tool** if exported minutes are to go to clients.
- **Keep real and client material out** until sign-in, user separation and logging have been checked in Phase 2.
