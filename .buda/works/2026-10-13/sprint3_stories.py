"""Sprint 3 stories: US-05 (Multilingual NLP Understanding), US-06 (Automatic Query Classification).
story_text is copied verbatim from the master 'user-stories' sheet (verified by script after build)."""

STORIES = [
    {
        "id": "US-05",
        "title": "Multilingual NLP Understanding",
        "story_text": (
            "Multilingual NLP Understanding: As a Student, I want to ask questions in Kazakh, "
            "Russian, or English with colloquial terms and typos, so that the bot understands my "
            "intent and replies naturally in my preferred language."
        ),
        "stakeholders": "Student",
        "responsibilities": [
            "Detect whether each student message is written in Kazakh, Russian, or English and reply in that same language.",
            "Interpret colloquial wording, slang, abbreviations, and common typos and map them to the correct existing help desk topic.",
            "Answer from the existing English knowledge_base/ files and present the facts in the student's language without changing numbers, dates, contacts, URLs, or the cited source.",
            "Provide Kazakh and Russian versions of the fixed bot messages: the 4-topic menu, the out-of-scope fallback, and the retry/error notice.",
            "Reply to messages in any other language with a short English notice listing the three supported languages and the topic menu.",
        ],
        "constraints": [
            "Language detection, understanding, and translation must run through Buda agent prompt rules in SOUL.md within the same reply, without an external translation or NLP service.",
            "The English knowledge_base/ files remain the only content source; translated copies of knowledge-base files must not be created.",
            "If a message with typos or slang cannot be understood with confidence, the bot must ask the student to rephrase in the same language instead of guessing a topic.",
        ],
        "tags": "Volatility = Medium, Priority = High, Effort = HCHV (6/10), Sprint = 3",
        "test_scripts": [
            "System: (Pass) Student asks a documented question in Kazakh (e.g. \"Оқу ақысын қашан төлеу керек?\") and receives a correct Kazakh answer with the original source cited.",
            "System: (Pass) Student asks in colloquial Russian with a typo (e.g. \"какие доки нужны для обшаги?\") and the bot resolves the dormitory topic and replies in Russian.",
            "System: (Pass) Student asks in slang English with typos (e.g. \"wen do i hav to pay tuishn\") and the bot answers from the tuition topic.",
            "System: (Fail) Student writes in Russian or Kazakh and the bot replies in English or in the wrong language.",
            "System: (Fail) A translated answer changes a number, date, phone number, e-mail, or URL compared with the English source file.",
            "System: (Deferred) Messages typed in Latin letters (e.g. \"oplata za semestr\") or mixing two languages are understood only partially.",
        ],
        "maintenance": [
            "Task (New): Replace the English-only language rule in SOUL.md with a three-language rule (reply language, unsupported-language notice).",
            "Task (New): Add approved Kazakh and Russian wording for the menu, out-of-scope fallback, and retry notice to SOUL.md so these messages are not improvised.",
            "Task (New): Add common Kazakh and Russian keyword variants (e.g. \"оплата\", \"жатақхана\", \"общага\") to the keywords lists in the knowledge_base/ front-matter.",
            "Task (New): Prepare at least five test questions per language for each topic, including typos and slang, and verify the replies in a real Telegram chat; ask a native Kazakh speaker to review the Kazakh replies.",
        ],
        "scenarios": [
            {
                "name": "Kazakh question receives a Kazakh answer",
                "steps": [
                    ("Given", "The knowledge-base file for the topic is written in English."),
                    ("When", "The student asks a documented question in Kazakh."),
                    ("Then", "The bot replies in Kazakh with the same facts as the English answer."),
                    ("And", "The reply cites the same official source as the English answer."),
                ],
            },
            {
                "name": "Colloquial Russian with typos resolves to the right topic",
                "steps": [
                    ("Given", "The student writes in informal Russian using slang and a spelling mistake."),
                    ("When", "The message clearly refers to one help desk topic."),
                    ("Then", "The bot identifies the intended topic."),
                    ("And", "The bot replies in Russian with the answer for that topic."),
                ],
            },
            {
                "name": "English slang and typos resolve to the right topic",
                "steps": [
                    ("Given", "The student writes informal English with misspelled words."),
                    ("When", "The message clearly refers to one help desk topic."),
                    ("Then", "The bot answers from that topic without asking the student to retype the question."),
                ],
            },
            {
                "name": "Facts stay identical after translation",
                "steps": [
                    ("Given", "The English source answer contains numbers, dates, phone numbers, e-mails, or URLs."),
                    ("When", "The bot presents that answer in Kazakh or Russian."),
                    ("Then", "Every number, date, contact, and URL matches the English source exactly."),
                    ("And", "The reply contains no fact that is absent from the source file."),
                ],
            },
            {
                "name": "Reply language follows the student's latest message",
                "steps": [
                    ("Given", "The student has been chatting in Russian."),
                    ("When", "The student writes the next question in Kazakh or English."),
                    ("Then", "The bot switches to the language of that latest message."),
                    ("And", "A language-neutral input such as a menu number keeps the language of the previous message."),
                ],
            },
            {
                "name": "Unsupported language receives a supported-language notice",
                "steps": [
                    ("Given", "The student writes in a language other than Kazakh, Russian, or English."),
                    ("When", "The bot detects the unsupported language."),
                    ("Then", "The bot replies in English that Kazakh, Russian, and English are supported."),
                    ("And", "The reply shows the 4-topic menu."),
                ],
            },
            {
                "name": "Menu and fixed notices are shown in the student's language",
                "steps": [
                    ("Given", "The student is writing in Kazakh or Russian."),
                    ("When", "The student asks something outside the 4 topics or requests the menu."),
                    ("Then", "The out-of-scope notice and the topic menu appear in that language."),
                    ("And", "The menu numbers 1-4 still work as shortcuts."),
                ],
            },
        ],
        "rules": [
            "The bot must support exactly three languages: Kazakh, Russian, and English.",
            "The reply language must match the language of the student's most recent message.",
            "Numbers, dates, contacts, URLs, and cited sources must match the English knowledge-base file exactly.",
            "Translated knowledge-base copies must not exist; the English files remain the single source.",
            "Messages that cannot be understood with confidence must lead to a request to rephrase, not a guessed topic.",
            "Language handling must run through SOUL.md prompt rules without an external translation service.",
        ],
    },
    {
        "id": "US-06",
        "title": "Automatic Query Classification",
        "story_text": (
            "Automatic Query Classification: As an Advisor, I want incoming student questions "
            "automatically categorized (e.g., Tuition, Add/Drop, Regulations, Campus Services), so "
            "that inquiry trends and recurring student issues are tracked."
        ),
        "stakeholders": "Advisor",
        "responsibilities": [
            "Assign each student question to one primary category: Tuition, Add/Drop, Regulations, or Campus Services (dormitory and transcripts/Student Service Center), or to \"Other / Not covered\" when it fits none.",
            "Classify by meaning, so that shortcut triggers and free-form questions, in any supported language, receive the same category label for the same issue.",
            "Record every classified question in a query log file in the agent's Drive with timestamp, category, question language, outcome (answered or not covered), and a short question summary.",
            "Perform classification and logging silently in the same turn, without showing the label to the student or delaying the reply.",
        ],
        "constraints": [
            "Classification and logging must run through Buda agent prompt rules in SOUL.md and a Drive file write, without an external classifier, database, or server.",
            "The category list and its mapping to the knowledge_base/ folders must be defined in one place in the agent's Drive, and the labels must be stored in English so later reports use identical names.",
            "The log must not contain student names, IIN, passwords, bank card details, or other sensitive data; only a short neutral summary of the question is stored.",
            "The log must stay in the agent's Drive and must never be sent into a student chat (advisor-level access control is handled separately in US-07).",
        ],
        "tags": "Volatility = Low, Priority = High, Effort = LCHV (4/10), Sprint = 3",
        "test_scripts": [
            "System: (Pass) Student asks a tuition question and the bot replies normally while one log record with category Tuition, timestamp, language, and outcome is added.",
            "System: (Pass) The same issue is asked once in Kazakh and once in English and both records carry the same English category label.",
            "System: (Pass) Student asks an unrelated question and the record is stored as Other / Not covered with outcome not covered.",
            "System: (Fail) A dormitory question is logged under Tuition, or a question is stored without any category.",
            "System: (Fail) The log file cannot be written and the student receives no reply or an error message about logging.",
            "System: (Deferred) A question that mixes two topics is counted only under its primary category, so the second topic is missing from the trend data.",
        ],
        "maintenance": [
            "Task (New): Define the category list and mapping in one Drive file (Tuition = tuition/, Add/Drop = registration/, Regulations = academic_regulations/, Campus Services = dormitory/ and transcripts/).",
            "Task (New): Create the query log file in the Drive with a header row for timestamp, category, language, outcome, and summary.",
            "Task (New): Add the silent classification and logging rules to SOUL.md and extend its file-access rule, which currently allows only knowledge_base/ and documents/manifest.json, to permit appending to the query log.",
            "Task (New): Test at least five questions per category in Kazakh, Russian, and English in a real Telegram chat and compare each new log row with the expected label.",
        ],
        "scenarios": [
            {
                "name": "Free-form question is classified and logged",
                "steps": [
                    ("Given", "The query log file exists in the agent's Drive."),
                    ("When", "The student asks a free-form question about tuition."),
                    ("Then", "The bot replies normally and one new log record with category Tuition is added."),
                    ("And", "The record contains timestamp, language, outcome, and a short summary."),
                ],
            },
            {
                "name": "Shortcut and free-form questions get the same category",
                "steps": [
                    ("Given", "A student sends the dormitory shortcut and another student asks a free-form dormitory question."),
                    ("When", "Both messages are logged."),
                    ("Then", "Both records carry the category Campus Services."),
                ],
            },
            {
                "name": "The same issue in different languages is counted together",
                "steps": [
                    ("Given", "Two students ask about the same issue, one in Kazakh and one in English."),
                    ("When", "Both questions are classified."),
                    ("Then", "Both records use the same English category label."),
                    ("And", "The language field shows the language each student used."),
                ],
            },
            {
                "name": "Out-of-scope question is logged as not covered",
                "steps": [
                    ("Given", "A student asks a question outside the 4 topics and the knowledge base."),
                    ("When", "The bot gives the out-of-scope reply."),
                    ("Then", "A record with category Other / Not covered is added."),
                    ("And", "The outcome field marks the question as not covered so recurring gaps can be spotted."),
                ],
            },
            {
                "name": "Personal data is kept out of the log",
                "steps": [
                    ("Given", "A student includes a name or an IIN in the question."),
                    ("When", "The bot writes the log record."),
                    ("Then", "The summary describes the question neutrally and contains no name or IIN."),
                ],
            },
            {
                "name": "Logging never blocks or changes the student's reply",
                "steps": [
                    ("Given", "The query log file is temporarily unavailable."),
                    ("When", "The student asks a documented question."),
                    ("Then", "The student still receives the normal answer."),
                    ("And", "The reply contains no category label and no mention of logging."),
                ],
            },
        ],
        "rules": [
            "Each student question must receive exactly one primary category from the agreed list, or Other / Not covered.",
            "Category labels must be stored in English regardless of the question language.",
            "Each log record must contain timestamp, category, language, outcome, and a short summary without personal data.",
            "Greetings and menu requests must not be logged as student questions.",
            "Classification and logging must be invisible to the student and must not block or delay the reply.",
            "The log must stay in the agent's Drive, never be sent into a student chat, and be written through SOUL.md prompt rules without an external service.",
        ],
    },
]
