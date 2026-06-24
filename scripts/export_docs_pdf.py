from __future__ import annotations

import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

SOURCES = [
    (DOCS / "PROJECT_STATUS_V1.md", DOCS / "PROJECT_STATUS_V1.pdf"),
    (DOCS / "GUIA_USUARIO.md", DOCS / "GUIA_USUARIO.pdf"),
    (DOCS / "MANUAL_TECNICO.md", DOCS / "MANUAL_TECNICO.pdf"),
]


def clean_inline(text: str) -> str:
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r"`([^`]+)`", r"<font name='Courier'>\1</font>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    return text


def build_styles():
    base = getSampleStyleSheet()
    return {
        "h1": ParagraphStyle("h1", parent=base["Heading1"], fontName="Helvetica-Bold", fontSize=19, leading=23, textColor=colors.HexColor("#153F2B"), spaceAfter=8),
        "h2": ParagraphStyle("h2", parent=base["Heading2"], fontName="Helvetica-Bold", fontSize=14, leading=18, textColor=colors.HexColor("#153F2B"), spaceBefore=10, spaceAfter=5),
        "h3": ParagraphStyle("h3", parent=base["Heading3"], fontName="Helvetica-Bold", fontSize=11, leading=14, textColor=colors.HexColor("#5B351E"), spaceBefore=7, spaceAfter=4),
        "body": ParagraphStyle("body", parent=base["BodyText"], fontName="Helvetica", fontSize=9, leading=12, spaceAfter=5),
        "bullet": ParagraphStyle("bullet", parent=base["BodyText"], fontName="Helvetica", fontSize=9, leading=12),
        "code": ParagraphStyle("code", parent=base["Code"], fontName="Courier", fontSize=7.5, leading=9, backColor=colors.HexColor("#F4F6F3"), borderColor=colors.HexColor("#D7DEE3"), borderWidth=0.3, borderPadding=5),
        "small": ParagraphStyle("small", parent=base["BodyText"], fontName="Helvetica", fontSize=7.5, leading=9, textColor=colors.HexColor("#65756B")),
    }


def flush_paragraph(lines: list[str], story: list, styles):
    if not lines:
        return
    text = " ".join(line.strip() for line in lines if line.strip())
    if text:
        story.append(Paragraph(clean_inline(text), styles["body"]))
    lines.clear()


def flush_bullets(lines: list[str], story: list, styles):
    if not lines:
        return
    items = [ListItem(Paragraph(clean_inline(line), styles["bullet"]), leftIndent=8) for line in lines]
    story.append(ListFlowable(items, bulletType="bullet", start="circle", leftIndent=14))
    story.append(Spacer(1, 2 * mm))
    lines.clear()


def flush_table(rows: list[list[str]], story: list, styles):
    if not rows:
        return
    cleaned = [[Paragraph(clean_inline(cell.strip()), styles["small"]) for cell in row] for row in rows]
    col_count = max(len(row) for row in rows)
    table = Table(cleaned, colWidths=[(180 / col_count) * mm] * col_count, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EAF0EA")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#153F2B")),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#D7DEE3")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(table)
    story.append(Spacer(1, 4 * mm))
    rows.clear()


def markdown_to_story(markdown: str):
    styles = build_styles()
    story = []
    paragraph: list[str] = []
    bullets: list[str] = []
    table_rows: list[list[str]] = []
    code_lines: list[str] = []
    in_code = False

    for raw in markdown.splitlines():
        line = raw.rstrip()
        if line.startswith("```"):
            flush_paragraph(paragraph, story, styles)
            flush_bullets(bullets, story, styles)
            flush_table(table_rows, story, styles)
            if in_code:
                story.append(Preformatted("\n".join(code_lines), styles["code"]))
                story.append(Spacer(1, 4 * mm))
                code_lines.clear()
            in_code = not in_code
            continue

        if in_code:
            code_lines.append(line)
            continue

        if not line.strip():
            flush_paragraph(paragraph, story, styles)
            flush_bullets(bullets, story, styles)
            flush_table(table_rows, story, styles)
            continue

        if line.startswith("|") and line.endswith("|"):
            flush_paragraph(paragraph, story, styles)
            flush_bullets(bullets, story, styles)
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            if not all(set(cell) <= {"-", ":", " "} for cell in cells):
                table_rows.append(cells)
            continue

        flush_table(table_rows, story, styles)

        if line.startswith("# "):
            flush_paragraph(paragraph, story, styles)
            flush_bullets(bullets, story, styles)
            if story:
                story.append(PageBreak())
            story.append(Paragraph(clean_inline(line[2:].strip()), styles["h1"]))
        elif line.startswith("## "):
            flush_paragraph(paragraph, story, styles)
            flush_bullets(bullets, story, styles)
            story.append(Paragraph(clean_inline(line[3:].strip()), styles["h2"]))
        elif line.startswith("### "):
            flush_paragraph(paragraph, story, styles)
            flush_bullets(bullets, story, styles)
            story.append(Paragraph(clean_inline(line[4:].strip()), styles["h3"]))
        elif line.lstrip().startswith("- "):
            flush_paragraph(paragraph, story, styles)
            bullets.append(line.lstrip()[2:].strip())
        else:
            flush_bullets(bullets, story, styles)
            paragraph.append(line)

    flush_paragraph(paragraph, story, styles)
    flush_bullets(bullets, story, styles)
    flush_table(table_rows, story, styles)
    return story


def draw_footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(colors.HexColor("#65756B"))
    canvas.drawString(15 * mm, 9 * mm, "Gestion de Muestras Cafe Verde - Indian Ecotrade")
    canvas.drawRightString(A4[0] - 15 * mm, 9 * mm, f"Pagina {doc.page}")
    canvas.restoreState()


def export_pdf(source: Path, target: Path):
    markdown = source.read_text(encoding="utf-8")
    story = markdown_to_story(markdown)
    doc = SimpleDocTemplate(
        str(target),
        pagesize=A4,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title=source.stem,
        author="Indian Ecotrade",
    )
    doc.build(story, onFirstPage=draw_footer, onLaterPages=draw_footer)


def main():
    for source, target in SOURCES:
        if not source.exists():
            raise FileNotFoundError(source)
        export_pdf(source, target)
        print(f"{target.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
