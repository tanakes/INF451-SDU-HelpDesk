"""
Annotated schema template for build_story_xlsx.py.

Copy this file for each new sprint's stories, replace the example STORIES list
with real content, then run:
    python3 build_story_xlsx.py sprintN_stories.py SprintN_UserStories.xlsx

Each dict in STORIES produces TWO worksheets: "<id>" (the user story sheet)
and "<id>-QA" (the QA sheet), matching the real project spreadsheet's
US-01/US-01-QA and US-02/US-02-QA tabs exactly.

------------------------------------------------------------------------------
FIELD-BY-FIELD RULES
------------------------------------------------------------------------------

id              Short code, e.g. "US-05". Must match the tab name convention
                already used in the spreadsheet (US-01, US-02, ...).

title           Short title before the colon in story_text, e.g.
                "Automatic Query Classification". Used only in the QA sheet's
                A2 header line — keep it word-for-word identical to the title
                inside story_text.

story_text      The FULL "As a <role>, I want <goal>, so that <benefit>"
                sentence, written exactly as it will appear in cell A3 of
                both sheets. Format: "<Title>: As a <role>, I want <goal>,
                so that <benefit>." This is the one sentence everything else
                in both sheets must trace back to — do not let
                responsibilities/constraints/scenarios drift from it.

stakeholders    Short string for cell C3, e.g. "Student" or
                "Student, University Administration / Academic Advisor
                (Authorizing Stakeholder)" (see US-03 for the authorization-
                stakeholder pattern, when a human approval step is involved).

responsibilities
                List of strings, one per bullet under "responsibilities".
                Each one must describe something concretely buildable on the
                Buda platform (see BUDA PLATFORM CAPABILITIES below) — not a
                vague aspiration. Look at real US-01/US-02 responsibilities
                for the right grain size: one clear, testable capability per
                line, phrased as an action ("Provide...", "Map...",
                "Return...", "Connect...").

constraints     List of strings, one per bullet under "constraints". These
                are the hard boundaries/non-functional rules — what the
                solution MUST or MUST NOT do structurally. Good constraints
                name a concrete mechanism (e.g. "must use Buda agent prompts,
                not a custom Telegram Bot API server") so they are testable,
                not vague principles.

tags            Single string for the one tags line, formatted exactly like
                the real sheets: "Volatility = Low, Priority = High, Effort =
                LCHV (3/10), Sprint = N". Keep the same vocabulary
                (Volatility: Low/Medium/High; Priority: Low/Medium/High;
                Effort: a short code + /10 score; Sprint: the sprint number).

test_scripts    List of strings, one per row under "test scripts". Format:
                "System: (Pass|Fail|Deferred) <scenario description>".
                Include at least one Pass, one Fail, and ideally one Deferred
                case, same as the real sheets. These should map 1:1 to
                failure/edge modes a Buda agent can actually hit (prompt
                misfires, missing knowledge-base file, channel disconnect,
                rate limits) — not generic "server crashes" scenarios that
                don't apply to a serverless agent architecture.

maintenance     List of strings, one per row under "maintenance". Format:
                "Task (New|Verified): <task description>". These are the
                concrete setup/configuration/verification chores a human
                does on the Buda dashboard (SOUL.md edits, Drive uploads,
                channel settings) — not generic SDLC filler.

scenarios       List of dicts, each with:
                  "name": short scenario label (string, goes in column B
                          next to "Scenario N")
                  "steps": list of (label, text) tuples, label is one of
                           "Given" / "When" / "Then" / "And". Use "And" for
                           any step after the first Given/When/Then of its
                           kind, exactly like the real sheet (see US-02-QA
                           Scenario 1's "And" row after "Then").
                Aim for 5-7 scenarios per story: the real US-02-QA has 6,
                covering the happy path, a variation/fuzzy-match path, an
                unrecognized-input fallback, a rendering/formatting check,
                and a failure/error-handling check. Use that spread as the
                default shape unless the story's responsibilities suggest a
                different one.

rules           List of strings, one per "Rule" row at the bottom of the QA
                sheet. Each rule should restate one constraint or
                responsibility as a single testable sentence — same
                information as above, just in rule form for a tester to tick
                off quickly. Don't invent new requirements only here that
                aren't already in responsibilities/constraints.

------------------------------------------------------------------------------
AVOIDING DUPLICATE COVERAGE ACROSS SPRINTS (read this before writing anything)
------------------------------------------------------------------------------

Before drafting a new story, re-read every PREVIOUS story's responsibilities,
constraints, test_scripts, and QA rules in the real spreadsheet. If a new
story's draft responsibility is already fully satisfied by something built in
an earlier sprint, do NOT restate it as a new responsibility — either drop it,
or if the new story genuinely builds on it, phrase it as something NEW the
earlier mechanism now needs to additionally support (don't just copy the old
sentence into a new tab).

Known already-covered ground as of Sprint 3 (do not re-litigate these in a
new story unless you are genuinely changing them):
  - Telegram channel connection, session continuity              -> US-01
  - Topic menu, quick keyword triggers, Telegram-safe formatting -> US-02
  - Grounding answers in knowledge_base/ files, out-of-scope
    fallback, academic-year currency, stakeholder authorization
    gate for restricted documents                                -> US-03
  - Link/file/unavailable dispatch via documents/manifest.json   -> US-04
  - Kazakh/Russian/English detection and replies, slang/typo
    understanding, exact-fact translation, fixed messages in
    three languages, unsupported-language notice               -> US-05
  - Silent classification into 5 English labels, advisor query
    log (query_log/), personal-data stripping, log never shown
    to students, logging failure never blocks a reply          -> US-06

If a new story's natural QA scenario is "the bot still only answers from the
knowledge base" or "the bot still formats cleanly on Telegram," that is
redundant with US-02/US-03 and should be left out — cross-reference it in
your sprint ODT walkthrough's "covered" field instead of re-testing it here.

------------------------------------------------------------------------------
BUDA PLATFORM CAPABILITIES (ground every story in something real)
------------------------------------------------------------------------------

Only write responsibilities/constraints that map to a real Buda capability.
As used in this project so far:
  - Native Telegram Channel connector (BotFather token, per-chat-ID session)
  - SOUL.md as the agent's natural-language rulebook (persona, grounding
    rules, formatting rules, dispatch rules) — no custom backend code
  - Drive-based knowledge_base/*.md files with YAML front-matter as the
    single source of truth for both menu triggers and deep answers
  - documents/manifest.json as a declarative link/file/unavailable dispatch
    table, read and acted on by the agent per SOUL.md rules
  - deliver_to_channel-style file dispatch for sending real PDFs/files into
    a chat, as opposed to just text
  - Memory files (MEMORY.md, memory/YYYY-MM-DD.md) for persistent context
    across sessions, if a future story needs the bot to remember something
    about a specific returning student within privacy limits
  - Scheduled automations (cron/interval tasks) if a future story needs
    proactive, time-based behavior (e.g. "remind students before a tuition
    deadline") rather than only reactive replies
  - Multi-step agent reasoning/tool calls, but NOT a custom database, NOT a
    separately hosted server, NOT a vector DB/RAG pipeline unless the
    project has actually set one up — don't invent infrastructure Buda
    doesn't natively provide and this project hasn't built.

If a prospective responsibility needs infrastructure beyond this list (e.g.
"integrate with the official student information system API to pull live
grades"), flag that explicitly as a stretch/future item rather than writing
it as if it is buildable today — the real project's "known gaps" sections
(see e.g. petition-form unavailability in Sprint 2) are the right place for
that kind of honesty, not a QA sheet that pretends it works.

------------------------------------------------------------------------------
"""

STORIES = [
    {
        "id": "US-EXAMPLE",
        "title": "Example Story Title",
        "story_text": (
            "Example Story Title: As a Student, I want an example capability, "
            "so that I get an example benefit."
        ),
        "stakeholders": "Student",
        "responsibilities": [
            "Describe one concrete, buildable capability here.",
            "Describe a second one here.",
        ],
        "constraints": [
            "Name a concrete platform mechanism boundary here.",
        ],
        "tags": "Volatility = Low, Priority = Medium, Effort = LCHV (3/10), Sprint = N",
        "test_scripts": [
            "System: (Pass) Describe the happy-path test here.",
            "System: (Fail) Describe a realistic failure mode here.",
            "System: (Deferred) Describe a known-deferred edge case here.",
        ],
        "maintenance": [
            "Task (New): Describe a setup/configuration chore here.",
            "Task (Verified): Describe a verification chore here.",
        ],
        "scenarios": [
            {
                "name": "Happy path example",
                "steps": [
                    ("Given", "Some precondition."),
                    ("When", "The student does something."),
                    ("Then", "The expected result happens."),
                ],
            },
        ],
        "rules": [
            "Restate one constraint/responsibility as a single testable rule.",
        ],
    },
]
