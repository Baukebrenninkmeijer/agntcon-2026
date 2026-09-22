# ruff: noqa: E501

"""Generate the README banner as one self-contained SVG.

Fonts are embedded so the banner keeps the deck's typography wherever it is rendered, and the
scatter reuses the grey-zone construction from `build_deck.py`: two overlapping classes with one
boundary drawn through the overlap.
"""

import base64
import math
import os
import pathlib
import random

# Same typeface as the deck. DECK_FONT_DIR overrides the location.
FONT_DIR = os.environ.get(
    "DECK_FONT_DIR", str(pathlib.Path.home() / ".claude/skills/orq-chart-style/fonts")
)
OUTPUT = pathlib.Path(__file__).parents[1] / "docs" / "assets" / "banner.svg"

WIDTH, HEIGHT = 1280, 400


def b64(name: str) -> str:
    return base64.b64encode((pathlib.Path(FONT_DIR) / name).read_bytes()).decode()


def font_faces() -> str:
    if not FONT_DIR or not pathlib.Path(FONT_DIR).is_dir():
        return ""
    return f"""      @font-face{{font-family:"Kurrent";src:url(data:font/woff2;base64,{b64("ESKlarheitKurrent-Smbd.woff2")}) format("woff2");font-weight:600}}
      @font-face{{font-family:"Kurrent";src:url(data:font/woff2;base64,{b64("ESKlarheitKurrent-Rg.woff2")}) format("woff2");font-weight:400}}
      @font-face{{font-family:"Kurrent Mono";src:url(data:font/ttf;base64,{b64("ESKlarheitKurrentMono-Md.ttf")}) format("truetype");font-weight:500}}"""


def scatter() -> str:
    """Two classes of cases, drifting apart from left to right, plus a few on the boundary."""

    rng = random.Random(11)
    marks = []
    for _ in range(120):
        x = rng.uniform(620, 1270)
        y = rng.uniform(20, 380)
        side = (x - 620) / 650 - (y - 20) / 360 + rng.gauss(0, 0.16)
        fill = "#9fe8dd" if side > 0 else "#f2f0eb"
        opacity = 0.5 + 0.45 * min(1.0, (x - 620) / 650)
        marks.append(
            f'<circle cx="{x:.0f}" cy="{y:.0f}" r="4.5" fill="{fill}" opacity="{opacity:.2f}"/>'
        )
    return "".join(marks)


def boundary() -> str:
    """One defensible line through the overlap, in the deck's orange."""

    points = [(660 + i * 13, 190 + 110 * math.sin(i / 7.0) * 0.5 + i * 2.4) for i in range(48)]
    d = f"M{points[0][0]:.0f},{points[0][1]:.0f}" + "".join(
        f" L{x:.0f},{y:.0f}" for x, y in points[1:]
    )
    return f'<path d="{d}" fill="none" stroke="#ff9747" stroke-width="5" stroke-linecap="round" opacity=".92"/>'


svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" width="{WIDTH}" height="{HEIGHT}" role="img" aria-label="Building the evaluation flywheel: a human-aligned evaluation loop for an LLM data-analysis agent">
  <defs>
    <style>
{font_faces()}
      .sans{{font-family:"Kurrent",Inter,-apple-system,system-ui,sans-serif}}
      .mono{{font-family:"Kurrent Mono",ui-monospace,"SF Mono",Menlo,monospace}}
    </style>
    <linearGradient id="ground" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#013f42"/>
      <stop offset="0.55" stop-color="#025558"/>
      <stop offset="1" stop-color="#04716e"/>
    </linearGradient>
    <linearGradient id="fade" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#025558" stop-opacity="0.98"/>
      <stop offset="0.52" stop-color="#025558" stop-opacity="0.88"/>
      <stop offset="1" stop-color="#025558" stop-opacity="0"/>
    </linearGradient>
    <pattern id="rule" width="9" height="{HEIGHT}" patternUnits="userSpaceOnUse">
      <rect x="0" width="1" height="{HEIGHT}" fill="#ffffff" opacity="0.035"/>
    </pattern>
  </defs>

  <rect width="{WIDTH}" height="{HEIGHT}" fill="url(#ground)"/>
  <g>{scatter()}</g>
  {boundary()}
  <rect width="{WIDTH}" height="{HEIGHT}" fill="url(#rule)"/>
  <rect width="{WIDTH}" height="{HEIGHT}" fill="url(#fade)"/>

  <text class="mono" x="88" y="120" font-size="15" letter-spacing="3.6" fill="rgba(250,249,245,.55)">BAUKE BRENNINKMEIJER &#183; ORQ.AI</text>
  <text class="mono" x="88" y="196" font-size="17" letter-spacing="4.4" fill="#9fe8dd">FIFTY CASES &#183; ALIGNED JUDGES &#183; AGENT EVALS</text>
  <text class="sans" x="86" y="268" font-size="56" font-weight="600" letter-spacing="-1.6" fill="#faf9f5">building the evaluation flywheel</text>
  <text class="sans" x="88" y="316" font-size="22" font-weight="400" fill="rgba(250,249,245,.78)">Humans draw the boundary. The judge is validated against them. Then it scales.</text>
</svg>
"""

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.write_text(svg, encoding="utf-8")
print(f"wrote {OUTPUT} ({len(svg) / 1024:.0f} KB)")
