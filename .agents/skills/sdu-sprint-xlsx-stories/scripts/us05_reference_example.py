"""
Worked reference example for build_story_xlsx.py — US-05 "Automatic Query
Classification," used only to prove the generator produces a correct xlsx and
to show what a non-duplicative, Buda-grounded story looks like in practice.

This is a DEMONSTRATION story, not a real delivered one for this project —
when writing a real new sprint's stories, replace this file's content with
the user's actual next user story, verified against the live spreadsheet and
against what was really built, exactly like every other document in this
project.
"""

STORIES = [
    {
        "id": "US-05",
        "title": "Automatic Query Classification",
        "story_text": (
            "Automatic Query Classification: As a Student, I want the bot to "
            "automatically detect which help desk topic my free-form question "
            "belongs to, so that I get the right answer even when I don't use "
            "the exact menu keyword or number."
        ),
        "stakeholders": "Student",
        "responsibilities": [
            "Classify a free-form student question into one of the existing "
            "knowledge_base/ categories (tuition, registration, dormitory, "
            "transcripts, academic_regulations) using the agent's own "
            "reasoning, without requiring an exact keyword match.",
            "Fall back to the US-03 out-of-scope response when the question "
            "does not clearly belong to any existing category, instead of "
            "guessing a category.",
            "Reuse the existing per-category knowledge_base/*.md files as the "
            "only source of truth for the matched category's answer — "
            "classification decides WHICH file to read, it does not introduce "
            "a new content source.",
        ],
        "constraints": [
            "Classification must run as part of the same SOUL.md-driven agent "
            "reasoning used for every other reply; it must not require a "
            "separate hosted classifier service or external ML API.",
            "A low-confidence classification must trigger the US-03 "
            "safe-failure response rather than an incorrect topic answer.",
        ],
        "tags": "Volatility = Medium, Priority = High, Effort = LCHV (5/10), Sprint = 3",
        "test_scripts": [
            "System: (Pass) Student asks a free-form question with no menu "
            "keyword (e.g. \"when do I need to pay this semester\") and the "
            "bot classifies it as tuition and answers from tuition_fees.md.",
            "System: (Pass) Student asks a question that mixes two topics "
            "(e.g. \"do I need to pay before I can register for next "
            "semester\") and the bot asks a clarifying question instead of "
            "guessing one category.",
            "System: (Fail) Student asks a vague question with no clear topic "
            "signal (e.g. \"can you help me\") and the bot incorrectly "
            "guesses a specific category instead of showing the menu.",
            "System: (Deferred) Classification accuracy degrades for "
            "very short, single-word questions typed without context.",
        ],
        "maintenance": [
            "Task (New): Add classification guidance to SOUL.md describing "
            "how free-form questions map to the existing knowledge_base/ "
            "category folders.",
            "Task (New): Define the exact clarifying-question wording for "
            "ambiguous multi-topic questions.",
            "Task (Verified): Test classification against a list of real "
            "paraphrased student questions per category and confirm each "
            "resolves to the correct knowledge_base/ file.",
        ],
        "scenarios": [
            {
                "name": "Free-form question resolves to the correct topic",
                "steps": [
                    ("Given", "The student has an active Telegram chat with "
                              "the bot."),
                    ("When", "The student asks a free-form question that "
                              "clearly relates to one topic without using "
                              "its menu keyword."),
                    ("Then", "The bot answers using the matching "
                              "knowledge_base/ category's file."),
                    ("And", "The response cites the same source it would "
                             "have cited via the US-02 menu/keyword path."),
                ],
            },
            {
                "name": "Keyword and free-form phrasing resolve identically",
                "steps": [
                    ("Given", "A topic has both a US-02 menu keyword and "
                              "several natural free-form phrasings."),
                    ("When", "The student asks the same underlying question "
                              "once via the keyword and once via free-form "
                              "phrasing in a separate message."),
                    ("Then", "Both messages resolve to the same "
                              "knowledge_base/ category."),
                ],
            },
            {
                "name": "Ambiguous multi-topic question triggers clarification",
                "steps": [
                    ("Given", "A student question contains signals for more "
                              "than one knowledge_base/ category."),
                    ("When", "The bot cannot confidently pick a single "
                              "category."),
                    ("Then", "The bot asks a short clarifying question "
                              "instead of answering from a guessed category."),
                ],
            },
            {
                "name": "No clear topic falls back to the menu",
                "steps": [
                    ("Given", "A student question has no identifiable "
                              "connection to any existing category."),
                    ("When", "The bot classifies the question as "
                              "out-of-scope."),
                    ("Then", "The bot returns the same US-03 safe-failure "
                              "response and re-shows the 4-topic menu."),
                ],
            },
            {
                "name": "Classification never bypasses the knowledge base",
                "steps": [
                    ("Given", "A question is successfully classified into a "
                              "category."),
                    ("When", "The bot generates its answer."),
                    ("Then", "The answer content still comes only from that "
                              "category's knowledge_base/*.md file, not from "
                              "the model's general knowledge."),
                ],
            },
        ],
        "rules": [
            "Classification must only choose among the existing "
            "knowledge_base/ categories, never introduce an undefined one.",
            "Low-confidence or multi-topic questions must trigger "
            "clarification or the US-03 fallback, never a guessed answer.",
            "Classification must run inside the existing SOUL.md agent "
            "reasoning, not a separate hosted classifier.",
            "A correctly classified question must be answered using the "
            "same knowledge_base/ grounding rules established in US-03.",
        ],
    },
]
