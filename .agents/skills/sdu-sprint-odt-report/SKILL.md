---
name: sdu-sprint-odt-report
description: Generates plain-language, step-by-step ODT walkthrough reports for SDU Help Desk Bot sprints (e.g. "create the Sprint 3 ODT", "make a step-by-step report for this sprint", "I need the walkthrough document with screenshot instructions"). Use this skill whenever the user asks for a sprint implementation report in ODT format that explains spreadsheet user-story cells in plain language, shows how each requirement was implemented on the Buda platform, explains how to demonstrate it to a teacher, and tells the reader exactly what to screenshot. Trigger this even if the user just says "make the walkthrough doc" or "give me the ODT for this sprint" without repeating the full format description — they mean this exact format, established in a prior sprint.
---

# SDU Sprint ODT Report Generator

Produces an ODT file that explains a sprint's implementation to a non-technical reader
(a teacher), one spreadsheet cell at a time, with explicit instructions on what to
screenshot and where. This format was established for Sprint 2 (US-03/US-04) after
several rounds of user feedback — follow it exactly unless the user asks for a change.

## The exact format (do not deviate without asking)

Every "step" in the document follows this fixed sequence:

1. **Exact spreadsheet quote** — cell reference (e.g. `US-03 ! A7`) + the verbatim text
   from the project spreadsheet. Never paraphrase this.
2. **HOW IT WAS IMPLEMENTED** — plain-language description of the real file, folder, or
   SOUL.md rule that satisfies this cell. Must reference something that actually exists —
   never describe a feature that wasn't really built.
3. **HOW TO SHOW THE TEACHER** — a concrete live action (ask the bot X in Telegram, open
   file Y in the Drive tab) that proves the implementation works.
4. **📷 SCREENSHOT THIS** — tells the reader exactly what to capture and why it proves the
   step. This is the whole point of the document: the user takes real screenshots and
   pastes them in manually, so be specific (not "take a screenshot of the result").
5. **"This same step also already covers:"** — a bullet list cross-referencing test
   scripts / QA scenarios / QA rules from the same user story's QA sheet that this exact
   same implementation already satisfies, so nothing gets explained twice.

A short primer section (Section 0) comes first, explaining — for a reader with zero
platform knowledge — that Telegram is just the front door, SOUL.md is the agent's
rulebook, and `knowledge_base/`/`documents/manifest.json` (or whatever the sprint's
equivalent files are) are the facts the bot is allowed to use. Keep this primer short
(a few short subsections, 1-2 screenshots) — it only needs to repeat once per document,
not once per sprint if the user is generating a whole series and already has the primer
memorized (ask them if they want it trimmed for later sprints).

End with a short, honest "known gaps" section if any requirement could not be fully
implemented — call it out plainly instead of hiding it, same as Sprint 2's "petition
forms are not available anywhere" gap.

**Tone:** plain language, no fluff, no restating the same fact twice. Group tightly
related constraints into a single step when they're implemented by the same mechanism
(see `sprint2_reference_example.py` Step 7, which groups two constraints together).
Don't inflate the step count — one step per responsibility/constraint/QA-scenario that
actually needs its own explanation, not one step per spreadsheet row.

## How to generate the document

1. **Gather real source material before writing anything.** Re-download the project
   spreadsheet fresh (do not reuse a stale local copy) and dump the exact cells for the
   relevant user story + QA sheets. Read the actual files that were built for this sprint
   (SOUL.md sections, knowledge_base files, manifests, etc.) so every "implemented" claim
   points to something real.
2. **Copy `scripts/sprint2_reference_example.py`** to a working file for the new sprint
   (e.g. `/agent/sdu-helpdesk-bot/writeup/sprint3_data.py`). This is the real Sprint 2 data
   previously delivered to the user — use it as the fidelity bar and structural reference.
   Read `scripts/steps_template.py` for the annotated schema if anything is unclear.
3. **Fill in `DOCUMENT`** with the new sprint's real stories/steps, following the schema
   exactly. Keep the primer section unless the user says to drop/trim it for a later sprint
   in the series.
4. **Run the generator:**
   ```
   python3 /agent/.agents/skills/sdu-sprint-odt-report/scripts/build_sprint_odt.py \
       /path/to/sprintN_data.py \
       /agent/sdu-helpdesk-bot/writeup/SDU_HelpDesk_SprintN_StepByStep.odt
   ```
5. **Verify before delivering** — load the generated ODT back with odfpy and check:
   - It loads without error.
   - Every spreadsheet quote you intended to include is actually present (grep for a
     distinctive fragment of each).
   - No now-stale claims leaked in (e.g. don't claim something "is not documented" if a
     later check showed it actually is — see Known Pitfalls below).
   - Screenshot marker count matches the number of `screenshots` entries you wrote.
   A short verification script pattern:
   ```python
   from odf.opendocument import load
   import odf.teletype as teletype
   doc = load(path)
   texts = []
   def walk(node):
       for child in node.childNodes:
           tag = child.qname[1] if hasattr(child, 'qname') else None
           if tag in ('h', 'p'):
               texts.append(teletype.extractText(child))
           if hasattr(child, 'childNodes'):
               walk(child)
   walk(doc.text)
   full = '\n'.join(texts)
   ```
   (Walk `doc.text.childNodes` recursively rather than `doc.getElementsByType(H/P)`
   separately — the latter loses document order when concatenated, making it look like
   content is missing/misplaced when it isn't. This caused a false alarm during this
   skill's own creation; see Known Pitfalls.)
6. **Deliver** via the send-file script, same as any other file.

## Regenerating only part of an existing ODT (when the user already has one open with pasted screenshots)

If the user has an in-progress ODT with real screenshots already pasted into earlier
sections, and asks to fix/regenerate only a later section, do NOT regenerate the whole
file top to bottom — that would discard their pasted images. Instead:

1. Ask the user to attach their current ODT file.
2. Unzip it (`unzip file.odt -d extracted/`) and locate the exact byte offset in
   `extracted/content.xml` where the target section's heading starts (search for a
   unique fragment of that heading's text, then find the nearest preceding `<text:h`).
3. Generate a **separate, full** ODT via this skill's script containing the corrected
   content (easiest to reason about — do not try to hand-edit XML for complex prose).
4. Extract that new ODT's `content.xml`, isolate the equivalent section's XML fragment,
   and splice it into the original file's XML in place of the stale section — keep
   everything before the target section byte-for-byte from the original.
5. Before splicing, confirm the two files share identical custom style names (true if
   both were generated by this same script) so no missing-style errors occur. Check
   whether the "replacement" fragment references any image frames — if the stale section
   had no pasted screenshots yet (common, since it's "ahead" of where the user has
   gotten to), there should be no frames to preserve/lose in that part.
6. Re-zip (`mimetype` must be the first entry, stored uncompressed... in practice,
   `zip -r -X` on the extracted folder works fine for this use case) and reload with
   odfpy to confirm the spliced file is still valid before delivering.

## Known pitfalls (learned from building Sprint 2's reports)

- **Don't let an "undocumented" claim go stale.** When an SOUL.md/knowledge_base rule
  says "X is not documented," re-check that claim against the ACTUAL current state of the
  knowledge base before reusing it in a new sprint's report — a later authorization or
  content addition can make an old "not available" claim factually wrong. This happened
  with a tuition installment-plan example that became outdated once a regulation PDF was
  authorized that covered discounts. Always re-verify "not covered" claims against the
  live files, don't just reuse old wording.
- **Verify document text with document-order traversal, not separate type queries.**
  `doc.getElementsByType(H) + doc.getElementsByType(P)` then joining does NOT preserve
  true reading order — it can make correctly-ordered content look broken. Walk
  `doc.text.childNodes` recursively instead.
- **Every list-type field in the data (`code_blocks`, `quotes`, `screenshots`, `covered`)
  needs ALL its real entries, not just the first.** A single missing list entry silently
  drops content with no error — always diff the rendered text against your source
  material cell-by-cell before delivering.
- **Keep prose scoped to what the user actually asked about.** If a user corrects the
  scope mid-project (e.g. "this report should only cover US-03/US-04, not US-01/US-02"),
  remove the out-of-scope sections entirely and renumber headings/figures — don't just
  add a disclaimer.
