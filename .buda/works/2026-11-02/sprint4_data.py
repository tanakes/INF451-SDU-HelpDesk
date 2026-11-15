"""Sprint 4 (US-07 + US-08) walkthrough data.
Quotes are read straight from the live project workbook so they are verbatim;
implementation claims point at real files in /agent/sdu-helpdesk-bot.
"""
import openpyxl

_WB = openpyxl.load_workbook("/agent/sdu-helpdesk-bot/user-stories.xlsx", data_only=True)


def cell(sheet, ref):
    v = _WB[sheet][ref].value
    assert v is not None, f"Empty cell: {sheet} ! {ref}"
    return str(v).strip()


def q(sheet, ref):
    return {"ref": f"{sheet} ! {ref}", "text": cell(sheet, ref)}


def scen(sheet, n, row):
    return f'{sheet} Scenario {n}: "{cell(sheet, "B" + str(row))}"'


def rule(sheet, ref):
    return f'{sheet} Rule {ref}: "{cell(sheet, ref)}"'


def test(sheet, ref):
    return f'Test script {ref}: "{cell(sheet, ref)}"'


US07 = {
    "heading": "1. US-07 — Advisor Authorization & Multi-Department RBAC Controls",
    "intro_quotes": [q("US-07", "A3")],
    "intro_body": [
        "In plain words: university staff, advisors, and department coordinators need administrative "
        "visibility into incoming student inquiry trends and unanswered questions, while students must "
        "remain completely locked out of internal data and advisor tools.",
        "Instead of asking non-technical university staff to type passwords or maintain fragile lists "
        "of numeric Telegram IDs, Sprint 4 implements Architectural Channel Isolation: a public student "
        "bot for campus Q&A, and a dedicated Staff Advisor Bot locked exclusively inside the authorized "
        "SDU Help Desk private staff group. Direct messages (DMs) to the staff bot are strictly blocked.",
    ],
    "steps": [
        {
            "heading": "Step 1 — Dual-Channel Architectural Separation (Responsibility A5, Constraint A11)",
            "quotes": [q("US-07", "A5"), q("US-07", "A11")],
            "implemented": (
                "Buda's multi-channel architecture is used to bind two separate Telegram bot accounts to the workspace: "
                "the public student bot (@sdu_helpdesk_bot) and the private Helpdesk Staff Bot. Access control is enforced "
                "directly at the channel boundary and in SOUL.md Core Truth #0: public student sessions run purely in "
                "Help Desk Mode with zero administrative tooling, while administrative commands run only within the "
                "private staff group."
            ),
            "demonstrate": (
                "Open the Buda dashboard Settings → Channels. Show the two connected Telegram bots: the public student bot "
                "and the Helpdesk Staff Bot. Show that each channel maps to distinct sessions in Buda."
            ),
            "screenshots": [
                "Buda dashboard Channels tab showing both 'helpdeskbot' (public) and 'Helpdesk Staff Bot' (staff).",
                "SOUL.md Core Truth #0 showing the 'Dual-Channel Separation & Access Control Guard'.",
            ],
            "covered": [
                "Maintenance A24 (New): \"" + cell("US-07", "A24") + "\"",
                rule("US-07-QA", "B37"),
                rule("US-07-QA", "B41"),
            ],
        },
        {
            "heading": "Step 2 — Private Staff Group Command Execution (Responsibility A6, A8)",
            "quotes": [q("US-07", "A6"), q("US-07", "A8")],
            "implemented": (
                "Inside the private SDU Help Desk staff group (chat: -5323769996), the staff bot accepts operational "
                "management triggers: 'summary' / 'stat' runs summarize_log.py and posts live query volumes, category breakdowns, "
                "and top unanswered student questions; 'sessions' reads session_logs/INDEX.md and lists recent active student "
                "conversations. Advisors never have to enter credentials or passwords to perform their daily duties."
            ),
            "demonstrate": (
                "In Telegram, open the authorized private SDU Helpdesk Staff Group. Send 'summary'. Show that the bot "
                "immediately responds with the live department analytics report and top student questions. Then send 'sessions' "
                "to view active student conversations."
            ),
            "screenshots": [
                "Telegram chat in the private SDU Helpdesk Staff Group showing the 'summary' command returning live statistics.",
                "Telegram chat in the staff group showing the 'sessions' command listing active student chat files.",
            ],
            "covered": [
                scen("US-07-QA", 1, 6),
                scen("US-07-QA", 2, 12),
                test("US-07", "A17"),
                test("US-07", "A18"),
                "Maintenance A27 (New): \"" + cell("US-07", "A27") + "\"",
            ],
        },
        {
            "heading": "Step 3 — Direct Message (DM) Security Guard & Access Restriction (Responsibility A7, Constraint A13)",
            "quotes": [q("US-07", "A7"), q("US-07", "A13")],
            "implemented": (
                "To prevent unauthorized students from discovering the staff bot and private-messaging it, SOUL.md enforces "
                "a strict Group-Only Guard: if any user opens a 1-on-1 private DM with the staff bot and sends any message, "
                "the bot immediately returns '🔒 Access Restricted: This advisor bot operates only inside the authorized SDU "
                "Helpdesk Staff Group.' It never shows student greetings, menus, or internal data in private DM."
            ),
            "demonstrate": (
                "In Telegram, open a direct private message (DM) with the Staff Bot. Type 'hi' or 'summary'. Show that the bot "
                "blocks the request and returns the access restricted message."
            ),
            "screenshots": [
                "Telegram private chat with the Staff Bot showing the '🔒 Access Restricted' refusal response.",
                "SOUL.md Case A under Core Truth #0 showing the private DM restriction rule.",
            ],
            "covered": [
                scen("US-07-QA", 4, 24),
                test("US-07", "A21"),
                rule("US-07-QA", "B39"),
            ],
        },
        {
            "heading": "Step 4 — Student Channel Isolation & Silent Rejection (Constraint A12, Rule B38)",
            "quotes": [q("US-07", "A12"), {"ref": "US-07-QA ! B38", "text": cell("US-07-QA", "B38")}],
            "implemented": (
                "In the public student bot (@sdu_helpdesk_bot), if a student sends administrative words like 'summary', 'stat', "
                "or 'admin', the bot treats the message as an out-of-scope student inquiry. It displays the friendly 4-topic "
                "student menu and never reveals the existence of administrative scripts or staff tools."
            ),
            "demonstrate": (
                "In Telegram, open the public student bot. Type 'summary' or 'admin'. Show that the bot responds with the "
                "welcoming student menu and offers help with tuition, registration, and dormitory without disclosing advisor tools."
            ),
            "screenshots": [
                "Telegram chat in the public student bot showing 'summary' resulting in the standard student menu.",
            ],
            "covered": [
                scen("US-07-QA", 3, 18),
                test("US-07", "A20"),
            ],
        },
        {
            "heading": "Step 5 — Departmental Triage & PII Scrubbing (Responsibility A9, Maintenance A25)",
            "quotes": [q("US-07", "A9"), q("US-07", "A25")],
            "implemented": (
                "summarize_log.py was enhanced with a '--category' filter flag, allowing staff to inspect question volumes for a "
                "single department (Tuition, Add/Drop, Regulations, Campus Services). When generating summaries or displaying logs, "
                "all student emails, phone numbers, IINs, and passwords scrubbed during US-06 logging remain excluded, ensuring zero "
                "confidential data leaks to group chats."
            ),
            "demonstrate": (
                "In Terminal, run 'python3 /agent/sdu-helpdesk-bot/query_log/summarize_log.py --category Tuition'. Show the clean, "
                "department-specific summary with PII-free summaries. Run the automated test suite to show passing tests."
            ),
            "screenshots": [
                "Terminal: running summarize_log.py --category Tuition showing the filtered department breakdown.",
                "Terminal: unit test output showing test_category_filter passing.",
            ],
            "covered": [
                scen("US-07-QA", 5, 30),
                test("US-07", "A19"),
                rule("US-07-QA", "B40"),
            ],
        },
    ],
}


US08 = {
    "heading": "2. US-08 — Student Profile Context & Academic Personalization",
    "intro_quotes": [q("US-08", "A3")],
    "intro_body": [
        "In plain words: SDU has distinct academic regulations for undergraduates (Bachelor), graduate students "
        "(Master), and doctoral candidates (PhD), as well as faculty-specific assessment rules (like SSBL Law School). "
        "A student can specify their major and year of study, and the bot remembers it across sessions to tailor all "
        "future academic answers accordingly.",
        "Profile setup is 100% optional: freshmen asking for the campus map or Wi-Fi are never blocked, and students can "
        "switch or reset their profile anytime with 'profile reset'.",
    ],
    "steps": [
        {
            "heading": "Step 1 — Conversational Profile Extraction & Persistence (Responsibility A5, A6)",
            "quotes": [q("US-08", "A5"), q("US-08", "A6")],
            "implemented": (
                "A dedicated profile manager was built at 'profiles/manage_profile.py'. When a student states their degree level, "
                "major, or study year in chat (e.g. 'I am a 1st year Master student in Law'), the bot extracts the degree (Bachelor, "
                "Master, PhD), year (1st-4th), and faculty, saving it to a persistent JSON file under 'profiles/<user_slug>.json'. "
                "The bot confirms the update with a warm acknowledgement."
            ),
            "demonstrate": (
                "In Telegram, send 'I am a 1st year Master student in Law'. Show the bot's confirmation message. Open the Drive tab "
                "at 'sdu-helpdesk-bot/profiles/' and show the generated JSON file with degree, year, and major attributes."
            ),
            "screenshots": [
                "Telegram chat showing the student setting their profile and the bot's confirmation message.",
                "Drive tab: profiles/ folder showing the created user JSON file with structured academic attributes.",
            ],
            "covered": [
                scen("US-08-QA", 1, 6),
                test("US-08", "A17"),
                "Maintenance A24 (New): \"" + cell("US-08", "A24") + "\"",
                rule("US-08-QA", "B36"),
                rule("US-08-QA", "B37"),
            ],
        },
        {
            "heading": "Step 2 — Tailored Academic Regulations by Degree & Major (Responsibility A7, Constraint A11)",
            "quotes": [q("US-08", "A7"), q("US-08", "A11")],
            "implemented": (
                "SOUL.md Section 10 instructs the bot to inspect the active profile before answering academic questions. If the student "
                "is an identified Master's student, the bot cites graduate policies (120 ECTS curriculum, individual scientific research "
                "plans НИРМ/ҒЗЖМ, priority registration window) instead of undergraduate semester rules. If a student is in Law / SSBL, "
                "it references the SSBL School final examination regulations."
            ),
            "demonstrate": (
                "Ask 'How many credits can I register for this semester?' as a Master's student. Show that the bot identifies the "
                "Master's Degree Program, explains the 120 ECTS scientific-pedagogical framework, cites research practice credits, "
                "and provides the priority registration window (>60 ECTS)."
            ),
            "screenshots": [
                "Telegram chat: asking 'How many credits can I register for this semester?' showing the Master-specific answer.",
                "SOUL.md Section 10 showing the degree and faculty regulation mapping rules.",
            ],
            "covered": [
                scen("US-08-QA", 2, 12),
                test("US-08", "A21") + " — prevented by this rule.",
                rule("US-08-QA", "B38"),
                "Maintenance A25 (New): \"" + cell("US-08", "A25") + "\"",
            ],
        },
        {
            "heading": "Step 3 — Zero-Block Default for General Campus Inquiries (Responsibility A9, Constraint A13)",
            "quotes": [q("US-08", "A9"), q("US-08", "A13")],
            "implemented": (
                "Setting an academic profile is strictly optional. General university questions (campus map, lecture halls, Wi-Fi "
                "credentials, dormitory rules, Kaspi payment) answer immediately without ever demanding a student profile, login, or ID."
            ),
            "demonstrate": (
                "In Telegram, ask 'Where is wifi zone?' or 'How to connect to wifi?' without a profile set. Show that the bot answers "
                "immediately with the campus map and network credentials without blocking."
            ),
            "screenshots": [
                "Telegram chat showing an immediate answer to a campus inquiry without any profile prompt.",
            ],
            "covered": [
                scen("US-08-QA", 3, 18),
                test("US-08", "A18"),
                test("US-08", "A20") + " — prevented by this rule.",
                rule("US-08-QA", "B39"),
            ],
        },
        {
            "heading": "Step 4 — Profile Reset & Switching (Responsibility A8)",
            "quotes": [q("US-08", "A8")],
            "implemented": (
                "Students can clear their profile at any time by sending 'profile reset' or 'сбросить профиль'. manage_profile.py deletes "
                "the JSON file from Drive, and subsequent questions immediately revert to standard university-wide regulations."
            ),
            "demonstrate": (
                "In Telegram, send 'profile reset'. The bot confirms: 'Profile reset. Standard university-wide regulations will now apply.' "
                "Ask the credit limit question again and show the standard general answer."
            ),
            "screenshots": [
                "Telegram chat showing 'profile reset' confirmation and the subsequent general answer.",
                "Terminal / Drive: verifying the profile JSON file was cleanly removed.",
            ],
            "covered": [
                scen("US-08-QA", 4, 24),
                test("US-08", "A19"),
            ],
        },
        {
            "heading": "Step 5 — Privacy Protection & PII Scrubbing (Constraint A12, Rule B40)",
            "quotes": [q("US-08", "A12"), {"ref": "US-08-QA ! B40", "text": cell("US-08-QA", "B40")}],
            "implemented": (
                "manage_profile.py defensively sanitizes profile inputs using regex filters: any long numeric runs (such as national IIN "
                "or bank card digits) and password fragments are scrubbed before writing to JSON. Only degree level, study year, and major "
                "are retained."
            ),
            "demonstrate": (
                "Run the automated test 'test_pii_scrubbed_from_profile' in tests/test_manage_profile.py. Show that it passes with "
                "sensitive numbers cleanly redacted."
            ),
            "screenshots": [
                "Terminal: unit test output showing test_pii_scrubbed_from_profile passing.",
                "manage_profile.py code showing REDACT_PATTERNS regex scrubbing.",
            ],
            "covered": [
                scen("US-08-QA", 5, 30),
                "Maintenance A27 (New): \"" + cell("US-08", "A27") + "\"",
            ],
        },
    ],
}


STAKEHOLDERS = {
    "heading": "3. Stakeholder Discovery & Multi-Department Triage Alignment",
    "intro_quotes": [],
    "intro_body": [
        "During team discovery with the SDU Help Desk staff in October 2026, the administration highlighted their single biggest "
        "operational challenge: categorizing and routing student emails and inquiries to the appropriate department (IT Services vs "
        "Medical Center vs Accounting vs Registrar/SSC vs Dormitory).",
        "Sprint 4 directly delivers this university capability:",
        "• Administrative Isolation: University staff use their own private Telegram group for analytics, ensuring sensitive operational "
        "data never leaks to students.",
        "• Multi-Department Filter: summarize_log.py allows staff to isolate ticket volumes and unanswered student questions per department "
        "without technical complexity.",
        "• Personalization without Bureaucracy: Profile context allows the bot to cite specialized school regulations (SSBL Law School, "
        "Master's Research Practice) automatically without asking students to sift through 32 official PDF regulations.",
    ],
    "steps": [],
}


STUDENT_FEEDBACK = {
    "heading": "4. Student Survey Findings & UX Improvements (Beyond the Spreadsheet)",
    "intro_quotes": [],
    "intro_body": [
        "In addition to implementing the spreadsheet user stories, our team conducted hands-on hallway testing and gathered direct "
        "feedback from SDU students who tested the bot live on Telegram. This user feedback uncovered critical UX flaws and resulted "
        "in immediate improvements to the conversational flow, knowledge base, and mobile rendering.",
    ],
    "steps": [
        {
            "heading": "Step 1 — Shifting from Restrictive Menus to Open-Ended Inquiries",
            "quotes": [],
            "implemented": (
                "Student Survey Finding: When a student asked an uncatalogued question like 'Where is H canteen?', the bot previously replied: "
                "'📌 I can currently only assist with our 4 quick topics below. Please select a topic from the menu: 1. Tuition Fees, 2. Course Add/Drop...'. "
                "Real session logs revealed that students interpreted this as a strict restriction, believing they were forbidden from asking their own questions "
                "and were forced to only pick 1 to 4 (the user immediately stopped asking questions and just typed '1' and '2').\n\n"
                "Solution: All welcome prompts, fallbacks, and out-of-scope notices across English, Russian, and Kazakh in SOUL.md were rewritten. "
                "The bot now explicitly encourages open-ended questions first ('Feel free to ask me any question about university life, studies, payments, "
                "documents, and campus services!'), mentioning the 4 topics merely as secondary quick-start examples."
            ),
            "demonstrate": (
                "In Telegram, ask a campus question outside the 4 topics (e.g. 'Where is H canteen?'). Show that the bot no longer claims it can only assist "
                "with 4 topics; it answers warmly and offers helpful navigation guidance."
            ),
            "screenshots": [
                "Session transcript or chat showing the previous restrictive message where the student felt blocked.",
                "Telegram chat showing the new open-ended welcoming prompt and conversational out-of-scope response.",
            ],
            "covered": [],
        },
        {
            "heading": "Step 2 — Knowledge Base Expansion: SDU Wi-Fi & Freedom Wi-Fi",
            "quotes": [],
            "implemented": (
                "Student Request: Students frequently ask how to connect to the campus internet. We added a comprehensive Wi-Fi guide to the "
                "knowledge base ('knowledge_base/campus_services/campus_wifi.md') based on the official SDU Student Services portal (https://sdu.edu.kz/en/student-services/):\n"
                "• Explains enterprise WPA2 authentication: students log in using their personal Moodle username and password.\n"
                "• Documents all campus SSIDs: SDU_WiFi (academic blocks), SDU_Dorm (Student House), Eduroam (academic roaming), and SDU_Guest / Freedom Wi-Fi.\n"
                "• SDU SSO Password Reset: Includes direct link to https://password.sdu.edu.kz, which synchronizes passwords across Wi-Fi, Moodle, and Office 365."
            ),
            "demonstrate": (
                "In Telegram, ask 'How to connect to wifi?' or 'Какой пароль от вайфая?'. Show the bot explaining Moodle credential login and password.sdu.edu.kz."
            ),
            "screenshots": [
                "Telegram chat showing the detailed Wi-Fi setup and Moodle credential instructions.",
                "Drive tab: showing knowledge_base/campus_services/campus_wifi.md.",
            ],
            "covered": [],
        },
        {
            "heading": "Step 3 — Campus Layout Map Dispatch & 'Бочки' Lecture Hall Navigation",
            "quotes": [],
            "implemented": (
                "Student Navigation Need: SDU campus has unique naming conventions, including large amphitheater lecture halls known as 'Бочки' (A1 to D2). "
                "Students often get lost trying to match schedule codes (e.g. D117, D218) to physical rooms.\n"
                "• Added 'knowledge_base/campus_services/campus_map_and_cabinets.md' mapping all schedule codes to cabinet numbers (A1=D117, A2=D218, B1=D116, "
                "B2=D217, C1=D113, C2=D214, D1=E117, D2=E221) and landmarks (Main Entrance, Advisor Desk, Red Canteen).\n"
                "• Integrated the SDU Campus Layout Map ('documents/assets/SDU_map.jpg' registered in documents/manifest.json). The bot automatically dispatches "
                "the visual map directly into Telegram whenever students ask for locations, noting that it covers Blocks A–H (with Block I as a recent addition)."
            ),
            "demonstrate": (
                "In Telegram, ask 'Where is bochka C1?' or 'Где находится D117?'. Show the bot identifying the hall, floor, landmark, and dispatching the map."
            ),
            "screenshots": [
                "Telegram chat showing the bot sending the SDU Campus Layout Map and explaining lecture hall cabinet locations.",
                "Drive tab: showing documents/assets/SDU_map.jpg and campus_map_and_cabinets.md.",
            ],
            "covered": [],
        },
        {
            "heading": "Step 4 — Context Disambiguation & Mobile Clean-Formatting (Zero Asterisks)",
            "quotes": [],
            "implemented": (
                "Context Disambiguation: Student testing revealed that asking 'Where is wifi zone?' caused the bot to dump internet setup instructions because "
                "of naive keyword matching on 'wifi'. We taught the bot that 'Wi-Fi Zone' is a physical lounge on campus (Location intent > Keyword match). "
                "Similarly, the bot was trained to clarify when a name resembles another (e.g. asking if the student meant Red Canteen when asking about Red Hall).\n\n"
                "Telegram Mobile Rendering Fix: Telegram's webhook parser was displaying raw asterisks ('**') and clumping paragraphs together. "
                "We updated SOUL.md to enforce a strict Zero-Asterisk rule, using clear emojis, capitalized labels, and mandatory double line-breaks (\\n\\n) "
                "so text and bullet lists render cleanly on all mobile screens."
            ),
            "demonstrate": (
                "In Telegram, ask 'Where is wifi zone?'. Show that the bot sends the campus map and location guidance instead of network passwords. "
                "Show that the text is completely free of raw asterisks and formatted with clean line breaks."
            ),
            "screenshots": [
                "Telegram chat showing 'Where is wifi zone?' returning the campus map with clean, non-clumped, asterisk-free formatting.",
                "SOUL.md Telegram Message Formatting Rules showing the Zero-Asterisk and Double Line Break standards.",
            ],
            "covered": [],
        },
    ],
}


DOCUMENT = {
    "title": "SDU Help Desk Virtual Assistant — Sprint 4 Walkthrough Report",
    "subtitle": (
        "Cell-by-cell walkthrough of US-07 (Advisor Authorization & Multi-Department RBAC) and "
        "US-08 (Student Profile Context), plus direct student survey findings, UX redesign, and "
        "campus services knowledge base expansions."
    ),
    "primer": {
        "heading": "0. Quick Platform Primer (How the bot runs on Buda)",
        "intro": [
            "Before walking through each spreadsheet cell, here is a 60-second summary of the Buda architecture for non-technical readers.",
        ],
        "subsections": [
            {
                "heading": "0.1 — Dual-Channel Gateway Architecture",
                "body": [
                    "Buda supports multi-channel bindings. The workspace connects to two independent Telegram bots: the Public Student Bot "
                    "for general inquiries, and the Helpdesk Staff Bot locked inside the private staff team group. This delivers security by "
                    "isolation: students have zero access to administrative commands.",
                ],
            },
            {
                "heading": "0.2 — SOUL.md is the Agent's Central Governance Engine",
                "body": [
                    "SOUL.md is the persistent rulebook in the agent's Drive. In Sprint 4 it gained Core Truth #0 (the Dual-Channel "
                    "Security Guard, blocking unauthorized DMs and routing group commands) and Section 10 (Student Profile Context).",
                ],
                "screenshots": [
                    "Drive tab: showing SOUL.md and the project directory structure.",
                ],
            },
            {
                "heading": "0.3 — Persistent Storage Architecture (Logs and Profiles)",
                "body": [
                    "Because Buda's interface shows the 10 most recent active sessions, our project maintains persistent file storage "
                    "on Drive: 'session_logs/INDEX.md' (full conversation transcripts), 'query_log/query_log.csv' (anonymous inquiry stats), "
                    "and 'profiles/<user>.json' (persistent student academic standing).",
                ],
                "screenshots": [
                    "Drive tab: the sdu-helpdesk-bot folder showing profiles/, query_log/, session_logs/, and tests/.",
                ],
            },
        ],
        "closing": [
            "The following sections walk through each spreadsheet cell in exact order, with instructions on what to demonstrate and screenshot.",
        ],
    },
    "stories": [US07, US08, STAKEHOLDERS, STUDENT_FEEDBACK],
    "closing_section": {
        "heading": "5. Honest Gaps & Future Roadmap",
        "body": [
            "• Direct SIS Integration Deferred: Student profiles are currently set via conversational natural language and stored in "
            "Drive JSON files. Automated real-time synchronization with the university's Oracle SIS database is deferred to enterprise phases (US-08 Test Script A22).",
            "• Group Chat Identification: In Telegram groups, Telegram privacy mode requires bots to either be group administrators or receive "
            "direct mentions/replies. Ensure the Staff Bot has group admin privileges in the staff group.",
            "• Human Escalation Ticket Queue (US-09 & US-10): Sprint 4 establishes the staff channel and profile context; the formal support "
            "ticket creation and advisor claim queue are scheduled for Sprint 5.",
        ],
        "screenshots": [
            "Terminal: running 'python3 -m unittest discover -s /agent/sdu-helpdesk-bot/tests' showing all 23 tests passing.",
        ],
    },
}
