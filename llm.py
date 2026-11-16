"""LLM integration for the SDU Help Desk Bot.

Calls NVIDIA Nemotron 3.5 Lightning 30B via the OpenAI-compatible API at
https://integrate.api.nvidia.com/v1. System prompt distilled from SOUL.md rules:
zero asterisks, double line breaks between paragraphs, no Markdown headings,
strict grounding in knowledge base, Kazakh/Russian/English replies.
"""
from __future__ import annotations

import os
import json
import re

import httpx

from knowledge_base import find_relevant_docs

NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
NVIDIA_MODEL = "nvidia/nemotron-3.5-lightning-30b-a3b"


SYSTEM_PROMPT = """You are the SDU University Help Desk Assistant, an official university support bot operating via Telegram and web chat.

Scope: student onboarding, tuition fees, course add/drop, dormitory, transcripts, campus services, and official SDU regulations.

HARD RULES (never break):
1. NEVER use asterisks (* or **) anywhere in your reply. Telegram shows them literally.
2. Put a blank line between EVERY paragraph, heading, bullet, and image marker. No clumped text.
3. NEVER use Markdown headings (#, ##, ###). Telegram renders # as raw text. Use emojis instead.
4. Ground every factual answer strictly in the provided knowledge base context. Cite a source at the very end of your reply (last line/paragraph), not at the beginning. Use only official sources (official URL or official PDF/regulation name) when available. If no official source is available, cite "Student Community Guide". Never cite internal .md files or internal system paths.
5. If the answer is not in the knowledge base, say so concisely, direct the student to the SSC in Block B, and offer to escalate to a human advisor. Never hallucinate.
6. Reply in the language of the student's most recent message (Kazakh, Russian, or English).
7. Keep facts (numbers, dates, contacts, URLs, regulation codes) exactly as written in the knowledge base.
8. If a student profile is provided, use it to personalize the answer when relevant (for example, mention their degree/major/year and give the most relevant program-specific guidance available in the knowledge base) instead of giving an unnecessarily generic answer.
9. Be professional, helpful, accurate, and empathetic.

Dispatch marker: if you need to send an official file/image, place [send:path/to/file] on its own line with blank lines above and below.

Do not output internal monologue, planning, or status updates. Output only the final user-facing reply.
"""


def _display_source(doc) -> str:
    src = (getattr(doc, "source_url", None) or "").strip()
    if src:
        if src.startswith("http://") or src.startswith("https://"):
            return src
        name = src.rstrip("/").split("/")[-1].split("?")[0]
        if name:
            name = name.replace("%20", " ")
            if name.lower().endswith(".md"):
                name = name[:-3]
            return name
        return src
    label = (getattr(doc, "source_label", None) or "").strip()
    if label:
        if label.lower().endswith(".md") or "knowledge_base" in label.replace("\\", "/"):
            label = ""
        else:
            return label
    # No official URL/label -> community/informal guide (never expose internal .md)
    return "Student Community Guide"


def build_context(docs) -> str:
    if not docs:
        return "No relevant knowledge-base documents found."
    parts = ["Relevant knowledge-base sources:"]
    for doc in docs:
        parts.append(
            f"\n--- {doc.title} ({doc.category}) ---\n"
            f"Source: {_display_source(doc)}\n"
            f"{doc.body[:1500]}"
        )
    return "\n".join(parts)


def build_profile_context(profile: dict | None) -> str:
    if not profile:
        return "Student profile: not provided."
    degree = profile.get("degree") or "N/A"
    major = profile.get("major") or "N/A"
    year = profile.get("year")
    year_text = str(year) if year is not None else "N/A"
    return (
        "Student profile:\n"
        f"- Degree: {degree}\n"
        f"- Major: {major}\n"
        f"- Year: {year_text}\n"
        "Use this profile to tailor the answer when relevant."
    )


def _strip_thinking(text: str) -> str:
    """Aggressively remove thinking/analysis patterns from model output."""
    if not text:
        return ""

    # Remove thinking markers and blocks
    patterns_to_remove = [
        r"Here's a thinking process:.*",
        r"Here's my thinking process:.*",
        r"Here's my thought process:.*",
        r"Let me think through.*",
        r"Let me reconsider.*",
        r"Thinking process:.*",
        r"Analysis:.*",
        r"Step \d+:.*",
        r"\d+\.\s*\**Analyze.*",
        r"\d+\.\s*\**Review.*",
        r"\d+\.\s*\**Check.*",
        r"\d+\.\s*\**Examine.*",
        r"\d+\.\s*\**Determine.*",
        r"\d+\.\s*\**Draft.*",
        r"\d+\.\s*\**Structure.*",
        r"Rule \d+:.*",
        r"Here's a thinking process.*",
    ]

    result = text
    for pat in patterns_to_remove:
        result = re.sub(pat, "", result, flags=re.IGNORECASE | re.DOTALL)

    # Remove numbered list items that are clearly thinking steps
    lines = result.split("\n")
    cleaned_lines = []
    skip_next = False
    for i, line in enumerate(lines):
        if skip_next:
            skip_next = False
            continue
        stripped = line.strip()
        # Skip lines that are clearly thinking steps
        if re.match(r"^\d+\.\s", stripped):
            if any(kw in stripped.lower() for kw in [
                "analyze", "review", "check", "examine", "determine",
                "draft", "structure", "user input", "hard rule", "rule ",
                "knowledge base", "constraint", "strategy",
            ]):
                continue
        cleaned_lines.append(line)

    result = "\n".join(cleaned_lines)

    # Remove blank line clusters
    result = re.sub(r"\n{3,}", "\n\n", result)

    # Strip leading/trailing whitespace
    result = result.strip()

    return result


def _looks_like_thinking(text: str) -> bool:
    """Check if text looks like internal reasoning rather than a final answer."""
    if not text or len(text) < 10:
        return True

    thinking_indicators = [
        "here's a thinking",
        "let me reconsider",
        "step 1",
        "step 2",
        "step 3",
        "step 4",
        "rule 1:",
        "rule 2:",
        "rule 3:",
        "rule 4:",
        "rule 5:",
        "rule 6:",
        "rule 7:",
        "rule 8:",
        "analyze user input",
        "let's draft",
        "important:",
        "but i need",
        "no asterisks",
        "no markdown",
        "blank line",
    ]

    text_lower = text.lower()
    count = sum(1 for ind in thinking_indicators if ind in text_lower)
    return count >= 3


def _sanitize_telegram(text: str) -> str:
    if not text:
        return text
    # Strip markdown emphasis/heading markers that render poorly in Telegram
    text = text.replace("**", "").replace("__", "").replace("`", "")
    text = re.sub(r"^#{1,6}\s*", "", text, flags=re.M)
    # Convert markdown bullets to plain bullets
    text = re.sub(r"^\s*[\*\-]\s+", "• ", text, flags=re.M)
    # Remove remaining single-asterisk emphasis
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    # Remove any stray asterisks
    text = text.replace("*", "")
    # Normalize spacing
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


async def answer(student_message: str, api_key: str, model_name: str = NVIDIA_MODEL, profile: dict | None = None) -> str:
    if not api_key:
        return "I'm temporarily unable to answer. No AI API key is configured. Please contact the SSC in Block B."

    docs = find_relevant_docs(student_message)
    context = build_context(docs)
    profile_context = build_profile_context(profile)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"{profile_context}\n\n{context}\n\nStudent question: {student_message}\n\nAnswer the student following the hard rules above. If you cite a source, put it at the end."},
        ],
        "temperature": 0.3,
        "max_tokens": 4000,
        "reasoning": {"effort": "low"},
    }

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{NVIDIA_BASE_URL}/chat/completions",
                headers=headers,
                json=payload,
            )
            if resp.status_code >= 400:
                # Some endpoints/models may reject reasoning param; retry without it.
                payload.pop("reasoning", None)
                resp = await client.post(
                    f"{NVIDIA_BASE_URL}/chat/completions",
                    headers=headers,
                    json=payload,
                )
            resp.raise_for_status()
            data = resp.json()
        msg = data["choices"][0]["message"]
        content = msg.get("content") or ""
        text = ""
        if content and len(content) > 10:
            text = content
        else:
            reasoning = msg.get("reasoning_content") or ""
            cleaned = _strip_thinking(reasoning)
            if cleaned and len(cleaned) > 10:
                text = cleaned
        if not text:
            return "I could not generate a reply. Please try again."
        # Normalize source placement: move "Source:" lines/blocks to the end.
        lines = [ln.rstrip() for ln in text.strip().splitlines()]
        source_lines = []
        other_lines = []
        for ln in lines:
            is_source = ln.strip().lower().startswith("source:")
            if not is_source and "/knowledge_base/" in ln.lower() and "source" in ln.lower():
                is_source = True
            if is_source:
                cleaned = ln.strip()
                m = re.search(r"Source:\s*(.+)$", cleaned, flags=re.IGNORECASE)
                if m:
                    val = m.group(1).strip()
                    norm = val.replace("\\", "/")
                    if "/knowledge_base/" in norm or norm.lower().endswith(".md") or norm.lower().startswith("knowledge_base/") or re.search(r"\bcampus_map_and_cabinets\.md\b", norm, flags=re.IGNORECASE):
                        # Not an official source; use community guide label
                        val = "Student Community Guide"
                    if norm.lower().endswith(".md"):
                        base = os.path.splitext(os.path.basename(norm))[0]
                        candidate = base.replace("_", " ").strip()
                        if candidate and "knowledge base" not in candidate.lower():
                            val = candidate if (norm.startswith("http") or "official" in candidate.lower()) else "Student Community Guide"
                    cleaned = f"Source: {val}"
                source_lines.append(cleaned)
            else:
                other_lines.append(ln)
        if source_lines:
            while other_lines and not other_lines[0].strip():
                other_lines.pop(0)
            while other_lines and not other_lines[-1].strip():
                other_lines.pop()
            # dedupe while preserving order
            seen = set()
            uniq_sources = []
            for sline in source_lines:
                key = sline.lower()
                if key not in seen:
                    seen.add(key)
                    uniq_sources.append(sline)
            text = "\n".join(other_lines).strip() + "\n\n" + "\n".join(uniq_sources).strip()
        text = _sanitize_telegram(text)
        return text.strip()
    except httpx.HTTPStatusError as exc:
        return f"I'm temporarily unable to answer (API error {exc.response.status_code}). Please contact the SSC in Block B or try again later."
    except Exception as exc:  # pragma: no cover - runtime safety
        return f"I'm temporarily unable to answer. Please contact the SSC in Block B or try again later. ({exc})"
