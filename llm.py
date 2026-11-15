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
4. Ground every factual answer strictly in the provided knowledge_base context. Cite the source file/page when you use it.
5. If the answer is not in the knowledge base, say so concisely, direct the student to the SSC in Block B, and offer to escalate to a human advisor. Never hallucinate.
6. Reply in the language of the student's most recent message (Kazakh, Russian, or English).
7. Keep facts (numbers, dates, contacts, URLs, regulation codes) exactly as written in the knowledge base.
8. Be professional, helpful, accurate, and empathetic.

Dispatch marker: if you need to send an official file/image, place [send:path/to/file] on its own line with blank lines above and below.

Do not output internal monologue, planning, or status updates. Output only the final user-facing reply.
"""


def build_context(docs) -> str:
    if not docs:
        return "No relevant knowledge-base documents found."
    parts = ["Relevant knowledge-base sources:"]
    for doc in docs:
        parts.append(
            f"\n--- {doc.title} ({doc.category}) ---\n"
            f"Source: {doc.path}\n"
            f"{doc.body[:1500]}"
        )
    return "\n".join(parts)


def _extract_final_answer(reasoning_content: str) -> str:
    """Extract the final user-facing answer from reasoning_content.

    NVIDIA Nemotron puts its internal thinking process in reasoning_content.
    The final answer typically appears after all thinking sections. We take
    the last substantial block of text as the answer.
    """
    if not reasoning_content:
        return ""

    blocks = [b.strip() for b in reasoning_content.split("\n\n") if b.strip()]

    # Return the last block that's substantial enough to be an answer
    for block in reversed(blocks):
        if len(block) > 40:
            return block

    return ""


async def answer(student_message: str, api_key: str, model_name: str = NVIDIA_MODEL) -> str:
    if not api_key:
        return "I'm temporarily unable to answer. No AI API key is configured. Please contact the SSC in Block B."

    docs = find_relevant_docs(student_message)
    context = build_context(docs)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"{context}\n\nStudent question: {student_message}\n\nAnswer the student following the hard rules above."},
        ],
        "temperature": 0.3,
        "max_tokens": 1000,
    }

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{NVIDIA_BASE_URL}/chat/completions",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
        msg = data["choices"][0]["message"]
        content = msg.get("content") or ""
        if not content:
            content = _extract_final_answer(msg.get("reasoning_content") or "")
        return content or "I could not generate a reply. Please try again."
    except httpx.HTTPStatusError as exc:
        return f"I'm temporarily unable to answer (API error {exc.response.status_code}). Please contact the SSC in Block B or try again later."
    except Exception as exc:  # pragma: no cover - runtime safety
        return f"I'm temporarily unable to answer. Please contact the SSC in Block B or try again later. ({exc})"
