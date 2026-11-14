# Step 6: Word and Excel export tools

Built and tested on 2026-11-14. Two small Python tools were added to Open WebUI: one turns the model's text into a Word file (.docx), the other turns tables into an Excel file (.xlsx). Each was tested in the browser with all three models. The six files produced are in `output/tools/` (not tracked in Git).

A tool in Open WebUI is a short Python file that the model can choose to run. The model decides when to use it and what to pass in; Open WebUI runs the code and gives the result back to the model.

## Result in one line

It works with all three models. Each one wrote the minutes, called both tools without being told how, and gave back working download links. Building both tools took about an hour, most of it finding out how a tool should hand a file back, which the documentation does not cover.

## What was built

| File | What it does |
| --- | --- |
| `tools/export_word.py` | Takes a title and the text in Markdown (the plain-text formatting models write in). Produces a Word file with real headings, bullet and numbered lists, tables and bold. |
| `tools/export_excel.py` | Takes a title and one or more Markdown tables. Each table becomes a sheet, named after the heading above it, with a bold frozen header row, sensible column widths and plain numbers stored as numbers. |
| `scripts/install_tools.py` | Loads both files into Open WebUI. The same can be done by hand: Workspace > Tools > +, then paste the file. |

The files are saved in Open WebUI's own file store, so a download belongs to the user who asked for it. No extra software was installed: the Word and Excel libraries (python-docx, openpyxl) are already inside the Open WebUI image.

## Test

Same request to each model, in the browser, with both tools switched on: write minutes for an excerpt of invented transcript 01, then save the minutes as a Word document and the actions table as an Excel file. (Claude was asked for the Excel file in a follow-up message, with a second "Budget" sheet.) The excerpt has two decisions and three actions.

| Measure | Claude Fable 5.2 | Qwen 3.8 27B (local) | Mistral Small 3.2 24B (local) |
| --- | --- | --- | --- |
| Called the Word tool correctly | Yes | Yes | Yes |
| Called the Excel tool correctly | Yes | Yes | Yes |
| Gave working download links | Yes | Yes | Yes |
| Word file: headings, lists, table | All present | All present | All present, but thin |
| Excel file | Two sheets, 18000 stored as a number | One sheet, dates written as 2026-11-18 | One sheet |
| Actions in the files (of 3) | 3 | 3 | 2 (missed Dan's deduplication by 18 November) |
| Showed the minutes in the chat as well | Yes | Yes | No, links only |
| Time from sending to finished | About 30 seconds per request | About 5 minutes | About 6 minutes |

Files were checked by reading them back with the same libraries (headings, list styles, table cells, sheet names, cell types). They were not opened in Word or Excel themselves; Rob should open one of each.

## What this shows

- **Local models can use tools.** Both Qwen and Mistral called two tools in one turn with correct inputs. This was the main doubt, since tool use is where smaller models often fail.
- **The content of the file is only as good as the model.** Mistral's Word file was well formed but left out an action, the same weakness seen in step 4.
- **Tools are quick to write once you know the pattern.** Each file is about 100 lines.

## Problems and limits

- **Documentation gap.** The Open WebUI docs explain tool structure well but do not say how a tool should give the user a file. The working method (calling Open WebUI's internal upload function) came from reading its source code inside the container. Internal functions can change between versions, so this could break on an update.
- **Only one file shows as an attachment.** When a model makes two files in one reply, the attachment shown above the reply is the last one only. Both links in the text of the reply work.
- **Tools do not run through the API the way they do in the browser.** A plain API request returns the model's tool request without running it. So this step was tested in the browser, driven by Claude's built-in browser.
- **A new tool does not appear until the page is reloaded.**
- **Tools must be switched on.** Either per chat (the + button, then Tools), per model by an administrator, or with a link such as `http://localhost:3000/?tool-ids=export_word,export_excel`.
- **Simple formatting only.** No house template, logo, page numbers or styles. Dates in Excel stay as text. A branded Alchemmy template would be the obvious next improvement and python-docx supports it.
- **Tools run with full access inside the Open WebUI container.** Fine for a single-user spike. For Phase 2, who may add or edit tools needs to be restricted to administrators and logged.
- **Not tested:** clicking the download link in a normal browser session and opening the files in Word and Excel; long documents; one run per model.

## Checked against current documentation

Open WebUI tool docs read on 2026-11-14 (docs.openwebui.com, Tools and Tool development pages), version 0.13.3 running. Native function calling is the default mode and was used.
