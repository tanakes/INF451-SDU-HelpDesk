---
name: sdu-workspace-backup
description: Creates a complete, portable .tar.gz backup of the SDU Help Desk workspace — including all agent config/persona files (SOUL.md, AGENTS.md, USER.md, IDENTITY.md, MEMORY.md, TOOLS.md, HEARTBEAT.md), memory notes, custom skills (.agents/skills/), .buda/works build scripts, and the full sdu-helpdesk-bot project (knowledge_base, documents, query_log, session_logs, tests, writeup). Trigger whenever the user says "backup", "make a backup", "export the workspace", or asks to save a snapshot of the project and settings.
---

# SDU Workspace Backup Skill (`sdu-workspace-backup`)

Use this skill whenever the user asks to back up or export the current workspace, project files, skills, and configurations.

## Quick Workflow

1. **Run the backup generator script:**
   ```bash
   python3 /agent/.agents/skills/sdu-workspace-backup/scripts/backup_workspace.py
   ```
   - By default, this creates/updates `/agent/backups/sdu_workspace_full_backup.tar.gz`.
   - If the user asks for a dated/versioned snapshot in addition to the latest file, pass `--timestamped`:
     ```bash
     python3 /agent/.agents/skills/sdu-workspace-backup/scripts/backup_workspace.py --timestamped
     ```

2. **Deliver the download card in chat:**
   Always verify and emit the inline download marker using the `send-file` script:
   ```bash
   node "${BUDA_SYSTEM_ROOT:-/system}/.agents/skills/buda-machine-info/scripts/send-file.mjs" backups/sdu_workspace_full_backup.tar.gz
   ```
   Embed the returned `[send:backups/sdu_workspace_full_backup.tar.gz]` marker directly in the response.

3. **Include the 1-line restore command** when the user is migrating to another workspace:
   ```bash
   tar -xzf /agent/sdu_workspace_full_backup.tar.gz -C /agent
   ```

## What Is Packaged
- Root persona & configuration files: `SOUL.md`, `AGENTS.md`, `USER.md`, `IDENTITY.md`, `MEMORY.md`, `TOOLS.md`, `HEARTBEAT.md`
- Long-term & daily memory: `memory/`
- All custom skills: `.agents/` and `.pi/agent/skills/`
- Build scripts & sprint artifacts: `.buda/`
- Full project folder: `sdu-helpdesk-bot/` (including `knowledge_base/`, `documents/`, `query_log/`, `session_logs/`, `tests/`, `writeup/`, spreadsheets, and helper scripts)

## What Is Excluded
- Transient runtime caches (`.local`, `.cache`, `.npm`, `.trash`, `.homebrew-cache`, `__pycache__`, `node_modules`, `.pyc`) and `/agent/backups/` itself (to prevent recursive archive growth).
