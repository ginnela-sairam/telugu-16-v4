#!/usr/bin/env python3
# ============================================================================
#  generate_master_guide_pdf.py - rebuild the master guide BODY (V4.1 final)
# ----------------------------------------------------------------------------
#  The shipped docs/T16_V4_MASTER_GUIDE.pdf = Template-07 cover + this body.
#  This script regenerates the body (TOC + 19 chapters + appendix).
#
#  NEEDS:  python3 + reportlab + pillow, and the system fonts FreeSerif
#          (fonts-freefont-ttf) and DejaVuSansMono (fonts-dejavu-core).
#          The figures come from docs/ (chart_*.png, diagram_*.png).
#
#  RUN:    python3 tools/generate_master_guide_pdf.py
#  OUT:    docs/T16_V4_MASTER_GUIDE_BODY.pdf
#
#  The build sources live in tools/pdfgen/ (lib + two content modules),
#  exactly as used for the shipped edition. Re-merging the cover requires
#  an HTML->PDF renderer plus docs/cover_master_guide.html.
# ============================================================================
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "pdfgen"))

import guide41_lib as L
from guide41_lib import GuideDocTemplate, PageBreak, Paragraph, make_toc, paint_page
from reportlab.lib.pagesizes import A4
import guide41_content_a as A
import guide41_content_b as B

PKG_ROOT = os.path.dirname(_HERE)
OUT = os.path.join(PKG_ROOT, "docs", "T16_V4_MASTER_GUIDE_BODY.pdf")


def build():
    story = []
    story.append(Paragraph("<b>Table of Contents</b>", L.S["tochead"]))
    story.append(make_toc())
    story.append(PageBreak())
    for fn in (A.ch1, A.ch2, A.ch3, A.ch4, A.ch5, A.ch6, A.ch7, A.ch8,
               A.ch9, B.ch10, B.ch11, B.ch12, B.ch13, B.ch14, B.ch15,
               B.ch16, B.ch17, B.ch18, B.ch19, B.appendix):
        fn(story)
    doc = GuideDocTemplate(
        OUT, pagesize=A4,
        leftMargin=L.MARGIN, rightMargin=L.MARGIN,
        topMargin=0.95 * 72, bottomMargin=0.85 * 72,
        title=L.DOC_TITLE, author=L.DOC_AUTHOR,
        creator="Z.ai", subject="T-16 V4.1 complete master guide")
    doc.multiBuild(story, onFirstPage=paint_page, onLaterPages=paint_page)
    print("body written:", OUT)


if __name__ == "__main__":
    build()
