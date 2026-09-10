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
flagged_size = len(queue)
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

html = r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Evaluating Agents at Scale</title>
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
  .define{max-width:1280px;margin-top:76px;border-left:8px solid var(--orange);padding:14px 0 14px 46px;opacity:0;transform:translateY(14px);transition:opacity .5s cubic-bezier(.16,1,.3,1),transform .5s cubic-bezier(.16,1,.3,1)}
  .slide[data-step="1"] .define{opacity:1;transform:none}
  @media (prefers-reduced-motion:reduce){.define{transition:none;transform:none}}
  .define .word{font-size:86px;font-weight:600;line-height:1.05;letter-spacing:-.02em;color:var(--ink)}
  .define .gram{font-family:var(--mono);font-size:22px;letter-spacing:.08em;color:var(--ink2);margin:12px 0 26px}
  .define .meaning{font-size:38px;line-height:1.32;color:var(--ink2)}
  h1{font-size:128px;line-height:1.01;letter-spacing:-.03em;font-weight:600;margin-bottom:36px}
  h2{font-size:82px;line-height:1.06;letter-spacing:-.025em;font-weight:600;margin-bottom:48px;max-width:1760px}
  h3{font-size:42px;line-height:1.15;font-weight:500;color:var(--ink);margin-bottom:20px}
  .sub{font-size:36px;line-height:1.42;color:var(--ink2);max-width:1450px}
  .body{font-size:34px;line-height:1.42;color:var(--ink2)}
  .body b{color:var(--ink);font-weight:500}
  .hl{color:var(--orange-dark)}
  .tl{color:var(--teal-deep)}
  .mono{font-family:var(--mono)}
  .byline{display:flex;gap:54px;margin-top:82px;font-family:var(--mono);font-size:23px;color:var(--muted)}
  .cols{display:grid;grid-template-columns:1fr 1fr;gap:76px;align-items:center}
  .cols.wide{grid-template-columns:1.25fr 1fr}
  .cols.grey-layout{grid-template-columns:1.55fr .9fr;gap:54px}
  .statement h2{font-size:104px;margin:0;max-width:1800px}
  ul.plain{list-style:none;display:flex;flex-direction:column;gap:26px;font-size:34px;line-height:1.35;color:var(--ink2)}
  ul.plain li{position:relative;padding-left:42px}
  ul.plain li::before{content:"";position:absolute;left:0;top:17px;width:14px;height:14px;border-radius:50%;background:var(--orange)}
  .stats{display:grid;grid-auto-flow:column;gap:44px;margin-top:26px}
  .stat{border-top:3px solid var(--teal-deep);padding-top:25px}
  .stat .n{font-size:126px;font-weight:600;line-height:1;letter-spacing:-.04em}
  .stat .l{font-size:27px;line-height:1.3;color:var(--ink2);margin-top:14px}
  .ph{border:3px dashed var(--muted);border-radius:14px;padding:36px;color:var(--muted);font-family:var(--mono);font-size:23px;letter-spacing:.06em;text-transform:uppercase;display:grid;place-items:center;text-align:center;line-height:1.45;background:rgba(255,255,255,.45)}
  .compare{display:grid;grid-template-columns:1fr 1fr;gap:56px;margin-top:44px;max-width:1500px}
  .answer{border-top:6px solid var(--teal);padding:34px 0 0;min-height:0}
  .answer.b{border-color:var(--orange)}
  .answer .tag{font-family:var(--mono);font-size:19px;letter-spacing:.1em;color:var(--ink2);margin-bottom:22px}
  .answer p{font-size:33px;line-height:1.38;color:var(--ink2)}
  .answer strong{color:var(--ink);font-weight:500}
  .answer .quiet{font-size:27px;color:var(--muted);margin-top:18px}
  .answer mark{background:rgba(77,162,150,.24);color:var(--ink);padding:.06em .12em;border-radius:4px;box-decoration-break:clone;-webkit-box-decoration-break:clone}
  .answer code{font-family:var(--mono);font-size:.88em;color:var(--teal-deep)}
  .source{position:absolute;left:48px;bottom:26px;font-family:var(--mono);font-size:18px;color:var(--muted);letter-spacing:.04em}
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
  .life-axis .tick{fill:var(--bg)}
  .life-axis .beat{fill:var(--ink2)}
  svg text{font-family:var(--sans)}
  .lbl{fill:var(--ink2);font-size:28px}
  .lbl.dark{fill:var(--ink)}
  .lbl.small{font-size:21px;fill:var(--muted);font-family:var(--mono);letter-spacing:.08em}
  .stroke-t{stroke:var(--teal);fill:none;stroke-width:5}
  .stroke-o{stroke:var(--orange);fill:none;stroke-width:6}
  .stroke-d{stroke:var(--muted);fill:none;stroke-width:3}
  .cols.origin-layout{grid-template-columns:1.5fr .85fr;gap:60px}
  .origin{display:block;width:100%;max-width:640px;margin:0 auto}
  .origin .arm{fill:none;stroke:var(--teal);stroke-width:5}
  .origin .pod{fill:var(--paper);stroke:var(--ink);stroke-width:4}
  .origin .name{font-size:34px;fill:var(--ink)}
  .origin .side{font-family:var(--mono);font-size:24px;fill:var(--ink2)}
  .origin .break{stroke:var(--orange-dark);stroke-width:7;fill:none;stroke-linecap:round}
  .lineage{display:block;width:100%;max-width:1720px;margin:56px auto 0}
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
  .grey-loop-stage h3{font-size:32px;line-height:1.16;margin:0 auto 13px;max-width:9em}
  .grey-loop-stage p{font-size:22px;line-height:1.32;color:var(--ink2);max-width:12em;margin:0 auto}
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
  .traj-legend{display:flex;gap:40px;font-size:25px;color:var(--ink2);margin-top:30px}
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
  .deck3d{position:absolute;left:660px;top:300px;transform-style:preserve-3d;transition:transform 1.1s cubic-bezier(.16,1,.3,1)}
  .slide[data-step="1"] .deck3d{transform:translateX(30px) scale(.64) rotateX(12deg) rotateY(-27deg)}
  .layer{position:absolute;left:-195px;top:-195px;width:390px;height:390px;display:grid;grid-template-columns:repeat(3,1fr);gap:14px;transform:translateZ(calc(var(--i) * -88px));opacity:0;transition:opacity .9s ease}
  .layer.front{opacity:1}
  .slide[data-step="1"] .layer{opacity:.42}
  .slide[data-step="1"] .layer.front{opacity:1}
  .layer i{border-radius:10px;background:var(--teal)}
  .layer i.f{background:var(--orange-dark)}
  .layer i.n{background:var(--muted)}
  .gridwrap .axis{position:absolute;left:0;top:105px;height:390px;width:420px;display:flex;flex-direction:column;justify-content:space-around;text-align:right;font-family:var(--mono);font-size:26px;color:var(--ink2);transition:opacity .6s ease}
  .gridwrap .reps{position:absolute;left:465px;top:56px;width:390px;text-align:center;font-family:var(--mono);font-size:24px;color:var(--muted);transition:opacity .6s ease}
  .slide[data-step="1"] .gridwrap .axis,.slide[data-step="1"] .gridwrap .reps{opacity:0}
  .gridwrap .depth{position:absolute;left:290px;top:500px;font-family:var(--mono);font-size:26px;color:var(--muted);opacity:0;transition:opacity .8s ease .5s}
  .slide[data-step="1"] .gridwrap .depth{opacity:1}
  .grid-cap{transition:opacity .4s ease}
  .grid-cap.step1,.slide[data-step="1"] .grid-cap.step0{position:absolute;opacity:0}
  .slide[data-step="1"] .grid-cap.step1{position:static;opacity:1}
  @media (prefers-reduced-motion:reduce){.deck3d,.layer,.gridwrap .axis,.gridwrap .reps,.gridwrap .depth{transition-duration:.01ms}}
  .queue-line{margin-top:34px;opacity:0;transition:opacity .4s ease}
  .slide[data-step="2"] .queue-line{opacity:1}
  .legend{display:flex;gap:34px;font-size:24px;color:var(--ink2);margin-top:20px}
  .legend span{display:flex;align-items:center;gap:12px}
  .swatch{width:28px;height:28px;border-radius:50%;border:3px dashed var(--orange)}
  .swatch.w{border-color:var(--ink);border-style:dotted}
  .verdicts{display:grid;grid-template-columns:285px 285px;align-items:center;gap:26px 34px;margin-top:70px}
  .verdict{width:285px;height:205px;border:5px solid var(--teal);border-radius:24px;display:grid;place-items:center;background:var(--paper);font-size:54px;font-weight:600;color:var(--teal-deep)}
  .verdict.fail{border-color:var(--orange);color:var(--orange-dark)}
  .verdict-note{grid-column:1/-1;font-family:var(--mono);font-size:20px;line-height:1.4;color:var(--muted);text-transform:uppercase;letter-spacing:.07em;text-align:center}
  .replay{display:grid;grid-template-columns:1.2fr 90px 1fr;align-items:center;gap:20px}
  .process-card{min-height:180px;border:4px solid var(--teal);border-radius:22px;background:var(--paper);padding:34px;display:flex;flex-direction:column;justify-content:center;text-align:center}
  .process-card.orange{border-color:var(--orange)}
  .process-card.dark{border-color:var(--ink)}
  .process-card h3{margin:0;font-size:38px}
  .process-card p{margin-top:14px;font-family:var(--mono);font-size:18px;line-height:1.35;color:var(--muted);letter-spacing:.05em;text-transform:uppercase}
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
  .learning-flow{display:grid;grid-template-columns:repeat(3,1fr);gap:46px;margin-top:24px}
  .learning-stage{border-top:4px solid var(--teal);padding-top:28px;position:relative}
  .learning-stage:nth-child(3){border-color:var(--orange)}
  .learning-stage:nth-child(2)::after{color:var(--orange)}
  .learning-stage:not(:last-child)::after{content:"→";position:absolute;right:-40px;top:6px;color:var(--teal);font-size:38px}
  .learning-label{font-family:var(--mono);font-size:19px;letter-spacing:.1em;color:var(--muted);text-transform:uppercase;margin-bottom:22px}
  .learning-stage p{font-size:26px;line-height:1.38;color:var(--ink2)}
  .learning-stage strong{display:block;font-size:31px;line-height:1.24;font-weight:500;color:var(--ink);margin-bottom:18px}
  .learning-rerun{margin-top:64px;font-size:29px;color:var(--orange-dark);text-align:right}
  .flow-arrow{font-size:64px;color:var(--orange);text-align:center}
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
  .factory{display:grid;grid-template-columns:repeat(9,auto);align-items:center;gap:14px;margin-top:38px}
  .factory .process-card{width:272px;min-height:205px;padding:26px 14px}
  .factory .process-card h3{font-size:34px}
  .factory .flow-arrow{font-size:48px;color:var(--teal)}
  .feedback{margin-top:34px;text-align:center;font-family:var(--mono);font-size:20px;letter-spacing:.08em;color:var(--muted)}
  .sphere-brand{display:flex;align-items:center;gap:26px;margin-bottom:50px}
  .sphere-mark{width:78px;height:78px;border-radius:50%;border:5px solid var(--teal-deep);position:relative;flex:none}
  .sphere-mark::before,.sphere-mark::after{content:"";position:absolute;border:4px solid var(--orange);border-radius:50%}
  .sphere-mark::before{inset:14px -17px;transform:rotate(-18deg)}
  .sphere-mark::after{inset:-9px 21px;transform:rotate(28deg)}
  .sphere-word{font-size:62px;font-weight:600;letter-spacing:-.035em}
  .spine{list-style:none;margin:56px 0 0;padding:0 0 0 58px;border-left:5px solid var(--teal)}
  .spine li{position:relative;padding:0 0 42px 0}
  .spine li:last-child{padding-bottom:0}
  .spine li::before{content:"";position:absolute;left:-72px;top:26px;width:24px;height:24px;border-radius:50%;background:var(--teal)}
  .spine li.last::before{background:var(--orange)}
  .spine .n{display:block;font-family:var(--mono);font-size:21px;letter-spacing:.16em;color:var(--muted);margin-bottom:8px}
  .spine li.last .n{color:var(--orange-dark)}
  .spine p{margin:0;font-size:38px;line-height:1.2;color:var(--ink);font-weight:500}
  .cols.spine-layout{grid-template-columns:1.35fr .85fr;gap:80px}
  .cost .big{font-size:76px;font-weight:600;line-height:1.05;letter-spacing:-.03em;color:var(--orange-dark)}
  .cost .cap{font-size:31px;line-height:1.4;color:var(--ink2);margin-top:26px}
  .ambiguity{display:grid;grid-template-columns:.88fr 1.12fr .92fr;gap:54px;align-items:start;margin-top:18px}
  .ambiguity section{border-top:5px solid var(--teal);padding-top:27px;min-height:410px}
  .ambiguity section:nth-child(2){border-color:var(--orange);padding-left:8px;padding-right:8px}
  .ambiguity section:nth-child(3){border-color:var(--ink)}
  .ambiguity-label{font-family:var(--mono);font-size:20px;letter-spacing:.12em;color:var(--muted);text-transform:uppercase;margin-bottom:27px}
  .ambiguity-question{font-size:39px;line-height:1.3;color:var(--ink2)}
  .ambiguity-answer{font-size:92px;line-height:1;font-weight:600;color:var(--orange-dark);margin-top:42px}
  .ambiguity-rule{font-size:37px;line-height:1.28;color:var(--teal-deep);font-weight:500}
  .ambiguity-gap{font-size:31px;line-height:1.35;color:var(--ink2);margin-top:34px}
  .ambiguity-gap b{color:var(--ink);font-weight:500}
  .ambiguity-metrics{display:grid;gap:22px}
  .ambiguity-metric{display:grid;grid-template-columns:145px 1fr;gap:22px;align-items:baseline}
  .ambiguity-metric strong{font-size:57px;line-height:1;color:var(--orange-dark);font-weight:600;letter-spacing:-.03em}
  .ambiguity-metric span{font-size:27px;line-height:1.22;color:var(--ink2)}
  .ambiguity-takeaway{margin-top:42px;padding-top:25px;border-top:3px solid var(--muted);font-size:35px;line-height:1.3;color:var(--ink)}
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
  <h1>Evaluating Agents<br>at Scale</h1>
  <p class="sub">From human judgment to an evaluator that can support continuous improvement.</p>
  <div class="byline"><span>Bauke Brenninkmeijer</span><span>Orq.ai</span><span>September 2026</span></div>
</section>

<!-- 2 · Evaluation gap -->
<section class="slide">
  <div class="eyebrow">The evaluation gap</div>
  <h2>Two correct answers.<br>One useful decision.</h2>
  <div class="compare">
    <div class="answer">
      <div class="tag">ANSWER A · ANALYTICALLY VALID</div>
      <p>The average Regional Chains order is <strong>$2,572.98</strong>.</p>
    </div>
    <div class="answer b">
      <div class="tag">ANSWER B · DECISION SUPPORT</div>
      <p>The average Regional Chains order is <strong>$2,572.98</strong>. <mark>The median is <strong>$1,658.88</strong>. The mean runs 55% above the middle order, so for a representative order value you want the median.</mark></p>
    </div>
  </div>
</section>

<!-- 3 · Speaker -->
<section class="slide">
  <div class="eyebrow">Who is saying this</div>
  <div>
      <h2 style="font-size:66px;margin-bottom:44px">Bauke Brenninkmeijer</h2>
      <ul class="plain">
        <li>Research Engineer @ Orq.ai</li>
        <li>6 years data science @ ABN AMRO &amp; ING</li>
        <li>Lead @ Agentic AI Foundation Amsterdam</li>
      </ul>
  </div>
</section>

<!-- 4 · Questions -->
<section class="slide">
  <div class="eyebrow">Where this goes</div>
  <h2>Three questions</h2>
  <ol class="spine" aria-label="Questions this talk answers">
    <li><span class="n">01</span><p>How do you get a first signal with no labels?</p></li>
    <li><span class="n">02</span><p>When can you trust a judge instead of a human?</p></li>
    <li class="last"><span class="n">03</span><p>What do you evaluate in an agent that is not the final answer?</p></li>
  </ol>
</section>

<!-- 5 · Origin -->
<section class="slide">
  <div class="cols origin-layout">
    <div>
      <div class="eyebrow">Where this started</div>
      <h2>We came for optimization.<br>We got stuck on the signal.</h2>
      <p class="body">Feed the judge's critiques back into the agent and let it improve itself. That works &#8212; <b>if you can trust the judge</b>. An unaligned judge optimizes the agent toward its own mistakes.</p>
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

<!-- 6 · Lineage -->
<section class="slide">
  <div class="eyebrow">We have been here before</div>
  <h2>Hard metrics gave way to judgement.<br>Judgement had to be measured.</h2>
  <svg class="lineage" viewBox="0 0 1840 420" aria-label="Timeline of evaluation metrics, from countable targets to LLM judges">
    <line x1="60" y1="120" x2="1780" y2="120" class="stroke-d"/>
    <g>
      <circle cx="200" cy="120" r="18" fill="var(--teal)"/>
      <text x="200" y="200" text-anchor="middle" class="lbl">countable target</text>
      <text x="200" y="245" text-anchor="middle" class="lbl small">accuracy &#183; P/R/F1</text>
    </g>
    <g>
      <circle cx="680" cy="120" r="18" fill="var(--teal)"/>
      <text x="680" y="200" text-anchor="middle" class="lbl">human relevance</text>
      <text x="680" y="245" text-anchor="middle" class="lbl small">assessors disagree</text>
    </g>
    <g>
      <circle cx="1160" cy="120" r="18" fill="var(--teal)"/>
      <text x="1160" y="200" text-anchor="middle" class="lbl">n-gram overlap</text>
      <text x="1160" y="245" text-anchor="middle" class="lbl small">stops correlating</text>
    </g>
    <g>
      <circle cx="1640" cy="120" r="22" fill="var(--orange)"/>
      <text x="1640" y="200" text-anchor="middle" class="lbl" fill="var(--ink)">LLM judge</text>
      <text x="1640" y="245" text-anchor="middle" class="lbl small">agreement is the metric</text>
    </g>
    <text x="60" y="382" class="lbl">The task got more open-ended, the metric got softer, and <tspan fill="var(--orange-dark)">agreement between judges</tspan> became what had to be measured.</text>
  </svg>
</section>

<!-- 7 · Ordering constraint -->
<section class="slide">
  <div class="eyebrow">The ordering constraint</div>
  <h2>You cannot use evals to improve an agent<br>before the eval is <span class="hl">aligned</span>.</h2>
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

<!-- 9 · Review pool -->
<section class="slide">
  <div class="eyebrow"><span class="qn">Question 01</span> · Start with humans</div>
  <h2>A fifty-case review pool</h2>
  <div class="stats">
    <div class="stat"><div class="n">50</div><div class="l">distinct business situations</div></div>
    <div class="stat"><div class="n">30</div><div class="l">development cases</div></div>
    <div class="stat"><div class="n">20</div><div class="l">held-out test cases</div></div>
    <div class="stat"><div class="n hl">0</div><div class="l">human labels so far</div></div>
  </div>
</section>

<!-- 10 · Binary -->
<section class="slide">
  <div class="cols wide">
    <div>
      <div class="eyebrow">How do you create an eval?</div>
      <h2>Pass or fail</h2>
      <div class="verdicts"><div class="verdict">PASS</div><div class="verdict fail">FAIL</div><div class="verdict-note">The critique carries the nuance</div></div>
    </div>
    <ul class="plain">
      <li>Clear enough to act on</li>
      <li>No false precision from a 1–5 scale</li>
      <li>Lower cognitive load and faster review</li>
      <li>Agreement and false passes become measurable</li>
      <li><b class="hl">No maybe bucket means a harder alignment problem</b></li>
    </ul>
  </div>
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

<!-- 12 · Criterion -->
<section class="slide statement">
  <div class="eyebrow">One criterion for this talk</div>
  <h2>Does the answer help the <span class="hl">decision</span>?</h2>
</section>

<!-- 13 · Two loops -->
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

<!-- 14 · Two lifecycles -->
<section class="slide">
  <h2>Two lifecycles, not one</h2>
  <p class="sub">The application loop only moves as fast as the evaluation loop it trusts.</p>
  <svg class="twoloop" viewBox="0 0 1720 640" role="img" aria-label="The application cycle and the evaluation cycle, each three stages, coupled by a release gate and by new failures becoming new cases">
    <defs>
      <marker id="mT" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0 1 L9 5 L0 9 z" fill="var(--teal)"/></marker>
      <marker id="mO" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0 1 L9 5 L0 9 z" fill="var(--orange)"/></marker>
    </defs>

    <path class="ring t" d="M480.8 136.2 A210 210 0 0 1 631.9 397.9" marker-end="url(#mT)"/>
    <path class="ring t" d="M581.1 485.9 A210 210 0 0 1 278.9 485.9" marker-end="url(#mT)"/>
    <path class="ring t" d="M228.1 397.9 A210 210 0 0 1 379.2 136.2" marker-end="url(#mT)"/>
    <circle class="node t" cx="430" cy="130" r="13"/>
    <circle class="node t" cx="612" cy="445" r="13"/>
    <circle class="node t" cx="248" cy="445" r="13"/>
    <text class="stage" x="430" y="185" text-anchor="middle">build</text>
    <text class="stage" x="564" y="425" text-anchor="middle">ship</text>
    <text class="stage" x="296" y="425" text-anchor="middle">observe</text>
    <text class="ring-name" x="430" y="356" text-anchor="middle">application</text>

    <path class="ring o" d="M1340.8 136.2 A210 210 0 0 1 1491.9 397.9" marker-end="url(#mO)"/>
    <path class="ring o" d="M1441.1 485.9 A210 210 0 0 1 1138.9 485.9" marker-end="url(#mO)"/>
    <path class="ring o" d="M1088.1 397.9 A210 210 0 0 1 1239.2 136.2" marker-end="url(#mO)"/>
    <circle class="node o" cx="1290" cy="130" r="13"/>
    <circle class="node o" cx="1472" cy="445" r="13"/>
    <circle class="node o" cx="1108" cy="445" r="13"/>
    <text class="stage" x="1290" y="185" text-anchor="middle">criteria</text>
    <text class="stage" x="1424" y="425" text-anchor="middle">label</text>
    <text class="stage" x="1156" y="425" text-anchor="middle">align</text>
    <text class="ring-name" x="1290" y="356" text-anchor="middle">evaluation</text>

    <line class="link o" x1="1072" y1="300" x2="668" y2="300" marker-end="url(#mO)"/>
    <text class="stage" x="870" y="272" text-anchor="middle">gates every release</text>
    <line class="link t" x1="668" y1="400" x2="1072" y2="400" marker-end="url(#mT)"/>
    <text class="stage" x="870" y="372" text-anchor="middle">failures become cases</text>

    <text class="stage dim" x="860" y="604" text-anchor="middle">same cases &#183; same prompt versions &#183; same human labels</text>
  </svg>
</section>

<!-- 15 · Two ways to get labels -->
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
      <text class="sub" x="1450" y="208">expert–delegate agreement</text>
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
      <text class="sub" x="1450" y="418">expert–judge agreement</text>
    </g>
  </svg>
  <p class="body analogy-note">In both cases, agreement with the expert decides whether to trust the delegate.</p>
</section>

<!-- 16 · Judge grid -->
<section class="slide" data-steps="1">
  <h2>Two ways a verdict fails to hold still</h2>
  <p class="sub">Three judges &#183; three repetitions &#183; one real case</p>
  <div class="gridwrap">
    <div class="axis">__JUDGE_NAMES__</div>
    <div class="reps">3 repetitions &#8594;</div>
    <div class="deck3d">__JUDGE_LAYERS__</div>
    <div class="depth">&hellip; &times; 50 cases</div>
  </div>
  <p class="body grid-cap step0">Judges disagree with each other, and one judge disagrees with itself.</p>
  <p class="body grid-cap step1">Both signals exist for every case in the pool.</p>
</section>

<!-- 17 · Lazy queue -->
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
      <h2>We are lazy</h2>
      <p class="sub">Use the unaligned judge to decide what humans inspect first.</p>
      <ul class="plain">
        <li>Each judge votes three times: disagreement between judges, instability within one</li>
        <li><b class="hl">Those cases go to the front of the human queue</b></li>
      </ul>
      <p class="body queue-line">__FLAGGED__ of 50 were flagged. Review four of them, plus four sampled at random.</p>
    </div>
  </div>
</section>

<!-- 18 · Alignment -->
<section class="slide">
  <div class="eyebrow">Treat the judge like a model</div>
  <h2>Develop on 30.<br>Measure on 20.</h2>
  <div class="stats">
    <div class="stat"><div class="n">30</div><div class="l">read critiques<br>revise the rubric</div></div>
    <div class="stat"><div class="n">20</div><div class="l">held out<br>until measurement</div></div>
    <div class="stat"><div class="n hl">FP</div><div class="l">false passes<br>receive special attention</div></div>
  </div>
  <p class="body" style="margin-top:58px">Consensus only shows that models agree. Human labels establish whether that agreement is useful.</p>
</section>

<!-- 19 · One human answer exposes another ambiguity -->
<section class="slide">
  <h2>One answer exposed another ambiguity</h2>
  <div class="ambiguity">
    <section>
      <div class="ambiguity-label">Human question</div>
      <p class="ambiguity-question">Should visible analytical claims always be valid and correct?</p>
      <div class="ambiguity-answer">Yes.</div>
    </section>
    <section>
      <div class="ambiguity-label">Evaluator rule</div>
      <p class="ambiguity-rule">Claims visible in the evidence must be valid.</p>
      <p class="ambiguity-gap">The judges then split on <b>unsupported</b>: factually wrong, or simply not proven by the visible evidence?</p>
    </section>
    <section>
      <div class="ambiguity-label">Development signals</div>
      <div class="ambiguity-metrics">
        <div class="ambiguity-metric"><strong>4 to 8</strong><span>panel disagreements</span></div>
        <div class="ambiguity-metric"><strong>6 to 8</strong><span>unstable judges</span></div>
        <div class="ambiguity-metric"><strong>0</strong><span>aggregate verdict flips</span></div>
      </div>
    </section>
  </div>
  <p class="ambiguity-takeaway">We aligned the principle, but not <b>what counts as unsupported</b>.</p>
</section>

<!-- 20 · Grey-zone loop -->
<section class="slide" data-steps="1">
  <h2>The grey-zone loop</h2>
  <p class="sub">Disagreement shows where the evaluator still needs a human decision.</p>
  <div class="grey-loop">
    <div class="sealed-note">HELD-OUT TEST SET STAYS SEALED</div>
    <div class="grey-loop-grid">
      <div class="grey-loop-stage"><span class="n">01</span><h3>Run the jury</h3><p>Same frozen development cases</p></div>
      <div class="grey-loop-stage"><span class="n">02</span><h3>Surface instability</h3><p>Disagreement and self-flips</p></div>
      <div class="grey-loop-stage"><span class="n">03</span><h3>Collaborator reads the reasons</h3><p>Find competing interpretations</p></div>
      <div class="grey-loop-stage human"><span class="n">04</span><h3>Ask one boundary question</h3><p>The human chooses the rule</p></div>
      <div class="grey-loop-stage"><span class="n">05</span><h3>Update the evaluator</h3><p>Encode the accepted rule</p></div>
    </div>
    <div class="grey-loop-return"><span>RERUN THE SAME FROZEN DEVELOPMENT CASES</span></div>
  </div>
  <div class="case-proof" aria-label="Three real development cases labelled after the boundary questions were resolved">
    <div class="proof-case"><strong>PASS</strong><h4>Clarify the metric first</h4><p>Valid evidence supports the scoped answer.</p></div>
    <div class="proof-case fail"><strong>FAIL</strong><h4>Best month net</h4><p>Visible evidence contradicts the stated definition.</p></div>
    <div class="proof-case"><strong>PASS</strong><h4>Earlier context still counts</h4><p>The response established the context earlier in the conversation.</p></div>
  </div>
</section>

<!-- 21 · Experiment grid -->
<section class="slide">
  <h2>Human labels reveal the judge limits</h2>
  <div class="shot"><img src="data:image/jpeg;base64,__EXPERIMENT_GRID__" alt="Orq experiment grid: three evaluator prompt versions scored by three evaluators over the frozen development cases"></div>
  <p class="shot-caption">Jury signals helped us find the unresolved questions. Once the human decisions became labels, we could see which judges reproduced them.</p>
</section>

<!-- 22 · Question 03 -->
<section class="slide">
  <div class="eyebrow"><span class="qn">Question 03</span></div>
  <h2>What changes<br>with agents?</h2>
</section>

<!-- 23 · Agent evaluation -->
<section class="slide" data-steps="1">
  <h2>The answer is only the endpoint</h2>
  <p class="sub">Fifty Sphere.com cases. Each bar is one run, each block one message, sized by how much context it added.</p>
  <svg class="traj" viewBox="0 0 1824 __TRAJ_H__" width="1824" height="__TRAJ_H__" aria-label="Fifty agent trajectories, each split into user, assistant, tool call and tool result segments">
    __TRAJ_ROWS__
  </svg>
  <div class="traj-legend">
    <span><i style="background:#25232e"></i>user turn</span>
    <span><i style="background:#4da296"></i>assistant</span>
    <span><i style="background:#ff9747"></i>tool call</span>
    <span><i style="background:#8c8a91;opacity:.55"></i>tool result</span>
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
  <p class="body" style="margin-top:36px">The criterion moves between modes only while production stays inside the slice validated by humans.</p>
</section>

<!-- 25 · Lifecycle -->
<section class="slide">
  <h2>Build the eval once.<br>Then it guards every commit.</h2>
  <div class="phases">
    <div class="phase">
      <div class="lead">FIRST</div>
      <h3>Build with humans</h3>
      <svg class="chart" viewBox="0 0 800 380" role="img" aria-label="Pass rate climbs from a deliberately low start toward the target over rounds of human review">
        <line class="target" x1="70" y1="72" x2="782" y2="72"/>
        <text class="lbl dim" x="782" y="52" text-anchor="end">TARGET</text>
        <line class="axis" x1="70" y1="18" x2="70" y2="300"/>
        <line class="axis" x1="70" y1="300" x2="782" y2="300"/>
        <path class="curve build" d="M84 276 C200 268, 250 236, 330 208 S520 148, 768 100"/>
        <text class="lbl" x="70" y="344">ROUNDS OF HUMAN REVIEW &#8594;</text>
      </svg>
      <p>Hard cases and edge cases. A low pass rate at the start is the point.</p>
    </div>
    <div class="phase">
      <div class="lead">THEN</div>
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
      <p>Known behavior and core paths. Everything passes, or the commit stops.</p>
    </div>
  </div>
</section>

<!-- 26 · Finding to knowledge -->
<section class="slide">
  <h2>What a failed eval teaches<br>the agent and the rubric</h2>
  <div class="learning-flow" aria-label="A failed evaluation becomes both a Sphere skill update and an evaluator update">
    <div class="learning-stage"><div class="learning-label">Evaluator finding</div><strong>The analysis reports declining revenue.</strong><p>It never explains what the CFO should decide.</p></div>
    <div class="learning-stage"><div class="learning-label">Agent loop &#183; Sphere skill update</div><strong>Connect the analysis to the decision.</strong><p>Explain the commercial drivers, separate evidence from assumptions, lead with the implication.</p></div>
    <div class="learning-stage"><div class="learning-label">Evaluator loop &#183; evaluator update</div><strong>Say what unsupported means.</strong><p>A claim fails when the visible evidence contradicts it, not merely when proof is absent.</p></div>
  </div>
  <div class="learning-rerun">Then rerun <span class="mono">decision_support_quality</span></div>
</section>

<!-- 27 · Software factory -->
<section class="slide">
  <div class="eyebrow">Evals in the software factory</div>
  <h2>Automate the preparation.<br>Keep the decision human.</h2>
  <p class="sub">With software we write tests. With a software factory we build evals.</p>
  <div class="factory" aria-label="Agents prepare an analyzed and validated pull request for human review">
    <div class="process-card"><h3>evaluation</h3><p>finding</p></div><div class="flow-arrow">→</div>
    <div class="process-card"><h3>analysis agent</h3><p>structural cause</p></div><div class="flow-arrow">→</div>
    <div class="process-card orange"><h3>improvement agent</h3><p>opens PR</p></div><div class="flow-arrow">→</div>
    <div class="process-card"><h3>validation agent</h3><p>regression evidence</p></div><div class="flow-arrow">→</div>
    <div class="process-card dark"><h3>human</h3><p>review + merge</p></div>
  </div>
  <div class="feedback">↶ HUMAN FEEDBACK IMPROVES THE NEXT ANALYSIS</div>
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
    .replace("__GREY_DOTS__", grey_dot_svg)
    .replace("__GREY_P1__", grey_paths[0])
    .replace("__GREY_P2__", grey_paths[1])
    .replace("__GREY_P3__", grey_paths[2])
    .replace("__CASE_DOTS__", case_dot_svg)
    .replace("__TRAJ_ROWS__", traj_svg)
    .replace("__TRAJ_H__", str(traj_height))
    .replace("__FLAGGED__", str(flagged_size))
    .replace("__JUDGE_NAMES__", judge_names)
    .replace("__JUDGE_LAYERS__", judge_layers)
)

output = pathlib.Path(__file__).with_name("pydata-2026.html")
output.write_text(html)
print(f"wrote {output}")
