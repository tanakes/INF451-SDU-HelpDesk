"""Sprint 3 (US-05 + US-06) walkthrough data. Quotes are read straight from the project workbook
so they are verbatim; implementation claims point at files that exist in /agent/sdu-helpdesk-bot."""
import openpyxl

_WB = openpyxl.load_workbook("/agent/.buda/works/2026-10-13/new_sheet.xlsx", data_only=True)


def cell(sheet, ref):
    v = _WB[sheet][ref].value
    assert v, (sheet, ref)
    return str(v).strip()


def q(sheet, ref):
    return {"ref": f"{sheet} ! {ref}", "text": cell(sheet, ref)}


def scen(sheet, n, row):
    """QA scenario cover line: scenario number + its name (cell B of the Scenario row)."""
    return f'{sheet} Scenario {n}: "{cell(sheet, "B" + str(row))}"'


def rule(sheet, ref):
    return f'{sheet} Rule {ref}: "{cell(sheet, ref)}"'


def test(sheet, ref):
    return f'Test script {ref}: "{cell(sheet, ref)}"'


US05 = {
    "heading": "1. US-05 — Multilingual NLP Understanding",
    "intro_quotes": [q("US-05", "A3")],
    "intro_body": [
        "In plain words: a student may write in Kazakh, Russian, or English — with slang and spelling "
        "mistakes — and the bot must understand what they mean and answer in the same language, "
        "without changing a single fact from the official English documents.",
        "Before this sprint the bot was strictly English-only. The main change is therefore a "
        "rewrite of the language rules in SOUL.md plus small additions to the knowledge-base files.",
    ],
    "steps": [
        {
            "heading": "Step 1 — Detect the language and reply in it (Responsibility A5, Constraint A11)",
            "quotes": [q("US-05", "A5"), q("US-05", "A11")],
            "implemented": (
                "The old rule \"Language Scope (English Only)\" in SOUL.md Core Truths was removed. In its place "
                "SOUL.md now says the bot supports exactly three languages — Kazakh, Russian, English — and must "
                "reply in the language of the student's most recent message (new Section 6.A). Because the rule "
                "lives in SOUL.md, the AI model itself detects the language in the same turn it writes the "
                "reply; no translation service, server, or extra tool exists. A menu number such as \"3\" keeps "
                "the language of the previous message, and a student who switches language is followed."
            ),
            "demonstrate": (
                "In Telegram, ask a question in Russian, then a second question in Kazakh, then in English. "
                "Show that each answer comes back in the language of that question. Then send \"3\" right "
                "after a Russian message and show the answer stays Russian."
            ),
            "screenshots": [
                "SOUL.md open in the Drive tab, scrolled to \"6. US-05: Multilingual NLP Understanding\", "
                "section A (\"Language Detection and Reply Language\").",
                "One Telegram chat showing three consecutive questions (Russian, Kazakh, English) and three "
                "replies in the matching languages.",
            ],
            "covered": [
                "Maintenance A24 (New): \"" + cell("US-05", "A24") + "\"",
                scen("US-05-QA", 5, 29),
                rule("US-05-QA", "B49"),
                rule("US-05-QA", "B48"),
                rule("US-05-QA", "B53"),
                test("US-05", "A20") + " — this is the failure case; the rule above exists to prevent it.",
            ],
        },
        {
            "heading": "Step 2 — Understand slang, abbreviations, and typos (Responsibility A6, Constraint A13)",
            "quotes": [q("US-05", "A6"), q("US-05", "A13")],
            "implemented": (
                "SOUL.md Section 6.B tells the bot to interpret wording by meaning, not by exact words, and "
                "gives worked examples taken from the test scripts (\"wen do i hav to pay tuishn\", "
                "\"какие доки нужны для обшаги?\", \"оқу ақысын қашан төлеу керек?\"). It also contains the "
                "safety rule from Constraint A13: when the bot cannot tell with confidence which topic is "
                "meant, it must not guess — it asks the student, in the same language, to rephrase "
                "(approved English, Russian, and Kazakh wording is written into SOUL.md). In addition, the "
                "keywords list at the top of each of the four category files now also contains common Russian "
                "and Kazakh words (for example \"оплата\", \"общага\", \"жатақхана\", \"транскрипт\"), so the "
                "quick shortcuts work in all three languages."
            ),
            "demonstrate": (
                "Send \"wen do i hav to pay tuishn\" and \"какие доки нужны для обшаги?\" in Telegram and show "
                "that each reaches the correct topic. Then send a deliberately unclear message such as "
                "\"asdf the thing??\" and show the polite \"please rephrase\" reply instead of a guessed answer."
            ),
            "screenshots": [
                "Telegram: the slang-English tuition question and its correct answer.",
                "Telegram: the Russian dormitory question with the typo and its Russian answer.",
                "The first lines (front-matter) of knowledge_base/dormitory/dormitory.md in the Drive tab, "
                "showing the keywords list that now includes \"общежитие\", \"общага\", \"жатақхана\".",
            ],
            "covered": [
                test("US-05", "A18"),
                test("US-05", "A19"),
                "Maintenance A26 (New): \"" + cell("US-05", "A26") + "\"",
                scen("US-05-QA", 2, 12),
                scen("US-05-QA", 3, 18),
                rule("US-05-QA", "B52"),
            ],
        },
        {
            "heading": "Step 3 — Answer from the English documents without changing any fact (Responsibility A7, Constraint A12)",
            "quotes": [q("US-05", "A7"), q("US-05", "A12")],
            "implemented": (
                "No translated copy of any knowledge-base file was created — the English files remain the "
                "only source. SOUL.md Section 6.C gives the bot a fixed procedure: find the facts in the "
                "English file exactly as before, then present them in the student's language while copying "
                "every number, date, time, phone number, e-mail address, URL, ECTS count, percentage, and "
                "name exactly as written in the source. The bot also translates the word \"Source\" "
                "(\"Источник:\" / \"Дереккөз:\") but keeps the URL or regulation code unchanged, so the "
                "citation rule from Sprint 2 still holds in every language."
            ),
            "demonstrate": (
                "Ask the same question in English and in Kazakh (for example the tuition payment question). "
                "Place the two answers side by side and point at the numbers, dates and the source line: they "
                "are identical. Then open the knowledge_base folder and show that there is no Kazakh or "
                "Russian copy of any file."
            ),
            "screenshots": [
                "Telegram: the same question answered in English and in Kazakh, both visible in one "
                "screenshot, with the matching numbers/dates/source line clearly readable.",
                "Drive tab: the knowledge_base/ folder tree showing only the original English files.",
            ],
            "covered": [
                test("US-05", "A17"),
                test("US-05", "A21") + " — this is the failure case; the exact-copy rule above exists to prevent it.",
                scen("US-05-QA", 1, 6),
                scen("US-05-QA", 4, 23),
                rule("US-05-QA", "B50"),
                rule("US-05-QA", "B51"),
            ],
        },
        {
            "heading": "Step 4 — Kazakh and Russian versions of the fixed messages (Responsibility A8)",
            "quotes": [q("US-05", "A8"), q("US-05", "A25")],
            "implemented": (
                "SOUL.md Section 6.C now contains approved Russian and Kazakh wording for the four fixed "
                "messages: the 4-topic menu, the out-of-scope notice, the \"not in my knowledge base\" "
                "notice, and the retry/error notice (plus the \"please rephrase\" request). Writing the exact "
                "text into SOUL.md means the bot does not improvise these messages. The menu numbers 1–4 "
                "work exactly as before. The old English retry notice in the Core Truths now points to the "
                "Russian or Kazakh version when the chat is in that language."
            ),
            "demonstrate": (
                "In a Kazakh chat send \"menu\" (or \"мәзір\") and show the Kazakh menu; then ask something "
                "unrelated such as \"what is the weather\" in Russian and show the Russian out-of-scope notice. "
                "Finally send \"2\" and show it still works as a shortcut."
            ),
            "screenshots": [
                "Telegram: the Russian menu and the Kazakh menu (two screenshots, or one combined).",
                "Telegram: the Russian out-of-scope notice.",
                "SOUL.md, Section 6.C, showing the block of approved Russian and Kazakh messages.",
            ],
            "covered": [
                scen("US-05-QA", 7, 41),
            ],
        },
        {
            "heading": "Step 5 — Politely handle any other language (Responsibility A9)",
            "quotes": [q("US-05", "A9")],
            "implemented": (
                "SOUL.md Section 6.D defines the reply for an unsupported language: a short English notice "
                "saying that Kazakh, Russian, and English are supported, followed by the 4-topic menu. This "
                "replaces the old sentence \"Currently, I can only assist in English\", which would now be wrong."
            ),
            "demonstrate": "Send a short message in another language (for example German or Turkish) and show the English notice with the menu.",
            "screenshots": [
                "Telegram: the unsupported-language message and the bot's English notice with the menu.",
            ],
            "covered": [
                scen("US-05-QA", 6, 35),
            ],
        },
        {
            "heading": "Step 6 — Test with real questions in Telegram (Maintenance A27)",
            "quotes": [q("US-05", "A27")],
            "implemented": (
                "The test questions in this document come straight from the story's test scripts (A17–A19) "
                "and the rules above. The configuration is finished; the live Telegram run is the part you "
                "do and screenshot. Please also ask a native Kazakh speaker to read the Kazakh messages in "
                "SOUL.md Section 6.C and the Kazakh answers — see the honest-gaps section at the end."
            ),
            "demonstrate": (
                "Use the table in the screenshots below as a checklist: for each of the four topics ask at "
                "least one question in each language, including one with a typo, and tick off the result."
            ),
            "screenshots": [
                "A simple checklist (a table in any note or this document) with topics as rows and "
                "Kazakh / Russian / English as columns, filled in after you tried each question.",
            ],
            "covered": [],
        },
    ],
}

US06 = {
    "heading": "2. US-06 — Automatic Query Classification",
    "intro_quotes": [q("US-06", "A3")],
    "intro_body": [
        "In plain words: every time a student asks something, the bot quietly files the question under "
        "one topic label and writes one line into a log that advisors can open later. The student "
        "never sees any of this — they only get their normal answer.",
        "Real files were added for this: a small category definition file, a log file, and two small Python "
        "helpers (standard library only): one appends a line to the log safely, the other turns the log into "
        "a short plain-text summary that a non-technical person can read. SOUL.md tells the bot when and how "
        "to call the first one.",
    ],
    "steps": [
        {
            "heading": "Step 1 — One agreed list of categories (Responsibility A5, Constraint A11)",
            "quotes": [q("US-06", "A5"), q("US-06", "A11"), q("US-06", "A24")],
            "implemented": (
                "The file sdu-helpdesk-bot/query_log/categories.json is the single place where the category list "
                "is defined. It holds five English labels — Tuition, Add/Drop, Regulations, Campus Services, "
                "Other / Not covered — and, for each label, which knowledge_base/ folders belong to it "
                "(Tuition = tuition/, Add/Drop = registration/, Regulations = academic_regulations/, "
                "Campus Services = dormitory/ + transcripts/). It also lists the allowed languages and outcomes. "
                "SOUL.md Section 7.A repeats the labels so the bot picks exactly one of them, and the helper "
                "script rejects any label that is not in this file."
            ),
            "demonstrate": "Open categories.json in the Drive tab and walk through the five labels and their folders.",
            "screenshots": [
                "Drive tab: sdu-helpdesk-bot/query_log/categories.json opened, showing the five labels and their \"maps_to\" folders.",
            ],
            "covered": [
                rule("US-06-QA", "B41"),
                rule("US-06-QA", "B42"),
                test("US-06", "A20") + " — this is the failure case; the fixed label list and the script's validation prevent a missing or invented category.",
            ],
        },
        {
            "heading": "Step 2 — Classify by meaning, in any language (Responsibility A6)",
            "quotes": [q("US-06", "A6")],
            "implemented": (
                "SOUL.md Section 7.A tells the bot to choose the category by meaning, so that a shortcut "
                "(\"3\", \"dorm\") and a free-form question about the same topic get the same label, and the "
                "same issue asked in Kazakh and in English gets the same English label. A question that mixes "
                "two topics is counted under its primary topic only. A topical question that the knowledge base "
                "cannot answer (for example installments) keeps its topic label with the outcome \"not covered\"."
            ),
            "demonstrate": (
                "Ask the same tuition question once in Kazakh and once in English, then open query_log.csv "
                "and show that both rows have category Tuition and different language values."
            ),
            "screenshots": [
                "The query_log.csv file in the Drive tab with the two rows (same category, languages Kazakh and English).",
            ],
            "covered": [
                test("US-06", "A18"),
                scen("US-06-QA", 2, 12),
                scen("US-06-QA", 3, 17),
                test("US-06", "A22") + " — marked Deferred: a mixed-topic question is stored under its primary topic only.",
            ],
        },
        {
            "heading": "Step 3 — Record every question in a log (Responsibility A7)",
            "quotes": [q("US-06", "A7"), q("US-06", "A25")],
            "implemented": (
                "The file sdu-helpdesk-bot/query_log/query_log.csv was created with a header row "
                "(timestamp_utc, category, language, outcome, summary). After preparing each reply the bot runs "
                "the helper script sdu-helpdesk-bot/query_log/log_query.py, which adds exactly one row. The "
                "timestamp is created by the script, not typed by the AI. The outcome is \"answered\" when the "
                "knowledge base answered, or \"not covered\" when the bot said the information is not available, "
                "gave the out-of-scope notice, or asked to rephrase. Greetings and menu requests are not logged "
                "(SOUL.md Section 7.B). Unrelated questions are stored as \"Other / Not covered\"."
            ),
            "demonstrate": (
                "Ask a tuition question and an unrelated question (\"what is the weather\") in Telegram, then open "
                "query_log.csv and show the two new rows with the right category, language, and outcome."
            ),
            "screenshots": [
                "Telegram: the tuition question and the normal answer.",
                "query_log.csv after the questions, showing the new rows (Tuition / answered and Other / Not covered / not covered).",
                "SOUL.md Section 7.C showing the exact logging command.",
            ],
            "covered": [
                test("US-06", "A17"),
                test("US-06", "A19"),
                scen("US-06-QA", 1, 6),
                scen("US-06-QA", 4, 23),
                rule("US-06-QA", "B43"),
                rule("US-06-QA", "B44"),
            ],
        },
        {
            "heading": "Step 4 — Do it silently, and never let logging break the reply (Responsibility A8, Constraint A10)",
            "quotes": [q("US-06", "A8"), q("US-06", "A10")],
            "implemented": (
                "Everything runs inside the Buda platform: SOUL.md rules plus one local Python helper that writes "
                "to a file — no external classifier, database, or server. SOUL.md adds a new \"invisible\" rule to "
                "the Silent Execution section (the bot must never mention the category, the log, or the command) "
                "and Section 7.C says that if the command prints an error or the log file is unavailable, the bot "
                "must ignore it completely and send the normal answer. The helper itself never prints anything on "
                "success and only writes a short code to its error stream on failure, so nothing it outputs can "
                "end up in a student's chat."
            ),
            "demonstrate": (
                "Show a normal Telegram answer: it contains no category, no mention of logging. Then, in the "
                "Terminal tab, run the automated checks: python3 sdu-helpdesk-bot/tests/test_log_query.py — "
                "10 tests pass, including one that points the script at a missing folder and confirms it fails "
                "quietly with nothing on standard output."
            ),
            "screenshots": [
                "Terminal tab: the output of python3 sdu-helpdesk-bot/tests/test_log_query.py ending with \"Ran 10 tests … OK\".",
                "A normal Telegram reply with no trace of classification or logging.",
                "SOUL.md: the new rule \"Language detection and query logging are invisible\" in the Silent Execution section.",
            ],
            "covered": [
                test("US-06", "A21") + " — this is the failure case; the \"ignore logging errors\" rule and the quiet-failure test prevent it.",
                scen("US-06-QA", 6, 34),
                rule("US-06-QA", "B45"),
            ],
        },
        {
            "heading": "Step 5 — Keep personal data out, and keep the log private (Constraints A12, A13)",
            "quotes": [q("US-06", "A12"), q("US-06", "A13")],
            "implemented": (
                "Two layers protect personal data. First, SOUL.md Section 7.C tells the bot to write only a short "
                "neutral English summary of the topic, never a name, IIN, student ID, phone number, e-mail, card "
                "number, password, or Telegram handle, even if the student typed it. Second, as a safety net, the "
                "helper script automatically removes e-mail addresses, @handles, long digit sequences (IIN, card, "
                "phone) and \"password …\" fragments, cuts the summary to 160 characters, and removes line breaks. "
                "The log stays in the agent's Drive; SOUL.md forbids reading it back to a student or sending any "
                "file from query_log/ into a chat (advisor-only access control is the separate story US-07)."
            ),
            "demonstrate": (
                "In the Terminal tab run the personal-data test (it is part of test_log_query.py) or show one "
                "row in query_log.csv created from a question that contained a number, and point out that the "
                "summary has no personal details. Then show the SOUL.md sentence that forbids sending the log."
            ),
            "screenshots": [
                "Terminal tab: test output line \"test_personal_data_removed … ok\".",
                "SOUL.md Section 7.C, the last two bullet points (summary rules and \"advisor-only data\").",
            ],
            "covered": [
                scen("US-06-QA", 5, 29),
                rule("US-06-QA", "B46"),
            ],
        },
        {
            "heading": "Step 6 — SOUL.md rules and the live check (Maintenance A26, A27)",
            "quotes": [q("US-06", "A26"), q("US-06", "A27")],
            "implemented": (
                "The silent classification and logging rules were added to SOUL.md (new Section 7). The old "
                "file-access rule that allowed only knowledge_base/ and documents/manifest.json now makes one "
                "explicit exception for the logging command, and nothing else. The configuration is finished; "
                "the live check across languages is the part you do and screenshot."
            ),
            "demonstrate": (
                "Ask at least one question per category (Tuition, Add/Drop, Regulations, Campus Services) in each "
                "language, then open query_log.csv and compare every new row with the label you expected."
            ),
            "screenshots": [
                "query_log.csv showing at least one row for each of the four categories, in different languages.",
                "SOUL.md Core Truths item 4 showing the sentence about the one allowed logging command.",
            ],
            "covered": [],
        },
        {
            "heading": "Step 7 — Make the log readable for non-technical people (addition, not a separate spreadsheet cell)",
            "quotes": [],
            "implemented": (
                "This step adds no new spreadsheet requirement. It exists because the purpose of the story, in its "
                "own words, is that \"inquiry trends and recurring student issues are tracked\" (US-06 ! A3), and a "
                "raw CSV file is not something an advisor or administrator will open. The helper "
                "sdu-helpdesk-bot/query_log/summarize_log.py reads query_log.csv (it never changes it) and prints a "
                "short report: number of questions, how many were answered or not covered, questions per category and "
                "per language, and the most frequent questions the bot could not answer. Identical wording is counted "
                "together, and the report can be limited to a date range (--since) or saved to a file (--out). It has "
                "its own 7 automated tests. For the pilot, the project team runs it and hands the report to the "
                "stakeholders; letting advisors open it themselves needs access control (US-07) and a proper view "
                "(US-10, US-14)."
            ),
            "demonstrate": (
                "In the Terminal tab run: python3 sdu-helpdesk-bot/query_log/summarize_log.py — after a few "
                "questions have been asked in Telegram, it prints the summary. Point at the \"could not answer\" "
                "list: it shows which topics are missing from the knowledge base. Then run "
                "python3 sdu-helpdesk-bot/tests/test_summarize_log.py to show its checks pass."
            ),
            "screenshots": [
                "Terminal tab: the printed summary report (categories, languages, answered vs not covered, list of unanswered questions).",
                "Terminal tab: test_summarize_log.py ending with \"Ran 7 tests … OK\".",
            ],
            "covered": [
                "Story purpose (US-06 ! A3): \"so that inquiry trends and recurring student issues are tracked.\"",
            ],
        },
    ],
}

STAKEHOLDERS = {
    "heading": "3. How Sprint 3 helps the stakeholders (the teacher's question about adoption)",
    "intro_quotes": [],
    "intro_body": [
        "The teacher asked how this prototype becomes something university staff adopt and trust. The short "
        "answer: SDU staff are not meant to configure Buda themselves. In the pilot, the project team acts as the "
        "implementation team and maintainer; students use only Telegram; staff get simple, non-technical "
        "touchpoints. Those touchpoints are built across Sprints 3–7, so each sprint must be explained by what "
        "it gives the stakeholders. Sprint 3 contributes the following.",
        "• Student Service Center advisors and staff: US-06 now shows what students actually ask, in which "
        "language, and which questions the bot could not answer — with a readable summary (US-06 Step 7). "
        "Repeated unanswered questions are the clearest list of what to add to the knowledge base next.",
        "• Students: US-05 lets them write in Kazakh, Russian, or English, with slang and typos, and get an "
        "answer in the same language with the same cited facts. No app and no login — still only Telegram.",
        "• University leadership and IT: grounding and the citation rule stay unchanged in every language, "
        "personal data is kept out of the log (checked by automated tests), and the whole feature runs on "
        "SOUL.md rules plus two small local scripts — no new external service or database to approve or pay for.",
        "• What the next sprints add on top of this (from the project backlog): Sprint 4 restricts who can see "
        "advisor information (US-07); Sprint 5 adds escalation tickets and an advisor queue (US-09, US-10); "
        "Sprint 6 lets advisors update the knowledge base without touching code (US-11) and collects student "
        "ratings (US-12); Sprint 7 adds deadline reminders and management reports (US-13, US-14).",
        "• What Sprint 3 does NOT yet do: advisors cannot open the summary by themselves, nobody is access-"
        "controlled, and there is no measured saving of staff time yet. The log is what will make such "
        "numbers measurable later; we do not claim figures such as a percentage of questions deflected until "
        "real pilot data exists.",
    ],
    "steps": [],
}

DOCUMENT = {
    "title": "SDU Help Desk Bot — Sprint 3 Walkthrough",
    "subtitle": (
        "A plain-language, step-by-step guide to how US-05 (Multilingual NLP Understanding) and "
        "US-06 (Automatic Query Classification) were built on the Buda platform — "
        "with exact screenshot instructions."
    ),
    "intro_bullets_intro": [
        "This document explains Sprint 3 from scratch, assuming no prior knowledge of how the Buda AI "
        "agent platform works. Each numbered step follows the same pattern:",
    ],
    "intro_bullets": [
        "The exact task we had to satisfy (quoted directly from the project spreadsheet).",
        "What we actually built or changed, in plain words.",
        "How to prove it works live, in front of the teacher.",
        "Exactly which screen or file to screenshot, and why that screenshot matters.",
    ],
    "intro_outro": [
        "First, a short primer on how the bot works at all, since everything else refers back to these pieces.",
    ],
    "primer": {
        "heading": "0. How the Buda bot actually works (read this first)",
        "subsections": [
            {
                "heading": "0.1 — Telegram is just the \"front door\"",
                "body": [
                    "Buda has a built-in connector that links an agent directly to a Telegram bot account. "
                    "Students type messages in Telegram; Buda forwards them to the agent and sends the agent's "
                    "reply back. No custom server was written for this.",
                ],
            },
            {
                "heading": "0.2 — SOUL.md is the agent's \"brain\" / rulebook",
                "body": [
                    "SOUL.md is a plain-text file in the agent's Drive, written in normal English. The AI reads it "
                    "before answering any message — think of it as the employee handbook the bot has to follow. "
                    "In Sprint 3 it gained two new sections: Section 6 (languages) and Section 7 (silent "
                    "classification and logging).",
                ],
                "screenshots": [
                    "Open SOUL.md in the Drive tab so the file is visible on screen. You will reuse this open "
                    "file for several steps below — just scroll to the relevant part each time.",
                ],
            },
            {
                "heading": "0.3 — The files the bot uses",
                "body": [
                    "knowledge_base/ and documents/manifest.json are the facts the bot may use (unchanged facts; "
                    "only the shortcut keyword lists gained Russian and Kazakh words). New in Sprint 3 is the folder "
                    "query_log/ with four files: categories.json (the label list), query_log.csv (the log), "
                    "log_query.py (appends one safe line to the log), and summarize_log.py (turns the log into a "
                    "readable report). A tests/ folder holds automated checks for both helpers.",
                ],
                "screenshots": [
                    "Drive tab: the sdu-helpdesk-bot folder showing knowledge_base/, documents/, query_log/ "
                    "(with its four files), and tests/.",
                ],
            },
        ],
        "closing": [
            "With that primer done, the rest of this document walks through each user story exactly as it is "
            "written in the project spreadsheet, cell by cell.",
        ],
    },
    "stories": [US05, US06, STAKEHOLDERS],
    "closing_section": {
        "heading": "4. Honest gaps worth mentioning to the teacher",
        "body": [
            "• Kazakh wording has not been reviewed by a native speaker. The Kazakh menu and notices in SOUL.md "
            "Section 6.C were written carefully but should be checked (this is part of the story's own maintenance "
            "task A27). The bot's Kazakh answers can also contain small grammar slips.",
            "• Language understanding and classification are done by the AI model following SOUL.md, so they are "
            "not 100% deterministic. Only the log writing itself (the Python helper) is deterministic and covered "
            "by automated tests; the choice of label and language is judged by the model each time. This is why "
            "the live Telegram check in US-05 Step 6 and US-06 Step 6 matters.",
            "• Test scripts marked Deferred in the spreadsheet stay deferred: text typed in Latin letters or mixing "
            "two languages (US-05 A22) is understood only on a best-effort basis, and a question that mixes two "
            "topics is counted under its primary topic only (US-06 A22).",
            "• Anyone who can open the Drive can open query_log.csv. Restricting the log to authorized advisors "
            "is the separate story US-07 (Sprint 4); US-06 only guarantees the bot never shows or sends the log "
            "to students.",
            "• The readable summary (US-06 Step 7) is run by the project team from the Terminal during the pilot. "
            "Self-service for advisors (their own login, a ticket queue, management reports) is planned in Sprints 4, "
            "5 and 7 and does not exist yet.",
        ],
        "screenshots": [
            "SOUL.md Section 6.B showing the sentence about best-effort handling of Latin-letter and mixed-language messages.",
        ],
    },
}
