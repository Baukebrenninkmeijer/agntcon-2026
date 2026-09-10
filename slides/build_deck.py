# ruff: noqa: E501

import base64
import json
import math
import pathlib
import random

FONT_DIR = pathlib.Path("/Users/baukebrenninkmeijer/.claude/skills/orq-chart-style/fonts")


def b64(name: str) -> str:
    return base64.b64encode((FONT_DIR / name).read_bytes()).decode()


fonts = {
    "RG": b64("ESKlarheitKurrent-Rg.woff2"),
    "MD": b64("ESKlarheitKurrent-Md.woff2"),
    "SB": b64("ESKlarheitKurrent-Smbd.woff2"),
    "MONO": b64("ESKlarheitKurrentMono-Md.ttf"),
}

experiment_grid = base64.b64encode(
    (pathlib.Path(__file__).parent / "assets" / "experiment-grid.jpg").read_bytes()
).decode()

cartoon = base64.b64encode(
    (pathlib.Path(__file__).parent / "assets" / "cartoon-bauke.jpg").read_bytes()
).decode()


# Preserved grey-zone visual: overlapping classes and several defensible boundaries.
rng = random.Random(7)
grey_dots: list[tuple[float, float, str]] = []
for _ in range(60):
    x = rng.uniform(80, 1120)
    y = rng.uniform(80, 620)
    score = (x / 1200) - (y / 700) + rng.gauss(0, 0.13)
    grey_dots.append((x, y, "a" if score > 0 else "b"))

grey_dot_svg = "\n".join(
    f'<circle class="d {kind}" cx="{x:.0f}" cy="{y:.0f}" r="9"/>'
    for x, y, kind in grey_dots
)


# Slide 20: the grey zone redrawn, one dot per reviewed case. Positions are the
# slide-12 illustration reused; the highlighted counts are the real development
# signals (four split cases before the rule, eight after, no verdict flips).
amb_rng = random.Random(11)
amb_dots = [
    (amb_rng.uniform(70, 1130), amb_rng.uniform(70, 630))
    for _ in range(50)
]


def ambiguity_zone(spread: float, highlighted: int, gradient_id: str) -> str:
    top, bottom = -90 - spread, 220 + spread
    parts = [
        f'<svg class="ambz" viewBox="0 0 1200 700" aria-label="The reviewed cases against the boundary band, {highlighted} of them inside it">',
        f'<defs><linearGradient id="{gradient_id}" x1="0" y1="0" x2="1" y2="1">'
        '<stop offset="0" stop-color="#ffffff" stop-opacity="0"/>'
        '<stop offset=".5" stop-color="#b9b8b6" stop-opacity=".65"/>'
        '<stop offset="1" stop-color="#ffffff" stop-opacity="0"/></linearGradient></defs>',
        f'<path class="band" d="M 0 {top:.0f} L 1200 {top + 580:.0f} L 1200 {bottom + 580:.0f} L 0 {bottom:.0f} Z" fill="url(#{gradient_id})"/>',
        f'<path class="edge" d="M 0 {top:.0f} L 1200 {top + 580:.0f}"/>',
        f'<path class="edge" d="M 0 {bottom:.0f} L 1200 {bottom + 580:.0f}"/>',
    ]
    centre = (top + bottom) / 2
    inside, outside = [], []
    for x, y in amb_dots:
        (inside if abs(y - (centre + x * 580 / 1200)) < spread else outside).append((x, y))
    for x, y in outside:
        parts.append(f'<circle class="d" cx="{x:.0f}" cy="{y:.0f}" r="9"/>')
    inside.sort()
    step = max(1, len(inside) // highlighted)
    for x, y in inside[::step][:highlighted]:
        parts.append(f'<circle class="d hi" cx="{x:.0f}" cy="{y:.0f}" r="13"/>')
    parts.append("</svg>")
    return "\n".join(parts)


def wiggle(amplitude: float, frequency: float, phase: float, drift: float) -> str:
    def y_value(x: float) -> float:
        t = x / 1200
        taper = 0.35 + 0.65 * math.sin(math.pi * t)
        return 0.50 * x + 55 + drift + amplitude * taper * math.sin(frequency * x + phase)

    points = [(x, y_value(x)) for x in range(20, 1200, 55)]
    path = f"M {points[0][0]:.0f} {points[0][1]:.0f}"
    for index in range(len(points) - 1):
        p0 = points[index - 1] if index else points[0]
        p1 = points[index]
        p2 = points[index + 1]
        p3 = points[index + 2] if index + 2 < len(points) else p2
        c1 = (
            p1[0] + (p2[0] - p0[0]) / 6,
            p1[1] + (p2[1] - p0[1]) / 6,
        )
        c2 = (
            p2[0] - (p3[0] - p1[0]) / 6,
            p2[1] - (p3[1] - p1[1]) / 6,
        )
        path += (
            f" C {c1[0]:.0f} {c1[1]:.0f}, {c2[0]:.0f} {c2[1]:.0f},"
            f" {p2[0]:.0f} {p2[1]:.0f}"
        )
    return path


grey_paths = (
    wiggle(70, 0.0105, 0.4, -28),
    wiggle(62, 0.0082, 2.4, 22),
    wiggle(58, 0.0150, 4.2, 0),
)


# Real signals from the canonical v4 jury run (runs/v4-jury-20260907.jsonl, 2026-09-07).
# disagreement = panel raw agreement below 1.0; wobble = a judge changed its own vote across repetitions.
case_signals = json.loads(
    pathlib.Path(__file__).with_name("case-signals-v4.json").read_text(encoding="utf-8")
)
queue = sorted(
    (case for case in case_signals if case["disagree"] or case["wobble"]),
    key=lambda case: (not case["disagree"], not case["wobble"], case["raw_agreement"]),
)
# The recommended review batch: the four highest-signal flagged cases, plus four
# unflagged cases sampled at random, so the human sees a control alongside the queue.
review_batch = 4
queue_rank = {case["i"]: rank for rank, case in enumerate(queue[:review_batch])}
unflagged = [case["i"] for case in case_signals if not (case["disagree"] or case["wobble"])]
sample_rank = {
    index: rank
    for rank, index in enumerate(random.Random(4).sample(unflagged, review_batch))
}

case_marks: list[str] = []
for case in case_signals:
    index = case["i"]
    cx = 110 + (index % 10) * 116
    cy = 290 + (index // 10) * 96
    classes = ["g"]
    style = f"--x:{cx}px;--y:{cy}px"
    if index in queue_rank:
        classes.append("q")
        style += f";--qx:{152 + queue_rank[index] * 116}px;--qy:108px"
    elif index in sample_rank:
        classes.append("q sam")
        style += f";--qx:{728 + sample_rank[index] * 116}px;--qy:108px"
    if case["wobble"]:
        classes.append("wob")
    if case["disagree"]:
        classes.append("dis")
    rings = ""
    if case["disagree"]:
        rings += '<circle class="ring disagree" r="43"/>'
    if case["wobble"]:
        rings += '<circle class="ring wobble" r="35"/>'
    case_marks.append(
        f'<g class="{" ".join(classes)}" style="{style}">'
        f'{rings}<circle class="case" r="27"'
        f' style="animation-delay:{(index * 137 % 240) / 100:.2f}s"/></g>'
    )
case_dot_svg = "\n".join(case_marks)

# Slide 10 scatter: illustrative cases resting on either side of the boundary. Fixed offsets, so the
# layout is stable across builds; the seam sits at 50% and no case is placed within 6% of it.
binary_cases = "".join(
    f'<i style="left:{left}%;top:{top}px"></i>'
    for left, top in (
        (7, 8), (13, -46), (19, 34), (26, -18), (32, 52), (38, -34), (43, 14),
        (57, -12), (62, 44), (68, -40), (74, 22), (81, -24), (88, 40), (93, -6),
    )
)

# Real jury verdicts from the v3 decision-support run
# (runs/decision-support-jury-prompt-v3-20260908.jsonl, 2026-09-08). One layer per case, nine cells
# per layer: three judges by three repetitions. The front layer is the case discussed out loud.
judge_grid = json.loads(
    pathlib.Path(__file__).with_name("judge-grid-v3.json").read_text(encoding="utf-8")
)
judge_names = "".join(f"<span>{name}</span>" for name in judge_grid["judges"])
judge_layers = "".join(
    f'<div class="layer{" front" if depth == 0 else ""}" style="--i:{depth}">'
    + "".join(f'<i class="{cell}"></i>' for cell in layer)
    + "</div>"
    for depth, layer in enumerate(judge_grid["layers"])
)

# Real agent trajectories from the canonical v4 observation run
# (runs/v4-observations-retry-20260907.jsonl, 2026-09-07). One bar per case; each segment is one
# message, its width the size of that message, its colour the kind of turn.
trajectories = json.loads(
    pathlib.Path(__file__).with_name("trajectories-v4.json").read_text(encoding="utf-8")
)
trajectories = sorted(
    trajectories, key=lambda run: sum(size for _, size in run["segments"])
)
_widest = max(sum(size for _, size in run["segments"]) for run in trajectories)
_row_height = 8
_row_gap = 4
traj_rows: list[str] = []
for row, run in enumerate(trajectories):
    y = row * (_row_height + _row_gap)
    x = 0.0
    parts = [f'<g class="tr" style="animation-delay:{row * 0.022:.2f}s">']
    last_index = len(run["segments"]) - 1
    for position, (kind, size) in enumerate(run["segments"]):
        width = size / _widest * 1824
        final = " final" if position == last_index else ""
        parts.append(
            f'<rect class="seg {kind}{final}" x="{x:.1f}" y="{y}" width="{max(width - 1.5, 1.2):.1f}"'
            f' height="{_row_height}" rx="2"/>'
        )
        x += width
    parts.append("</g>")
    traj_rows.append("".join(parts))
traj_svg = "\n".join(traj_rows)
traj_height = len(trajectories) * (_row_height + _row_gap) - _row_gap

ORQMARK = """<symbol id="orqmark" viewBox="0 0 100 100">
        <path fill="currentColor"
          d="M82.9268 27.8049C82.9268 30.8783 82.9268 32.4151 82.3287 33.589C81.8026 34.6216 80.963 35.4611 79.9304 35.9872C78.7565 36.5854 77.2198 36.5854 74.1463 36.5854H72.1951C69.1217 36.5854 67.5849 36.5854 66.411 35.9872C65.3784 35.4611 64.5389 34.6216 64.0128 33.589C63.4146 32.4151 63.4146 30.8783 63.4146 27.8049V25.6098C63.4146 22.7662 63.4146 21.3444 62.9005 20.2417C62.3552 19.0724 61.4154 18.1326 60.2461 17.5873C59.1434 17.0732 57.7216 17.0732 54.8781 17.0732C52.0345 17.0732 50.6127 17.0732 49.51 16.559C48.3407 16.0137 47.4009 15.0739 46.8556 13.9046C46.3415 12.802 46.3415 11.3802 46.3415 8.53659C46.3415 5.69299 46.3415 4.27119 46.8556 3.16856C47.4009 1.99924 48.3407 1.05943 49.51 0.514165C50.6127 0 52.0446 0 54.9084 0C57.7723 0 59.2042 0 60.3068 0.514165C61.4761 1.05943 62.4159 1.99924 62.9612 3.16856C63.4754 4.27119 63.4754 5.69299 63.4754 8.53659C63.4754 11.3802 63.4754 12.802 63.9895 13.9046C64.5348 15.0739 65.4746 16.0137 66.6439 16.559C67.7466 17.0732 69.1684 17.0732 72.012 17.0732H74.1463C77.2198 17.0732 78.7565 17.0732 79.9304 17.6713C80.963 18.1974 81.8026 19.037 82.3287 20.0696C82.9268 21.2435 82.9268 22.7802 82.9268 25.8537V27.8049Z" />
        <path fill="currentColor"
          d="M27.8049 17.0732C30.8783 17.0732 32.4151 17.0732 33.589 17.6713C34.6216 18.1974 35.4611 19.037 35.9872 20.0696C36.5854 21.2435 36.5854 22.7802 36.5854 25.8537V27.8049C36.5854 30.8783 36.5854 32.4151 35.9872 33.589C35.4611 34.6216 34.6216 35.4611 33.589 35.9872C32.4151 36.5854 30.8783 36.5854 27.8049 36.5854L25.6098 36.5854C22.7662 36.5854 21.3444 36.5854 20.2417 37.0995C19.0724 37.6448 18.1326 38.5846 17.5873 39.7539C17.0732 40.8566 17.0732 42.2784 17.0732 45.122C17.0732 47.9656 17.0732 49.3874 16.559 50.49C16.0137 51.6593 15.0739 52.5991 13.9046 53.1444C12.802 53.6585 11.3802 53.6585 8.53659 53.6585C5.69299 53.6585 4.27119 53.6585 3.16856 53.1444C1.99924 52.5991 1.05943 51.6593 0.514165 50.49C1.81721e-07 49.3874 1.25306e-07 47.9554 1.236e-10 45.0916C-1.25059e-07 42.2277 -1.81721e-07 40.7958 0.514164 39.6932C1.05943 38.5239 1.99924 37.5841 3.16856 37.0388C4.27119 36.5246 5.69299 36.5246 8.53658 36.5246C11.3802 36.5246 12.802 36.5246 13.9046 36.0105C15.0739 35.4652 16.0137 34.5254 16.559 33.3561C17.0732 32.2534 17.0732 30.8316 17.0732 27.988V25.8537C17.0732 22.7802 17.0732 21.2435 17.6713 20.0696C18.1974 19.037 19.037 18.1974 20.0696 17.6713C21.2435 17.0732 22.7802 17.0732 25.8537 17.0732H27.8049Z" />
        <path fill="currentColor"
          d="M36.5854 91.4634C36.5854 88.6198 36.5854 87.198 36.0712 86.0954C35.5259 84.9261 34.5861 83.9863 33.4168 83.441C32.3142 82.9268 30.8924 82.9268 28.0488 82.9268H25.8537C22.7802 82.9268 21.2435 82.9268 20.0696 82.3287C19.037 81.8026 18.1974 80.963 17.6713 79.9304C17.0732 78.7565 17.0732 77.2198 17.0732 74.1463V72.1951C17.0732 69.1217 17.0732 67.5849 17.6713 66.411C18.1974 65.3784 19.037 64.5389 20.0696 64.0128C21.2435 63.4146 22.7802 63.4146 25.8537 63.4146L27.8049 63.4146C30.8783 63.4146 32.4151 63.4146 33.589 64.0128C34.6216 64.5389 35.4611 65.3784 35.9872 66.411C36.5854 67.5849 36.5854 69.1217 36.5854 72.1951V74.3295C36.5854 77.1731 36.5854 78.5949 37.0995 79.6975C37.6448 80.8669 38.5846 81.8067 39.7539 82.3519C40.8566 82.8661 42.2783 82.8661 45.1219 82.8661C47.9655 82.8661 49.3873 82.8661 50.49 83.3803C51.6593 83.9255 52.5991 84.8653 53.1444 86.0347C53.6585 87.1373 53.6585 88.5692 53.6585 91.433C53.6585 94.2969 53.6585 95.7288 53.1444 96.8314C52.5991 98.0008 51.6593 98.9406 50.49 99.4858C49.3873 100 47.9656 100 45.122 100C42.2784 100 40.8566 100 39.7539 99.4858C38.5846 98.9406 37.6448 98.0008 37.0995 96.8314C36.5854 95.7288 36.5854 94.307 36.5854 91.4634Z" />
        <path fill="currentColor"
          d="M72.1951 82.9268C69.1217 82.9268 67.5849 82.9268 66.411 82.3287C65.3784 81.8026 64.5389 80.963 64.0128 79.9304C63.4146 78.7565 63.4146 77.2198 63.4146 74.1463V72.1951C63.4146 69.1217 63.4146 67.5849 64.0128 66.411C64.5389 65.3784 65.3784 64.5389 66.411 64.0128C67.5849 63.4146 69.1217 63.4146 72.1951 63.4146H74.3902C77.2338 63.4146 78.6556 63.4146 79.7583 62.9005C80.9276 62.3552 81.8674 61.4154 82.4127 60.2461C82.9268 59.1434 82.9268 57.7216 82.9268 54.8781C82.9268 52.0345 82.9268 50.6127 83.441 49.51C83.9863 48.3407 84.9261 47.4009 86.0954 46.8556C87.198 46.3415 88.6198 46.3415 91.4634 46.3415C94.307 46.3415 95.7288 46.3415 96.8314 46.8556C98.0008 47.4009 98.9406 48.3407 99.4858 49.51C100 50.6127 100 52.0446 100 54.9084C100 57.7723 100 59.2042 99.4858 60.3068C98.9406 61.4761 98.0008 62.4159 96.8314 62.9612C95.7288 63.4754 94.307 63.4754 91.4634 63.4754C88.6198 63.4754 87.198 63.4754 86.0954 63.9895C84.9261 64.5348 83.9863 65.4746 83.441 66.6439C82.9268 67.7466 82.9268 69.1684 82.9268 72.012V74.1463C82.9268 77.2198 82.9268 78.7565 82.3287 79.9304C81.8026 80.963 80.963 81.8026 79.9304 82.3287C78.7565 82.9268 77.2198 82.9268 74.1463 82.9268H72.1951Z" />
        <path fill="currentColor"
          d="M50 58.5366C47.4439 58.5366 46.1659 58.5366 45.1504 58.1403C43.6417 57.5516 42.4483 56.3583 41.8596 54.8496C41.4634 53.834 41.4634 52.556 41.4634 50C41.4634 47.444 41.4634 46.166 41.8596 45.1504C42.4483 43.6417 43.6417 42.4484 45.1504 41.8597C46.1659 41.4634 47.4439 41.4634 50 41.4634C52.556 41.4634 53.834 41.4634 54.8495 41.8597C56.3582 42.4484 57.5516 43.6417 58.1403 45.1504C58.5365 46.166 58.5365 47.444 58.5365 50C58.5365 52.556 58.5365 53.834 58.1403 54.8496C57.5516 56.3583 56.3582 57.5516 54.8495 58.1403C53.834 58.5366 52.556 58.5366 50 58.5366Z" />
      </symbol>"""

html = r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Building the evaluation flywheel</title>
<link rel="icon" href="data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%2064%2064%22%3E%3Crect%20width%3D%2264%22%20height%3D%2264%22%20rx%3D%2214%22%20fill%3D%22%23025558%22%2F%3E%3Ccircle%20cx%3D%2218%22%20cy%3D%2219%22%20r%3D%227%22%20fill%3D%22%23f9f8f6%22%2F%3E%3Ccircle%20cx%3D%2246%22%20cy%3D%2247%22%20r%3D%227%22%20fill%3D%22%23f9f8f6%22%2F%3E%3Cpath%20d%3D%22M6%2046%20C22%2046%2026%2018%2058%2018%22%20stroke%3D%22%23ff9747%22%20stroke-width%3D%228%22%20fill%3D%22none%22%20stroke-linecap%3D%22round%22%2F%3E%3C%2Fsvg%3E">
<style>
  @font-face{font-family:"Kurrent";src:url(data:font/woff2;base64,__RG__) format("woff2");font-weight:400;font-display:swap}
  @font-face{font-family:"Kurrent";src:url(data:font/woff2;base64,__MD__) format("woff2");font-weight:500;font-display:swap}
  @font-face{font-family:"Kurrent";src:url(data:font/woff2;base64,__SB__) format("woff2");font-weight:600;font-display:swap}
  @font-face{font-family:"Kurrent Mono";src:url(data:font/ttf;base64,__MONO__) format("truetype");font-weight:500;font-display:swap}
  :root{
    --bg:#f9f8f6;--paper:#fff;--ink:#25232e;--ink2:#55535c;--muted:#8c8a91;
    --orange:#ff9747;--orange-dark:#df5325;--red:#c94f45;--teal:#4da296;--teal-deep:#025558;
    --sans:"Kurrent",-apple-system,"Inter",system-ui,sans-serif;
    --mono:"Kurrent Mono",ui-monospace,"SF Mono",Menlo,monospace;
  }
  *{box-sizing:border-box;margin:0;padding:0}
  html,body{height:100%;overflow:hidden;background:var(--bg);color:var(--ink);font-family:var(--sans);-webkit-font-smoothing:antialiased}
  #stage{position:fixed;left:50%;top:50%;width:1920px;height:1080px;transform-origin:center;transform:translate(-50%,-50%) scale(1)}
  .slide{position:absolute;inset:0;padding:42px 48px;display:flex;flex-direction:column;justify-content:center;opacity:0;pointer-events:none;transition:opacity .3s ease}
  .slide.active{opacity:1;pointer-events:auto}
  .eyebrow{font-family:var(--mono);font-size:24px;letter-spacing:.14em;text-transform:uppercase;color:var(--teal-deep);margin-bottom:38px}
  .eyebrow .qn{color:var(--orange-dark)}
  .slide[data-step="1"] .define{opacity:1;transform:none}
  @media (prefers-reduced-motion:reduce){.define{transition:none;transform:none}}
  h1{font-size:128px;line-height:1.01;letter-spacing:-.03em;font-weight:600;margin-bottom:36px}
  h2{font-size:82px;line-height:1.06;letter-spacing:-.025em;font-weight:600;margin-bottom:48px;max-width:1760px}
  h3{font-size:42px;line-height:1.15;font-weight:500;color:var(--ink);margin-bottom:20px}
  .sub{font-size:36px;line-height:1.42;color:var(--ink2);max-width:1450px}
  .body{font-size:34px;line-height:1.42;color:var(--ink2)}
  .body b{color:var(--ink);font-weight:500}
  .hl{color:var(--orange-dark)}
  .mono{font-family:var(--mono)}
  body:has(.who-slide.active){background:radial-gradient(circle at 50% 40%, #0a6b66 0%, var(--teal-deep) 46%, #022f2f 100%)}
  .who-slide{padding:0;display:grid;place-items:center;overflow:hidden}
  .who-slide::before{content:"";position:absolute;width:860px;height:860px;border-radius:50%;background:repeating-radial-gradient(circle, transparent 0 40px, rgba(255,255,255,.04) 40px 41px);pointer-events:none}
  .who{position:relative;display:flex;flex-direction:column;align-items:center;gap:30px;text-align:center}
  .who-ring{position:relative;width:600px;height:600px;border-radius:50%;display:grid;place-items:center;background:rgba(255,255,255,.06);box-shadow:0 30px 90px rgba(0,0,0,.45)}
  .who-ring::after{content:"";position:absolute;inset:-16px;border-radius:50%;border:2px solid rgba(255,255,255,.18)}
  .who-ring img{width:100%;height:100%;object-fit:cover;border-radius:50%;border:8px solid var(--paper)}
  .who-name{font-size:58px;font-weight:600;color:var(--paper);letter-spacing:-.01em}
  .who-role{margin-top:10px;font-family:var(--mono);font-size:26px;letter-spacing:.14em;text-transform:uppercase;color:#9fcfca}
  .who-line{margin-top:16px;font-family:var(--mono);font-size:21px;line-height:1.45;color:rgba(250,249,245,.62)}
  .who-slide .counter{color:rgba(250,249,245,.45)}
  .orq-slide h2{margin-bottom:34px}
  .orq-band,.orq-cards{width:100%;max-width:1560px;margin-left:auto;margin-right:auto}
  .orq-band{display:flex;align-items:center;gap:26px;background:var(--teal-deep);border-radius:22px;padding:26px 34px;color:var(--paper)}
  .orq-band .mark{flex:none;width:66px;height:66px;display:grid;place-items:center;background:rgba(255,255,255,.12);border-radius:16px}
  .orq-band .mark svg{width:40px;height:40px}
  .orq-band p{font-size:32px;line-height:1.4}
  .orq-band p b{font-weight:600}
  .orq-band p span{color:#9fcfca}
  .orq-cards{display:grid;grid-template-columns:repeat(3,1fr);gap:22px;margin-top:24px}
  .orq-card{border-radius:22px;padding:28px 30px;min-height:430px;display:flex;flex-direction:column;gap:14px}
  .orq-card.build{background:var(--teal-deep);color:var(--paper)}
  .orq-card.ship{background:#1cd3ac;color:#0a2f2c}
  .orq-card.optimize{background:var(--orange-dark);color:var(--paper)}
  .orq-card .top{display:flex;align-items:center;justify-content:space-between}
  .orq-card .top svg{width:44px;height:44px;opacity:.95}
  .orq-card .verb{font-family:var(--mono);font-size:19px;font-weight:600;letter-spacing:.14em;text-transform:uppercase;padding:6px 14px;border-radius:999px;background:rgba(255,255,255,.16)}
  .orq-card.ship .verb{background:rgba(10,47,44,.14)}
  .orq-card .name{font-size:48px;font-weight:600;line-height:1.05}
  .orq-card .desc{font-size:26px;line-height:1.4;opacity:.92}
  .orq-card .peer{margin-top:auto;font-family:var(--mono);font-size:19px;letter-spacing:.02em;opacity:.72;padding-top:14px;border-top:1px solid currentColor}
  .funnel{width:1720px;margin-top:62px;overflow:visible}
  .funnel .fdot{fill:none;stroke:var(--orange);stroke-width:4;stroke-dasharray:5 7}
  .funnel .fline{fill:none;stroke:var(--orange);stroke-width:2.5;opacity:.38}
  .funnel .flab,.funnel .tlab{font-family:var(--mono);font-size:21px;letter-spacing:.14em;fill:var(--muted)}
  .funnel .target{fill:var(--teal-deep)}
  .funnel .qmark{fill:var(--paper);font-family:var(--sans);font-size:108px;font-weight:600;text-anchor:middle;dominant-baseline:central}
  .funnel-sub{margin-top:52px}
  .byline{display:flex;gap:54px;margin-top:82px;font-family:var(--mono);font-size:23px;color:var(--muted)}
  .cols{display:grid;grid-template-columns:1fr 1fr;gap:76px;align-items:center}
  .cols.wide{grid-template-columns:1.25fr 1fr}
  .cols.grey-layout{grid-template-columns:1.55fr .9fr;gap:54px}
  .statement h2{font-size:104px;margin:0;max-width:1800px}
  .statement .sub{margin-top:40px}
  body:has(.statement.inverted.active){background:var(--teal-deep)}
  .statement.inverted{color:var(--paper)}
  .statement.inverted::before{content:"";position:absolute;inset:0;background:radial-gradient(circle at 22% 34%,rgba(255,255,255,.07) 0%,transparent 58%);pointer-events:none}
  .statement.inverted h2{color:var(--paper)}
  .statement.inverted .sub{color:rgba(250,249,245,.74)}
  .statement.inverted .fac-note{color:#9fcfca}
  .statement.inverted .counter{color:rgba(250,249,245,.45)}
  .ship-read{display:flex;flex-direction:column;gap:34px;margin-top:64px;max-width:1720px}
  .ship-read .row span{display:block;font-family:var(--mono);font-size:23px;letter-spacing:.14em;color:rgba(250,249,245,.58);margin-bottom:13px}
  .ship-read .track{height:46px;border-radius:8px;background:rgba(255,255,255,.13);overflow:hidden}
  .ship-read .track i{display:block;height:100%;background:rgba(250,249,245,.86);border-radius:8px}
  .ship-read .row.read span{color:var(--orange)}
  .ship-read .row.read i{width:5%;background:var(--orange);transform:scaleX(0);transform-origin:left;transition:transform .55s cubic-bezier(.16,1,.3,1)}
  .slide[data-step="1"] .ship-read .row.read i{transform:none}
  @media (prefers-reduced-motion:reduce){.ship-read .row.read i{transition:none}}
  .price{position:relative;margin-top:76px;padding-top:26px}
  .price::before{content:"";position:absolute;left:0;top:0;width:140px;border-top:4px solid var(--orange)}
  .price .setup{display:block;font-family:var(--mono);font-size:25px;letter-spacing:.14em;text-transform:uppercase;color:var(--teal-deep)}
  .price .value{display:block;margin-top:10px;font-size:76px;line-height:1.04;font-weight:600;letter-spacing:-.025em;color:var(--orange-dark)}
  ul.plain{list-style:none;display:flex;flex-direction:column;gap:26px;font-size:34px;line-height:1.35;color:var(--ink2)}
  ul.plain li{position:relative;padding-left:42px}
  ul.plain li::before{content:"";position:absolute;left:0;top:17px;width:14px;height:14px;border-radius:50%;background:var(--orange)}
  .stat .l{font-size:27px;line-height:1.3;color:var(--ink2);margin-top:14px}
  .criterion-q{font-size:100px;line-height:1.05;margin-bottom:30px;max-width:1700px}
  .setup-strip{display:flex;gap:110px;margin-top:120px;border-top:3px solid var(--teal-deep);padding-top:34px}
  .setup-strip div{display:flex;align-items:baseline;gap:24px}
  .setup-strip b{font-size:88px;font-weight:600;letter-spacing:-.04em}
  .setup-strip span{font-size:31px;color:var(--ink2)}
  .ask{margin-top:46px;font-size:40px;color:var(--ink);font-weight:500}
  .compare{display:grid;grid-template-columns:1fr 1fr;gap:56px;margin-top:38px;max-width:1500px}
  .answer{border-top:6px solid var(--teal);padding:34px 0 0;min-height:0}
  .answer.b{border-color:var(--orange)}
  .answer .tag{font-family:var(--mono);font-size:19px;letter-spacing:.1em;color:var(--ink2);margin-bottom:22px}
  .answer p{font-size:33px;line-height:1.38;color:var(--ink2)}
  .answer strong{color:var(--ink);font-weight:500}
  .answer mark{background:rgba(77,162,150,.24);color:var(--ink);padding:.06em .12em;border-radius:4px;box-decoration-break:clone;-webkit-box-decoration-break:clone}
  .answer code{font-family:var(--mono);font-size:.88em;color:var(--teal-deep)}
  .checks{display:flex;flex-direction:column;gap:26px}
  .check{display:grid;grid-template-columns:58px 1fr;gap:26px;align-items:center;font-size:35px;color:var(--ink2)}
  .check i{width:58px;height:58px;border:3px solid var(--teal);border-radius:50%;display:grid;place-items:center;font-style:normal;color:var(--teal);font-size:31px}
  .life-axis{display:block;width:100%;margin-top:30px}
  .life-axis .ax{stroke:var(--ink);stroke-width:3}
  .life-axis .rel{stroke:var(--muted);stroke-width:3;stroke-dasharray:10 10}
  .life-axis .mono{font-family:var(--mono);font-size:21px;letter-spacing:.11em;fill:var(--muted)}
  .life-axis .name{font-family:var(--sans);font-size:38px;font-weight:600;fill:var(--ink)}
  .life-axis .meta{font-family:var(--sans);font-size:26px;fill:var(--ink2)}
  .life-axis .band{fill:rgba(37,35,46,.10)}
  .life-axis .beat{fill:var(--ink2)}
  svg text{font-family:var(--sans)}
  .lbl{fill:var(--ink2);font-size:28px}
  .lbl.dark{fill:var(--ink)}
  .lbl.small{font-size:21px;fill:var(--muted);font-family:var(--mono);letter-spacing:.08em}
  .stroke-d{stroke:var(--muted);fill:none;stroke-width:3}
  .cols.origin-layout{grid-template-columns:1.5fr .85fr;gap:60px}
  .origin{display:block;width:100%;max-width:640px;margin:0 auto}
  .origin .arm{fill:none;stroke:var(--teal);stroke-width:5}
  .origin .pod{fill:var(--paper);stroke:var(--ink);stroke-width:4}
  .origin .name{font-size:34px;fill:var(--ink)}
  .origin .side{font-family:var(--mono);font-size:24px;fill:var(--ink2)}
  .origin .break{stroke:var(--orange-dark);stroke-width:7;fill:none;stroke-linecap:round}
  .lineage{display:block;width:100%;max-width:1720px;margin:56px auto 0}
  .lineage-content{width:100%;transition:transform .55s cubic-bezier(.16,1,.3,1)}
  .lineage-slide .lineage{transition:transform .55s cubic-bezier(.16,1,.3,1)}
  .lineage-loops{position:absolute;left:90px;right:90px;bottom:120px;width:calc(100% - 180px);height:320px;opacity:0;transform:translateY(190px);transition:opacity .45s ease,transform .55s cubic-bezier(.16,1,.3,1);pointer-events:none}
  .lineage-loops .loop{fill:none;stroke:var(--teal);stroke-width:5}
  .lineage-loops .entity{fill:var(--paper);stroke:var(--ink);stroke-width:4}
  .lineage-loops .name{font-size:36px;fill:var(--ink)}
  .lineage-slide[data-step="1"] .lineage-content{transform:translateY(-20px)}
  .lineage-slide[data-step="1"] .lineage{transform:translateY(-145px)}
  .lineage-slide[data-step="1"] .lineage-loops{opacity:1;transform:none}
  @media (prefers-reduced-motion:reduce){.lineage-content,.lineage-slide .lineage,.lineage-loops{transition:none}}
  .gz .d.a{fill:var(--ink)}.gz .d.b{fill:var(--teal)}
  .gz .band{opacity:0;transform:scaleY(.15);transform-origin:center;animation:none}
  .gz .d{opacity:0;animation:none}
  .gz .p{stroke:var(--orange);fill:none;stroke-width:6;stroke-linecap:round;stroke-dasharray:1800;stroke-dashoffset:1800;animation:none}
  .slide.active .gz .band{animation:bandIn .8s ease .15s forwards}
  .slide.active .gz .d{animation:dotIn .35s ease .55s forwards}
  .slide.active .gz .p:not(.p1):not(.p2):not(.p3){animation:drawLine 1.15s ease 1s forwards}
  .gz .p1,.gz .p2{transition:opacity .45s ease}
  .slide.active[data-step="1"] .gz .p1,.slide.active[data-step="2"] .gz .p1{animation:drawLine 1.15s ease 0s forwards}
  .slide.active[data-step="1"] .gz .p2,.slide.active[data-step="2"] .gz .p2{animation:drawLine 1.15s ease .3s forwards}
  .slide.active[data-step="1"] .gz .p3,.slide.active[data-step="2"] .gz .p3{animation:drawLine 1.15s ease .6s forwards}
  .slide.active[data-step="2"] .gz .p1,.slide.active[data-step="2"] .gz .p2{opacity:0}
  @keyframes bandIn{to{opacity:.68;transform:scaleY(1)}}
  @keyframes dotIn{to{opacity:1}}
  @keyframes drawLine{to{stroke-dashoffset:0}}
  .grey-loop{position:relative;margin-top:42px}
  .grey-loop-grid{display:grid;grid-template-columns:repeat(5,1fr);gap:52px;position:relative}
  .grey-loop-grid::before{content:"";position:absolute;left:6%;right:6%;top:72px;border-top:4px solid rgba(77,162,150,.38);z-index:0}
  .grey-loop-stage{position:relative;z-index:1;background:var(--bg);padding:0 14px;text-align:center}
  .grey-loop-stage .n{width:58px;height:58px;border-radius:50%;display:grid;place-items:center;margin:0 auto 24px;background:var(--teal);color:var(--paper);font-family:var(--mono);font-size:23px}
  .grey-loop-stage.human .n{background:var(--orange);color:var(--ink)}
  .grey-loop-stage h3{font-size:38px;line-height:1.16;margin:0 auto;max-width:9em}
  .grey-loop-return{position:relative;height:68px;margin:20px 9% 0;border-right:4px solid rgba(77,162,150,.55);border-bottom:4px solid rgba(77,162,150,.55);border-left:4px solid rgba(77,162,150,.55);border-radius:0 0 34px 34px}
  .grey-loop-return::before{content:"";position:absolute;left:-11px;top:-8px;width:18px;height:18px;border-top:4px solid var(--teal);border-right:4px solid var(--teal);transform:rotate(-45deg)}
  .grey-loop-return span{position:absolute;left:50%;bottom:-16px;transform:translateX(-50%);background:var(--bg);padding:0 22px;font-family:var(--mono);font-size:19px;letter-spacing:.1em;color:var(--teal-deep);white-space:nowrap}
  .sealed-note{position:absolute;right:0;top:-96px;font-family:var(--mono);font-size:19px;letter-spacing:.12em;color:var(--muted)}
  .case-proof{position:relative;display:grid;grid-template-columns:repeat(3,1fr);align-items:start;gap:64px;margin-top:58px;padding:42px 46px 0;border-top:3px solid rgba(140,138,145,.42);opacity:.15;transition:opacity .45s ease}
  .case-proof::before{content:"AFTER THE BOUNDARY QUESTIONS · APPLY THE DECISIONS TO CASES";position:absolute;left:50%;top:-15px;transform:translateX(-50%);background:var(--bg);padding:0 22px;font-family:var(--mono);font-size:19px;letter-spacing:.1em;color:var(--muted);white-space:nowrap}
  .slide[data-step="1"] .case-proof{opacity:1}
  .proof-case{text-align:center}
  .proof-case strong{display:grid;place-items:center;width:78px;height:78px;border-radius:50%;margin:0 auto 12px;background:var(--teal);color:var(--paper);font-family:var(--mono);font-size:23px}
  .proof-case.fail strong{background:var(--red)}
  .proof-case h4{font-size:25px;line-height:1.2;font-weight:500;margin-bottom:7px}
  .proof-case p{font-size:21px;line-height:1.3;color:var(--ink2);max-width:25em;margin:0 auto}
  @media (prefers-reduced-motion:reduce){.case-proof{transition:none}}
  .traj .seg{shape-rendering:crispEdges;transition:opacity .55s ease}
  .slide[data-step="1"] .traj .seg:not(.final){opacity:.3}
  .slide[data-step="1"] .traj .result:not(.final){opacity:.17}
  .traj .user{fill:var(--ink)}
  .traj .assistant{fill:var(--teal)}
  .traj .call{fill:var(--orange)}
  .traj .result{fill:var(--muted);opacity:.55}
  .traj .tr{opacity:0;transform:translateX(-26px)}
  .slide.active .traj .tr{animation:trIn .5s ease forwards}
  @keyframes trIn{to{opacity:1;transform:translateX(0)}}
  .traj{display:block;width:100%;height:auto}
  .cols.traj-layout{display:block;position:relative;margin-top:30px}
  .traj-axis{margin-top:14px;font-family:var(--mono);font-size:21px;letter-spacing:.1em;color:var(--muted)}
  .traj-caption{margin-top:26px;font-size:27px}
  .traj-evals{position:absolute;z-index:2;right:0;top:6px;width:360px;padding:12px 0 0 38px;background:linear-gradient(90deg,rgba(248,247,245,.9),var(--bg) 16%)}
  .traj-evals-label{font-family:var(--mono);font-size:17px;letter-spacing:.14em;color:var(--muted);margin-bottom:24px}
  .traj-eval{position:relative;padding-top:11px;margin-bottom:24px}
  .traj-eval::before{content:"";position:absolute;left:0;top:0;width:42px;border-top:2px solid rgba(224,145,72,.62)}
  .traj-eval strong{display:block;font-size:27px;font-weight:500;color:var(--ink)}
  .traj-legend{display:flex;gap:34px;font-size:23px;color:var(--ink2);margin-top:22px}
  .traj-legend span{display:flex;align-items:center;gap:13px}
  .traj-legend i{width:26px;height:26px;border-radius:5px;display:block}
  .dots .case{fill:var(--teal)}
  .dots .ring{fill:none;stroke:var(--orange);stroke-width:4}
  .dots .ring.disagree{stroke-dasharray:9 9}
  .dots .ring.wobble{stroke:var(--ink);stroke-width:3;stroke-dasharray:3 9}
  .dots .g{transform:translate(var(--x),var(--y));transition:transform .9s cubic-bezier(.2,.7,.25,1),opacity .5s ease}
  .dots .ring{opacity:0;transition:opacity .5s ease}
  .slide[data-step="1"] .dots .ring,.slide[data-step="2"] .dots .ring{opacity:1}
  .slide[data-step="1"] .dots .wob .case,.slide[data-step="1"] .dots .dis .case,.slide[data-step="2"] .dots .wob .case,.slide[data-step="2"] .dots .dis .case{fill:url(#unstable)}
  @media (prefers-reduced-motion:reduce){.dots .wob .case,.dots .dis .case{fill:var(--teal)}}
  .slide[data-step="2"] .dots .q{transform:translate(var(--qx),var(--qy)) scale(.82)}
  .slide[data-step="2"] .dots .g:not(.q){opacity:.22}
  .dots .lane{fill:none;stroke:var(--muted);stroke-width:3;stroke-dasharray:10 10;opacity:.55}
  .dots .lane-label{font-family:var(--mono);font-size:26px;letter-spacing:.14em;fill:var(--muted)}
  .dots .lane-count{font-family:var(--mono);font-size:30px;fill:var(--muted);text-anchor:end}
  .dots .lane-count.done{fill:var(--orange-dark);opacity:0}
  .slide[data-step="2"] .dots .lane-count.done{opacity:1}
  .slide[data-step="2"] .dots .lane-count.start{opacity:0}
  .gridwrap{position:relative;height:600px;margin-top:26px;perspective:2400px}
  .deck3d{position:absolute;left:770px;top:310px;transform-style:preserve-3d;transition:transform 1.1s cubic-bezier(.16,1,.3,1)}
  .slide[data-step="1"] .deck3d{transform:translateX(58px) scale(.76) rotateX(12deg) rotateY(-27deg)}
  .layer{position:absolute;left:-230px;top:-230px;width:460px;height:460px;display:grid;grid-template-columns:repeat(3,1fr);gap:16px;transform:translateZ(calc(var(--i) * -88px));opacity:0;transition:opacity .9s ease}
  .layer.front{opacity:1}
  .slide[data-step="1"] .layer{opacity:.42}
  .slide[data-step="1"] .layer.front{opacity:1}
  .layer i{border-radius:10px;background:var(--teal)}
  .layer i.f{background:var(--orange-dark)}
  .layer i.n{background:var(--muted)}
  .gridwrap .axis{position:absolute;left:20px;top:80px;height:460px;width:480px;display:flex;flex-direction:column;justify-content:space-around;text-align:right;font-family:var(--mono);font-size:26px;color:var(--ink2);transition:opacity .6s ease}
  .gridwrap .reps{position:absolute;left:540px;top:28px;width:460px;text-align:center;font-family:var(--mono);font-size:24px;color:var(--muted);transition:opacity .6s ease}
  .slide[data-step="1"] .gridwrap .axis,.slide[data-step="1"] .gridwrap .reps{opacity:0}
  .gridwrap .depth{position:absolute;left:330px;top:530px;font-family:var(--mono);font-size:26px;color:var(--muted);opacity:0;transition:opacity .8s ease .5s}
  .slide[data-step="1"] .gridwrap .depth{opacity:1}
  .grid-cap{transition:opacity .4s ease}
  .grid-cap.step1,.slide[data-step="1"] .grid-cap.step0{position:absolute;opacity:0}
  .slide[data-step="1"] .grid-cap.step1{position:static;opacity:1}
  @media (prefers-reduced-motion:reduce){.deck3d,.layer,.gridwrap .axis,.gridwrap .reps,.gridwrap .depth{transition-duration:.01ms}}
  .legend{display:flex;gap:34px;font-size:24px;color:var(--ink2);margin-top:20px}
  .legend span{display:flex;align-items:center;gap:12px}
  .swatch{width:28px;height:28px;border-radius:50%;border:3px dashed var(--orange)}
  .swatch.w{border-color:var(--ink);border-style:dotted}
  .binary-slide{padding:0}
  .binary-slide .tint{position:absolute;top:0;bottom:0;width:50%}
  .binary-slide .tint.l{left:0;background:rgba(77,162,150,.10)}
  .binary-slide .tint.r{right:0;background:rgba(255,151,71,.12)}
  .binary-slide .seam{position:absolute;left:50%;top:0;bottom:0;width:4px;background:var(--ink);opacity:.85}
  .binary-slide .head{position:absolute;left:48px;top:42px}
  .binary-slide .head .eyebrow{margin-bottom:26px}
  .binary-slide .benefits{position:absolute;right:48px;top:46px;width:640px;display:flex;flex-direction:column;gap:30px;text-align:right}
  .binary-slide .benefits div{font-size:32px;line-height:1.3;color:var(--ink2);border-top:3px solid var(--muted);padding-top:16px}
  .binary-slide .cases{position:absolute;left:0;right:0;top:52%}
  .binary-slide .cases i{position:absolute;width:26px;height:26px;border-radius:50%;background:var(--ink2);opacity:.45}
  .binary-slide .forced{position:absolute;left:50%;top:52%;transform:translateX(-50%);text-align:center;opacity:0;transition:opacity .45s ease}
  .binary-slide[data-step="1"] .forced{opacity:1}
  .binary-slide .forced b{display:block;width:44px;height:44px;border-radius:50%;background:var(--orange);margin:-9px auto 0;box-shadow:0 0 0 10px rgba(249,248,246,.9)}
  .binary-slide .forced span{display:inline-block;margin-top:60px;padding:8px 20px;border-radius:999px;background:rgba(249,248,246,.94);font-family:var(--mono);font-size:22px;letter-spacing:.12em;text-transform:uppercase;color:var(--orange-dark);white-space:nowrap}
  .binary-slide .zone{position:absolute;bottom:64px;font-size:96px;font-weight:600;letter-spacing:-.03em}
  .binary-slide .zone.l{left:48px;color:var(--teal-deep)}
  .binary-slide .zone.r{left:calc(50% + 48px);color:var(--orange-dark)}
  .binary-slide .nuance{position:absolute;left:48px;bottom:34px;font-family:var(--mono);font-size:20px;letter-spacing:.12em;text-transform:uppercase;color:var(--muted)}
  @media (prefers-reduced-motion:reduce){.binary-slide .forced{transition:none}}
  .phases{display:grid;grid-template-columns:1fr 1fr;gap:78px;margin-top:30px}
  .phase h3{font-size:40px;font-weight:600;line-height:1.15}
  .phase .lead{font-family:var(--mono);font-size:20px;letter-spacing:.12em;color:var(--ink2);margin-bottom:8px}
  .phase p{font-size:26px;line-height:1.35;color:var(--ink2);margin-top:14px;max-width:22em}
  .chart{display:block;width:100%;margin-top:20px}
  .chart .axis{stroke:var(--ink);stroke-width:3}
  .chart .target{stroke:var(--muted);stroke-width:3;stroke-dasharray:10 10}
  .chart .curve{fill:none;stroke-width:9;stroke-linecap:round;stroke-linejoin:round}
  .chart .curve.build{stroke:var(--teal)}
  .chart .curve.guard{stroke:var(--orange)}
  .chart .dip{fill:var(--orange-dark)}
  .chart .lbl{font-family:var(--mono);font-size:20px;letter-spacing:.1em;fill:var(--ink2)}
  .chart .lbl.dim{fill:var(--muted)}
  .fac-note{margin-top:64px;font-family:var(--mono);font-size:24px;letter-spacing:.13em;text-transform:uppercase;color:var(--teal-deep)}
  .factory-era{padding:0;overflow:hidden}
  .factory-era svg{display:block;width:100%;height:100%}
  .factory-era .timeline{stroke:url(#factory-fade);stroke-width:4}
  .factory-era .terminal{fill:var(--orange)}
  .factory-era .year{font-family:var(--mono);font-size:26px;letter-spacing:.14em;fill:var(--teal-deep);text-anchor:middle}
  .factory-era .name{font-family:var(--sans);font-size:68px;font-weight:600;letter-spacing:-.025em;fill:var(--ink);text-anchor:middle}
  .twin{display:grid;grid-template-columns:1fr 1fr;gap:64px;margin-top:56px}
  .twin-card{border:4px solid var(--muted);border-radius:22px;background:var(--paper);padding:36px 38px}
  .twin-card.ok{border-color:var(--teal-deep)}
  .twin-card.bad{border-color:var(--orange-dark)}
  .twin-lab{font-family:var(--mono);font-size:20px;letter-spacing:.13em;text-transform:uppercase;color:var(--muted);margin-bottom:24px}
  .twin-gauge{height:34px;border-radius:999px;background:rgba(140,138,145,.22);overflow:hidden}
  .twin-gauge i{display:block;height:100%;width:86%;background:var(--ink2);border-radius:999px}
  .twin-caption{margin-top:18px;font-size:27px;color:var(--ink2)}
  .twin-rule{margin:34px 0 26px;border-top:3px dashed var(--muted)}
  .twin-verdict{display:flex;align-items:baseline;gap:18px}
  .twin-verdict b{font-size:44px;font-weight:600;letter-spacing:-.02em}
  .twin-verdict span{font-size:27px;color:var(--ink2)}
  .twin-card.ok .twin-verdict b{color:var(--teal-deep)}
  .twin-card.bad .twin-verdict b{color:var(--orange-dark)}
  .twin-foot{margin-top:46px;font-size:31px;color:var(--ink)}
  .twin-foot b{color:var(--teal-deep);font-weight:500}
  .dual-loop{display:grid;grid-template-columns:auto 60px 1fr 60px 1fr;grid-template-rows:1fr 1fr;align-items:center;column-gap:0;row-gap:38px;margin-top:44px}
  .dual-loop .finding{grid-row:1 / span 2;align-self:stretch;display:flex;flex-direction:column;justify-content:center;width:420px;border:4px solid var(--ink);border-radius:22px;background:var(--paper);padding:34px}
  .dual-loop .finding strong{display:block;font-size:40px;line-height:1.15;color:var(--ink)}
  .dual-loop .finding span{margin-top:16px;font-family:var(--mono);font-size:18px;letter-spacing:.1em;text-transform:uppercase;color:var(--muted)}
  .dual-loop .arrow{font-size:52px;text-align:center;color:var(--teal)}
  .dual-loop .arrow.row2{color:var(--orange)}
  .dual-loop .step.row2{--accent:var(--orange)}
  .dual-loop .step{border-top:4px solid var(--accent,var(--teal));padding-top:26px}
  .dual-loop .step .lbl{font-family:var(--mono);font-size:19px;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);margin-bottom:18px}
  .dual-loop .step strong{display:block;font-size:34px;line-height:1.22;font-weight:500;color:var(--ink)}
  .dual-loop-note{margin-top:56px;font-size:34px;color:var(--orange-dark)}
  .twoloop{display:block;width:100%;max-width:1600px;margin:30px auto 0}
  .twoloop .ring{fill:none;stroke-width:6}
  .twoloop .ring.t{stroke:var(--teal)}
  .twoloop .ring.o{stroke:var(--orange)}
  .twoloop .node.t{fill:var(--teal)}
  .twoloop .node.o{fill:var(--orange)}
  .twoloop .link{stroke-width:3;stroke-dasharray:9 9}
  .twoloop .link.t{stroke:var(--teal)}
  .twoloop .link.o{stroke:var(--orange)}
  .twoloop .ring-name{font-size:46px;font-weight:500;fill:var(--ink)}
  .twoloop .stage{font-family:var(--mono);font-size:26px;letter-spacing:.06em;fill:var(--ink2)}
  .twoloop .stage.dim{font-size:23px;fill:var(--muted)}
  .analogy{display:block;width:100%;max-width:1660px;margin:56px auto 0}
  .analogy .track{stroke:var(--muted);stroke-width:5}
  .analogy .stop{fill:var(--muted)}
  .analogy .now .track,.analogy .now .stop{stroke:var(--orange);fill:var(--orange)}
  .analogy .now .track{fill:none}
  .analogy .tag{font-family:var(--mono);font-size:24px;letter-spacing:.14em;fill:var(--muted)}
  .analogy .head{font-size:38px;font-weight:500;fill:var(--ink);text-anchor:middle}
  .analogy .sub{font-size:27px;fill:var(--ink2);text-anchor:middle}
  .analogy-note{margin-top:52px;color:var(--orange-dark)}
  .sphere-brand{display:flex;align-items:flex-end;gap:26px;margin-bottom:50px}
  .sphere-mark{width:78px;height:78px;border-radius:50%;background:#f2c230;position:relative;flex:none;margin-top:28px}
  .sphere-mark::before{content:"";position:absolute;left:50%;top:-32px;transform:translateX(-50%);width:38px;height:38px;border-radius:50%;background:#f2c230}
  .sphere-word{font-size:62px;font-weight:600;letter-spacing:-.035em}
  .cost .cap{font-size:31px;line-height:1.4;color:var(--ink2);margin-top:26px}
  .ambiguity{display:grid;grid-template-columns:1fr 1fr;gap:72px;margin-top:22px;align-items:start}
  .ambiguity section{padding:0;border:0}
  .ambiguity-label{font-family:var(--mono);font-size:21px;letter-spacing:.14em;color:var(--muted);text-transform:uppercase;margin-bottom:12px}
  .ambiguity section.after .ambiguity-label{color:var(--orange-dark)}
  .ambz{display:block;width:100%;height:auto}
  .ambz .band{opacity:.85}
  .ambz .edge{fill:none;stroke:var(--ink);stroke-width:3;stroke-dasharray:14 12;opacity:.5}
  .ambz .d{fill:var(--muted);opacity:.42}
  .ambz .d.hi{fill:var(--orange);opacity:1}
  .ambiguity-count{margin-top:4px;font-size:30px;line-height:1.25;color:var(--ink2)}
  .ambiguity-count strong{font-size:52px;font-weight:600;color:var(--orange-dark);letter-spacing:-.02em;margin-right:14px}
  .ambiguity section.after{opacity:0;transition:opacity .5s ease}
  .slide[data-step="1"] .ambiguity section.after{opacity:1}
  .ambiguity-takeaway{margin-top:30px;padding-top:25px;border-top:3px solid var(--muted);font-size:35px;line-height:1.3;color:var(--ink)}
  .ambiguity-takeaway b{color:var(--orange-dark);font-weight:500}
  .shot{width:100%;max-width:1520px;margin:26px auto 0;border:1px solid rgba(37,35,46,.12);border-radius:12px;overflow:hidden;box-shadow:0 10px 30px rgba(37,35,46,.10)}
  .shot img{display:block;width:100%;height:auto}
  .shot-caption{font-family:var(--mono);font-size:23px;letter-spacing:.06em;color:var(--muted);margin-top:16px;text-align:center}
  .counter{position:absolute;right:48px;bottom:24px;font-family:var(--mono);font-size:18px;color:var(--muted);letter-spacing:.08em}
</style>
</head>
<body>
<div id="stage">

<!-- 1 · Title -->
<section class="slide active">
  <div class="eyebrow">PyData Amsterdam 2026</div>
  <h1>Building the<br>evaluation flywheel</h1>
  <p class="sub">How human judgment becomes an evaluator you can run on every change.</p>
  <div class="byline"><span>Bauke Brenninkmeijer</span><span>Orq.ai</span><span>September 2026</span></div>
</section>

<!-- 2 · Evaluation gap -->
<section class="slide">
  <div class="eyebrow">The evaluation gap</div>
  <h2>Two correct answers.<br>Only one you want</h2>
  <p class="ask">&#8220;Where is the station?&#8221;</p>
  <div class="compare">
    <div class="answer">
      <div class="tag">ANSWER A</div>
      <p><strong>52.3791&#176; N, 4.9003&#176; E.</strong></p>
    </div>
    <div class="answer b">
      <div class="tag">ANSWER B</div>
      <p><mark><strong>Two streets to your left</strong>, about five minutes on foot.</mark></p>
    </div>
  </div>
</section>

<!-- 3 · Origin -->
<section class="slide">
  <div class="cols origin-layout">
    <div>
      <div class="eyebrow">Where this started</div>
      <h2>We came for optimization.<br>We got stuck on the signal.</h2>
      <p class="body">Self-improvement runs on the judge's critiques. <b>A wrong judge, wrong improvements.</b></p>
    </div>
    <svg class="origin" viewBox="0 0 720 640" role="img" aria-label="An optimization loop between the agent and the judge, with the signal arm broken">
      <defs>
        <marker id="mOrg" viewBox="0 0 12 12" refX="9" refY="6" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
          <path d="M1 1 L10 6 L1 11 z" fill="var(--teal)"/>
        </marker>
      </defs>
      <path class="arm" d="M470 168 A230 230 0 0 1 470 472" marker-end="url(#mOrg)"/>
      <path class="arm" d="M250 472 A230 230 0 0 1 250 168" marker-end="url(#mOrg)"/>
      <circle class="pod" cx="360" cy="110" r="72"/>
      <text class="name" x="360" y="122" text-anchor="middle">agent</text>
      <circle class="pod" cx="360" cy="530" r="72"/>
      <text class="name" x="360" y="542" text-anchor="middle">judge</text>
      <text class="side" x="612" y="326" text-anchor="middle">signal</text>
      <text class="side" x="128" y="330" text-anchor="middle">prompt update</text>
      <path class="break" d="M501 294 L553 346 M553 294 L501 346"/>
    </svg>
  </div>
</section>

<!-- 4 · Lineage -->
<section class="slide lineage-slide" data-steps="1">
  <div class="lineage-content">
    <h2>Evaluation moved from correctness to alignment</h2>
    <svg class="lineage" viewBox="0 0 1840 420" aria-label="Evaluation evolved from checking known answers to aligning LLM judge labels with experts">
      <line x1="60" y1="120" x2="1780" y2="120" class="stroke-d"/>
      <g>
        <circle cx="260" cy="120" r="18" fill="var(--teal)"/>
        <text x="260" y="200" text-anchor="middle" class="lbl">Known answer</text>
        <text x="260" y="245" text-anchor="middle" class="lbl small">COMPARE WITH GROUND TRUTH</text>
      </g>
      <g>
        <circle cx="920" cy="120" r="18" fill="var(--teal)"/>
        <text x="920" y="200" text-anchor="middle" class="lbl">Human judgement</text>
        <text x="920" y="245" text-anchor="middle" class="lbl small">COMPARE WITH AN EXPERT</text>
      </g>
      <g>
        <circle cx="1580" cy="120" r="22" fill="var(--orange)"/>
        <text x="1580" y="200" text-anchor="middle" class="lbl" fill="var(--ink)">LLM judge</text>
        <text x="1580" y="245" text-anchor="middle" class="lbl small">COMPARE WITH EXPERT LABELS</text>
      </g>
      <text x="60" y="382" class="lbl">The evaluator now needs <tspan fill="var(--orange-dark)">its own evaluation.</tspan></text>
    </svg>
  </div>
  <svg class="lineage-loops" viewBox="0 0 1600 320" role="img" aria-label="Two feedback loops connecting Agent, Judge and Expert">
    <defs>
      <marker id="mLineageLoop" viewBox="0 0 12 12" refX="9" refY="6" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
        <path d="M1 1 L10 6 L1 11 z" fill="var(--teal)"/>
      </marker>
    </defs>
    <path class="loop" d="M300 105 C420 18 600 18 720 105" marker-end="url(#mLineageLoop)"/>
    <path class="loop" d="M720 215 C600 302 420 302 300 215" marker-end="url(#mLineageLoop)"/>
    <path class="loop" d="M880 105 C1000 18 1180 18 1300 105" marker-end="url(#mLineageLoop)"/>
    <path class="loop" d="M1300 215 C1180 302 1000 302 880 215" marker-end="url(#mLineageLoop)"/>
    <circle class="entity" cx="220" cy="160" r="72"/>
    <circle class="entity" cx="800" cy="160" r="72"/>
    <circle class="entity" cx="1380" cy="160" r="72"/>
    <text class="name" x="220" y="172" text-anchor="middle">Agent</text>
    <text class="name" x="800" y="172" text-anchor="middle">Judge</text>
    <text class="name" x="1380" y="172" text-anchor="middle">Expert</text>
  </svg>
</section>

<!-- 5 · Ordering constraint -->
<section class="slide">
  <div class="eyebrow">The ordering constraint</div>
  <h2>You cannot use evals to improve an agent<br>before the eval is <span class="hl">aligned</span>.</h2>
</section>

<!-- 6 · Speaker -->
<section class="slide who-slide">
  <div class="who">
    <div class="who-ring"><img src="data:image/jpeg;base64,__CARTOON__" alt="Bauke Brenninkmeijer"></div>
    <div>
      <div class="who-name">Bauke Brenninkmeijer</div>
      <div class="who-role">Applied AI Researcher &#183; orq.ai</div>
      <div class="who-line">Red teaming &#183; Evaluation &#183; Agent simulation</div>
      <div class="who-line">Lead @ Agentic AI Foundation Amsterdam</div>
    </div>
  </div>
</section>

<!-- 7 · What is orq.ai? -->
<section class="slide orq-slide">
  <svg width="0" height="0" style="position:absolute" aria-hidden="true">__ORQMARK__</svg>
  <div class="eyebrow">Context</div>
  <h2>What is orq.ai?</h2>
  <div class="orq-band">
    <div class="mark"><svg><use href="#orqmark"/></svg></div>
    <p><b>Generative AI collaboration platform.</b> <span>One control plane to build, ship, and optimize AI products.</span></p>
  </div>
  <div class="orq-cards">
    <div class="orq-card build">
      <div class="top"><svg><use href="#orqmark"/></svg><span class="verb">Build</span></div>
      <div class="name">Agents</div>
      <div class="desc">Deploy agents with tools, memory, and knowledge bases.</div>
      <div class="peer">think Letta &#183; LangGraph &#183; CrewAI</div>
    </div>
    <div class="orq-card ship">
      <div class="top"><svg><use href="#orqmark"/></svg><span class="verb">Ship</span></div>
      <div class="name">Router</div>
      <div class="desc">One API for model routing, failovers, caching, and budget.</div>
      <div class="peer">think LiteLLM &#183; OpenRouter</div>
    </div>
    <div class="orq-card optimize">
      <div class="top"><svg><use href="#orqmark"/></svg><span class="verb">Optimize</span></div>
      <div class="name">Observability</div>
      <div class="desc">Traces, usage, evaluation, and annotation.</div>
      <div class="peer">think Langfuse &#183; LangSmith &#183; Arize</div>
    </div>
  </div>
</section>

<!-- 8 · Sphere -->
<section class="slide">
  <div class="eyebrow">The case</div>
  <div class="cols wide">
    <div>
      <div class="sphere-brand" aria-label="Sphere.com logo"><span class="sphere-mark"></span><span class="sphere-word">sphere.com</span></div>
      <p class="sub">A B2B wholesaler of physical home appliances. The board wants to understand the quality of growth.</p>
    </div>
    <div class="checks">
      <div class="check"><i>1</i><span>Discounts and realized revenue</span></div>
      <div class="check"><i>2</i><span>Refunds and cancellations</span></div>
      <div class="check"><i>3</i><span>Regional and category mix</span></div>
      <div class="check"><i>4</i><span>Answers shaped for a business decision</span></div>
    </div>
  </div>
</section>

<!-- 9 · Evaluation decisions -->
<section class="slide">
  <h2 class="criterion-q">Does the answer support the <span class="hl">decision</span>?</h2>
  <p class="sub">One subjective criterion, agreed by humans before any judge sees it.</p>
  <div class="setup-strip">
    <div><b>50</b><span>distinct business situations</span></div>
  </div>
</section>

<!-- 10 · Binary -->
<section class="slide binary-slide" data-steps="1">
  <div class="tint l"></div>
  <div class="tint r"></div>
  <div class="seam"></div>
  <div class="head">
    <div class="eyebrow">How do you create an eval?</div>
    <h2>Pass or fail</h2>
  </div>
  <div class="benefits">
    <div>Clear enough to act on</div>
    <div>No false precision from a 1 to 5 scale</div>
    <div>Agreement and false passes become measurable</div>
  </div>
  <div class="cases">__BINARY_CASES__</div>
  <div class="forced"><b></b><span>No space to stand</span></div>
  <div class="zone l">PASS</div>
  <div class="zone r">FAIL</div>
  <p class="nuance">The critique carries the nuance</p>
</section>

<!-- 11 · Grey zone -->
<section class="slide" data-steps="2">
  <div class="cols grey-layout">
    <svg class="gz" viewBox="0 0 1200 700" width="1220" height="710" aria-label="Several plausible boundaries through an overlapping grey zone">
      <defs>
        <linearGradient id="band" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stop-color="#ffffff" stop-opacity="0"/>
          <stop offset=".5" stop-color="#b9b8b6" stop-opacity=".65"/>
          <stop offset="1" stop-color="#ffffff" stop-opacity="0"/>
        </linearGradient>
      </defs>
      <path class="band" d="M 0 -90 L 1200 490 L 1200 810 L 0 220 Z" fill="url(#band)"/>
      __GREY_DOTS__
      <path class="p p1" d="__GREY_P1__"/>
      <path class="p p2" d="__GREY_P2__"/>
      <path class="p p3" d="__GREY_P3__"/>
    </svg>
    <div>
      <h2>The grey zone</h2>
      <p class="sub">Every evaluation has one.<br>All plausible. All different.</p>
    </div>
  </div>
</section>

<!-- 12 · Two loops -->
<section class="slide">
  <div class="eyebrow"><span class="qn">Question 02</span> · Trust the judge</div>
  <h2>Every failure has two suspects</h2>
  <div class="dual-loop" aria-label="One failing evaluation starts either the system loop or the evaluator loop">
    <div class="finding"><strong>The eval says FAIL</strong><span>one case, one criterion</span></div>
    <div class="arrow">&#8599;</div>
    <div class="step"><div class="lbl">System loop</div><strong>The answer really was wrong</strong></div>
    <div class="arrow">&#8594;</div>
    <div class="step"><div class="lbl">Fix</div><strong>Update the agent</strong></div>
    <div class="arrow row2">&#8600;</div>
    <div class="step row2"><div class="lbl">Evaluator loop</div><strong>The judge was wrong</strong></div>
    <div class="arrow row2">&#8594;</div>
    <div class="step row2"><div class="lbl">Fix</div><strong>Update the evaluator</strong></div>
  </div>
  <p class="dual-loop-note">Aligning the judge to humans is how you tell the two apart.</p>
</section>

<!-- 13 · Two ways to get labels -->
<section class="slide">
  <h2>The quality-control process<br>has not changed</h2>
  <svg class="analogy" viewBox="0 0 1720 430" role="img" aria-label="Both annotation methods compare a delegate's labels with an expert's labels">
    <g class="then">
      <text class="tag" x="0" y="98">THEN</text>
      <line class="track" x1="150" y1="90" x2="1680" y2="90"/>
      <circle class="stop" cx="330" cy="90" r="13"/>
      <text class="head" x="330" y="162">An expert annotates</text>
      <text class="sub" x="330" y="208">the reference cases</text>
      <circle class="stop" cx="900" cy="90" r="13"/>
      <text class="head" x="900" y="162">A non-expert annotates</text>
      <text class="sub" x="900" y="208">student or Mechanical Turk worker</text>
      <circle class="stop" cx="1450" cy="90" r="13"/>
      <text class="head" x="1450" y="162">Compare the annotations</text>
      <text class="sub" x="1450" y="208">expert / delegate agreement</text>
    </g>
    <g class="now">
      <text class="tag" x="0" y="308">NOW</text>
      <line class="track" x1="150" y1="300" x2="1680" y2="300"/>
      <circle class="stop" cx="330" cy="300" r="13"/>
      <text class="head" x="330" y="372">An expert annotates</text>
      <text class="sub" x="330" y="418">the reference cases</text>
      <circle class="stop" cx="900" cy="300" r="13"/>
      <text class="head" x="900" y="372">An LLM judge annotates</text>
      <text class="sub" x="900" y="418">the same cases</text>
      <circle class="stop" cx="1450" cy="300" r="13"/>
      <text class="head" x="1450" y="372">Compare the annotations</text>
      <text class="sub" x="1450" y="418">expert / judge agreement</text>
    </g>
  </svg>
  <p class="body analogy-note">In both cases, agreement with the expert decides whether to trust the delegate.</p>
</section>

<!-- 14 · Lazy -->
<section class="slide statement">
  <h2>But we are lazy</h2>
  <p class="sub">Let the LLM judges find the ambiguous cases, then spend human time only there.</p>
  <p class="price"><span class="setup">The most valuable thing is</span><span class="value">human attention.</span></p>
</section>

<!-- 15 · Judge grid -->
<section class="slide" data-steps="1">
  <h2>Two ways of disagreement</h2>
  <p class="sub">Three judges &#183; three repetitions</p>
  <div class="gridwrap">
    <div class="axis">__JUDGE_NAMES__</div>
    <div class="reps">3 repetitions &#8594;</div>
    <div class="deck3d">__JUDGE_LAYERS__</div>
    <div class="depth">&hellip; &times; 50 cases</div>
  </div>
  <p class="body grid-cap step0">Judges disagree with each other, and one judge disagrees with itself.</p>
  <p class="body grid-cap step1">Both signals exist for every case in the pool.</p>
</section>

<!-- 16 · Lazy queue -->
<section class="slide" data-steps="2">
  <div class="cols wide">
    <div>
      <svg class="dots" viewBox="0 0 1200 800" width="1220" height="813" aria-label="Fifty cases; judge disagreement and instability flag twelve, four of which go to the review batch alongside four randomly sampled cases">
        <defs>
          <linearGradient id="unstable" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0" stop-color="var(--teal)"/>
            <stop offset="1" stop-color="var(--orange-dark)"/>
            <animateTransform attributeName="gradientTransform" type="rotate" from="0 .5 .5" to="360 .5 .5" dur="7s" repeatCount="indefinite"/>
          </linearGradient>
        </defs>
        <rect class="lane" x="62" y="56" width="540" height="104" rx="14"/>
        <text class="lane-label" x="62" y="34">REVIEW FIRST</text>
        <text class="lane-count start" x="602" y="34">0</text>
        <text class="lane-count done" x="602" y="34">4 flagged</text>
        <rect class="lane" x="638" y="56" width="540" height="104" rx="14"/>
        <text class="lane-label" x="638" y="34">CONTROL</text>
        <text class="lane-count start" x="1178" y="34">0</text>
        <text class="lane-count done" x="1178" y="34">4 sampled</text>
        __CASE_DOTS__
      </svg>
      <div class="legend"><span><i class="swatch"></i>judges disagree</span><span><i class="swatch w"></i>one judge unstable</span></div>
    </div>
    <div>
      <h2>The judge<br>sorts the queue</h2>
      <p class="sub">Flagged cases go first. A random sample comes along to catch the cases the judges agreed on and got wrong.</p>
    </div>
  </div>
</section>

<!-- 17 · Disagreement gives us a question -->
<section class="slide">
  <h2>Disagreement gives us<br>a question</h2>
  <svg class="funnel" viewBox="0 0 1720 430" role="img" aria-label="The cases the panel split on converging on a single boundary question">
    <text class="flab" x="60" y="-10">CASES THE PANEL SPLIT ON</text>
    <path class="fline" d="M104 24 C 418 24, 820 215.0, 1038 215.0"/>
    <path class="fline" d="M222 96 C 536 96, 820 215.0, 1038 215.0"/>
    <path class="fline" d="M112 190 C 426 190, 820 215.0, 1038 215.0"/>
    <path class="fline" d="M258 262 C 572 262, 820 215.0, 1038 215.0"/>
    <path class="fline" d="M130 356 C 444 356, 820 215.0, 1038 215.0"/>
    <path class="fline" d="M326 178 C 640 178, 820 215.0, 1038 215.0"/>
    <path class="fline" d="M294 372 C 608 372, 820 215.0, 1038 215.0"/>
    <circle class="fdot" cx="78" cy="24" r="18"/>
    <circle class="fdot" cx="196" cy="96" r="18"/>
    <circle class="fdot" cx="86" cy="190" r="18"/>
    <circle class="fdot" cx="232" cy="262" r="18"/>
    <circle class="fdot" cx="104" cy="356" r="18"/>
    <circle class="fdot" cx="300" cy="178" r="18"/>
    <circle class="fdot" cx="268" cy="372" r="18"/>
    <circle class="target" cx="1150" cy="215.0" r="104"/>
    <text class="qmark" x="1150" y="215.0">?</text>
    <text class="tlab" x="1296" y="203.0">ONE BOUNDARY</text>
    <text class="tlab" x="1296" y="243.0">QUESTION</text>
  </svg>
  <p class="sub funnel-sub">The flagged cases produced no labels. They produced the question the criterion never answered.</p>
</section>

<!-- 18 · One human answer exposes another ambiguity -->
<section class="slide" data-steps="1">
  <h2>One answer exposed another ambiguity</h2>
  <p class="sub">The human answered one boundary question: claims visible in the evidence must be valid. Then the rule went into the evaluator.</p>
  <div class="ambiguity">
    <section>
      <div class="ambiguity-label">Before the rule</div>
      __AMB_BEFORE__
      <p class="ambiguity-count"><strong>4</strong>cases the panel split on</p>
    </section>
    <section class="after">
      <div class="ambiguity-label">After the rule</div>
      __AMB_AFTER__
      <p class="ambiguity-count"><strong>8</strong>cases the panel split on</p>
    </section>
  </div>
  <p class="ambiguity-takeaway">We aligned the principle, but not <b>what counts as unsupported</b>.</p>
</section>

<!-- 19 · Grey-zone loop -->
<section class="slide" data-steps="1">
  <h2>The grey-zone loop</h2>
  <p class="sub">Disagreement shows where the evaluator still needs a human decision.</p>
  <div class="grey-loop">
    <div class="sealed-note">HELD-OUT TEST SET STAYS SEALED</div>
    <div class="grey-loop-grid">
      <div class="grey-loop-stage"><span class="n">01</span><h3>Run the jury</h3></div>
      <div class="grey-loop-stage"><span class="n">02</span><h3>Surface instability</h3></div>
      <div class="grey-loop-stage"><span class="n">03</span><h3>Collaborator reads the reasons</h3></div>
      <div class="grey-loop-stage human"><span class="n">04</span><h3>Ask one boundary question</h3></div>
      <div class="grey-loop-stage"><span class="n">05</span><h3>Update the evaluator</h3></div>
    </div>
    <div class="grey-loop-return"><span>RERUN THE SAME FROZEN DEVELOPMENT CASES</span></div>
  </div>
  <div class="case-proof" aria-label="Three real development cases labelled after the boundary questions were resolved">
    <div class="proof-case"><strong>PASS</strong><h4>Clarify the metric first</h4><p>Valid evidence supports the scoped answer.</p></div>
    <div class="proof-case fail"><strong>FAIL</strong><h4>Best month net</h4><p>Visible evidence contradicts the stated definition.</p></div>
    <div class="proof-case"><strong>PASS</strong><h4>Earlier context still counts</h4><p>The response established the context earlier in the conversation.</p></div>
  </div>
</section>

<!-- 20 · Experiment grid -->
<section class="slide">
  <h2>Human labels reveal the judge limits</h2>
  <div class="shot"><img src="data:image/jpeg;base64,__EXPERIMENT_GRID__" alt="Orq experiment grid: three evaluator prompt versions scored by three evaluators over the frozen development cases"></div>
  <p class="shot-caption">Jury signals helped us find the unresolved questions. Once the human decisions became labels, we could see which judges reproduced them.</p>
</section>

<!-- 21 · Question 03 -->
<section class="slide">
  <div class="eyebrow"><span class="qn">Question 03</span></div>
  <h2>What changes<br>with agents?</h2>
</section>

<!-- 22 · Agent evaluation -->
<section class="slide" data-steps="1">
  <h2>The answer is only the endpoint</h2>
  <p class="sub">Agents require evaluating behavior, rather than final answers.</p>
  <div class="cols traj-layout">
    <div>
      <svg class="traj" viewBox="0 0 1824 __TRAJ_H__" preserveAspectRatio="xMinYMin meet" aria-label="Fifty agent trajectories, each split into user, assistant, tool call and tool result segments">
        __TRAJ_ROWS__
      </svg>
      <div class="traj-axis">NR. OF TOKENS &#8594;</div>
      <div class="traj-legend">
        <span><i style="background:#25232e"></i>user turn</span>
        <span><i style="background:#4da296"></i>assistant</span>
        <span><i style="background:#ff9747"></i>tool call</span>
        <span><i style="background:#8c8a91;opacity:.55"></i>tool result</span>
      </div>
      <p class="body traj-caption">Fifty Sphere.com cases. Each bar is one run, each block one message, sized by how much context it added.</p>
    </div>
    <div class="traj-evals">
      <div class="traj-evals-label">EVALS ON THE BEHAVIOR</div>
      <div class="traj-eval"><strong>Tool-call efficiency</strong></div>
      <div class="traj-eval"><strong>Error recovery</strong></div>
      <div class="traj-eval"><strong>Instruction adherence</strong></div>
    </div>
  </div>
</section>

<!-- 23 · Lifecycle -->
<section class="slide">
  <h2>Build the eval once.<br>Then it guards every commit.</h2>
  <div class="phases">
    <div class="phase">
      <div class="lead">DISCOVERY</div>
      <h3>Build with humans</h3>
      <svg class="chart" viewBox="0 0 800 380" role="img" aria-label="Pass rate climbs from a deliberately low start toward the target over rounds of human review">
        <line class="target" x1="70" y1="72" x2="782" y2="72"/>
        <text class="lbl dim" x="782" y="52" text-anchor="end">TARGET</text>
        <line class="axis" x1="70" y1="18" x2="70" y2="300"/>
        <line class="axis" x1="70" y1="300" x2="782" y2="300"/>
        <path class="curve build" d="M84 276 C200 268, 250 236, 330 208 S520 148, 768 100"/>
        <text class="lbl" x="70" y="344">ROUNDS OF HUMAN REVIEW &#8594;</text>
      </svg>
      <p>Hard cases and edge cases. A low pass rate is the eval working; one that never fails is too easy.</p>
    </div>
    <div class="phase">
      <div class="lead">REGRESSION</div>
      <h3>Guard every commit</h3>
      <svg class="chart" viewBox="0 0 800 380" role="img" aria-label="Pass rate sits at the target on every commit until one commit dips below it and is stopped">
        <line class="target" x1="70" y1="72" x2="782" y2="72"/>
        <text class="lbl dim" x="782" y="52" text-anchor="end">TARGET</text>
        <line class="axis" x1="70" y1="18" x2="70" y2="300"/>
        <line class="axis" x1="70" y1="300" x2="782" y2="300"/>
        <path class="curve guard" d="M84 86 L380 86 L440 244 L500 86 L768 86"/>
        <circle class="dip" cx="440" cy="244" r="12"/>
        <text class="lbl" x="440" y="288" text-anchor="middle">CAUGHT</text>
        <text class="lbl" x="70" y="344">EVERY COMMIT &#8594;</text>
      </svg>
      <p>Known behavior and core paths. Everything passes, or something broke and the commit stops.</p>
    </div>
  </div>
</section>

<!-- 24 · Operating modes -->
<section class="slide">
  <div class="eyebrow">Scaling evaluation</div>
  <h2>Offline, online, continuous</h2>
  <svg class="life-axis" viewBox="0 0 1800 510" role="img" aria-label="Offline runs before release, online after it, and continuous spans both">
    <line class="rel" x1="800" y1="40" x2="800" y2="300"/>
    <text class="mono" x="812" y="56">RELEASE</text>
    <rect x="40" y="86" width="720" height="76" rx="8" fill="var(--teal)"/>
    <text class="name" x="40" y="212">Offline</text>
    <text class="meta" x="40" y="252">The curated 50, when you ask.</text>
    <rect x="840" y="86" width="920" height="76" rx="8" fill="var(--orange)"/>
    <text class="name" x="840" y="212">Online</text>
    <text class="meta" x="840" y="252">Sampled production traces, as traffic arrives.</text>
    <line class="ax" x1="40" y1="304" x2="1760" y2="304"/>
    <g class="beat"><rect x="40" y="330" width="130" height="68" rx="8"/><rect x="184" y="330" width="130" height="68" rx="8"/><rect x="329" y="330" width="130" height="68" rx="8"/><rect x="474" y="330" width="130" height="68" rx="8"/><rect x="618" y="330" width="130" height="68" rx="8"/><rect x="762" y="330" width="130" height="68" rx="8"/><rect x="907" y="330" width="130" height="68" rx="8"/><rect x="1052" y="330" width="130" height="68" rx="8"/><rect x="1196" y="330" width="130" height="68" rx="8"/><rect x="1340" y="330" width="130" height="68" rx="8"/><rect x="1485" y="330" width="130" height="68" rx="8"/><rect x="1630" y="330" width="130" height="68" rx="8"/></g>
    <text class="name" x="40" y="456">Continuous</text>
    <text class="meta" x="40" y="496">Both, on every change and then on a schedule.</text>
  </svg>
  <p class="body" style="margin-top:36px">The same criterion runs in all three, and it holds only while production stays inside the slice humans validated.</p>
</section>

<!-- 25 · Software factory era -->
<section class="slide factory-era">
  <svg viewBox="0 0 1920 1080" role="img" aria-label="A timeline whose visible endpoint is 2026, marked Software Factory">
    <defs>
      <linearGradient id="factory-fade" gradientUnits="userSpaceOnUse" x1="-240" y1="650" x2="1540" y2="650">
        <stop offset="0%" stop-color="var(--muted)" stop-opacity="0"/>
        <stop offset="58%" stop-color="var(--muted)" stop-opacity=".18"/>
        <stop offset="100%" stop-color="var(--muted)" stop-opacity=".72"/>
      </linearGradient>
    </defs>
    <line class="timeline" x1="-240" y1="650" x2="1540" y2="650"/>
    <circle class="terminal" cx="1540" cy="650" r="27"/>
    <text class="year" x="1540" y="582">2026</text>
    <text class="name" x="1540" y="760">Software Factory</text>
  </svg>
</section>

<!-- 26 · Unreviewed -->
<section class="slide statement inverted" data-steps="1">
  <h2>Most software will ship<br>without a human reading it.</h2>
  <div class="ship-read">
    <div class="row"><span>SHIPPED</span><div class="track"><i style="width:100%"></i></div></div>
    <div class="row read"><span>READ</span><div class="track"><i></i></div></div>
  </div>
  <p class="fac-note">Evals in the software factory</p>
</section>

<!-- 27 · Software factory -->
<section class="slide">
  <div class="eyebrow">Evals in the software factory</div>
  <h2>Same throughput.<br>Different factory.</h2>
  <div class="twin">
    <div class="twin-card ok">
      <div class="twin-lab">Factory A</div>
      <div class="twin-gauge"><i></i></div>
      <p class="twin-caption">Most pull requests merge untouched.</p>
      <div class="twin-rule"></div>
      <div class="twin-verdict"><b>Holding</b><span>the criterion still passes</span></div>
    </div>
    <div class="twin-card bad">
      <div class="twin-lab">Factory B</div>
      <div class="twin-gauge"><i></i></div>
      <p class="twin-caption">Most pull requests merge untouched.</p>
      <div class="twin-rule"></div>
      <div class="twin-verdict"><b>Rotting</b><span>the same criterion started failing</span></div>
    </div>
  </div>
  <p class="twin-foot">The factory reports how much moved. <b>Only an eval tells you which of these you are running.</b></p>
</section>

<!-- 28 · Close -->
<section class="slide">
  <div class="cols wide">
    <div>
      <div class="eyebrow">What to keep</div>
      <h2>Trust the slice<br>tested against humans</h2>
      <p class="body">Stop when disagreement, drift or false passes show that the system has left it.</p>
      <div class="byline"><span>Bauke Brenninkmeijer</span><span>Orq.ai</span></div>
    </div>
    <svg class="gz" viewBox="0 0 1200 700" width="760" height="443" aria-label="One boundary through the grey zone">
      __GREY_DOTS__
      <path class="p" d="__GREY_P3__"/>
    </svg>
  </div>
</section>

</div>
<script>
(() => {
  const stage = document.getElementById('stage');
  const slides = [...document.querySelectorAll('.slide')];
  let current = 0;
  let step = 0;
  const stepsOf = index => Number(slides[index].dataset.steps || 0);
  const fit = () => {
    const scale = Math.min(innerWidth / 1920, innerHeight / 1080);
    stage.style.transform = `translate(-50%,-50%) scale(${scale})`;
  };
  const render = () => {
    slides.forEach((slide, index) => slide.classList.toggle('active', index === current));
    slides[current].dataset.step = step;
    slides[current].querySelectorAll('.counter').forEach(node => node.remove());
    const counter = document.createElement('div');
    counter.className = 'counter';
    counter.textContent = `${current + 1} / ${slides.length}`;
    slides[current].appendChild(counter);
    location.hash = `s${current + 1}`;
  };
  const next = () => {
    if (step < stepsOf(current)) { step += 1; }
    else if (current < slides.length - 1) { current += 1; step = 0; }
    render();
  };
  const previous = () => {
    if (step > 0) { step -= 1; }
    else if (current > 0) { current -= 1; step = stepsOf(current); }
    render();
  };
  addEventListener('resize', fit);
  addEventListener('keydown', event => {
    if (['ArrowRight', 'ArrowDown', ' ', 'PageDown'].includes(event.key)) { event.preventDefault(); next(); }
    if (['ArrowLeft', 'ArrowUp', 'PageUp'].includes(event.key)) { event.preventDefault(); previous(); }
    if (event.key === 'Home') { current = 0; step = 0; render(); }
    if (event.key === 'End') { current = slides.length - 1; step = stepsOf(current); render(); }
    if (event.key.toLowerCase() === 'f') { document.fullscreenElement ? document.exitFullscreen() : document.documentElement.requestFullscreen(); }
  });
  addEventListener('click', event => {
    if (!document.fullscreenElement) return;
    if (event.clientX > innerWidth / 2) next(); else previous();
  });
  const match = location.hash.match(/^#s(\d+)$/);
  if (match) current = Math.min(slides.length - 1, Math.max(0, Number(match[1]) - 1));
  fit();
  render();
})();
</script>
</body>
</html>
'''

html = (
    html.replace("__RG__", fonts["RG"])
    .replace("__MD__", fonts["MD"])
    .replace("__SB__", fonts["SB"])
    .replace("__MONO__", fonts["MONO"])
    .replace("__EXPERIMENT_GRID__", experiment_grid)
    .replace("__CARTOON__", cartoon)
    .replace("__ORQMARK__", ORQMARK)
    .replace("__AMB_BEFORE__", ambiguity_zone(55, 4, "ambBefore"))
    .replace("__AMB_AFTER__", ambiguity_zone(165, 8, "ambAfter"))
    .replace("__GREY_DOTS__", grey_dot_svg)
    .replace("__GREY_P1__", grey_paths[0])
    .replace("__GREY_P2__", grey_paths[1])
    .replace("__GREY_P3__", grey_paths[2])
    .replace("__CASE_DOTS__", case_dot_svg)
    .replace("__BINARY_CASES__", binary_cases)
    .replace("__TRAJ_ROWS__", traj_svg)
    .replace("__TRAJ_H__", str(traj_height))
    .replace("__JUDGE_NAMES__", judge_names)
    .replace("__JUDGE_LAYERS__", judge_layers)
)

output = pathlib.Path(__file__).with_name("pydata-2026.html")
output.write_text(html)
print(f"wrote {output}")
