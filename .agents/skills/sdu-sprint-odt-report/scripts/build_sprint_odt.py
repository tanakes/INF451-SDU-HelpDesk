#!/usr/bin/env python3
"""
Generic builder for SDU Help Desk "Step-by-Step Sprint Walkthrough" ODT reports.

Usage:
    python3 build_sprint_odt.py <steps_module.py> <output.odt>

<steps_module.py> must define a module-level variable `DOCUMENT` — see
steps_template.py in this same folder for the exact schema and a fully
worked example (Sprint 2 / US-03 / US-04).

Do not hardcode sprint-specific prose in this file. All sprint-specific
content (titles, quotes, implementation text, screenshot instructions)
belongs in the steps_module.py data file, not here.
"""
import sys
import importlib.util

from odf.opendocument import OpenDocumentText
from odf.style import Style, TextProperties, ParagraphProperties, FontFace
from odf.text import H, P, Span


def load_document_data(path):
    spec = importlib.util.spec_from_file_location("steps_module", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.DOCUMENT


def build(doc_data, output_path):
    doc = OpenDocumentText()

    # ---------- Fonts ----------
    doc.fontfacedecls.addElement(FontFace(name="Arial", fontfamily="Arial"))
    doc.fontfacedecls.addElement(FontFace(name="Consolas", fontfamily="Consolas"))

    # ---------- Styles (fixed visual language — do not vary per sprint) ----------
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
    code_inline = add_style("CodeInline", "text", [
        TextProperties(fontfamily="Consolas", fontsize="9.5pt", color="#0b3d5c",
                        backgroundcolor="#eef2f6"),
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

    # ---------- Helper emitters ----------
    def para(style, text=None):
        p = P(stylename=style)
        if text is not None:
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
        if not items:
            return
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

    def body(text):
        if text:
            doc.text.addElement(para(body_style, text))

    def code(text):
        p = P(stylename=body_style)
        p.addElement(Span(stylename=code_inline, text=text))
        doc.text.addElement(p)

    # ---------- Render cover ----------
    doc.text.addElement(para(title_style, doc_data["title"]))
    doc.text.addElement(para(subtitle_style, doc_data["subtitle"]))
    for line in doc_data.get("intro_bullets_intro", []):
        body(line)
    for b in doc_data.get("intro_bullets", []):
        bullet(b)
    for line in doc_data.get("intro_outro", []):
        body(line)

    # ---------- Render primer (section 0) ----------
    primer = doc_data.get("primer")
    if primer:
        h1_nobreak(primer["heading"])
        for sub in primer["subsections"]:
            h2(sub["heading"])
            for line in sub.get("body", []):
                body(line)
            for shot in sub.get("screenshots", []):
                screenshot(shot)
        for line in primer.get("closing", []):
            body(line)

    # ---------- Render user story sections ----------
    for story in doc_data["stories"]:
        h1(story["heading"])
        for line in story.get("intro_quotes", []):
            quote(line["ref"], line["text"])
        for line in story.get("intro_body", []):
            body(line)

        for step in story["steps"]:
            h2(step["heading"])
            for q in step.get("quotes", []):
                quote(q["ref"], q["text"])
            if step.get("implemented"):
                implemented(step["implemented"])
            for extra in step.get("extra_body", []):
                body(extra)
            for c in step.get("code_blocks", []):
                code(c)
            if step.get("demonstrate"):
                demonstrate(step["demonstrate"])
            for shot in step.get("screenshots", []):
                screenshot(shot)
            if step.get("covered"):
                covered(step["covered"])

        for line in story.get("closing_body", []):
            body(line)

    # ---------- Render closing / known-gaps section ----------
    closing = doc_data.get("closing_section")
    if closing:
        h1(closing["heading"])
        for line in closing.get("body", []):
            body(line)
        for shot in closing.get("screenshots", []):
            screenshot(shot)

    doc.save(output_path)
    print(f"Saved: {output_path}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 build_sprint_odt.py <steps_module.py> <output.odt>")
        sys.exit(1)
    data = load_document_data(sys.argv[1])
    build(data, sys.argv[2])
