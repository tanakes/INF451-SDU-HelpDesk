---
name: sdu-sprint-xlsx-stories
description: Generates copy-paste-ready xlsx user-story and QA sheets for future SDU Help Desk Bot sprints (e.g. "generate the xlsx for US-05", "make the user story and QA sheet for the next sprint", "I need a spreadsheet tab I can paste into the project sheet"). Use this skill whenever the user asks for a new user story + QA test sheet in the exact format already used by US-01/US-01-QA and US-02/US-02-QA in the project spreadsheet. Trigger even if they just say "make the next sprint's story sheet" without repeating the full format — they mean this exact layout.
---

# SDU Sprint xlsx Story + QA Generator

Produces an `.xlsx` file with one "user story" worksheet and one matching
"QA" worksheet per story, laid out cell-for-cell like the real project
spreadsheet's **US-01/US-01-QA** and **US-02/US-02-QA** tabs — the two sheets
the user has confirmed are good examples. The user copy-pastes the generated
tabs into the canonical Google Sheet (no live Sheets write access exists from
this environment).

**Do not use US-03/US-03-QA or US-04/US-04-QA as a format reference.** The
user has flagged these as weak (written by a teammate without full context
of the bot, with scenarios that duplicate US-01/US-02). Use them only as a
reminder of what NOT to repeat — never as a structural template.

## Exact sheet layout (verified against the live spreadsheet)

**User story sheet** (one per story, tab name = story ID, e.g. `US-05`):

| Cell | Content |
|---|---|
| A2 | `"User Story"` (header) |
| C2 | `Stakeholders:` (header) |
| A3 | Full story text: `<Title>: As a <role>, I want <goal>, so that <benefit>.` |
| C3 | Stakeholder(s), e.g. `Student` |
| A4 | `responsibilities` (section header) |
| A5... | One responsibility per row |
| A(n) | `constraints` (section header) |
| A(n+1)... | One constraint per row |
| A(n) | `tags` (section header) |
| A(n+1) | `Volatility = ..., Priority = ..., Effort = ... (x/10), Sprint = N` |
| A(n) | `test scripts` (section header) |
| A(n+1)... | `System: (Pass\|Fail\|Deferred) <description>` |
| A(n) | `maintenance` (section header) |
| A(n+1)... | `Task (New\|Verified): <description>` |

**QA sheet** (tab name = `<story ID>-QA`, e.g. `US-05-QA`):

| Cell | Content |
|---|---|
| A1 | `<ID> QA Tests` |
| A2 | `User Story: <ID> <Title>` |
| A3 | Full story text (same sentence as the story sheet's A3) |
| A5 | `The Given/When/Then Acceptance Criteria` |
| A6/B6 | `Scenario 1` / scenario name |
| A7-.../B7-... | `Given`/`When`/`Then`/`And` rows, one blank row after each scenario |
| A(n) | `Rule-oriented acceptance criteria` |
| A(n+1)...  / B(n+1)... | `Rule` / rule text |

## How to generate a new sprint's sheets

1. **Re-sync the live spreadsheet first** and read every existing story's
   responsibilities, constraints, test_scripts, and QA rules — not just the
   last sprint's. This is required before writing a single new line (see
   anti-duplication rules below).
2. **Copy `scripts/story_schema_template.py`** to a working file for the new
   sprint, e.g. `/agent/sdu-helpdesk-bot/sprint3_stories.py`. Read the
   template's docstring fully — it has the field-by-field rules, the
   anti-duplication checklist, and the Buda-platform-capabilities list.
   Look at `scripts/us05_reference_example.py` for a complete, correctly
   shaped worked example (a demo story, not a real delivered one).
3. **Fill in `STORIES`** with the new, real story/stories for that sprint.
   Each entry becomes two worksheets automatically.
4. **Run:**
   ```
   python3 /agent/.agents/skills/sdu-sprint-xlsx-stories/scripts/build_story_xlsx.py \
       /path/to/sprintN_stories.py \
       /agent/sdu-helpdesk-bot/SprintN_UserStories.xlsx
   ```
5. **Verify before delivering** — reopen with openpyxl and print every cell,
   compare row-by-row against the layout table above, and specifically check:
   - A3 of the story sheet and A3 of the QA sheet contain the identical
     story_text string.
   - No responsibility/constraint/rule duplicates something already fully
     covered by an earlier sprint's sheet (cross-check against the
     "Known already-covered ground" list in the schema template, updating
     that list in the template file itself once a new sprint ships).
   - Every GWT scenario step uses one of exactly `Given`/`When`/`Then`/`And`.
6. Deliver the `.xlsx` via the send-file script. Remind the user it's meant
   to be copy-pasted as new tabs into the canonical Google Sheet, not treated
   as a replacement workbook.

## Anti-duplication is the main point of this skill

The user has explicitly said future sheets must (a) reflect real Buda
platform capabilities and (b) never re-cover ground already handled by an
earlier sprint's sheet. Before adding any responsibility, constraint, test
script, or QA rule, ask: "does an earlier sprint's sheet already guarantee
this?" If yes, leave it out of the new sheet — a later walkthrough document
(see the `sdu-sprint-odt-report` skill) is the right place to cross-reference
it, not a second QA sheet re-testing the same thing.

Keep the "Known already-covered ground" section inside
`scripts/story_schema_template.py` up to date as each new sprint ships, so
the next sprint's generation pass has an accurate list to check against
without re-reading the entire spreadsheet from scratch every time (re-reading
the live sheet is still required as the source of truth, but this list is a
fast first-pass sanity check).

## Grounding in real Buda capabilities

Every responsibility and constraint must map to something the Buda platform
actually does today in this project (native Telegram channel connector,
SOUL.md-driven reasoning, Drive-based knowledge_base/*.md files,
documents/manifest.json dispatch, deliver_to_channel file sends, memory
files, scheduled automations). See the full list and the "don't invent
infrastructure" warning inside `scripts/story_schema_template.py`. If a
story idea needs something beyond that list (e.g. a live SIS/grades API
integration), say so explicitly as a stretch/future item instead of writing
QA scenarios that pretend it already works.

## Known pitfalls

- Don't reuse US-03/US-04's structure or scenario style as a model — they
  are the acknowledged weak examples.
- Don't skip re-syncing the live spreadsheet before drafting — a stale local
  copy can hide what was already covered in a sprint you don't remember in
  full detail.
- Keep story_text byte-for-byte identical between the story sheet's A3 and
  the QA sheet's A3 — the real spreadsheet does this, and the user has
  previously flagged exact-match requirements between sheets as important.
- Don't inflate scenario count. The real US-02-QA has 6 scenarios covering
  happy path, fuzzy-match variation, fallback, formatting, and failure
  handling — use that spread as the default shape, not a fixed number to hit
  mechanically.
