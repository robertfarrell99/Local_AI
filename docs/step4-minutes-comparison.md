# Step 4: minutes comparison across models

Run on 2026-11-13 with `scripts/run_minutes.py`. The same prompt and the three invented transcripts went to each model through Open WebUI's API, one run per model per transcript. Outputs are in `output/minutes/` (not tracked in Git); timings are in `output/minutes/results.csv`.

**Prompt:** "Write minutes for the meeting transcript below. Give: attendees and apologies, a short summary, decisions, and an actions table with owner and due date. Use only what was said."

## Result in one line

Claude was complete and added nothing that was not said. Qwen 3.8 27B matched it on decisions and actions, with a few small errors, and took about ten times as long. Mistral Small 3.2 was correct on the main points but thin, and made up several due dates.

## Scores against the answer key

| Measure | Claude Fable 5.2 | Qwen 3.8 27B (local) | Mistral Small 3.2 24B (local) |
| --- | --- | --- | --- |
| Decisions found (of 10) | 10 | 10 | 9 |
| Actions with the right owner (of 19) | 19 | 19 | 17 |
| Invented or wrong details | 0 | 3 | 7 |
| Traps handled | All | All but one | Avoided errors mostly by leaving the detail out |
| Supporting figures in the summary (budgets, percentages, counts) | Full | Full | Mostly missing |
| Off-topic thread left out (transcript 03) | Yes | Yes | Yes |

**What each model got wrong**

- **Claude:** nothing found. It was also the only one to note that transcript 02 never states a currency, and to flag that no date was agreed for the data extract.
- **Qwen:**
  - Transcript 01: added an action that was never assigned ("Tom to convene the next steering group") and worded one action as "the approved change request" when it was not approved.
  - Transcript 02: described the rejected cheaper option as three depots; it was two.
  - Transcript 03: gave "by end November" as a due date that was not set.
- **Mistral:**
  - Transcript 01: missed the "no decision" on vulnerability flags as a decision; gave Dan an action that was Tom's; put "today" as the due date on two actions where none was stated; left out the budget, the record counts and the rejected December date.
  - Transcript 02: gave an action to Imran Shah, who was not on the call; invented "before 16 November" twice; listed the findings date as a decision rather than an action.
  - Transcript 03: all decisions and actions right; invented "ASAP" and "next meeting to be scheduled".

## Speed

| Measure | Claude Fable 5.2 | Qwen 3.8 27B | Mistral Small 3.2 24B |
| --- | --- | --- | --- |
| Time per transcript | 18–23 seconds | 3 min 4 s – 4 min 13 s | 1 min 36 s – 2 min 16 s |
| Output speed (tokens per second) | about 110 | 13.1–13.5 | 7.4–8.2 |
| Output length (tokens) | 1,900–2,600 | 2,000–2,900 | 545–565 |

- Token counts for Claude and Qwen include reasoning the model does before the visible answer; the visible minutes are 580–700 words for both. Mistral does not reason first and writes about 300 words.
- Claude's speed is worked out from total time, so it understates the true rate slightly.
- Qwen is faster per token than Mistral on this Mac. Ollama runs Qwen on its MLX engine and Mistral on llama.cpp, which is the likely reason; not confirmed.

## Limits of this test

- **One run each.** Model output varies between runs. Nine runs is enough to see the pattern, not to quote exact scores.
- **Scored by Claude.** The scoring, the transcripts and the answer key were all produced by Claude (the assistant running this spike), and Claude is also one of the models tested. Rob should spot-check a few outputs against the answer key before relying on the ranking.
- **Short transcripts.** Each is about 1,100 words. The long-transcript test below covers a realistic one-hour meeting.
- **Memory was tight.** The Mac had about 14 GB of swap in use during the runs, with other apps open. Local speeds may improve with those closed.
- **API, not the browser.** The runs used Open WebUI's API with the transcript pasted into the prompt. Uploading a file in the browser, which is how a consultant would do it, has not been tested yet.

## Long transcript test (one-hour meeting, 9,037 words)

Run on 2026-11-13 with `python3 scripts/run_minutes.py --only 04 ...`. Transcript 04 is an invented one-hour programme board with 7 decisions and 15 actions in the answer key. It came to about 15,500 tokens of input for the local models, about half of the 32K context.

### Result in one line

The 32K context setting works: neither local model dropped the start of the meeting. Qwen stayed close to Claude on a long meeting but took over 12 minutes. Mistral lost a third of the actions.

### Scores

| Measure | Claude Fable 5.2 | Qwen 3.8 27B (local) | Mistral Small 3.2 24B (local) |
| --- | --- | --- | --- |
| Decisions found (of 7) | 7 | 7 | 6 |
| Actions with the right owner (of 15) | 15 | 14 | 9 |
| Decision from the first 3 minutes (£38,400, 1 December) | Yes | Yes | Yes |
| Reversed decision reported as reversed (12 April, not 1 February) | Yes | Yes | Yes |
| Action from the last 30 seconds | Yes | Yes | Yes |
| Action that changed owner (letter: Gareth, not Stuart) | Yes | Yes | Yes |
| Corrected figures (12,400 duplicates; 348 of 600 trained) | Right | Right | Not mentioned |
| Rejected option and deferred topic | Right | Right | Right |
| Off-topic tangent left out | Yes | Yes | Yes |
| Wrong details | None found | 3 | 1 |
| Time taken | 48 seconds | 12 min 36 s | 8 min 55 s |
| Output speed (tokens per second) | about 118 | 12.0 | 6.3 |

**What each model got wrong**

- **Claude:** nothing found against the answer key. It listed 23 actions, including the minor ones the key allows and three more (set up accounts for the temps, update the risk rating, resolve agent training) that were not checked against the transcript.
- **Qwen:**
  - Missed Chloe's action to re-profile the budget by 30 November (mentioned in the summary, not as an action).
  - Said Chloe was present "until 13:40"; the meeting started at 14:00 and she left at 14:40.
  - Described release 7.3 as "two weeks late on its second rescheduled date", which is garbled.
  - Stated the £115,000 headroom as the position; it rests on an untested £65,000 estimate.
- **Mistral:**
  - Missed the decision not to migrate pre-2012 records.
  - Missed six actions: the retention schedule check, the trial migration report, raising the freeze at the forum, the memo to heads of school, the budget re-profile, and Helen's call to the supplier's chief executive.
  - Left template placeholders at the end ("Minutes prepared by: [Your Name]").
  - Gave no budget figures and did not record who joined late or left early.

### What this adds to the short-transcript results

- **Context length.** A one-hour meeting is about 15,500 tokens, so 32K covers it with room for the answer. A two-hour meeting would be close to the limit and would need a higher setting, which costs memory and time.
- **Waiting time is the main gap.** For a real meeting, a consultant would wait 9–13 minutes for a local model on this Mac against under a minute for Claude. Most of the local time is the model reading the transcript before it writes anything.
- **Qwen holds up on length; Mistral does not.** Mistral's answer stayed at about 500 words whether the meeting was 7 minutes or an hour, so it drops more as the meeting gets longer.
- **Same limits as above:** one run each, scored by Claude, memory tight during the runs.
