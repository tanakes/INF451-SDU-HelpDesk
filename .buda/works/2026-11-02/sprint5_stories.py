"""Sprint 5 stories: US-09 (Human Advisor Escalation), US-10 (Advisor Ticket Queue & Logs).
story_text is copied verbatim from the master 'user-stories' sheet (verified by build script)."""

STORIES = [
    {
        "id": "US-09",
        "title": "Human Advisor Escalation",
        "story_text": (
            "Human Advisor Escalation: As a Student, I want the bot to offer an escalation option "
            "when my issue is complex or unresolvable by AI, so that an official support ticket "
            "is created with my details."
        ),
        "stakeholders": "Student",
        "responsibilities": [
            "Detect when a student query remains unanswered after repeated fallback prompts (automatic triage) or upon explicit request.",
            "Offer a human advisor escalation option to the student in a helpful, supportive tone.",
            "Capture the student's conversation context (summary of recent inquiry) and prepare a ticket record without exposing sensitive PII.",
            "Notify the authorized staff group immediately via the private advisor bot upon ticket creation.",
            "Provide the student with a friendly confirmation that their case has been escalated for human review.",
        ],
        "constraints": [
            "Ticket creation must persist on the Agent Drive in a secure 'pending' folder.",
            "Escalation notification must ONLY be sent to the authorized staff channel/group, never to public student channels.",
            "Personally Identifiable Information (PII) must be scrubbed from the ticket context before saving to Drive.",
        ],
        "tags": "Volatility = Low, Priority = High, Effort = HCHV (6/10), Sprint = 5",
        "test_scripts": [
            "System: (Pass) Student query remains unanswered twice and the bot offers escalation; accepting triggers a ticket.",
            "System: (Pass) Student explicitly asks for an advisor and a ticket is created instantly.",
            "System: (Pass) Staff advisor bot pings the authorized staff group with the escalation alert.",
            "System: (Fail) Ticket created for a student includes IIN, passwords, or bank data.",
            "System: (Fail) Escalation request appears in the public student bot instead of the staff group.",
        ],
        "maintenance": [
            "Task (New): Create 'tickets/pending/' and 'tickets/resolved/' directories on the Agent Drive.",
            "Task (New): Implement 'tickets/manage_tickets.py' for creating, listing, and resolving escalation entries.",
            "Task (New): Update SOUL.md to include the automatic triage rules and staff group notification protocols.",
            "Task (New): Add automated unit tests verifying ticket persistence and PII safety.",
        ],
        "scenarios": [
            {
                "name": "Automatic triage triggers escalation offer",
                "steps": [
                    ("Given", "The student has asked the same issue twice without success."),
                    ("When", "The bot identifies the issue as 'not covered' for the second time."),
                    ("Then", "The bot offers a human advisor escalation."),
                    ("And", "The student's escalation request triggers a ticket in the 'pending' folder."),
                ],
            },
            {
                "name": "Explicit escalation via natural language",
                "steps": [
                    ("Given", "The student is interacting with the bot."),
                    ("When", "The student says 'I want an advisor' or 'connect me to human'."),
                    ("Then", "The bot triggers immediate ticket creation."),
                    ("And", "The bot sends a notification to the authorized staff group."),
                ],
            },
        ],
        "rules": [
            "Escalation is only available to students via explicit request or automatic triage after repeated failure.",
            "Tickets must be saved to the Drive securely and never expose PII.",
            "Staff group ping must happen automatically upon successful ticket creation.",
        ],
    },
    {
        "id": "US-10",
        "title": "Advisor Ticket Queue & Logs",
        "story_text": (
            "Advisor Ticket Queue & Logs: As an Advisor, I want to review logged escalation "
            "tickets and unanswered student questions, so that our team can follow up with "
            "students efficiently."
        ),
        "stakeholders": "Advisor",
        "responsibilities": [
            "Allow staff to view a ranked queue of open escalation tickets using natural language triggers.",
            "Allow staff to resolve and archive tickets once they have contacted the student.",
            "Ensure the ticket queue only displays current pending issues and excludes sensitive student data.",
            "Provide the staff group with a consistent interface for managing student escalations.",
        ],
        "constraints": [
            "Management commands must only function within the authorized staff Telegram group.",
            "Ticket resolution must atomically move the file from 'pending/' to 'resolved/' on Drive.",
            "No slash commands are allowed (use natural language).",
        ],
        "tags": "Volatility = Low, Priority = High, Effort = HCHV (5/10), Sprint = 5",
        "test_scripts": [
            "System: (Pass) Staff advisor sends 'show open tickets' and sees the list of all tickets from the 'pending/' folder.",
            "System: (Pass) Staff advisor sends 'Resolve ticket for [User ID]' and the file moves to 'resolved/'.",
            "System: (Pass) Resolved tickets are hidden from the 'show open tickets' queue but remain retrievable by logs.",
            "System: (Fail) Unauthorized user in the student bot attempts to list the ticket queue.",
        ],
        "maintenance": [
            "Task (New): Update manage_tickets.py to handle listing and moving JSON ticket files.",
            "Task (New): Integrate ticket management commands into the staff advisor bot's natural language parser.",
            "Task (New): Add unit tests for listing and moving tickets.",
        ],
        "scenarios": [
            {
                "name": "Staff advisor lists open tickets",
                "steps": [
                    ("Given", "There are pending tickets in 'tickets/pending/'."),
                    ("When", "An advisor sends 'Show open tickets' or 'list queue' in the staff group."),
                    ("Then", "The bot lists all pending tickets with their context and timestamp."),
                ],
            },
            {
                "name": "Staff advisor resolves a ticket",
                "steps": [
                    ("Given", "An active ticket exists in 'tickets/pending/'."),
                    ("When", "The advisor sends 'Resolve ticket for [User ID]'."),
                    ("Then", "The bot moves the ticket file to 'tickets/resolved/'."),
                    ("And", "The bot confirms the resolution to the advisor group."),
                ],
            },
        ],
        "rules": [
            "Ticket management commands are only valid inside the private staff Telegram group.",
            "Only the Staff Advisor Bot can create, list, or resolve tickets.",
            "The resolution process must be verified by moving files between Drive folders.",
        ],
    },
]
