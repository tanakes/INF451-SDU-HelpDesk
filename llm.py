"""LLM integration for the SDU Help Desk Bot.

Builds a system prompt distilled from SOUL.md rules and calls Gemini.
All output must follow Telegram formatting rules: zero asterisks, double line
breaks between paragraphs, no Markdown headings (#, ##).
"""
from __future__ import annotations

import os
from typing import List

import google.generativeai as genai

from knowledge_base import KBDoc, find_relevant_docs


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


def _configure_gemini(api_key: str):
    genai.configure(api_key=api_key)


def build_context(docs: List[KBDoc]) -> str:
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


async def answer(student_message: str, api_key: str, model_name: str = "gemini-1.5-flash") -> str:
    _configure_gemini(api_key)
    docs = find_relevant_docs(student_message)
    context = build_context(docs)

    model = genai.GenerativeModel(model_name, system_instruction=SYSTEM_PROMPT)
    prompt = (
        f"{context}\n\n"
        f"Student question: {student_message}\n\n"
        "Answer the student following the hard rules above."
    )
    try:
        result = await model.generate_content_async(prompt)
        return result.text or "I could not generate a reply. Please try again."
    except Exception as exc:  # pragma: no cover - runtime safety
        return f"I'm temporarily unable to answer. Please contact the SSC in Block B or try again later. ({exc})"
