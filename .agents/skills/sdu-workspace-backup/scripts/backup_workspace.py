#!/usr/bin/env python3
"""Create a complete, portable backup archive of the SDU Help Desk workspace.

Packages all agent configuration/persona files, memory, custom skills,
.buda/works build scripts, and the entire sdu-helpdesk-bot project (including
knowledge_base, documents, query_log, session_logs, tests, and writeup) into
/agent/backups/sdu_workspace_full_backup.tar.gz (or a custom path).

Excludes transient caches (.local, .cache, .npm, .trash, .homebrew-cache,
__pycache__, and backups/ itself) so the archive stays clean and compact.
"""
import argparse
import os
import sys
import tarfile
from datetime import datetime, timezone

AGENT_ROOT = "/agent"
DEFAULT_OUT = "/agent/backups/sdu_workspace_full_backup.tar.gz"

INCLUDE_PATHS = [
    "SOUL.md",
    "AGENTS.md",
    "USER.md",
    "IDENTITY.md",
    "MEMORY.md",
    "TOOLS.md",
    "HEARTBEAT.md",
    "memory",
    ".agents",
    ".pi/agent/skills",
    ".buda",
    "sdu-helpdesk-bot",
]

EXCLUDE_DIR_NAMES = {
    "__pycache__",
    ".git",
    "node_modules",
    ".cache",
    ".pytest_cache",
}


def should_skip(tarinfo: tarfile.TarInfo) -> tarfile.TarInfo | None:
    parts = tarinfo.name.split("/")
    for part in parts:
        if part in EXCLUDE_DIR_NAMES:
            return None
    if tarinfo.name.endswith(".pyc") or tarinfo.name.endswith(".pyo"):
        return None
    return tarinfo


def build_backup(out_path: str, timestamped_copy: bool = False) -> list[str]:
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    tmp_path = out_path + ".tmp"

    included = []
    with tarfile.open(tmp_path, "w:gz") as tar:
        for rel in INCLUDE_PATHS:
            abs_p = os.path.join(AGENT_ROOT, rel)
            if os.path.exists(abs_p):
                tar.add(abs_p, arcname=rel, filter=should_skip)
                included.append(rel)

    os.replace(tmp_path, out_path)
    created = [out_path]

    if timestamped_copy:
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M%SZ")
        base_dir = os.path.dirname(os.path.abspath(out_path))
        stamped_path = os.path.join(base_dir, f"sdu_workspace_backup_{stamp}.tar.gz")
        import shutil
        shutil.copy2(out_path, stamped_path)
        created.append(stamped_path)

    size_mb = os.path.getsize(out_path) / (1024 * 1024)
    print(f"BACKUP_OK: {out_path} ({size_mb:.1f} MB)")
    print(f"INCLUDED ({len(included)}): {', '.join(included)}")
    for c in created[1:]:
        print(f"TIMESTAMPED_COPY: {c}")
    return created


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--out",
        default=DEFAULT_OUT,
        help=f"Output .tar.gz path (default: {DEFAULT_OUT})",
    )
    ap.add_argument(
        "--timestamped",
        action="store_true",
        help="Also save a UTC-timestamped copy alongside the main backup archive",
    )
    args = ap.parse_args()
    build_backup(args.out, timestamped_copy=args.timestamped)
    return 0


if __name__ == "__main__":
    sys.exit(main())
