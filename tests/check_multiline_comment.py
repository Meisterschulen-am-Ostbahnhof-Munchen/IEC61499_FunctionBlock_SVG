#!/usr/bin/env python3
"""Regression test: a Comment with line breaks (&#10;) is drawn as one <text>
line per line in the diagram header, the header grows accordingly, and the
widest line lies inside the viewBox horizontally.

Usage: python tests/check_multiline_comment.py
"""
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIXTURE = ROOT / "tests" / "fixtures" / "MultilineComment.fbt"
NS = "{http://www.w3.org/2000/svg}"
EXPECTED = [
    "Erste Zeile des Kommentars",
    "zweite Zeile, die deutlich laenger ist als die erste und trotzdem komplett im Diagramm "
    "sichtbar sein muss, auch wenn sie breiter als das Netzwerk ist",
    "dritte Zeile",
]


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "out.svg"
        subprocess.run([sys.executable, str(ROOT / "iec61499_network_to_svg.py"), str(FIXTURE), "-o", str(out)],
                       check=True, capture_output=True)
        root = ET.parse(out).getroot()

    texts = [t for t in root.iter(NS + "text") if t.get("fill") == "#333333" and t.get("font-weight") == "bold"]
    lines = ["".join(t.itertext()) for t in texts]
    errors = []
    if lines != EXPECTED:
        errors.append(f"header lines {lines!r}, expected {EXPECTED!r}")
    ys = [float(t.get("y")) for t in texts]
    if len(ys) != len(set(ys)) or ys != sorted(ys):
        errors.append(f"header lines must be on distinct, increasing y positions: {ys}")

    vb_x, _, vb_w, _ = (float(v) for v in re.split(r"[ ,]+", root.get("viewBox").strip()))
    for t in texts:
        # conservative lower bound of the glyph width, as in check_viewbox.py
        left = float(t.get("x"))
        width = len("".join(t.itertext())) * 3.0
        if left < vb_x or left + width > vb_x + vb_w:
            errors.append(f"comment line {''.join(t.itertext())!r} lies outside the viewBox")

    for e in errors:
        print("ERROR:", e)
    if not errors:
        print("OK: multi-line comment is drawn line by line inside the viewBox")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
