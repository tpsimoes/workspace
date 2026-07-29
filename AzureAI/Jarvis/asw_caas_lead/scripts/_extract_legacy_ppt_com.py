"""Extract text from legacy .ppt files (CFB/OLE) via PowerPoint COM automation.

Used as a fallback when markitdown fails with `BadZipFile` because the file is a
PowerPoint 97-2003 (.ppt) format despite carrying a `.pptx` extension.

Reads all failing PPTs from Output/caas_lead_reviews_jun2026/, uses PowerPoint COM
to walk slides/shapes and dump text, writes companion .md files that mimic
markitdown's slide-numbered output, then re-runs the review extractor.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import win32com.client
import pythoncom

ROOT      = Path(__file__).resolve().parents[3]
DOWNLOADS = ROOT / "Output" / "caas_lead_reviews_jun2026"


# Files known to be legacy .ppt (from the earlier BadZipFile failures)
LEGACY_PPT = [
    "[Zone 1] Bayer ASW CaaS Lead Status Update - June 26.pptx",
    "[Zone 2] Lego_CaaS.pptx",
    "[Zone 1] Woolworths CaaS Lead update July 2026.pptx",
    "[Zone 2] TJU CaaS Lead Update - June 2026.pptx",
    "[Zone 1] BHP presentation July 1st.pptx",
    "[Zone 2] McKesson-CaaS Lead Status July 1st 2026.pptx",
]


def _shape_text(shape) -> list[str]:
    """Recursively pull text from a shape (or nested group)."""
    out: list[str] = []
    try:
        if shape.HasTextFrame:
            tf = shape.TextFrame
            if tf.HasText:
                txt = tf.TextRange.Text or ""
                for line in txt.splitlines():
                    line = line.strip()
                    if line:
                        out.append(line)
    except Exception:
        pass
    # Nested groups
    try:
        if shape.Type == 6:  # msoGroup
            for sub in shape.GroupItems:
                out.extend(_shape_text(sub))
    except Exception:
        pass
    # Tables
    try:
        if shape.HasTable:
            for r in range(1, shape.Table.Rows.Count + 1):
                for c in range(1, shape.Table.Columns.Count + 1):
                    cell = shape.Table.Cell(r, c)
                    try:
                        t = cell.Shape.TextFrame.TextRange.Text or ""
                    except Exception:
                        t = ""
                    for line in t.splitlines():
                        line = line.strip()
                        if line:
                            out.append(line)
    except Exception:
        pass
    return out


def _col_of(left: float, width: float) -> int:
    """Return column bucket 1-3 based on shape Left position within slide width."""
    if width <= 0:
        return 2
    r = left / width
    if r < 0.33:
        return 1
    if r < 0.66:
        return 2
    return 3


def extract_ppt_text(pptx_path: Path) -> str:
    """Open a .ppt/.pptx with PowerPoint COM and return markdown-style text
    with `<!-- COL: N -->` markers before each shape so downstream parsers can
    route content to the correct visual column (1=About, 2=Key Update, 3=Reminder)."""
    pythoncom.CoInitialize()
    try:
        app = win32com.client.Dispatch("PowerPoint.Application")
        try:
            app.Visible = True
        except Exception:
            pass
        pres = app.Presentations.Open(
            str(pptx_path),
            ReadOnly=True,
            Untitled=False,
            WithWindow=False,
        )
        try:
            slide_width = float(pres.PageSetup.SlideWidth or 720)
            parts: list[str] = []
            for i in range(1, pres.Slides.Count + 1):
                slide = pres.Slides.Item(i)
                parts.append(f"\n<!-- Slide number: {i} -->\n")
                # Sort shapes by Top then Left for stable reading order
                shapes = []
                for j in range(1, slide.Shapes.Count + 1):
                    sh = slide.Shapes.Item(j)
                    try:
                        top  = float(sh.Top  or 0)
                        left = float(sh.Left or 0)
                    except Exception:
                        top, left = 0.0, 0.0
                    shapes.append((top, left, sh))
                shapes.sort(key=lambda t: (t[0], t[1]))
                for top, left, sh in shapes:
                    col = _col_of(left, slide_width)
                    lines = _shape_text(sh)
                    if not lines:
                        continue
                    parts.append(f"<!-- COL: {col} -->")
                    parts.extend(lines)
                # Speaker notes -> col 0 (untagged, will be ignored by column-aware parser)
                try:
                    notes_page = slide.NotesPage
                    for k in range(1, notes_page.Shapes.Count + 1):
                        ns = notes_page.Shapes.Item(k)
                        try:
                            if ns.HasTextFrame:
                                nt = ns.TextFrame.TextRange.Text or ""
                                notes_lines = [
                                    l.strip() for l in nt.splitlines()
                                    if l.strip() and not re.fullmatch(r"\d+", l.strip())
                                ]
                                if notes_lines:
                                    parts.append("<!-- COL: 0 -->")
                                    parts.extend(notes_lines)
                        except Exception:
                            pass
                except Exception:
                    pass
            return "\n".join(parts)
        finally:
            pres.Close()
    finally:
        try:
            app.Quit()
        except Exception:
            pass
        pythoncom.CoUninitialize()


def main() -> int:
    for name in LEGACY_PPT:
        p = DOWNLOADS / name
        if not p.exists():
            print(f"[SKIP] {name}: not found")
            continue
        md_path = DOWNLOADS / (p.stem + ".md")
        try:
            md = extract_ppt_text(p)
        except Exception as e:
            print(f"[FAIL] {name}: {e}")
            continue
        md_path.write_text(md, encoding="utf-8")
        print(f"[OK]   {name}  →  {md_path.name} ({len(md):,} chars)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
