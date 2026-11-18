"""
build_pdf.py: turn writeup.md plus the two figures into writeup.pdf (US letter).

A small Markdown reader handles what writeup.md uses: # and ## headings, paragraphs,
- bullets, 1. numbered items, one table, **bold** and *italic*.
Figures go in after the "What I found" section.
Run from the project folder:  python build_pdf.py
"""
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.fonts import addMapping
import sys
from reportlab.platypus import (Image, ListFlowable, ListItem, Paragraph, SimpleDocTemplate,
                                Spacer, Table, TableStyle, KeepTogether, PageBreak)

# ---- fonts (Arial covers ð, í, °, ×, ÷ and λ)
FONTS = "/System/Library/Fonts/Supplemental/"
for name, file in [("Arial", "Arial.ttf"), ("Arial-Bold", "Arial Bold.ttf"),
                   ("Arial-Italic", "Arial Italic.ttf"), ("Arial-BoldItalic", "Arial Bold Italic.ttf")]:
    pdfmetrics.registerFont(TTFont(name, FONTS + file))
addMapping("Arial", 0, 0, "Arial"); addMapping("Arial", 1, 0, "Arial-Bold")
addMapping("Arial", 0, 1, "Arial-Italic"); addMapping("Arial", 1, 1, "Arial-BoldItalic")

INK, INK2, RULE = colors.HexColor("#16202a"), colors.HexColor("#4a5663"), colors.HexColor("#d9e0e6")
body = ParagraphStyle("body", fontName="Arial", fontSize=9, leading=11.8, textColor=INK, spaceAfter=3.5)
small = ParagraphStyle("small", parent=body, fontSize=7.6, leading=9.8, textColor=INK2, spaceAfter=2)
h1 = ParagraphStyle("h1", parent=body, fontName="Arial-Bold", fontSize=16, leading=19, spaceAfter=2)
h2 = ParagraphStyle("h2", parent=body, fontName="Arial-Bold", fontSize=10.5, leading=13, spaceBefore=5, spaceAfter=2)
meta = ParagraphStyle("meta", parent=body, textColor=INK2, fontSize=8.5, spaceAfter=6)
cell = ParagraphStyle("cell", parent=body, fontSize=8.4, leading=10.5, spaceAfter=0)
caption = ParagraphStyle("cap", parent=small, spaceAfter=8)


def inline(text):
    # Markdown emphasis -> ReportLab markup
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<i>\1</i>", text)
    return text.replace("\\*", "*")


def figure(path, cap, width=7.0 * inch):
    img = Image(path)
    img.drawWidth, img.drawHeight = width, width * img.imageHeight / img.imageWidth
    return KeepTogether([img, Paragraph(cap, caption)])


def make_story():
  lines = Path("writeup.md").read_text().splitlines()
  story, section, i = [], None, 0
  in_refs = False
  while i < len(lines):
      line = lines[i].rstrip()
      if not line:
          i += 1; continue
      if line.startswith("# "):
          story.append(Paragraph(inline(line[2:]), h1))
          # the two meta lines that follow the title
          story.append(Paragraph(inline(lines[i + 1]) + "<br/>" + inline(lines[i + 2]), meta))
          i += 3; continue
      if line.startswith("## "):
          if section == "What I found":            # figures after the findings
              story.append(figure("fig1_drift_paths.png",
                                  "<b>Figure 1.</b> Every 6th daily launch, drifting at 500 hPa for 7 days. "
                                  "Grey is the 500 km gap; dots are active radiosonde stations [6, 7].", width=6.2 * inch))
              story.append(figure("fig2_gap_hours.png",
                                  "<b>Figure 2.</b> Gap-hours per launch over 21 days. Marker: median; "
                                  "bar: middle half of about 800 launches per site.", width=5.6 * inch))
          section = line[3:]
          in_refs = section == "References"
          if in_refs:
              story.append(PageBreak())             # references get their own page
          story.append(Paragraph(inline(section), h2))
          i += 1; continue
      if line.startswith("|"):                       # table
          rows = []
          while i < len(lines) and lines[i].startswith("|"):
              cells = [c.strip() for c in lines[i].strip("|").split("|")]
              if not set("".join(cells)) <= set("- "):
                  rows.append([Paragraph(inline(c), cell) for c in cells])
              i += 1
          t = Table(rows, colWidths=[2.3 * inch] + [0.96 * inch] * (len(rows[0]) - 1))
          t.setStyle(TableStyle([
              ("LINEBELOW", (0, 0), (-1, 0), 0.8, INK), ("LINEBELOW", (0, 1), (-1, -1), 0.4, RULE),
              ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("TOPPADDING", (0, 0), (-1, -1), 3),
              ("BOTTOMPADDING", (0, 0), (-1, -1), 3), ("LEFTPADDING", (0, 0), (-1, -1), 2),
          ]))
          story.append(t); story.append(Spacer(1, 4))
          continue
      m_bullet, m_num = re.match(r"^- (.*)", line), re.match(r"^(\d+)\. (.*)", line)
      if m_bullet or m_num:                          # a list: gather consecutive items
          items, numbered = [], bool(m_num)
          while i < len(lines) and re.match(r"^(- |\d+\. )", lines[i]):
              text = re.sub(r"^(- |\d+\. )", "", lines[i])
              items.append(ListItem(Paragraph(inline(text), small if in_refs else body), leftIndent=12))
              i += 1
          story.append(ListFlowable(items, bulletType="1" if numbered else "bullet", start="1" if numbered else "•",
                                    bulletFormat="%s." if numbered else None,
                                    leftIndent=14, bulletFontName="Arial",
                                    bulletFontSize=7.6 if in_refs else 9, bulletColor=INK2))
          continue
      style = small if (in_refs or line.startswith("\\*") or line.startswith("Coastlines")) else body
      story.append(Paragraph(inline(line), style))
      i += 1
  return story


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Arial", 7.5); canvas.setFillColor(INK2)
    canvas.drawRightString(letter[0] - 0.7 * inch, 0.45 * inch, f"Senan Tubridy · What one Iceland launch buys · {doc.page}")
    canvas.restoreState()


class Doc(SimpleDocTemplate):
    # records the page number each top-level section heading lands on
    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph) and flowable.style.name in ("h1", "h2"):
            self.placed.append((flowable.getPlainText(), self.page))


def build(path, story):
    doc = Doc(path, pagesize=letter, leftMargin=0.75 * inch, rightMargin=0.75 * inch,
              topMargin=0.55 * inch, bottomMargin=0.65 * inch,
              title="What one Iceland launch buys", author="Senan Tubridy")
    doc.placed = []
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return doc.placed


placed = build("writeup.pdf", make_story())
for name, page in placed:
    print(f"page {page}: {name}")
print("wrote writeup.pdf")
