"""
Data template for build_sprint_odt.py.

This file is a fully worked EXAMPLE (Sprint 2: US-03 + US-04) showing the
exact schema expected by the builder script. When writing a new sprint's
walkthrough, copy this file, keep the same top-level shape, and replace
the content with that sprint's real spreadsheet cells and real
implementation details.

Rules for filling this in for a new sprint (do not skip these):
1. Every `quotes` entry must be copied VERBATIM from the project
   spreadsheet (cell reference + exact text) — never paraphrase.
2. Every `implemented` string must point to a REAL file/rule that was
   actually built (e.g. an exact SOUL.md sentence, an exact file/folder
   path, an exact manifest field) — never describe a feature that
   wasn't actually implemented.
3. Every `screenshots` entry must tell the user EXACTLY what to open and
   why that screenshot proves the step — not a vague "take a screenshot
   of the result".
4. Use `covered` to cross-reference test scripts / QA scenarios / QA
   rules from the SAME user story's QA sheet that this exact step also
   satisfies — do not re-explain them from scratch, just list them.
5. Keep prose plain-language, no fluff, no restating the same fact twice.
6. Do not inflate step count — only create a step per responsibility/
   constraint/QA-scenario that needs its own explanation. Group tightly
   related constraints into one step if they're implemented by the same
   mechanism (see "Step 7" below for an example of grouping A13+A14).
"""

DOCUMENT = {
    "title": "SDU Help Desk Bot — Sprint 2 Walkthrough",
    "subtitle": (
        "A plain-language, step-by-step guide to how US-03 (Knowledge Base) and "
        "US-04 (Document & Guide Dispatch) were built on the Buda platform — "
        "with exact screenshot instructions."
    ),
    "intro_bullets_intro": [
        "This document explains this sprint from scratch, assuming no prior knowledge of how "
        "the Buda AI agent platform works. Each numbered step follows the same pattern:",
    ],
    "intro_bullets": [
        "The exact task we had to satisfy (quoted directly from the project spreadsheet).",
        "What we actually built or changed, in plain words.",
        "How to prove it works live, in front of the teacher.",
        "Exactly which screen or file to screenshot, and why that screenshot matters.",
    ],
    "intro_outro": [
        "First, a 2-minute primer on how the bot works at all, since everything else in this "
        "document refers back to these pieces.",
    ],

    "primer": {
        "heading": "0. How the Buda bot actually works (read this first)",
        "subsections": [
            {
                "heading": "0.1 — Telegram is just the \"front door\"",
                "body": [
                    "Buda has a built-in connector that links an agent directly to a Telegram "
                    "bot account. Students type messages in Telegram; Buda forwards them to "
                    "the agent and sends the agent's reply back. No custom server was written "
                    "for this — it is a built-in feature of the platform, turned on in the "
                    "agent's settings.",
                ],
            },
            {
                "heading": "0.2 — SOUL.md is the agent's \"brain\" / rulebook",
                "body": [
                    "SOUL.md is a plain-text file that lives in the agent's Drive. It is not "
                    "code — it is written in normal English, as a set of instructions the AI "
                    "reads before answering any message. Think of it as the employee handbook "
                    "the bot has to follow.",
                ],
                "screenshots": [
                    "Open SOUL.md in the Drive tab so the file is visible on screen. You will "
                    "reuse this same open file for several steps below — just scroll to the "
                    "relevant part each time.",
                ],
            },
            {
                "heading": "0.3 — knowledge_base/ and documents/manifest.json are the "
                           "\"facts\" the bot is allowed to use",
                "body": [
                    "These are regular files and folders sitting in the agent's Drive, exactly "
                    "like files in a normal folder on your computer. SOUL.md tells the bot: "
                    "\"only use facts from these specific files, never make something up.\"",
                ],
                "screenshots": [
                    "Open the Drive tab and show the folder tree: sdu-helpdesk-bot/"
                    "knowledge_base/ and sdu-helpdesk-bot/documents/manifest.json.",
                ],
            },
        ],
        "closing": [
            "With that primer done, the rest of this document walks through each user story "
            "exactly as it is written in the project spreadsheet, cell by cell.",
        ],
    },

    "stories": [
        {
            "heading": "1. US-03 — University Knowledge Base Setup",
            "intro_quotes": [
                {"ref": "US-03 ! A3", "text": (
                    "University Knowledge Base Setup: As a Student, I want the bot to answer "
                    "common questions regarding tuition, registration, and academic policies, "
                    "so that I receive immediate, accurate guidance based on official "
                    "university rules."
                )},
            ],
            "intro_body": [
                "In plain words: the bot must answer from real SDU documents, not from "
                "guesses, and the university must have a say in which documents it is allowed "
                "to use.",
            ],
            "steps": [
                {
                    "heading": "Step 1 — Collect the official documents (Responsibility A5)",
                    "quotes": [
                        {"ref": "US-03 ! A5", "text": (
                            "Collect official SDU documents covering the agreed help desk "
                            "categories: tuition fees, course add/drop, dormitory, transcripts "
                            "and academic regulations."
                        )},
                    ],
                    "implemented": (
                        "We pulled real content from the official SDU website for the 4 "
                        "everyday topics, and collected 32 official SDU regulation PDFs that "
                        "the project team provided."
                    ),
                    "demonstrate": (
                        "Open the Drive tab, go into sdu-helpdesk-bot/knowledge_base/, and show "
                        "the 5 category folders."
                    ),
                    "screenshots": [
                        "The knowledge_base/ folder with all 5 category folders visible.",
                    ],
                },
            ],
        },
    ],

    "closing_section": {
        "heading": "3. One honest gap worth mentioning to the teacher",
        "body": [
            "Example closing-section pattern: use this to flag anything that genuinely isn't "
            "implemented yet, instead of hiding it. Keep it brief and honest.",
        ],
        "screenshots": [
            "A screenshot proving the gap is documented, e.g. the relevant manifest entry's "
            "reason field.",
        ],
    },
}
