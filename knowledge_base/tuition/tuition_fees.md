---
category: tuition
menu_title: "Tuition Fees"
menu_number: 1
keywords: ["1", "tuition", "tuition fees", "fees", "payment", "kaspi", "оплата", "оплата обучения", "стоимость обучения", "платить за учебу", "оқу ақысы", "төлем", "төлеу"]
menu_summary: >
  Each semester a student can choose between 20-42 ECTS courses and needs
  to make payment accordingly before the start of the semester. Tuition
  fees differ between Multidisciplinary courses (MDE) and Professional
  program courses. Payments can be made online via the Kaspi app.
academic_year: "2026-2027"
source_url: https://sdu.edu.kz/en/tuition-fees/
last_verified: 2026-10-01
language: en
authorized: true
notes: >
  Per-program fee tables (Bachelor/Master/PhD breakdown by specialty) are
  published on the source page as downloadable documents rendered via
  JavaScript; they could not be captured as static PDFs during this fetch.
  The bot should dispatch the direct page link (US-04, link mode) for
  students who need the exact per-program fee table, since the figures
  vary significantly by educational program and are updated yearly.
---

# Tuition Fees at SDU University

## Fee Structure
- SDU uses the ECTS (European Credit Transfer System) credit model.
- Multidisciplinary Education (MDE) courses are billed at a different
  per-credit rate than Professional Program (major-specific) courses.
- Each educational program (major) has its own professional-program
  course fee — fees are **not uniform across all majors**.
- Each semester, a student selects between **20 and 42 ECTS credits** of
  coursework and must pay the corresponding tuition before the semester
  starts.

## Graduation Credit Requirements
| Degree | Required ECTS credits |
|---|---|
| Bachelor's | 240 ECTS |
| Master's | 120 ECTS |
| PhD | 180 ECTS |

## Where to Find Exact Fee Amounts
The university publishes year-specific and program-specific fee tables
(e.g. "Tuition fees 2026-2027 Bachelor", "Tuition fees 2026-2027 Master",
"Tuition fees 2026-2027 PhD", plus prior-year tables for 2nd/3rd/4th-year
cohorts) and a formal "Tuition Fee Rules" document on the official page.
Because the exact per-program amount depends on the student's major and
cohort year, the bot should direct students to the official Tuition Fees
page rather than quoting a single number.

## Payment
- Online payment is available via Kaspi.kz and the university's online
  payment portal.
- The official bank details (for wire transfer) are published on the
  university's accommodation/payment pages (institution: Suleyman Demirel
  University; BIN 960240000550; SWIFT HSBKKZKX; Halyk Bank of Kazakhstan).

## Tuition Discounts & SDU Grants
This public page does not list discount percentages or benefit rules —
for those, the official regulation `tuition_fees_regulation.pdf`
(and its summary at
`knowledge_base/academic_regulations/tuition_fees_regulation.md`) covers
discount types, application windows, the "Best student in speciality"
50% discount, and SDU Grant conditions. Answer discount/grant questions
from that regulation file instead of this one.

## Not Covered Here
Neither this file nor the tuition fees regulation documents a literal
"pay tuition in installments across the semester" plan — tuition is due
in full before the semester starts (see Fee Structure above). If a
student specifically asks about splitting one semester's payment into
multiple installments, the bot must say this information is not in the
knowledge base and refer them to the Student Service Center (SSC) in
Block B, per SOUL.md's "no extrapolation" rule. Refunds and
payment-deadline extensions are also not documented anywhere and should
get the same safe-failure response.
