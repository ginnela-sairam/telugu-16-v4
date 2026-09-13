#!/usr/bin/env python3
"""T-16 V4.1 Master Guide - shared library (ReportLab body components).

Palette: Template 07 Crystal Blue body subset (fixed by the template spec).
Fonts:   FreeSerif family (English body), DejaVuSansMono (code) - per the
         report brief's allowed-fonts table.
Layout:  continuous flow, CondPageBreak orphan prevention only,
         TocDocTemplate + multiBuild with roman front matter / arabic body.
"""
import hashlib
import os
import sys

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import registerFontFamily
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (CondPageBreak, Image, KeepTogether, PageBreak,
                                Paragraph, SimpleDocTemplate, Spacer, Table,
                                TableStyle)
from reportlab.platypus.tableofcontents import TableOfContents

# ---------------------------------------------------------------- fonts
FONT_DIR = "/usr/share/fonts"

pdfmetrics.registerFont(TTFont("FreeSerif", f"{FONT_DIR}/truetype/freefont/FreeSerif.ttf"))
pdfmetrics.registerFont(TTFont("FreeSerif-Bold", f"{FONT_DIR}/truetype/freefont/FreeSerifBold.ttf"))
pdfmetrics.registerFont(TTFont("FreeSerif-Italic", f"{FONT_DIR}/truetype/freefont/FreeSerifItalic.ttf"))
pdfmetrics.registerFont(TTFont("FreeSerif-BoldItalic", f"{FONT_DIR}/truetype/freefont/FreeSerifBoldItalic.ttf"))
pdfmetrics.registerFont(TTFont("NotoSerifSC", f"{FONT_DIR}/truetype/noto-serif-sc/NotoSerifSC-Regular.ttf"))
pdfmetrics.registerFont(TTFont("NotoSerifSC-Bold", f"{FONT_DIR}/truetype/noto-serif-sc/NotoSerifSC-Bold.ttf"))
pdfmetrics.registerFont(TTFont("DejaVuSans", f"{FONT_DIR}/truetype/dejavu/DejaVuSansMono.ttf"))
pdfmetrics.registerFont(TTFont("DejaVuSans-Bold", f"{FONT_DIR}/truetype/dejavu/DejaVuSansMono-Bold.ttf"))

registerFontFamily("FreeSerif", normal="FreeSerif", bold="FreeSerif-Bold",
                   italic="FreeSerif-Italic", boldItalic="FreeSerif-BoldItalic")
registerFontFamily("NotoSerifSC", normal="NotoSerifSC", bold="NotoSerifSC-Bold")
registerFontFamily("DejaVuSans", normal="DejaVuSans", bold="DejaVuSans-Bold")

# Optional skill fallback (present on the build server; absent in the wild)
try:
    _SKILL = "/home/z/my-project/skills/pdf/scripts"
    if os.path.isdir(_SKILL) and _SKILL not in sys.path:
        sys.path.insert(0, _SKILL)
    from pdf import install_font_fallback  # type: ignore
    install_font_fallback()
except Exception:  # pure-English content - fallback is a safety net only
    pass

# ------------------------------------------------------- palette (fixed)
# Template 07 Crystal Blue body subset (typesetting/cover.md)
PAGE_BG      = colors.HexColor("#f5f8fc")   # XL
SECTION_BG   = colors.HexColor("#edf2f9")   # XL
CARD_BG      = colors.HexColor("#e4ecf5")   # L
TABLE_STRIPE = colors.HexColor("#eef3fa")   # L
HEADER_FILL  = colors.HexColor("#1a4a7a")   # M
BORDER       = colors.HexColor("#c0d0e2")   # S
ACCENT       = colors.HexColor("#2d7ab3")   # XS
TEXT_PRIMARY = colors.HexColor("#142840")
TEXT_MUTED   = colors.HexColor("#5a7a96")

TABLE_HEADER_COLOR = HEADER_FILL
TABLE_ROW_EVEN = colors.white
TABLE_ROW_ODD = TABLE_STRIPE

# ------------------------------------------------------------ geometry
MARGIN = 0.9 * inch                       # symmetric left == right
PAGE_W, PAGE_H = A4
AVAIL_W = PAGE_W - 2 * MARGIN
AVAIL_H = PAGE_H - 2 * MARGIN
MAX_KEEP_HEIGHT = PAGE_H * 0.4

DOC_TITLE = "TELUGU T-16 - The Complete Master Guide"
DOC_AUTHOR = "Sairam Ginnela"

# --------------------------------------------------------------- styles
S = {}

S["h1"] = ParagraphStyle("H1", fontName="FreeSerif-Bold", fontSize=22,
                         leading=27, textColor=HEADER_FILL,
                         spaceBefore=18, spaceAfter=4)
S["h1kick"] = ParagraphStyle("H1Kick", fontName="DejaVuSans", fontSize=8,
                             leading=10, textColor=ACCENT, spaceBefore=16,
                             spaceAfter=2)
S["h2"] = ParagraphStyle("H2", fontName="FreeSerif-Bold", fontSize=15,
                         leading=19, textColor=TEXT_PRIMARY,
                         spaceBefore=14, spaceAfter=6)
S["h3"] = ParagraphStyle("H3", fontName="FreeSerif-Bold", fontSize=11.5,
                         leading=15, textColor=TEXT_PRIMARY,
                         spaceBefore=10, spaceAfter=5)
S["body"] = ParagraphStyle("Body", fontName="FreeSerif", fontSize=10.5,
                           leading=17, textColor=TEXT_PRIMARY,
                           alignment=TA_JUSTIFY, spaceAfter=8)
S["bullet"] = ParagraphStyle("Bullet", fontName="FreeSerif", fontSize=10.5,
                             leading=16, textColor=TEXT_PRIMARY,
                             alignment=TA_LEFT, leftIndent=14,
                             bulletIndent=4, spaceAfter=4)
S["code"] = ParagraphStyle("Code", fontName="DejaVuSans", fontSize=8.5,
                           leading=11.5, textColor=TEXT_PRIMARY,
                           alignment=TA_LEFT)
S["codelabel"] = ParagraphStyle("CodeLabel", fontName="DejaVuSans-Bold",
                                fontSize=7.5, leading=10, textColor=ACCENT,
                                alignment=TA_LEFT)
S["caption"] = ParagraphStyle("Caption", fontName="FreeSerif-Italic",
                              fontSize=8.5, leading=11, textColor=TEXT_MUTED,
                              alignment=TA_CENTER, spaceBefore=3,
                              spaceAfter=6)
S["th"] = ParagraphStyle("TH", fontName="FreeSerif-Bold", fontSize=9.5,
                         leading=12.5, textColor=colors.white,
                         alignment=TA_LEFT)
S["thc"] = ParagraphStyle("THC", parent=S["th"], alignment=TA_CENTER)
S["td"] = ParagraphStyle("TD", fontName="FreeSerif", fontSize=9.5,
                         leading=13, textColor=TEXT_PRIMARY,
                         alignment=TA_LEFT)
S["tdc"] = ParagraphStyle("TDC", parent=S["td"], alignment=TA_CENTER)
S["tdm"] = ParagraphStyle("TDM", fontName="DejaVuSans", fontSize=8.5,
                          leading=12, textColor=TEXT_PRIMARY,
                          alignment=TA_LEFT)
S["statnum"] = ParagraphStyle("StatNum", fontName="FreeSerif-Bold",
                              fontSize=17, leading=20, textColor=ACCENT,
                              alignment=TA_CENTER)
S["statlab"] = ParagraphStyle("StatLab", fontName="FreeSerif", fontSize=8,
                              leading=10.5, textColor=TEXT_MUTED,
                              alignment=TA_CENTER)
S["callout"] = ParagraphStyle("Callout", fontName="FreeSerif", fontSize=10.5,
                              leading=16.5, textColor=TEXT_PRIMARY,
                              alignment=TA_LEFT)
S["toc0"] = ParagraphStyle("TOC0", fontName="FreeSerif-Bold", fontSize=11,
                           leading=20, textColor=TEXT_PRIMARY, leftIndent=6)
S["toc1"] = ParagraphStyle("TOC1", fontName="FreeSerif", fontSize=9.5,
                           leading=15, textColor=TEXT_MUTED, leftIndent=24)
S["tochead"] = ParagraphStyle("TOCHead", fontName="FreeSerif-Bold",
                              fontSize=20, leading=25,
                              textColor=HEADER_FILL, spaceAfter=14)

# --------------------------------------------------------- doc template
class GuideDocTemplate(SimpleDocTemplate):
    """TocDocTemplate with roman front matter + arabic body numbering."""

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.body_start_page = None

    def afterPage(self):
        paint_footer(self.canv, self)

    def beforeDocument(self):
        # multiBuild runs several passes over the same doc object; a
        # body_start_page remembered from an earlier pass (when the TOC
        # was still empty and chapters sat one page higher) would poison
        # both the footers and the TOC labels. Start every pass fresh.
        self.body_start_page = None

    def afterFlowable(self, flowable):
        if getattr(flowable, "is_body_start", False):
            if self.body_start_page is None or self.page < self.body_start_page:
                self.body_start_page = self.page
        if hasattr(flowable, "bookmark_name"):
            level = getattr(flowable, "bookmark_level", 0)
            text = getattr(flowable, "bookmark_text", "")
            key = getattr(flowable, "bookmark_key", "")
            key_full = "p%s" % key
            self.canv.bookmarkPage(key_full)
            self.canv.addOutlineEntry(text, key_full, level=level, closed=False)
            if level == 0:  # printed TOC lists chapters only
                page_label = self.page
                if self.body_start_page is not None and self.page >= self.body_start_page:
                    page_label = self.page - self.body_start_page + 1
                else:
                    romans = {1: "i", 2: "ii", 3: "iii", 4: "iv", 5: "v"}
                    page_label = romans.get(self.page, str(self.page))
                self.notify("TOCEntry", (level, text, page_label, key))


ROMANS = ["i", "ii", "iii", "iv", "v", "vi", "vii", "viii", "ix", "x"]


def paint_page(canvas, doc):
    """Page BEGIN layer: full-bleed background + header (drawn under content)."""
    canvas.saveState()
    # full-bleed ultra-light blue page (Template 07 body XL tier)
    canvas.setFillColor(PAGE_BG)
    canvas.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    # header: title left + accent rule
    canvas.setFont("FreeSerif", 7.5)
    canvas.setFillColor(TEXT_MUTED)
    canvas.drawString(MARGIN, PAGE_H - 0.55 * inch, DOC_TITLE)
    canvas.setStrokeColor(ACCENT)
    canvas.setLineWidth(1.2)
    canvas.line(MARGIN, PAGE_H - 0.62 * inch, PAGE_W - MARGIN, PAGE_H - 0.62 * inch)
    canvas.restoreState()


def paint_footer(canvas, doc):
    """Page END layer: footer rule + author + page label.

    Runs from afterPage(), i.e. AFTER this page's flowables have been
    drawn - so body_start_page is already set when the first chapter
    heading flows on this very page. Drawing it at page begin instead
    (the onPage hook) would mislabel that page as front matter.
    """
    canvas.saveState()
    canvas.setStrokeColor(BORDER)
    canvas.setLineWidth(0.6)
    canvas.line(MARGIN, 0.62 * inch, PAGE_W - MARGIN, 0.62 * inch)
    canvas.setFont("FreeSerif", 7.5)
    canvas.setFillColor(TEXT_MUTED)
    canvas.drawString(MARGIN, 0.45 * inch, DOC_AUTHOR)
    body_start = getattr(doc, "body_start_page", None)
    if body_start is not None and doc.page >= body_start:
        label = str(doc.page - body_start + 1)
    else:
        label = ROMANS[doc.page - 1] if 0 < doc.page <= len(ROMANS) else str(doc.page)
    canvas.drawRightString(PAGE_W - MARGIN, 0.45 * inch, label)
    canvas.restoreState()


# ------------------------------------------------------------ components
def safe_keep_together(elements):
    total_h = 0
    for el in elements:
        try:
            _, h = el.wrap(AVAIL_W, PAGE_H)
        except Exception:
            h = 0
        total_h += h
    if total_h <= MAX_KEEP_HEIGHT:
        return [KeepTogether(elements)]
    if len(elements) >= 2:
        return [KeepTogether(elements[:2])] + list(elements[2:])
    return list(elements)


def add_heading(text, style, level=0, body_start=False):
    key = "h_%s" % hashlib.md5(text.encode()).hexdigest()[:8]
    p = Paragraph('<a name="%s"/><b>%s</b>' % (key, text), style)
    p.bookmark_name = key
    p.bookmark_level = level
    p.bookmark_text = text.replace("&", "&")
    p.bookmark_key = key
    if body_start:
        p.is_body_start = True
    return p


def h1_block(num, title, first_content, body_start=False, kicker=None):
    """Chapter opener: conditional break + kicker + title + rule + content."""
    kick_text = kicker if kicker is not None else ("CHAPTER %d" % num)
    kick = Paragraph(kick_text, S["h1kick"])
    if num == 20:
        head = add_heading("Appendix A  —  %s" % title.upper(),
                           S["h1"], level=0)
    else:
        head = add_heading("Chapter %d  —  %s" % (num, title.upper()),
                           S["h1"], level=0, body_start=body_start)
    rule = Table([[""]], colWidths=[AVAIL_W], rowHeights=[2])
    rule.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (-1, -1), 1.4, ACCENT),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    parts = [kick, head, rule, Spacer(1, 8)]
    _absorb(parts, first_content)
    out = [CondPageBreak(AVAIL_H * 0.22)]
    out.extend(safe_keep_together(parts))
    return out


def h2_block(title, first_content=None):
    head = add_heading(title, S["h2"], level=1)
    if first_content is not None:
        inner = [head]
        _absorb(inner, first_content)
        return safe_keep_together(inner)
    return [head]


def h3_block(title, first_content=None):
    head = Paragraph("<b>%s</b>" % title, S["h3"])
    if first_content is not None:
        inner = [head]
        _absorb(inner, first_content)
        return safe_keep_together(inner)
    return [head]



def _absorb(parts, content):
    if content is None:
        return
    if isinstance(content, (list, tuple)):
        parts.extend(content)
    else:
        parts.append(content)

def body(text):
    return [Paragraph(text, S["body"])]


def bullets(items):
    out = []
    for it in items:
        out.append(Paragraph("•  %s" % it, S["bullet"]))
    out.append(Spacer(1, 4))
    return out


def code_block(code_text, label=None):
    """Light-card code block with accent left border; chunked at 46 lines."""
    lines = code_text.rstrip("\n").split("\n")
    chunks = [lines[i:i + 46] for i in range(0, len(lines), 46)] or [[""]]
    flows = []
    for idx, chunk in enumerate(chunks):
        esc = "\n".join(
            ln.replace("&", "&").replace("<", "<").replace(">", ">")
            for ln in chunk)
        rows = []
        if idx == 0 and label:
            rows.append([Paragraph(label, S["codelabel"])])
        rows.append([Paragraph(esc.replace("\n", "<br/>"), S["code"])])
        t = Table(rows, colWidths=[AVAIL_W], hAlign="CENTER")
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), CARD_BG),
            ("LINEBEFORE", (0, 0), (0, -1), 2.2, ACCENT),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        flows.append(t)
        flows.append(Spacer(1, 8))
    return flows


def stat_row(stats):
    """Row of metric callout boxes: [(number, label), ...] max 4."""
    n = len(stats)
    gap = 8
    box_w = (AVAIL_W - gap * (n - 1)) / n
    cells = []
    for num, lab in stats:
        inner = Table(
            [[Paragraph("<b>%s</b>" % num, S["statnum"])],
             [Paragraph(lab, S["statlab"])]],
            colWidths=[box_w - 4])
        inner.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), SECTION_BG),
            ("BOX", (0, 0), (-1, -1), 0.8, BORDER),
            ("LINEABOVE", (0, 0), (-1, 0), 2, ACCENT),
            ("TOPPADDING", (0, 0), (-1, 0), 8),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 2),
            ("TOPPADDING", (0, 1), (-1, 1), 0),
            ("BOTTOMPADDING", (0, 1), (-1, 1), 8),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ]))
        cells.append(inner)
    outer = Table([cells], colWidths=[box_w] * n, hAlign="CENTER")
    outer.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), gap / 2.0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return [Spacer(1, 4), outer, Spacer(1, 10)]


def callout(text, title=None):
    rows = []
    if title:
        rows.append([Paragraph("<b>%s</b>" % title,
                               ParagraphStyle("ct", parent=S["callout"],
                                              fontName="FreeSerif-Bold",
                                              textColor=HEADER_FILL))])
    rows.append([Paragraph(text, S["callout"])])
    t = Table(rows, colWidths=[AVAIL_W], hAlign="CENTER")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), SECTION_BG),
        ("LINEBEFORE", (0, 0), (0, -1), 3, ACCENT),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
    ]))
    return [Spacer(1, 4), t, Spacer(1, 8)]


def data_table(header, rows, ratios, caption_text=None, mono_cols=(),
               center_cols=(), width_frac=1.0):
    """Standard striped table. All cells are Paragraphs. ratios sum to 1."""
    total_w = AVAIL_W * width_frac
    col_w = [r * total_w for r in ratios]
    assert abs(sum(ratios) - 1.0) < 0.01, "ratios must sum to 1"
    assert sum(col_w) <= AVAIL_W + 0.5, "table wider than frame"

    def hcell(i, txt):
        st = S["thc"] if i in center_cols else S["th"]
        return Paragraph("<b>%s</b>" % txt, st)

    def cell(i, txt):
        if i in mono_cols:
            return Paragraph(str(txt), S["tdm"])
        st = S["tdc"] if i in center_cols else S["td"]
        return Paragraph(str(txt), st)

    data = [[hcell(i, h) for i, h in enumerate(header)]]
    for r in rows:
        data.append([cell(i, c) for i, c in enumerate(r)])

    t = Table(data, colWidths=col_w, hAlign="CENTER", repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), TABLE_HEADER_COLOR),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4.5),
    ]
    for ri in range(1, len(data)):
        bg = TABLE_ROW_ODD if ri % 2 == 1 else TABLE_ROW_EVEN
        style.append(("BACKGROUND", (0, ri), (-1, ri), bg))
    t.setStyle(TableStyle(style))

    out = [Spacer(1, 10)]
    if caption_text is None or len(rows) <= 15:
        parts = [t]
        if caption_text:
            parts.append(Paragraph(caption_text, S["caption"]))
        out.extend(safe_keep_together(parts))
    else:
        out.append(t)
        if caption_text:
            out.append(Paragraph(caption_text, S["caption"]))
    out.append(Spacer(1, 8))
    return out


def figure(path, caption_text, max_h=None, width_frac=0.94):
    """Block-level image with preserved aspect + caption, kept together."""
    from PIL import Image as PILImage
    pil = PILImage.open(path)
    ow, oh = pil.size
    max_w = AVAIL_W * width_frac
    if max_h is None:
        max_h = PAGE_H * 0.35
    ratio = min(max_w / ow, max_h / oh, 1.0)
    img = Image(path, width=ow * ratio, height=oh * ratio)
    img.hAlign = "CENTER"
    cap = Paragraph(caption_text, S["caption"])
    return [Spacer(1, 16)] + safe_keep_together([img, cap]) + [Spacer(1, 14)]


def make_toc():
    toc = TableOfContents()
    toc.levelStyles = [S["toc0"], S["toc1"]]
    toc.dotsMinLevel = 0
    return toc
