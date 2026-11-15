"""Sprint 4 stories: US-07 (Advisor Authorization & RBAC Controls), US-08 (Student Profile Context).
story_text is copied verbatim from the master 'user-stories' sheet (verified by build script)."""

STORIES = [
    {
        "id": "US-07",
        "title": "Advisor Authorization & RBAC Controls",
        "story_text": (
            "Advisor Authorization & RBAC Controls: As an Advisor, I want administrative commands "
            "(ticket review, log export) restricted to authorized Telegram accounts or advisor credentials, "
            "so that sensitive student inquiries remain protected."
        ),
        "stakeholders": "Advisor",
        "responsibilities": [
            "Enforce strict channel-level access control by isolating the public student Telegram bot from the private staff advisor bot.",
            "Restrict all administrative commands (live department query summaries, session log index review) exclusively to the authorized private staff Telegram group.",
            "Silently reject or block administrative access attempts from private direct messages (DMs) or unauthorized student channels with a strict access restricted notice.",
            "Provide authorized advisors in the staff group with real-time operational tools (summary, stat, sessions, department question filters) without requiring manual password entry.",
            "Protect student confidentiality and privacy by keeping raw personal identifiers (PII) stripped from all group-level administrative reports.",
        ],
        "constraints": [
            "Access verification and role isolation must execute natively through Buda channel bindings and group ID guards without external identity providers.",
            "Administrative insights, query summaries, and session transcripts must remain completely inaccessible to students interacting through the public bot.",
            "The staff advisor bot must not respond to administrative inquiries in direct private chats outside the authorized staff group.",
        ],
        "tags": "Volatility = Low, Priority = High, Effort = LCHV (4/10), Sprint = 4",
        "test_scripts": [
            "System: (Pass) Authorized advisor in the private staff group sends 'summary' and the bot posts the live department analytics report.",
            "System: (Pass) Authorized staff member sends 'sessions' in the staff group and receives the list of recent active student conversations from INDEX.md.",
            "System: (Pass) Staff member asks a department-specific question (e.g. 'Show tuition questions') and the bot filters query logs for that department.",
            "System: (Fail) Student in the public bot channel sends 'summary' or asks for advisor statistics and is denied admin access, receiving standard student guidance.",
            "System: (Fail) User attempts to DM the staff bot directly and receives an access restricted notice blocking private administrative execution.",
            "System: (Deferred) Multi-factor biometric authentication and SSO integration with university Active Directory are deferred to future enterprise releases.",
        ],
        "maintenance": [
            "Task (New): Configure dual-channel bindings in Buda workspace settings for the public student bot and private staff group bot.",
            "Task (New): Update SOUL.md with top-priority dual-channel access control rules and private group security guards.",
            "Task (New): Document the staff Telegram group onboarding and triage workflow in the Help Desk Administrator Guide.",
            "Task (New): Verify automated session transcript logging (INDEX.md) and executive summary tools (summarize_log.py) for staff group use.",
        ],
        "scenarios": [
            {
                "name": "Authorized advisor requests department summary in staff group",
                "steps": [
                    ("Given", "The advisor is interacting inside the authorized private SDU Help Desk staff group."),
                    ("When", "The advisor sends 'summary', 'stat', or 'отчет'."),
                    ("Then", "The bot executes the query log summary tool."),
                    ("And", "The bot posts the live executive statistics and top unanswered student questions into the group."),
                ],
            },
            {
                "name": "Staff member reviews recent student conversation sessions",
                "steps": [
                    ("Given", "The interaction occurs within the authorized staff Telegram group."),
                    ("When", "A staff member sends 'sessions' or 'сессии'."),
                    ("Then", "The bot reads the master transcript index from INDEX.md."),
                    ("And", "The bot displays the active student conversation sessions without revealing sensitive student PII."),
                ],
            },
            {
                "name": "Unauthorized student in public bot cannot access advisor tools",
                "steps": [
                    ("Given", "A student is chatting with the public help desk bot."),
                    ("When", "The student sends 'summary', 'admin', or requests administrative logs."),
                    ("Then", "The bot treats the input as an out-of-scope student inquiry."),
                    ("And", "The bot displays the standard student 4-topic help desk menu without revealing staff tools."),
                ],
            },
            {
                "name": "Direct private message (DM) to staff bot is restricted",
                "steps": [
                    ("Given", "A user attempts to message the staff advisor bot in a private one-on-one Telegram chat."),
                    ("When", "The user sends any greeting or command to the bot."),
                    ("Then", "The bot enforces the private group security guard."),
                    ("And", "The bot returns an access restricted notice indicating it operates only inside the staff group."),
                ],
            },
            {
                "name": "Departmental triage query in staff group",
                "steps": [
                    ("Given", "An advisor is coordinating support inside the staff group."),
                    ("When", "The advisor asks for questions related to a specific department (e.g. 'Show tuition questions')."),
                    ("Then", "The bot filters the query logs for that department category."),
                    ("And", "The bot provides the specific volume and recurring issues for that department."),
                ],
            },
        ],
        "rules": [
            "Administrative commands (summary, sessions, triage) are restricted exclusively to the authorized private staff Telegram group.",
            "The public student bot must never execute or disclose administrative reporting tools to student chats.",
            "Direct messages (DMs) to the staff bot must be blocked with an access restriction notice.",
            "All administrative summaries and session lists must maintain student privacy by excluding personal identifiers (PII).",
            "Dual-channel isolation is enforced at the platform channel binding and prompt guard level.",
        ],
    },
    {
        "id": "US-08",
        "title": "Student Profile Context",
        "story_text": (
            "Student Profile Context: As a Student, I want to specify my major and year of study "
            "(or student ID), so that the bot can provide answers tailored to my academic standing "
            "and faculty regulations."
        ),
        "stakeholders": "Student",
        "responsibilities": [
            "Allow students to optionally specify their academic standing (degree level, major/faculty, study year) naturally in conversation.",
            "Store student profile attributes persistently across conversation sessions in the user transcript and profile storage.",
            "Tailor academic guidance (tuition schedules, ECTS credit loads, graduation requirements, faculty advisors) based on the active student profile.",
            "Support seamless profile updating or resetting upon student request (e.g. changing major or switching degree programs).",
            "Provide sensible general university defaults when no profile has been set, prompting for specialization only when necessary.",
        ],
        "constraints": [
            "Profile context must be stored locally in persistent workspace session storage without requiring external SIS database integrations.",
            "Sensitive identifiers such as national IIN, bank card details, or passwords must never be collected or stored in the student profile.",
            "Setting a profile must remain strictly optional; general university help desk inquiries must function without mandatory onboarding.",
        ],
        "tags": "Volatility = Low, Priority = Medium, Effort = LCLV (3/10), Sprint = 4",
        "test_scripts": [
            "System: (Pass) Student specifies 'Computer Science, 2nd year Bachelor' and receives CS-tailored tuition rates and faculty contact details.",
            "System: (Pass) Student asks a general tuition question without a profile set and receives general university rules with an offer to personalize.",
            "System: (Pass) Student resets their profile and subsequent answers revert to general university regulations.",
            "System: (Fail) Bot demands student ID or IIN before answering public help desk inquiries.",
            "System: (Fail) Bot gives undergraduate course load limits to an identified Master's or PhD student.",
            "System: (Deferred) Automated synchronization with the SDU Student Information System (SIS Portal API) is deferred to future enterprise releases.",
        ],
        "maintenance": [
            "Task (New): Create profile storage schema and helper tools for storing per-user academic standing in persistent storage.",
            "Task (New): Map faculty-specific regulations and tuition rates in the knowledge base to degree level and major tags.",
            "Task (New): Update SOUL.md with profile-aware response formatting rules and optional onboarding prompts.",
            "Task (New): Add automated unit tests verifying profile extraction, persistence, context injection, and reset flows.",
        ],
        "scenarios": [
            {
                "name": "Student sets academic profile successfully",
                "steps": [
                    ("Given", "The student is interacting with the help desk bot in Telegram."),
                    ("When", "The student specifies their faculty, major, and year (e.g. 'I am a 3rd year Law student')."),
                    ("Then", "The bot extracts and saves the academic standing into the student profile context."),
                    ("And", "The bot confirms the profile update with a friendly confirmation message."),
                ],
            },
            {
                "name": "Bot tailors guidance based on active student profile",
                "steps": [
                    ("Given", "The student has an active profile registered as 'Master of Education, 1st year'."),
                    ("When", "The student asks about graduation research requirements or thesis rules."),
                    ("Then", "The bot retrieves regulations specifically tailored to Master's degree programs."),
                    ("And", "The bot cites the official Master's Research Practice Regulation."),
                ],
            },
            {
                "name": "General inquiries function without mandatory profile",
                "steps": [
                    ("Given", "A student interacts with the bot for the first time without setting a profile."),
                    ("When", "The student asks a standard question about dormitory application deadlines."),
                    ("Then", "The bot delivers the general campus dormitory schedule immediately without blocking on profile setup."),
                ],
            },
            {
                "name": "Student updates or resets academic profile",
                "steps": [
                    ("Given", "A student has an existing profile saved in the system."),
                    ("When", "The student sends '/profile reset' or states they changed their degree program."),
                    ("Then", "The bot updates or clears the stored profile attributes."),
                    ("And", "The bot confirms that answers will now reflect the new academic profile."),
                ],
            },
            {
                "name": "Privacy protection during profile interactions",
                "steps": [
                    ("Given", "A student shares personal data (e.g. IIN or student password) during a profile setup message."),
                    ("When", "The bot parses the profile information."),
                    ("Then", "The bot ignores and does not store the sensitive credentials."),
                    ("And", "The bot reminds the student that only major, degree level, and year of study are required."),
                ],
            },
        ],
        "rules": [
            "Student profile attributes (degree level, major, year of study) are optional and enhance answer relevance.",
            "Profile data is stored persistently per user session in profiles context.",
            "When profile context is present, answers for faculty-specific policies and tuition must reflect that academic standing.",
            "If no profile exists, the bot must answer using standard university-wide defaults without blocking the student.",
            "Personal identifiers (IIN, passwords, phone numbers) must never be required or stored in student profiles.",
        ],
    },
]
