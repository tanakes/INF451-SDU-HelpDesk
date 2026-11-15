---
category: academic_regulations
status: AUTHORIZED
related_user_story: US-03 (University Knowledge Base Setup)
related_constraint: "US-03 Constraints A17 — restricted/portal-authenticated documents required stakeholder authorization before public dispatch; authorization has now been received"
related_stakeholder: "University Administration / Academic Advisor (Authorizing Stakeholder) — US-03 Stakeholders C3"
---

# Rules and Regulations — Authorized for Public Use

This folder contains 32 official SDU University policy and regulation
PDFs (provided by the project team via `uploads/rules-and-regulations.zip`),
covering admissions, assessment, examinations, academic integrity,
tuition, scholarships, AI-use policy, and related institutional
regulations — each with a companion `.md` summary for direct bot
grounding.

## Authorization Status

**AUTHORIZED.** Per US-03 constraint A17, these documents required
sign-off from the Authorizing Stakeholder (University Administration /
Academic Advisor) before the bot could use or dispatch them. That
authorization has been confirmed by the project owner and is recorded in
`manifest.json` (`"status": "AUTHORIZED"`, every document's `"authorized"`
flag set to `true`).

**Recommendation for formalization**: the current `authorized_by` field
in `manifest.json` is a generic placeholder ("Project team"). For a real
production deployment or for audit/compliance purposes, this should be
replaced with the actual named Authorizing Stakeholder and a verifiable
approval date/record (e.g. an email, signed memo, or governance board
minutes reference), consistent with how the regulations themselves cite
specific board protocol numbers and dates.

## What Changed from the Previous (Pending) State

- `manifest.json`: all 32 `"authorized"` fields flipped from `false` to
  `true`; top-level `status` changed from `PENDING_AUTHORIZATION` to
  `AUTHORIZED`.
- `SOUL.md`: the hard block preventing the bot from reading this folder
  has been removed; the bot can now ground answers in these summaries
  and dispatch the original PDFs via `documents/manifest.json`.
- Each PDF now has a matching `.md` summary file (e.g.
  `academic_integrity_policy.pdf` → `academic_integrity_policy.md`)
  giving the bot structured, student-facing grounding content instead of
  requiring full-PDF parsing at answer time.

## Inventory

32 documents spanning: academic integrity, academic leave, academic
mobility, academic performance monitoring, admissions, AI-startup final
attestation, AI tools use in academic activities, assessment policy,
bachelor/master graduate competency models (Russian), doctoral research
practice rules for the Applied Law PhD program (2 revisions, Russian,
scanned/OCR-limited), dual education organization, educational process
organization (credit technology), final assessment regulations (School
of Social Sciences, Business and Law), LMS Moodle usage, master's
research practice guidelines (Kazakh), migration policy (Russian),
non-formal education, occupational health & safety (chemistry
laboratory), office hours guidelines, offline/online examination rules,
pedagogical retraining program (Russian), PhD/Master's scientific
internship guidelines, reasonable adjustment for students with
disabilities, scholarship and grant programs, state education grant
vacancies (Kazakh), transfer & readmission policy, transfer &
reinstatement memo, tuition fees regulation, and Turnitin policy.

See `manifest.json` for the complete file-by-file list including
language tags and the `md_summary` filename for each PDF.

## Known Limitations
- Two documents (`doctoral_research_practice_rules_law_program_v1_ru.pdf`
  and `..._v2_ru.pdf`) are scanned images without a text layer, and
  Russian OCR was not available in this environment. Their `.md`
  summaries are based only on title-page/header information, not full
  content — flagged with `ocr_quality_warning: true` in their front
  matter.
- Several documents are Russian- or Kazakh-only in their original form
  (competency models, migration policy, pedagogical retraining, state
  grant vacancies, master's research practice). Their `.md` summaries
  are written in English for bot grounding, but the bot should disclose
  that the authoritative source document is in Russian/Kazakh when
  dispatching the original PDF.
