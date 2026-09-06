# ruff: noqa: E501

import base64
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


# Illustrative queue only. Real positions replace these after the jury run.
disagreement_cases = {3, 12, 17, 26, 35, 41}
wobble_cases = {8, 17, 21, 30, 41, 47}
case_marks: list[str] = []
for index in range(50):
    cx = 110 + (index % 10) * 116
    cy = 90 + (index // 10) * 116
    if index in disagreement_cases:
        case_marks.append(f'<circle class="ring disagree" cx="{cx}" cy="{cy}" r="43"/>')
    if index in wobble_cases:
        case_marks.append(f'<circle class="ring wobble" cx="{cx}" cy="{cy}" r="35"/>')
    case_marks.append(f'<circle class="case" cx="{cx}" cy="{cy}" r="27"/>')
case_dot_svg = "\n".join(case_marks)


html = r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Evaluating Agents at Scale</title>
<style>
  @font-face{font-family:"Kurrent";src:url(data:font/woff2;base64,__RG__) format("woff2");font-weight:400;font-display:swap}
  @font-face{font-family:"Kurrent";src:url(data:font/woff2;base64,__MD__) format("woff2");font-weight:500;font-display:swap}
  @font-face{font-family:"Kurrent";src:url(data:font/woff2;base64,__SB__) format("woff2");font-weight:600;font-display:swap}
  @font-face{font-family:"Kurrent Mono";src:url(data:font/ttf;base64,__MONO__) format("truetype");font-weight:500;font-display:swap}
  :root{
    --bg:#f9f8f6;--paper:#fff;--ink:#25232e;--ink2:#55535c;--muted:#8c8a91;
    --orange:#ff9747;--orange-dark:#df5325;--teal:#4da296;--teal-deep:#025558;
    --sans:"Kurrent",-apple-system,"Inter",system-ui,sans-serif;
    --mono:"Kurrent Mono",ui-monospace,"SF Mono",Menlo,monospace;
  }
  *{box-sizing:border-box;margin:0;padding:0}
  html,body{height:100%;overflow:hidden;background:var(--bg);color:var(--ink);font-family:var(--sans);-webkit-font-smoothing:antialiased}
  #stage{position:fixed;left:50%;top:50%;width:1920px;height:1080px;transform-origin:center;transform:translate(-50%,-50%) scale(1)}
  .slide{position:absolute;inset:0;padding:42px 48px;display:flex;flex-direction:column;justify-content:center;opacity:0;pointer-events:none;transition:opacity .3s ease}
  .slide.active{opacity:1;pointer-events:auto}
  .eyebrow{font-family:var(--mono);font-size:24px;letter-spacing:.14em;text-transform:uppercase;color:var(--teal-deep);margin-bottom:38px}
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
  .compare{display:grid;grid-template-columns:1fr 1fr;gap:36px}
  .answer{border-top:6px solid var(--teal);padding:30px 34px;background:var(--paper);min-height:330px}
  .answer.b{border-color:var(--orange)}
  .answer .tag{font-family:var(--mono);font-size:21px;letter-spacing:.1em;color:var(--muted);margin-bottom:22px}
  .answer p{font-size:32px;line-height:1.4;color:var(--ink2)}
  .answer strong{color:var(--ink);font-weight:500}
  .source{position:absolute;left:48px;bottom:26px;font-family:var(--mono);font-size:18px;color:var(--muted);letter-spacing:.04em}
  .checks{display:flex;flex-direction:column;gap:26px}
  .check{display:grid;grid-template-columns:58px 1fr;gap:26px;align-items:center;font-size:35px;color:var(--ink2)}
  .check i{width:58px;height:58px;border:3px solid var(--teal);border-radius:50%;display:grid;place-items:center;font-style:normal;color:var(--teal);font-size:31px}
  .pillrow{display:flex;gap:24px;align-items:stretch}
  .mode{flex:1;border-top:5px solid var(--teal);background:var(--paper);padding:34px;min-height:340px}
  .mode:nth-child(2){border-color:var(--orange)}
  .mode:nth-child(3){border-color:var(--ink)}
  .mode h3{font-size:48px}
  .mode p{font-size:30px;line-height:1.4;color:var(--ink2)}
  svg text{font-family:var(--sans)}
  .lbl{fill:var(--ink2);font-size:28px}
  .lbl.dark{fill:var(--ink)}
  .lbl.small{font-size:21px;fill:var(--muted);font-family:var(--mono);letter-spacing:.08em}
  .stroke-t{stroke:var(--teal);fill:none;stroke-width:5}
  .stroke-o{stroke:var(--orange);fill:none;stroke-width:6}
  .stroke-d{stroke:var(--muted);fill:none;stroke-width:3}
  .gz .d.a{fill:var(--ink)}.gz .d.b{fill:var(--teal)}
  .gz .band{opacity:0;transform:scaleY(.15);transform-origin:center;animation:none}
  .gz .d{opacity:0;animation:none}
  .gz .p{stroke:var(--orange);fill:none;stroke-width:6;stroke-linecap:round;stroke-dasharray:1800;stroke-dashoffset:1800;animation:none}
  .slide.active .gz .band{animation:bandIn .8s ease .15s forwards}
  .slide.active .gz .d{animation:dotIn .35s ease .55s forwards}
  .slide.active .gz .p1{animation:drawLine 1.15s ease 1s forwards}
  .slide.active .gz .p2{animation:drawLine 1.15s ease 1.3s forwards}
  .slide.active .gz .p3{animation:drawLine 1.15s ease 1.6s forwards}
  @keyframes bandIn{to{opacity:.68;transform:scaleY(1)}}
  @keyframes dotIn{to{opacity:1}}
  @keyframes drawLine{to{stroke-dashoffset:0}}
  .dots .case{fill:var(--teal)}
  .dots .ring{fill:none;stroke:var(--orange);stroke-width:4}
  .dots .ring.disagree{stroke-dasharray:9 9}
  .dots .ring.wobble{stroke:var(--ink);stroke-width:3;stroke-dasharray:3 9}
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
  .fork{font-size:62px;color:var(--teal);text-align:center}
  .stack{display:grid;gap:28px}
  .life-simple{display:grid;grid-template-columns:1fr 320px 1fr;align-items:center;gap:30px;margin-top:20px}
  .life-loop{height:350px;position:relative;display:grid;place-items:center}
  .life-loop svg{position:absolute;inset:0;width:100%;height:100%}
  .life-loop strong{position:relative;font-size:38px;font-weight:500;text-align:center;line-height:1.2}
  .life-bridge{text-align:center;font-size:29px;color:var(--ink2)}
  .life-bridge span{display:block;font-size:72px;line-height:.9;color:var(--teal)}
  .life-return{width:72%;margin:14px auto 0;padding-top:20px;border-top:3px dashed var(--muted);text-align:center;font-family:var(--mono);font-size:22px;letter-spacing:.06em;color:var(--muted)}
  .learning-flow{display:grid;grid-template-columns:1fr 1fr 1.12fr;gap:58px;margin-top:24px}
  .learning-stage{border-top:4px solid var(--teal);padding-top:28px;position:relative}
  .learning-stage:nth-child(2){border-color:var(--orange)}
  .learning-stage:not(:last-child)::after{content:"→";position:absolute;right:-47px;top:8px;color:var(--teal);font-size:44px}
  .learning-label{font-family:var(--mono);font-size:19px;letter-spacing:.1em;color:var(--muted);text-transform:uppercase;margin-bottom:22px}
  .learning-stage p{font-size:31px;line-height:1.38;color:var(--ink2)}
  .learning-stage strong{display:block;font-size:37px;line-height:1.24;font-weight:500;color:var(--ink);margin-bottom:18px}
  .learning-rerun{margin-top:52px;font-size:29px;color:var(--orange-dark);text-align:right}
  .flow-arrow{font-size:64px;color:var(--orange);text-align:center}
  .factory{display:grid;grid-template-columns:repeat(9,auto);align-items:center;gap:14px}
  .factory .process-card{width:272px;min-height:205px;padding:26px 18px}
  .factory .flow-arrow{font-size:48px;color:var(--teal)}
  .feedback{margin-top:34px;text-align:center;font-family:var(--mono);font-size:20px;letter-spacing:.08em;color:var(--muted)}
  .sphere-brand{display:flex;align-items:center;gap:26px;margin-bottom:50px}
  .sphere-mark{width:78px;height:78px;border-radius:50%;border:5px solid var(--teal-deep);position:relative;flex:none}
  .sphere-mark::before,.sphere-mark::after{content:"";position:absolute;border:4px solid var(--orange);border-radius:50%}
  .sphere-mark::before{inset:14px -17px;transform:rotate(-18deg)}
  .sphere-mark::after{inset:-9px 21px;transform:rotate(28deg)}
  .sphere-word{font-size:62px;font-weight:600;letter-spacing:-.035em}
  .steps4{display:grid;grid-template-columns:repeat(4,1fr);gap:34px;margin:72px 0 58px}
  .step4{border-top:4px solid var(--teal);padding-top:30px;font-size:31px;line-height:1.25;color:var(--ink2);position:relative}
  .step4:not(:last-child)::after{content:"→";position:absolute;right:-31px;top:16px;color:var(--teal);font-size:42px}
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
      <div class="ph" style="height:210px">Placeholder · Sphere response with result and SQL</div>
    </div>
    <div class="answer b">
      <div class="tag">ANSWER B · DECISION SUPPORT</div>
      <div class="ph" style="height:210px">Placeholder · Same result, framed for the CFO decision</div>
    </div>
  </div>
</section>

<!-- 3 · Sphere -->
<section class="slide">
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

<!-- 4 · Review pool -->
<section class="slide">
  <div class="eyebrow">Start with humans</div>
  <h2>A fifty-case review pool</h2>
  <div class="stats">
    <div class="stat"><div class="n">50</div><div class="l">distinct business situations</div></div>
    <div class="stat"><div class="n">30</div><div class="l">development cases</div></div>
    <div class="stat"><div class="n">20</div><div class="l">held-out test cases</div></div>
    <div class="stat"><div class="n hl">0</div><div class="l">human labels so far</div></div>
  </div>
  <p class="body" style="margin-top:60px">Stakeholder, decision, delivery setting and communication need are visible to the agent.</p>
</section>

<!-- 5 · Binary -->
<section class="slide">
  <div class="cols wide">
    <div>
      <div class="eyebrow">Binary verdict · written critique</div>
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

<!-- 6 · Grey zone -->
<section class="slide">
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
      <p class="sub">Every evaluation has one.<br>One defensible boundary becomes several.<br>All plausible. All different.</p>
    </div>
  </div>
</section>

<!-- 7 · Criterion -->
<section class="slide statement">
  <div class="eyebrow">One criterion for this talk</div>
  <h2>Does the response turn analysis into clear input for the stakeholder’s <span class="hl">decision</span>?</h2>
</section>

<!-- 8 · Historical method -->
<section class="slide">
  <h2>The historical method</h2>
  <p class="sub">Random sampling, manual review.</p>
  <div class="steps4" aria-label="Manual evaluation sequence"><div class="step4">random sample</div><div class="step4">human label +<br>written critique</div><div class="step4">split dev / test</div><div class="step4">identify gaps<br>with judge</div></div>
  <p class="body">Clean method. Expensive expert attention.</p>
</section>

<!-- 9 · Lazy queue -->
<section class="slide">
  <div class="cols wide">
    <div>
      <div class="eyebrow">A faster review queue</div>
      <h2>We are lazy</h2>
      <p class="sub">Use the unaligned judge to decide what humans inspect first.</p>
    </div>
    <div class="checks">
      <div class="check"><i>1</i><span>Repeat each judge to find self-wobble</span></div>
      <div class="check"><i>2</i><span>Compare models to find disagreement</span></div>
      <div class="check"><i>3</i><span>Review those cases first</span></div>
      <div class="check"><i>4</i><span>Sample unanimous cases as a control</span></div>
    </div>
  </div>
</section>

<!-- 10 · Disagreement dots -->
<section class="slide">
  <div class="cols wide">
    <div>
      <svg class="dots" viewBox="0 0 1200 700" width="1220" height="710" aria-label="Fifty cases with disagreement and self-wobble rings">
        __CASE_DOTS__
      </svg>
      <div class="legend"><span><i class="swatch"></i>models disagree</span><span><i class="swatch w"></i>one model wobbles</span></div>
    </div>
    <div>
      <div class="eyebrow">Three judges · one rubric</div>
      <h2>Disagreement sets the review order</h2>
      <ul class="plain">
        <li>Each dot is one Sphere.com case</li>
        <li>Each judge votes three times</li>
        <li><b class="hl">The rings move cases to the front of the human queue</b></li>
      </ul>
      <p class="mono" style="margin-top:38px;font-size:20px;color:var(--muted)">PLACEHOLDER · RING POSITIONS ARE ILLUSTRATIVE UNTIL THE JURY RUN LANDS</p>
    </div>
  </div>
</section>

<!-- 11 · Alignment -->
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

<!-- 12 · Walkthrough placeholder -->
<section class="slide">
  <div class="eyebrow">Short walkthrough</div>
  <h2>One case through the full loop</h2>
  <div class="ph" style="height:520px">Placeholder · stakeholder question · recorded response · nine votes · human critique · evaluator revision</div>
</section>

<!-- 13 · Agent evaluation -->
<section class="slide">
  <div class="eyebrow">What changes with agents</div>
  <h2>The answer is only the endpoint</h2>
  <div class="stats">
    <div class="stat"><div class="n" style="font-size:66px">trajectory</div><div class="l">the path from request to response</div></div>
    <div class="stat"><div class="n" style="font-size:66px">tools</div><div class="l">selection, arguments and use of results</div></div>
    <div class="stat"><div class="n" style="font-size:66px">context</div><div class="l">definitions and constraints across turns</div></div>
    <div class="stat"><div class="n" style="font-size:66px">state</div><div class="l">writes and other external effects</div></div>
  </div>
</section>

<!-- 14 · Replay -->
<section class="slide">
  <div class="cols wide">
    <div>
      <div class="eyebrow">Reproducible agent evaluation</div>
      <h2>Replay the trace</h2>
      <p class="sub">Keep the target behavior fixed while the evaluator changes.</p>
    </div>
    <div class="replay" aria-label="Recorded trace replayed to human and jury">
      <div class="process-card"><h3>recorded trace</h3><p>messages · tools · output</p></div>
      <div class="fork">⇉</div>
      <div class="stack"><div class="process-card orange"><h3>human</h3></div><div class="process-card orange"><h3>jury</h3></div></div>
    </div>
  </div>
</section>

<!-- 15 · Operating modes -->
<section class="slide">
  <div class="eyebrow">Scaling evaluation</div>
  <h2>Offline, online, continuous</h2>
  <div class="pillrow">
    <div class="mode"><h3>Offline</h3><p>Curated cases for development, alignment and comparisons.</p></div>
    <div class="mode"><h3>Online</h3><p>Sampled production traces reveal new failures and drift.</p></div>
    <div class="mode"><h3>Continuous</h3><p>Checks run on changes and repeat over time.</p></div>
  </div>
  <p class="body" style="margin-top:44px">The criterion can move between modes only while production stays inside the slice validated by humans.</p>
</section>

<!-- 16 · Lifecycle -->
<section class="slide">
  <h2>Build the eval once.<br>Then it guards every commit.</h2>
  <div class="life-simple" aria-label="Evaluation build lifecycle followed by regression lifecycle">
    <div class="life-loop"><svg viewBox="0 0 520 350" aria-hidden="true"><defs><marker id="cycleT" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0 L10 5 L0 10 z" fill="var(--teal)"/></marker></defs><path d="M112 250 A155 155 0 1 1 408 250" fill="none" stroke="var(--teal)" stroke-width="7" marker-end="url(#cycleT)"/><path d="M385 290 A155 155 0 0 1 135 290" fill="none" stroke="var(--teal)" stroke-width="7" marker-end="url(#cycleT)"/></svg><strong>Build with<br>humans</strong></div>
    <div class="life-bridge">Alignment holds<span>→</span></div>
    <div class="life-loop"><svg viewBox="0 0 520 350" aria-hidden="true"><defs><marker id="cycleO" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0 L10 5 L0 10 z" fill="var(--orange)"/></marker></defs><path d="M112 250 A155 155 0 1 1 408 250" fill="none" stroke="var(--orange)" stroke-width="7" marker-end="url(#cycleO)"/><path d="M385 290 A155 155 0 0 1 135 290" fill="none" stroke="var(--orange)" stroke-width="7" marker-end="url(#cycleO)"/></svg><strong>Guard every<br>commit</strong></div>
  </div>
  <div class="life-return">← Escapes become review cases</div>
</section>

<!-- 17 · Finding to knowledge -->
<section class="slide">
  <h2>What the agent learns<br>from a failed eval</h2>
  <div class="learning-flow" aria-label="A failed evaluation becomes a Sphere skill update">
    <div class="learning-stage"><div class="learning-label">Evaluator finding</div><strong>The analysis reports declining revenue.</strong><p>It never explains what the CFO should decide.</p></div>
    <div class="learning-stage"><div class="learning-label">Diagnosis</div><strong>Sphere’s decision criteria are missing.</strong><p>This is an agent knowledge gap, not a data or SQL error.</p></div>
    <div class="learning-stage"><div class="learning-label">Sphere skill update</div><strong>Connect the analysis to the decision.</strong><p>Explain the commercial drivers, separate evidence from assumptions, and lead with the business implication.</p></div>
  </div>
  <div class="learning-rerun">Then rerun <span class="mono">decision_support_quality</span></div>
</section>

<!-- 18 · Software factory -->
<section class="slide">
  <div class="eyebrow">Evals in the software factory</div>
  <h2>Automate the preparation.<br>Keep the decision human.</h2>
  <div class="factory" aria-label="Agents prepare an analyzed and validated pull request for human review">
    <div class="process-card"><h3>evaluation</h3><p>finding</p></div><div class="flow-arrow">→</div>
    <div class="process-card"><h3>analysis agent</h3><p>structural cause</p></div><div class="flow-arrow">→</div>
    <div class="process-card orange"><h3>improvement agent</h3><p>opens PR</p></div><div class="flow-arrow">→</div>
    <div class="process-card"><h3>validation agent</h3><p>regression evidence</p></div><div class="flow-arrow">→</div>
    <div class="process-card dark"><h3>human</h3><p>review + merge</p></div>
  </div>
  <div class="feedback">↶ HUMAN FEEDBACK IMPROVES THE NEXT ANALYSIS</div>
</section>

<!-- 19 · Close -->
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
  const fit = () => {
    const scale = Math.min(innerWidth / 1920, innerHeight / 1080);
    stage.style.transform = `translate(-50%,-50%) scale(${scale})`;
  };
  const render = () => {
    slides.forEach((slide, index) => slide.classList.toggle('active', index === current));
    slides[current].querySelectorAll('.counter').forEach(node => node.remove());
    const counter = document.createElement('div');
    counter.className = 'counter';
    counter.textContent = `${current + 1} / ${slides.length}`;
    slides[current].appendChild(counter);
    location.hash = `s${current + 1}`;
  };
  const next = () => { if (current < slides.length - 1) current += 1; render(); };
  const previous = () => { if (current > 0) current -= 1; render(); };
  addEventListener('resize', fit);
  addEventListener('keydown', event => {
    if (['ArrowRight', 'ArrowDown', ' ', 'PageDown'].includes(event.key)) { event.preventDefault(); next(); }
    if (['ArrowLeft', 'ArrowUp', 'PageUp'].includes(event.key)) { event.preventDefault(); previous(); }
    if (event.key === 'Home') { current = 0; render(); }
    if (event.key === 'End') { current = slides.length - 1; render(); }
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
    .replace("__GREY_DOTS__", grey_dot_svg)
    .replace("__GREY_P1__", grey_paths[0])
    .replace("__GREY_P2__", grey_paths[1])
    .replace("__GREY_P3__", grey_paths[2])
    .replace("__CASE_DOTS__", case_dot_svg)
)

output = pathlib.Path(__file__).with_name("pydata-2026.html")
output.write_text(html)
print(f"wrote {output}")
