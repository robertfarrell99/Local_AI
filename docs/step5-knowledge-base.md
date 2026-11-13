# Step 5: knowledge base test

Run on 2026-11-13 with `scripts/run_knowledge.py`. Three invented documents were loaded into an Open WebUI knowledge base ("Meridian Programme (invented test documents)"), and each model was asked the same seven questions with that knowledge base attached. Answers are in `output/knowledge/` (not tracked in Git).

A knowledge base in Open WebUI is a set of documents the tool splits into passages and indexes. When you ask a question, it finds the passages that look most relevant and gives those to the model along with the question. The model never sees the whole library, only what was found.

## Result in one line

It works, and all three models answered well from it. But three short documents are too small to test the search itself: almost the whole library was handed to the model for every question.

## Scores against the answer key

| Question | Tests | Claude Fable 5.2 | Qwen 3.8 27B (local) | Mistral Small 3.2 24B (local) |
| --- | --- | --- | --- | --- |
| q1 | Simple lookup | Right | Right | Right |
| q2 | Two documents, and a cap on a figure | Right | Right | Right |
| q3 | Two documents disagree on a date | Right | Right | Right |
| q4 | Conditions on a rule | Right | Right | Right |
| q5 | Arithmetic across two documents | Right | Right | Right |
| q6 | Answer is not in the documents | Right (said so) | Right (said so) | Right (said so) |
| q7 | Two documents, how a cost changes | Right, plus the overlap point | Right | Partly right |
| **Total right (of 7)** | | **7** | **7** | **6** |
| Time per question | | 3–12 seconds | 59–107 seconds | 60–91 seconds |

- **No model invented an answer.** On q6 all three said the Chief Executive's name was not in the documents.
- **All three picked the newer date on q3** (2 August 2027) and explained that it replaced September 2027 in the older document.
- **All three applied the 10% cap on q2** (£12,000, not £16,800) and combined the contract with the business case to say where the money goes.
- **Mistral on q7** gave the cost comparison correctly but missed how the charge rises (the lower of 4% or inflation each year), and filled the gap with unrelated points about service credits and contingency.
- **Claude added useful points beyond the key:** on q2 that the 20-working-day notice window closes before a seven-week-late delivery arrives, and on q7 that the university pays for both systems for about a year.
- **Citations.** Every model marked its statements with numbered references such as [1]. In the browser these link to the source passage. The numbers refer to passages, not documents, so the same document can appear as [1] in one answer and [2] in another.

## What this does and does not show

- **Setup was easy.** Creating the knowledge base and adding three documents took three API calls and a few seconds. Open WebUI's built-in indexing worked with no configuration and ran inside the container, so nothing was sent outside the Mac at that stage.
- **The search was not really tested.** Open WebUI retrieves the ten most relevant passages. Three short documents only make about ten passages, so every question got nearly everything (about 2,000–2,600 tokens). The results show the models can reason over retrieved text; they do not show whether the right passages would be found among hundreds of documents.
- **Markdown files only.** Word, PDF and PowerPoint files, which is what consultants actually have, were not tried. Document parsing is a common weak point and needs its own test.
- **Speed.** Local answers took about a minute to a minute and three quarters each, against 3–12 seconds for Claude. Most of the local time is reading the retrieved passages.
- **Same limits as step 4:** one run each, scored by Claude (also one of the models tested), memory tight during the runs.

## Suggested follow-up before Phase 2

Load a realistic set (30 or more real-format documents, non-sensitive) and repeat with questions whose answers sit in one specific document. That is the test of whether the knowledge base finds the right passage.
