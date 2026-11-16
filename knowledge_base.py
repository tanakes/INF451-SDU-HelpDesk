"""Knowledge-base retrieval for SDU Help Desk Bot.

Loads knowledge_base/<category>/*.md files, parses YAML front-matter, and
provides keyword-based retrieval so answers stay grounded in official docs.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import List, Optional

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover - optional dep fallback
    yaml = None


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KB_DIR = os.path.join(BASE_DIR, "knowledge_base")


@dataclass
class KBDoc:
    path: str
    category: str
    title: str
    menu_number: Optional[int]
    keywords: List[str]
    menu_summary: str
    source_url: Optional[str]
    source_label: Optional[str]
    body: str
    raw: str


def _parse_front_matter(text: str):
    """Return (front_matter_dict, body). Supports --- delimited YAML front matter."""
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end != -1:
            fm_text = text[4:end]
            body = text[end + 5:]
            if yaml is not None:
                try:
                    fm = yaml.safe_load(fm_text) or {}
                except Exception:
                    fm = {}
            else:
                fm = _simple_yaml(fm_text)
            return fm, body
    return {}, text


def _simple_yaml(text: str) -> dict:
    """Tiny YAML subset parser for scalar values and lists."""
    result: dict = {}
    current_key = None
    current_list: List[str] = []

    def _parse_inline_list(value: str):
        v = value.strip()
        if not (v.startswith("[") and v.endswith("]")):
            return None
        inner = v[1:-1].strip()
        if not inner:
            return []
        items = []
        for part in inner.split(","):
            p = part.strip().strip('"').strip("'")
            if p:
                items.append(p)
        return items

    for line in text.splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        m = re.match(r"^(\w+):\s*(.*)$", line)
        if m:
            if current_key is not None and current_list:
                result[current_key] = current_list
                current_list = []
            current_key = m.group(1)
            value = m.group(2).strip()
            if value == "":
                current_list = []
                continue
            inline = _parse_inline_list(value)
            if inline is not None:
                result[current_key] = inline
                current_key = None
                current_list = []
            else:
                result[current_key] = value.strip('"').strip("'")
                current_key = current_key  # keep for possible? no, scalar done
        elif line.lstrip().startswith("- ") and current_key is not None:
            current_list.append(line.lstrip()[2:].strip().strip('"').strip("'"))
    if current_key is not None and current_list:
        result[current_key] = current_list
    return result


def load_docs() -> List[KBDoc]:
    docs: List[KBDoc] = []
    if not os.path.isdir(KB_DIR):
        return docs
    for category in sorted(os.listdir(KB_DIR)):
        cat_dir = os.path.join(KB_DIR, category)
        if not os.path.isdir(cat_dir):
            continue
        for fname in sorted(os.listdir(cat_dir)):
            if not fname.endswith(".md"):
                continue
            path = os.path.join(cat_dir, fname)
            with open(path, "r", encoding="utf-8") as fh:
                raw = fh.read()
            fm, body = _parse_front_matter(raw)
            docs.append(
                KBDoc(
                    path=path,
                    category=str(fm.get("category", category)),
                    title=str(fm.get("menu_title", fname)),
                    menu_number=fm.get("menu_number"),
                    keywords=[str(k).lower() for k in (fm.get("keywords") or [])],
                    menu_summary=str(fm.get("menu_summary", "")),
                    source_url=fm.get("source_url"),
                    source_label=fm.get("source_label") or fm.get("source_name"),
                    body=body.strip(),
                    raw=raw,
                )
            )
    return docs


DOCS: List[KBDoc] = load_docs()


def find_relevant_docs(query: str, limit: int = 3) -> List[KBDoc]:
    """Score docs by keyword overlap and return top matches."""
    q = query.lower()
    scored = []
    for doc in DOCS:
        score = 0
        for kw in doc.keywords:
            if kw and kw in q:
                score += 2
        # menu_summary / title hints
        if doc.menu_summary and doc.menu_summary.lower() in q:
            score += 1
        if doc.title.lower() in q:
            score += 1
        if score > 0:
            scored.append((score, doc))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [doc for _, doc in scored[:limit]]
