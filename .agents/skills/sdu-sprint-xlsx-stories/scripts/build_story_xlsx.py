"""
Generic generator for SDU Help Desk Bot user-story + QA xlsx sheets.

Produces two worksheets per user story — "USER STORY" format and "QA" format —
matching the exact cell layout used in the real project spreadsheet's
US-01/US-01-QA and US-02/US-02-QA sheets (the good examples). Output is a
standalone .xlsx the user copy-pastes as new tabs into the master spreadsheet,
since this tool has no live write access to Google Sheets.

Usage:
    python3 build_story_xlsx.py path/to/story_data.py path/to/output.xlsx

story_data.py must define a module-level STORIES list — see
scripts/story_schema_template.py for the annotated schema and
scripts/us05_reference_example.py for a filled worked example.
"""
import importlib.util
import sys
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.utils import get_column_letter

BOLD = Font(bold=True)
HEADER_FILL = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
WRAP = Alignment(wrap_text=True, vertical="top")


def load_module(path):
    spec = importlib.util.spec_from_file_location("story_data", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def set_col_widths(ws, widths):
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w


def write_cell(ws, coord, value, bold=False, fill=False, wrap=True):
    cell = ws[coord]
    cell.value = value
    if bold:
        cell.font = BOLD
    if fill:
        cell.fill = HEADER_FILL
    if wrap:
        cell.alignment = WRAP


def build_user_story_sheet(wb, sheet_name, story):
    """
    Matches the real US-01 / US-02 sheet layout exactly:
      A2: '"User Story"'            C2: 'Stakeholders:'
      A3: <full story text>         C3: <stakeholder(s)>
      A4: 'responsibilities'
      A5..: one responsibility per row
      A(n): 'constraints'
      A(n+1..): one constraint per row
      A(n): 'tags'
      A(n+1): 'Volatility = ..., Priority = ..., Effort = ..., Sprint = ...'
      A(n): 'test scripts'
      A(n+1..): 'System: (Pass|Fail|Deferred) ...'
      A(n): 'maintenance'
      A(n+1..): 'Task (New|Verified): ...'
    """
    ws = wb.create_sheet(sheet_name)
    set_col_widths(ws, [90, 2, 30])

    write_cell(ws, "A2", '"User Story"', bold=True, fill=True)
    write_cell(ws, "C2", "Stakeholders:", bold=True, fill=True)
    write_cell(ws, "A3", story["story_text"])
    write_cell(ws, "C3", story["stakeholders"])

    r = 4
    write_cell(ws, f"A{r}", "responsibilities", bold=True, fill=True)
    r += 1
    for resp in story["responsibilities"]:
        write_cell(ws, f"A{r}", resp)
        r += 1

    write_cell(ws, f"A{r}", "constraints", bold=True, fill=True)
    r += 1
    for c in story["constraints"]:
        write_cell(ws, f"A{r}", c)
        r += 1

    write_cell(ws, f"A{r}", "tags", bold=True, fill=True)
    r += 1
    write_cell(ws, f"A{r}", story["tags"])
    r += 1

    write_cell(ws, f"A{r}", "test scripts", bold=True, fill=True)
    r += 1
    for t in story["test_scripts"]:
        write_cell(ws, f"A{r}", t)
        r += 1

    write_cell(ws, f"A{r}", "maintenance", bold=True, fill=True)
    r += 1
    for m in story["maintenance"]:
        write_cell(ws, f"A{r}", m)
        r += 1

    return ws


def build_qa_sheet(wb, sheet_name, story):
    """
    Matches the real US-01-QA / US-02-QA sheet layout exactly:
      A1: '<ID> QA Tests'
      A2: 'User Story: <ID> <Title>'
      A3: <full story text>
      A5: 'The Given/When/Then Acceptance Criteria'
      A6: 'Scenario 1'      B6: <scenario name>
      A7: 'Given'           B7: ...
      A8: 'When'            B8: ...
      A9: 'Then'            B9: ...
      A10: 'And'            B10: ... (optional, repeatable)
      ... one block per scenario ...
      A(n): 'Rule-oriented acceptance criteria'
      A(n+1..): 'Rule'      B(n+1..): <rule text>
    """
    ws = wb.create_sheet(sheet_name)
    set_col_widths(ws, [20, 95])

    write_cell(ws, "A1", f"{story['id']} QA Tests", bold=True, fill=True)
    write_cell(ws, "A2", f"User Story: {story['id']} {story['title']}", bold=True)
    write_cell(ws, "A3", story["story_text"])

    r = 5
    write_cell(ws, f"A{r}", "The Given/When/Then Acceptance Criteria", bold=True, fill=True)
    r += 1

    for i, scenario in enumerate(story["scenarios"], start=1):
        write_cell(ws, f"A{r}", f"Scenario {i}", bold=True)
        write_cell(ws, f"B{r}", scenario["name"])
        r += 1
        for step in scenario["steps"]:
            # step = (label, text) where label is 'Given'/'When'/'Then'/'And'
            write_cell(ws, f"A{r}", step[0])
            write_cell(ws, f"B{r}", step[1])
            r += 1
        r += 1  # blank row between scenarios, matching the real sheet's spacing

    write_cell(ws, f"A{r}", "Rule-oriented acceptance criteria", bold=True, fill=True)
    r += 1
    for rule in story["rules"]:
        write_cell(ws, f"A{r}", "Rule")
        write_cell(ws, f"B{r}", rule)
        r += 1

    return ws


def main():
    if len(sys.argv) != 3:
        print("Usage: python3 build_story_xlsx.py <story_data.py> <output.xlsx>")
        sys.exit(1)

    data_path, out_path = sys.argv[1], sys.argv[2]
    mod = load_module(data_path)
    stories = mod.STORIES

    wb = Workbook()
    wb.remove(wb.active)  # drop default empty sheet

    for story in stories:
        build_user_story_sheet(wb, story["id"], story)
        build_qa_sheet(wb, f"{story['id']}-QA", story)

    wb.save(out_path)
    print(f"Saved: {out_path}")


if __name__ == "__main__":
    main()
