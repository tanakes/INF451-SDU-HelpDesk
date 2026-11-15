#!/usr/bin/env python3
"""
Builds a plain-language, step-by-step ODT walkthrough of Sprint 2 (US-03, US-04)
implementation, with explicit "SCREENSHOT THIS" markers.
"""
from odf.opendocument import OpenDocumentText
from odf.style import (Style, TextProperties, ParagraphProperties, FontFace,
                        GraphicProperties)
from odf.text import H, P, List, ListItem, Span, LineBreak
from odf.draw import Frame, Image

doc = OpenDocumentText()

# ---------- Fonts ----------
doc.fontfacedecls.addElement(FontFace(name="Arial", fontfamily="Arial"))
doc.fontfacedecls.addElement(FontFace(name="Consolas", fontfamily="Consolas"))

# ---------- Styles ----------
def add_style(name, family, props_list):
    s = Style(name=name, family=family)
    for p in props_list:
        s.addElement(p)
    doc.styles.addElement(s)
    return s

title_style = add_style("TitleStyle", "paragraph", [
    TextProperties(fontsize="24pt", fontweight="bold", color="#0b3d5c", fontfamily="Arial"),
    ParagraphProperties(marginbottom="4mm", margintop="6mm"),
])
subtitle_style = add_style("SubtitleStyle", "paragraph", [
    TextProperties(fontsize="13pt", color="#16899b", fontfamily="Arial"),
    ParagraphProperties(marginbottom="10mm"),
])
h1_style = add_style("H1Style", "paragraph", [
    TextProperties(fontsize="16pt", fontweight="bold", color="#0b3d5c", fontfamily="Arial"),
    ParagraphProperties(margintop="8mm", marginbottom="3mm", breakbefore="page"),
])
h1_nobreak_style = add_style("H1NoBreakStyle", "paragraph", [
    TextProperties(fontsize="16pt", fontweight="bold", color="#0b3d5c", fontfamily="Arial"),
    ParagraphProperties(margintop="4mm", marginbottom="3mm"),
])
h2_style = add_style("H2Style", "paragraph", [
    TextProperties(fontsize="13pt", fontweight="bold", color="#0e5571", fontfamily="Arial"),
    ParagraphProperties(margintop="6mm", marginbottom="2mm"),
])
h3_style = add_style("H3Style", "paragraph", [
    TextProperties(fontsize="11pt", fontweight="bold", color="#333333", fontfamily="Arial"),
    ParagraphProperties(margintop="4mm", marginbottom="2mm"),
])
body_style = add_style("BodyStyle", "paragraph", [
    TextProperties(fontsize="10.5pt", fontfamily="Arial"),
    ParagraphProperties(marginbottom="2.5mm", lineheight="130%"),
])
quote_style = add_style("QuoteStyle", "paragraph", [
    TextProperties(fontsize="10pt", fontstyle="italic", fontfamily="Consolas", color="#1f2937"),
    ParagraphProperties(marginbottom="2mm", margintop="2mm",
                         marginleft="5mm", padding="2mm",
                         backgroundcolor="#eef2f6", borderleft="3pt solid #0b3d5c"),
])
step_label_style = add_style("StepLabelStyle", "text", [
    TextProperties(fontweight="bold", color="#ffffff", fontsize="9pt"),
])
impl_label = add_style("ImplLabelStyle", "text", [
    TextProperties(fontweight="bold", color="#227a3a", fontsize="9.5pt"),
])
demo_label = add_style("DemoLabelStyle", "text", [
    TextProperties(fontweight="bold", color="#a9711f", fontsize="9.5pt"),
])
shot_label = add_style("ShotLabelStyle", "text", [
    TextProperties(fontweight="bold", color="#ffffff", backgroundcolor="#c0392b", fontsize="9.5pt"),
])
cov_label = add_style("CovLabelStyle", "text", [
    TextProperties(fontweight="bold", color="#4b5563", fontsize="9.5pt"),
])
bold_inline = add_style("BoldInline", "text", [TextProperties(fontweight="bold")])
code_inline = add_style("CodeInline", "text", [
    TextProperties(fontfamily="Consolas", fontsize="9.5pt", color="#0b3d5c", backgroundcolor="#eef2f6"),
])

impl_block_style = add_style("ImplBlockStyle", "paragraph", [
    TextProperties(fontsize="10pt", fontfamily="Arial"),
    ParagraphProperties(marginbottom="2mm", margintop="1mm", marginleft="5mm",
                         padding="2mm", backgroundcolor="#eef7f0", borderleft="3pt solid #2f9e44"),
])
demo_block_style = add_style("DemoBlockStyle", "paragraph", [
    TextProperties(fontsize="10pt", fontfamily="Arial"),
    ParagraphProperties(marginbottom="2mm", margintop="1mm", marginleft="5mm",
                         padding="2mm", backgroundcolor="#fff6e8", borderleft="3pt solid #e8a33d"),
])
shot_block_style = add_style("ShotBlockStyle", "paragraph", [
    TextProperties(fontsize="10pt", fontfamily="Arial", fontweight="bold"),
    ParagraphProperties(marginbottom="3mm", margintop="1mm", marginleft="5mm",
                         padding="2mm", backgroundcolor="#fdf2f2", borderleft="3pt solid #c0392b"),
])
cov_block_style = add_style("CovBlockStyle", "paragraph", [
    TextProperties(fontsize="9.8pt", fontfamily="Arial"),
    ParagraphProperties(marginbottom="4mm", margintop="1mm", marginleft="5mm",
                         padding="2mm", backgroundcolor="#f8f8fb"),
])
list_style = add_style("ListParaStyle", "paragraph", [
    TextProperties(fontsize="10.3pt", fontfamily="Arial"),
    ParagraphProperties(marginbottom="1.5mm", marginleft="4mm"),
])

# ---------- Helpers ----------
def para(style, text=None, bold_runs=None):
    p = P(stylename=style)
    if text is not None:
        p.addText(text)
    return p

def rich_para(style, parts):
    """parts: list of (text, inline_style_or_None)"""
    p = P(stylename=style)
    for text, st in parts:
        if st:
            p.addElement(Span(stylename=st, text=text))
        else:
            p.addText(text)
    return p

def bullet(text):
    doc.text.addElement(para(list_style, "• " + text))

def quote(cell_ref, text):
    p = P(stylename=quote_style)
    p.addElement(Span(stylename=step_label_style, text=f" {cell_ref} "))
    p.addText("  " + text)
    doc.text.addElement(p)

def implemented(text):
    p = P(stylename=impl_block_style)
    p.addElement(Span(stylename=impl_label, text="HOW IT WAS IMPLEMENTED: "))
    p.addText(text)
    doc.text.addElement(p)

def demonstrate(text):
    p = P(stylename=demo_block_style)
    p.addElement(Span(stylename=demo_label, text="HOW TO SHOW THE TEACHER: "))
    p.addText(text)
    doc.text.addElement(p)

def screenshot(text):
    p = P(stylename=shot_block_style)
    p.addElement(Span(stylename=shot_label, text=" 📷 SCREENSHOT THIS "))
    p.addText("  " + text)
    doc.text.addElement(p)

def covered(items):
    p = P(stylename=cov_block_style)
    p.addElement(Span(stylename=cov_label, text="This same step also already covers: "))
    doc.text.addElement(p)
    for it in items:
        doc.text.addElement(para(list_style, "• " + it))

def h1(text):
    doc.text.addElement(H(outlinelevel=1, stylename=h1_style, text=text))

def h1_nobreak(text):
    doc.text.addElement(H(outlinelevel=1, stylename=h1_nobreak_style, text=text))

def h2(text):
    doc.text.addElement(H(outlinelevel=2, stylename=h2_style, text=text))

def h3(text):
    doc.text.addElement(H(outlinelevel=3, stylename=h3_style, text=text))

def body(text):
    doc.text.addElement(para(body_style, text))

def code(text):
    """inline code paragraph standalone"""
    p = P(stylename=body_style)
    p.addElement(Span(stylename=code_inline, text=text))
    doc.text.addElement(p)

# =========================================================================
# COVER
# =========================================================================
doc.text.addElement(para(title_style, "SDU Help Desk Bot — Sprint 2 Walkthrough"))
doc.text.addElement(para(subtitle_style,
    "A plain-language, step-by-step guide to how US-03 (Knowledge Base) and "
    "US-04 (Document & Guide Dispatch) were built on the Buda platform — "
    "with exact screenshot instructions."))
body("This document explains Sprint 2 from scratch, assuming no prior knowledge of how the "
     "Buda AI agent platform works. Each numbered step follows the same pattern:")
bullet("The exact task we had to satisfy (quoted directly from the project spreadsheet).")
bullet("What we actually built or changed, in plain words.")
bullet("How to prove it works live, in front of the teacher.")
bullet("Exactly which screen or file to screenshot, and why that screenshot matters.")
body("")
body("First, a 2-minute primer on how the bot works at all, since everything else in this "
     "document refers back to these three pieces.")

# =========================================================================
# SECTION 0 — HOW THE BOT WORKS (PRIMER)
# =========================================================================
h1_nobreak("0. How the Buda bot actually works (read this first)")

body("The bot is not a traditional app with its own database and backend code. It is an AI "
     "agent running on the Buda platform. Three things make it behave the way it does:")

h2("0.1 — Telegram is just the \"front door\"")
body("Buda has a built-in connector that links an agent directly to a Telegram bot account. "
     "Students type messages in Telegram; Buda forwards them to the agent and sends the "
     "agent's reply back. No custom server was written for this — it is a built-in feature of "
     "the platform, turned on in the agent's settings.")

h2("0.2 — SOUL.md is the agent's \"brain\" / rulebook")
body("SOUL.md is a plain-text file that lives in the agent's Drive. It is not code — it is "
     "written in normal English, as a set of instructions the AI reads before answering any "
     "message. Think of it as the employee handbook the bot has to follow: what tone to use, "
     "what it is and isn't allowed to say, and — most importantly for Sprint 2 — exactly where "
     "it is allowed to get its facts from.")
screenshot("Open SOUL.md in the Drive tab (or any text editor showing it) so the file is "
           "visible on screen. You will reuse this same open file for several steps below — "
           "just scroll to the relevant part each time.")

h2("0.3 — knowledge_base/ and documents/manifest.json are the \"facts\" the bot is allowed to use")
body("These are regular files and folders sitting in the agent's Drive, exactly like files in "
     "a normal folder on your computer. SOUL.md tells the bot: \"only use facts from these "
     "specific files, never make something up.\" Sprint 2 was mostly about building these files "
     "correctly and writing the SOUL.md rules that point to them.")
screenshot("Open the Drive tab and show the folder tree: sdu-helpdesk-bot/knowledge_base/ "
           "and sdu-helpdesk-bot/documents/manifest.json. This single screenshot proves these "
           "are real files on the agent's Drive, not something invented for the demo.")

body("With that primer done, the rest of this document walks through US-03 and US-04 exactly "
     "as they are written in the project spreadsheet, cell by cell.")

# =========================================================================
# SECTION 1 — US-03
# =========================================================================
h1("1. US-03 — University Knowledge Base Setup")

body("The user story, quoted exactly from the spreadsheet:")
quote("US-03 ! A3", "University Knowledge Base Setup: As a Student, I want the bot to answer "
      "common questions regarding tuition, registration, and academic policies, so that I "
      "receive immediate, accurate guidance based on official university rules.")
quote("US-03 ! C3", "Stakeholders: Student, University Administration / Academic Advisor "
      "(Authorizing Stakeholder)")

body("In plain words: the bot must answer from real SDU documents, not from guesses, and the "
     "university must have a say in which documents it is allowed to use.")

h2("Step 1 — Collect the official documents (Responsibility A5)")
quote("US-03 ! A5", "Collect official SDU documents covering the agreed help desk categories: "
      "tuition fees, course add/drop, dormitory, transcripts and academic regulations.")
implemented(
    "We pulled real content from the official SDU website (sdu.edu.kz) for the 4 everyday "
    "topics — tuition fees, course registration/academic calendar, dormitory, and transcripts "
    "— and we collected 32 official SDU regulation PDFs (admissions rules, academic integrity "
    "policy, exam rules, tuition regulation, scholarships, etc.) that the project team provided."
)
demonstrate(
    "Open the Drive tab, go into sdu-helpdesk-bot/knowledge_base/, and show the 5 folders: "
    "tuition, registration, dormitory, transcripts, academic_regulations."
)
screenshot(
    "The knowledge_base/ folder with all 5 category folders visible. This is the direct proof "
    "that official content for every required category was actually collected, not just "
    "planned."
)

h2("Step 2 — Put the documents on the agent's Drive (Responsibility A6)")
quote("US-03 ! A6", "Upload the collected documents to the agent's Buda Drive so that they "
      "form the searchable knowledge base used by the agent.")
implemented(
    "Every piece of collected content was saved as a real file inside "
    "sdu-helpdesk-bot/knowledge_base/ on the agent's own Drive — not an external link, not a "
    "separate database. The agent can read these files directly whenever it needs an answer."
)
demonstrate(
    "Open sdu-helpdesk-bot/knowledge_base/academic_regulations/ specifically, and scroll "
    "through it — you will see 32 PDF files, and next to each one a matching .md file with the "
    "same name."
)
screenshot(
    "The academic_regulations/ folder showing PDF + .md file pairs side by side (e.g. "
    "academic_integrity_policy.pdf next to academic_integrity_policy.md). This proves the raw "
    "official document and its bot-readable summary both really exist."
)

h2("Step 3 — Force the bot to only use these documents, never guess (Responsibility A7)")
quote("US-03 ! A7", "Ensure the agent answers student questions from the uploaded university "
      "documents rather than from general model knowledge.")
implemented(
    "This is a rule written directly into SOUL.md. The exact sentence the bot follows is:"
)
code('"Base all answers strictly on /agent/sdu-helpdesk-bot/knowledge_base/'
     '{tuition,registration,dormitory,transcripts,academic_regulations}/*.md"')
body("SOUL.md also has a second rule for when a detail simply isn't written down anywhere, "
     "so the bot can't quietly make something up, plus a reminder to check BOTH the public-page "
     "summary and its linked official regulation file before concluding something is missing "
     "(discount/benefit detail often lives only in the regulation file). The exact example built "
     "into SOUL.md is:")
code('If asked "Can I pay in installments?" — after checking the tuition_fees.md file AND its '
     "linked tuition_fees_regulation.md — no document describes splitting one semester's "
     'payment into parts, so the bot must say: "I do not have information about splitting '
     'tuition into installments within a semester in my knowledge base. Please visit the '
     'Student Service Center (SSC) in Block B for assistance." (Note: discounts and SDU Grant '
     'benefits ARE documented in the regulation file — a discount question gets answered from '
     'there instead of this safe-failure response.)')
demonstrate(
    "In Telegram, ask the bot something that sounds related to tuition but is not actually "
    "written in any file, e.g. \"Can I pay tuition in installments?\" The bot should say it "
    "doesn't have that information instead of inventing a plausible-sounding answer. Then, as "
    "a contrast, ask \"Do you have any tuition discounts?\" and show the bot answering correctly "
    "from the regulation file instead of giving the same safe-failure response."
)
screenshot(
    "Scroll to the \"NO Extrapolation or Plausible Inventions\" part of SOUL.md (Core Truth "
    "#1) showing the exact quoted rule above. Then also screenshot the two live Telegram replies "
    "(installments = not available, discounts = answered from the regulation file), so the rule "
    "and both real-world outcomes are documented together."
)
covered([
    "Test script A25 (Fail case): \"Knowledge base is empty or not indexed; the agent answers "
    "from general model knowledge instead of university documents\" — this is exactly the "
    "mistake this rule prevents.",
    "US-03-QA Scenario 1: \"Answer is grounded in official university documents\" / \"The "
    "answer contains no details that are absent from the source document.\"",
    "US-03-QA Rule B41: \"Answers must be grounded in the uploaded university documents rather "
    "than in general model knowledge.\"",
])

h2("Step 4 — Make the knowledge base power the topic menu too (Responsibility A8)")
quote("US-03 ! A8", "Provide the content layer that the US-02 topic menu and the US-06 "
      "automatic query classification depend on.")
implemented(
    "Each of the 4 everyday-topic files (tuition_fees.md, academic_calendar.md, "
    "boys_dormitory.md, student_service_center.md) has a small information block at the very "
    "top of the file (called \"front-matter\") that stores the menu number, keywords, and a "
    "short summary for that topic. This means the Sprint 1 menu and the Sprint 2 deep answers "
    "both read from the exact same file — there is only one place to update per topic, not two."
)
demonstrate(
    "Open knowledge_base/tuition/tuition_fees.md in the Drive tab. At the very top you'll see "
    "fields like menu_number: 1 and a list of keywords. In Telegram, type 1 or tuition and show "
    "the short summary text coming back — it matches the menu_summary field in that same file."
)
screenshot(
    "The top of tuition_fees.md showing the menu_title, menu_number, keywords, and "
    "menu_summary fields. Then screenshot the Telegram reply after typing \"tuition\" or \"1\" "
    "next to it, so the file field and the bot's real reply can be compared directly."
)
covered([
    "Constraint A15: \"Knowledge base categories must match the topic menu defined in US-02 "
    "and the classification categories in US-06\" — guaranteed automatically, since the menu "
    "data lives inside the same file as the deep-answer data.",
])

h2("Step 5 — Tell the student honestly when something isn't covered (Responsibility A9)")
quote("US-03 ! A9", "Inform the student when a requested topic is not covered by the "
      "knowledge base.")
implemented(
    "SOUL.md has a dedicated section for this exact situation, with the exact wording the bot "
    "must use:"
)
code('"I can currently only assist with our 4 quick topics below. For other inquiries, please '
     'consult the official SDU website or visit the Student Service Center (SSC) in Block B," '
     'followed by the 4-topic menu again.')
demonstrate(
    "Ask something completely outside scope, like \"What's the Wi-Fi password on campus?\" and "
    "show the bot politely declining and re-showing the menu, instead of trying to guess."
)
screenshot(
    "The live Telegram reply to an out-of-scope question, showing the polite decline + "
    "re-shown menu."
)
covered([
    "US-03-QA Scenario 3: \"Out-of-scope question is handled safely\" / \"The bot does not "
    "invent an answer from general model knowledge.\"",
    "US-03-QA Rule B42: \"When a topic is not covered by the knowledge base, the bot must state "
    "this instead of generating an answer.\"",
])

h2("Step 6 — Get permission before using restricted documents (Responsibility A10)")
quote("US-03 ! A10", "Obtain formal authorization from the academic advisor or university "
      "administration to access, index, and publicly serve internal portal-restricted \"Rules "
      "and Regulations\" documents.")
implemented(
    "This is a permissions/governance step, not a coding step. All 32 regulation PDFs were "
    "initially locked behind a \"PENDING_AUTHORIZATION\" flag in a manifest file — meaning the "
    "bot was technically blocked from using them at all until someone approved it. After the "
    "project owner confirmed authorization was granted, every one of the 32 documents was "
    "flipped from \"not allowed\" to \"authorized: true\" in that same manifest file."
)
demonstrate(
    "Open knowledge_base/academic_regulations/manifest.json and show the top-level "
    "\"status\": \"AUTHORIZED\" field, plus a couple of the per-document \"authorized\": true "
    "entries further down."
)
screenshot(
    "The top of manifest.json showing \"status\": \"AUTHORIZED\" and the "
    "\"authorization_required_from\" field noting authorization was received. This is the "
    "proof that the permission step genuinely happened and is recorded, not skipped."
)
covered([
    "Constraint A17: \"Documents restricted behind student portal authentication must only be "
    "ingested after obtaining explicit stakeholder approval.\"",
    "US-03-QA Rule B43: \"Internal portal documents requiring student authentication must have "
    "verified administrative approval before being added to the public knowledge base.\"",
])

h2("Step 7 — Only use real SDU sources, and keep them current (Constraints A13, A14)")
quote("US-03 ! A13", "Only official SDU sources may be used; unverified or external content "
      "must not be added to the knowledge base.")
quote("US-03 ! A14", "All documents must be current for the active academic year.")
implemented(
    "Every knowledge_base .md file has a small field at the top recording exactly where its "
    "content came from (source_url, e.g. the official sdu.edu.kz page) and when it was last "
    "checked (last_verified: 2026-10-01) or which academic year it covers "
    "(academic_year: \"2026-2027\")."
)
demonstrate(
    "Open any knowledge_base/*.md file and point to its source_url and last_verified fields at "
    "the top. In Telegram, ask about a different academic year (e.g. \"What was the deadline in "
    "2024?\") and show the bot explicitly saying it only has 2026–2027 data."
)
screenshot(
    "The source_url / last_verified / academic_year fields at the top of any one .md file, "
    "e.g. academic_calendar.md."
)
covered([
    "Test script A26 (Fail case): \"The agent returns information taken from an outdated "
    "academic-year document\" — prevented by the same currency check.",
    "US-03-QA Scenario 4: \"Outdated information is not served.\"",
    "US-03-QA Rule B38: \"The knowledge base must contain only official SDU sources.\"",
    "US-03-QA Rule B39: \"All documents in the knowledge base must be current for the active "
    "academic year.\"",
])

h2("Step 8 — Keep each category's content inside its own folder (QA Scenario 5)")
quote("US-03-QA ! Scenario 5", "Knowledge base supports automatic query classification — "
      "\"The documents are organized according to the agreed category list\" / \"The content "
      "retrieved by the bot belongs to that same category.\"")
implemented(
    "Every .md file has a category field matching the folder it physically lives in (e.g. the "
    "file inside the dormitory/ folder has category: dormitory). Because the file's location "
    "and its tag always match, a dormitory question can never accidentally pull in a tuition "
    "answer."
)
demonstrate(
    "Ask a dormitory-only question in Telegram and show the answer citing the dormitory source "
    "— never a tuition or transcript source."
)
screenshot(
    "The category: field at the top of any one .md file, matched against the folder it's "
    "sitting in on the Drive tab."
)

body("")
body("All of US-03's remaining spreadsheet cells (test scripts, maintenance tasks) describe "
     "testing and upkeep work that was carried out using the exact same files shown above — "
     "they do not require any separate screenshot.")

# =========================================================================
# SECTION 2 — US-04
# =========================================================================
h1("2. US-04 — Document & Guide Dispatch")

quote("US-04 ! A3", "Document & Guide Dispatch: As a Student, I want the bot to provide direct "
      "links and official PDF guides (academic calendars, petition forms) in our Telegram "
      "chat, so that I do not need to search through university portals.")
body("In plain words: when a student asks for a specific document, the bot should hand it over "
     "directly in the chat (a link or an actual file) — never make the student go hunting on "
     "the website themselves, and never send something fake.")

h2("Step 1 — Build the dispatch rulebook (documents/manifest.json)")
body("Before explaining the individual responsibilities, it helps to see the one file that "
     "powers all of US-04: documents/manifest.json. It is a simple list; each entry says which "
     "document it is, and whether the bot should send a link, send an actual file, or say it's "
     "unavailable.")
screenshot(
    "Open documents/manifest.json in the Drive tab and show 2–3 entries, including one with "
    "\"dispatch_mode\": \"link\" (e.g. academic_calendar) and one with \"dispatch_mode\": "
    "\"file\" (e.g. tuition_fees_regulation_pdf)."
)

h2("Step 2 — Send direct links for pages that only exist as a website (Responsibility A5)")
quote("US-04 ! A5", "Provide students with direct links to official university resources "
      "through the Telegram chat.")
implemented(
    "4 manifest entries use \"dispatch_mode\": \"link\" — the academic calendar, the tuition "
    "fees page, the dormitory page, and the student service center page. SOUL.md tells the bot "
    "exactly how to use these: \"share the exact url from the manifest as plain text... do not "
    "alter, shorten, or guess at the URL.\" Telegram automatically shows a link preview for "
    "plain URLs, so the student sees it directly in the chat."
)
demonstrate(
    "In Telegram, type \"send me the academic calendar\" and show the official URL arriving "
    "with Telegram's own automatic link preview."
)
screenshot(
    "The live Telegram reply to \"send me the academic calendar,\" showing the correct URL and "
    "its auto-generated preview."
)

h2("Step 3 — Send real PDF files when they exist (Responsibility A6)")
quote("US-04 ! A6", "Provide official PDF guides such as academic calendars, petition forms, "
      "and other relevant academic documents.")
implemented(
    "2 manifest entries use \"dispatch_mode\": \"file\" — the official Tuition Fees "
    "Regulation PDF, and a folder-level entry covering all 32 authorized regulation PDFs. For "
    "these, SOUL.md tells the bot to actually attach the file to the chat, not just describe "
    "it or link to it."
)
demonstrate(
    "In Telegram, ask \"send me the Academic Integrity Policy PDF\" and show the real PDF "
    "file arriving as a Telegram attachment that can be opened or downloaded."
)
screenshot(
    "The live Telegram reply showing the actual PDF file attached in the chat (not a link, an "
    "actual document bubble)."
)
covered([
    "Test script A19 (Pass): \"Student requests a petition form, and the bot provides the "
    "corresponding official form or PDF\" — see Step 5 below for why petition forms "
    "specifically are the one exception to this.",
])

h2("Step 4 — Match the right document to what the student actually asked for (Responsibility A7)")
quote("US-04 ! A7", "Identify the document or resource requested by the student and return "
      "the corresponding official link or PDF.")
implemented(
    "SOUL.md instructs the bot to match the student's wording against the id and title fields "
    "in the manifest, rather than relying on one exact phrase. This means different ways of "
    "asking for the same thing (\"send me the calendar\" vs. \"when does the semester start\") "
    "both resolve to the same correct entry."
)
demonstrate(
    "Ask for the same document two different ways (e.g. \"tuition fees page\" then later "
    "\"where can I pay tuition\") and show both resolving to the same correct link."
)
screenshot(
    "Two Telegram replies side by side, from two different phrasings, both returning the same "
    "correct resource."
)
covered([
    "Test script A20 (Pass): \"Student requests an available academic document, and the bot "
    "provides the correct official resource directly in the Telegram chat.\"",
    "US-04-QA Scenario 3: \"Requested academic document is matched correctly.\"",
    "US-04-QA Rule B46: \"The requested resource must match the student's request.\"",
])

h2("Step 5 — Never send anything that isn't official, and say so honestly when something "
   "doesn't exist (Responsibilities A8, A9)")
quote("US-04 ! A8", "Ensure that provided resources come from official university sources.")
quote("US-04 ! A9", "Inform the student when the requested document or resource is "
      "unavailable.")
implemented(
    "Every link in the manifest points to an sdu.edu.kz page, and every file comes from the "
    "official rules-and-regulations archive — there is no fallback or alternate source "
    "anywhere in the file. For documents that genuinely don't exist publicly (like petition "
    "forms), the manifest has an honest entry with \"dispatch_mode\": \"unavailable\" instead "
    "of a fake link. SOUL.md backs this up: \"do not substitute a different link or guess at a "
    "form name.\""
)
demonstrate(
    "Ask \"send me the petition form\" in Telegram and show the bot clearly saying it isn't "
    "available and pointing the student to the Student Service Center (SSC) in Block B — not "
    "a broken link, not a guess."
)
screenshot(
    "The live Telegram reply to the petition-form request, showing the honest \"not "
    "available, visit SSC\" message."
)
covered([
    "Constraint A11: \"The solution must provide only official university links and "
    "documents.\"",
    "Constraint A12: \"The bot must not provide unofficial or unverified external resources.\"",
    "Test script A21 (Fail case) and A22 (Fail case): providing an unrelated or broken "
    "document — avoided structurally, since no fake source exists anywhere to accidentally "
    "send.",
    "US-04-QA Scenario 2, 4, 5, and 6: petition-form handling, unavailable-document handling, "
    "preferring official sources, and broken-PDF handling — all covered by this same honest "
    "manifest design.",
    "US-04-QA Rules B44, B47, B48: official-only resources, no unverified substitutes, and "
    "clear messaging instead of silent failure.",
])

h2("Step 6 — Keep everything inside the Telegram chat (Constraint A14)")
quote("US-04 ! A14", "The interaction must remain within the Telegram chat without requiring "
      "the student to search university portals manually.")
implemented(
    "Both dispatch modes finish entirely inside the same Telegram message: a link renders with "
    "Telegram's own preview, and a file arrives as a native Telegram attachment. The bot never "
    "tells a student to \"go check the portal yourself\" for something it actually has."
)
demonstrate(
    "Show that both a link request and a file request are fully resolved without ever leaving "
    "the Telegram chat window."
)
covered([
    "US-04-QA Scenario 1 and 7: resource appearing directly in the chat, and links/PDFs "
    "rendering cleanly without broken formatting.",
    "US-04-QA Rule B49: \"Links and PDF resources must render cleanly and remain accessible "
    "through Telegram.\"",
])

body("")
body("All remaining US-04 maintenance tasks (keeping the manifest updated, re-testing links "
     "periodically) describe ongoing upkeep of the exact same manifest.json file shown above — "
     "no separate screenshot is needed for those.")

# =========================================================================
# SECTION 3 — ONE KNOWN GAP
# =========================================================================
h1("3. One honest gap worth mentioning to the teacher")
body("Petition / request forms (change of major, transcript requests, etc.) are not published "
     "anywhere on the public SDU website as downloadable PDFs. Rather than inventing a fake "
     "form or guessing a filename, the bot was deliberately built to say this is not available "
     "and point the student to the Student Service Center in Block B. This is called out "
     "directly in the manifest file's own reason field for that entry, so it is documented, not "
     "hidden.")
screenshot(
    "The \"petition_forms\" entry inside documents/manifest.json, showing "
    "\"dispatch_mode\": \"unavailable\" and its reason field explaining why."
)

doc.save("/agent/sdu-helpdesk-bot/writeup/SDU_HelpDesk_Sprint2_StepByStep.odt")
print("saved")
