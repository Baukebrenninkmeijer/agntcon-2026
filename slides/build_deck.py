import base64, random, pathlib

F = pathlib.Path('/Users/baukebrenninkmeijer/.claude/skills/orq-chart-style/fonts')
def b64(name): return base64.b64encode((F/name).read_bytes()).decode()
fonts = {
  'RG': b64('ESKlarheitKurrent-Rg.woff2'),
  'MD': b64('ESKlarheitKurrent-Md.woff2'),
  'SB': b64('ESKlarheitKurrent-Smbd.woff2'),
  'MONO': b64('ESKlarheitKurrentMono-Md.ttf'),
}

# ---- grey zone dots: two clusters along a diagonal, overlapping in the middle
rng = random.Random(7)
dots = []
for _ in range(60):
    x = rng.uniform(80, 1120); y = rng.uniform(80, 620)
    score = (x/1200) - (y/700) + rng.gauss(0, 0.13)
    dots.append((x, y, 'a' if score > 0 else 'b'))
gz_dots = '\n'.join(f'<circle class="d {c}" cx="{x:.0f}" cy="{y:.0f}" r="9"/>' for x,y,c in dots)

# ---- slide 15 dots: 50 in a 10x5 grid; 3 fails; 10 seeded rings (placeholder mapping)
fails = {3, 17, 41}
seeded = {3, 8, 12, 17, 21, 26, 30, 35, 41, 47}
s15 = []
for i in range(50):
    cx = 110 + (i % 10) * 116; cy = 90 + (i // 10) * 116
    cls = 'fail' if i in fails else 'pass'
    if i in seeded: s15.append(f'<circle class="ring" cx="{cx}" cy="{cy}" r="44"/>')
    s15.append(f'<circle class="{cls}" cx="{cx}" cy="{cy}" r="28"/>')
s15_dots = '\n'.join(s15)

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

  /* Design tokens — Orq palette on sand */
  :root{
    --bg:#f9f8f6; --bg-2:#ffffff;
    --ink:#25232e; --ink-2:#55535c; --ink-3:#8c8a91;
    --orange:#ff8f34; --orange-dark:#df5325;
    --teal:#299D8F; --teal-deep:#025558; --cyan:#28FFE2;
    --sans:"Kurrent",-apple-system,"Inter",system-ui,sans-serif;
    --mono:"Kurrent Mono",ui-monospace,"SF Mono",Menlo,monospace;
  }
  *{margin:0;padding:0;box-sizing:border-box}
  html,body{height:100%;background:var(--bg);color:var(--ink);font-family:var(--sans);-webkit-font-smoothing:antialiased;overflow:hidden}

  /* Locked 16:9 stage, scaled to viewport */
  #stage{position:fixed;left:50%;top:50%;width:1920px;height:1080px;transform-origin:center;transform:translate(-50%,-50%) scale(1)}
  .slide{position:absolute;inset:0;padding:36px 40px;display:flex;flex-direction:column;justify-content:center;opacity:0;pointer-events:none;transition:opacity .35s ease}
  .slide.active{opacity:1;pointer-events:auto}

  /* Type — template sizes ×2 */
  .eyebrow{font-family:var(--mono);font-size:24px;letter-spacing:.14em;text-transform:uppercase;color:var(--teal-deep);margin-bottom:40px}
  h1{font-weight:600;font-size:128px;line-height:1.02;letter-spacing:-.025em;margin-bottom:36px}
  h2{font-weight:600;font-size:84px;line-height:1.06;letter-spacing:-.02em;margin-bottom:56px;max-width:1700px}
  .sub{font-size:36px;line-height:1.45;color:var(--ink-2);max-width:1300px}
  .body{font-size:36px;line-height:1.45;color:var(--ink-2)}
  .body b{color:var(--ink);font-weight:500}
  .hl{color:var(--orange-dark)}
  .tl{color:var(--teal-deep)}
  .mono{font-family:var(--mono)}
  .byline{margin-top:90px;font-family:var(--mono);font-size:24px;color:var(--ink-3);display:flex;gap:56px}

  /* Statement slide */
  .statement h2{font-size:104px;max-width:1800px;margin-bottom:0}
  .statement .eyebrow{margin-bottom:56px}

  /* Two column */
  .cols{display:grid;grid-template-columns:1fr 1fr;gap:80px;align-items:center}
  .cols.wide{grid-template-columns:1.3fr 1fr}

  /* Lists */
  ul.plain{list-style:none;display:flex;flex-direction:column;gap:28px;font-size:36px;line-height:1.35;color:var(--ink-2)}
  ul.plain li{display:grid;grid-template-columns:26px 1fr;column-gap:26px}
  ul.plain li::before{content:"";width:14px;height:14px;border-radius:50%;background:var(--orange);margin-top:20px}

  /* Stat strip */
  .stats{display:grid;grid-auto-flow:column;gap:40px;margin-top:20px}
  .stat{border-top:2px solid var(--teal-deep);padding-top:28px}
  .stat .n{font-size:var(--n,132px);font-weight:600;letter-spacing:-.03em;line-height:1;color:var(--ink)}
  .stat .n.hl{color:var(--orange-dark)}
  .stat .l{margin-top:18px;font-size:28px;color:var(--ink-2);line-height:1.35}

  /* Quote */
  blockquote{border-left:6px solid var(--orange);padding:12px 0 12px 44px;font-size:40px;line-height:1.4;color:var(--ink);max-width:1600px}
  blockquote .src{display:block;margin-top:22px;font-family:var(--mono);font-size:22px;color:var(--ink-3);letter-spacing:.08em}

  /* Checklist */
  .checks{display:flex;flex-direction:column;gap:30px}
  .check{display:grid;grid-template-columns:64px 1fr;column-gap:32px;align-items:center;font-size:40px}
  .check i{width:64px;height:64px;border-radius:50%;border:3px solid var(--teal);display:grid;place-items:center;font-style:normal;color:var(--teal);font-size:34px}

  /* Placeholders */
  .ph{border:2px dashed var(--ink-3);border-radius:12px;padding:40px;color:var(--ink-3);font-family:var(--mono);font-size:24px;letter-spacing:.06em;text-transform:uppercase;display:grid;place-items:center;text-align:center;line-height:1.5}

  /* Build steps */
  [data-step]{opacity:0;transform:translateY(14px);transition:opacity .45s ease,transform .45s ease}
  [data-step].on{opacity:1;transform:none}

  /* SVG shared */
  svg text{font-family:var(--sans)}
  .lbl{fill:var(--ink-2);font-size:28px}
  .lbl.small{font-size:22px;fill:var(--ink-3);font-family:var(--mono);letter-spacing:.08em}
  .stroke-t{stroke:var(--teal);fill:none;stroke-width:5}
  .stroke-o{stroke:var(--orange);fill:none;stroke-width:6}
  .stroke-d{stroke:var(--ink-3);fill:none;stroke-width:3}

  /* Grey zone */
  .gz .d.a{fill:var(--ink)} .gz .d.b{fill:var(--teal)}
  .gz .band{opacity:.55;transition:opacity .8s ease,transform 1.2s cubic-bezier(.4,0,.2,1);transform-origin:center;transform-box:fill-box}
  .gz .p{stroke:var(--orange);fill:none;stroke-width:6;stroke-linecap:round;opacity:0;transition:opacity .6s ease,d 1.2s ease}
  .gz .crisp{stroke:var(--orange);fill:none;stroke-width:7;stroke-linecap:round;opacity:0;transition:opacity .9s ease .3s}
  .gz[data-gz="1"] .p1{opacity:1}
  .gz[data-gz="2"] .p1,.gz[data-gz="2"] .p2,.gz[data-gz="2"] .p3{opacity:1}
  .gz[data-gz="3"] .p{opacity:0}
  .gz[data-gz="3"] .band{opacity:0;transform:scaleY(.08)}
  .gz[data-gz="3"] .crisp{opacity:1}

  /* Dots (47/3/10) */
  .dots .pass{fill:var(--teal)} .dots .fail{fill:var(--orange)}
  .dots .ring{fill:none;stroke:var(--orange);stroke-width:4;stroke-dasharray:8 8}

  /* Rubric quadrants */
  .quad rect{fill:none;stroke:var(--teal);stroke-width:4;rx:18}
  .quad rect.on{stroke:var(--orange);stroke-width:6}
  .quad text{fill:var(--ink);font-size:34px;font-weight:500}
  .quad text.dim{fill:var(--ink-3);font-weight:400}
</style>
</head>
<body>
<div id="stage">

<!-- 1 · Title -->
<section class="slide active">
  <div class="eyebrow">PyData Amsterdam 2026</div>
  <h1>Evaluating Agents<br>at Scale</h1>
  <p class="sub">From 50 examples to a production flywheel — and why the eval is a system you have to validate before it can validate anything.</p>
  <div class="byline"><span>Bauke Brenninkmeijer</span><span>Orq.ai</span><span>September 2026</span></div>
</section>

<!-- 2 · Origin -->
<section class="slide">
  <div class="cols wide">
    <div>
      <div class="eyebrow">Where this started</div>
      <h2>We came for optimization.<br>We got stuck on the signal.</h2>
      <p class="body">Feed judge critiques back into the agent's prompt and let it improve itself. It works — <b>if you can trust the judge</b>. An unaligned judge optimizes the agent toward its own mistakes.</p>
    </div>
    <svg viewBox="0 0 700 700" width="700" height="700" aria-label="Optimization loop with broken signal">
      <circle cx="350" cy="350" r="250" class="stroke-t" stroke-dasharray="1200" />
      <circle cx="350" cy="100" r="46" fill="var(--bg)" class="stroke-t"/>
      <text x="350" y="112" text-anchor="middle" class="lbl" fill="var(--ink)">agent</text>
      <circle cx="350" cy="600" r="46" fill="var(--bg)" class="stroke-t"/>
      <text x="350" y="612" text-anchor="middle" class="lbl">judge</text>
      <path d="M 560 250 L 610 300 M 610 250 L 560 300" class="stroke-o"/>
      <text x="585" y="360" text-anchor="middle" class="lbl small">signal</text>
      <text x="120" y="360" text-anchor="middle" class="lbl small">prompt update</text>
    </svg>
  </div>
</section>

<!-- 3 · Statement -->
<section class="slide statement">
  <div class="eyebrow">The ordering constraint</div>
  <h2>You cannot use evals to improve an agent<br>before the eval is <span class="hl">aligned</span>.</h2>
</section>

<!-- 4 · Lineage -->
<section class="slide">
  <div class="eyebrow">We have been here before</div>
  <h2>Hard metrics gave way to judgement. Judgement had to be measured.</h2>
  <svg viewBox="0 0 1840 420" width="1840" height="420" aria-label="Timeline of evaluation metrics">
    <line x1="60" y1="120" x2="1780" y2="120" class="stroke-d"/>
    <g>
      <circle cx="200" cy="120" r="18" fill="var(--teal)"/>
      <text x="200" y="200" text-anchor="middle" class="lbl">countable target</text>
      <text x="200" y="245" text-anchor="middle" class="lbl small">accuracy · P/R/F1</text>
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
    <text x="60" y="380" class="lbl">The task got more open-ended → the metric got softer → <tspan fill="var(--orange)">agreement between judges</tspan> became what had to be measured.</text>
  </svg>
</section>

<!-- 5 · Agents break it + double loop -->
<section class="slide">
  <div class="cols">
    <div>
      <div class="eyebrow">Agents break it again</div>
      <h2>Two lifecycles,<br>not one.</h2>
      <ul class="plain">
        <li>Non-deterministic. Trajectories branch.</li>
        <li>State lives elsewhere.</li>
        <li><b>The eval loop must mature first.</b></li>
      </ul>
    </div>
    <svg viewBox="0 0 900 620" width="900" height="620" aria-label="Application loop and evaluation loop">
      <circle cx="200" cy="260" r="160" class="stroke-t"/>
      <circle cx="660" cy="260" r="160" class="stroke-o"/>
      <text x="200" y="272" text-anchor="middle" class="lbl" fill="var(--ink)">application</text>
      <text x="200" y="470" text-anchor="middle" class="lbl small">build · ship · observe</text>
      <text x="660" y="272" text-anchor="middle" class="lbl" fill="var(--ink)">evaluation</text>
      <text x="640" y="470" text-anchor="middle" class="lbl small">criteria · annotate · align</text>
      <path d="M 500 260 L 380 260" class="stroke-d"/>
      <rect x="392" y="222" width="76" height="76" rx="12" fill="var(--bg)" stroke="var(--ink-3)" stroke-width="3"/>
      <text x="430" y="270" text-anchor="middle" class="lbl small" fill="var(--ink)">gate</text>
      <text x="430" y="580" text-anchor="middle" class="lbl small">same object · prompt · dataset · versions · reviewer</text>
    </svg>
  </div>
</section>

<!-- 6 · Grey zone (build) -->
<section class="slide" id="greyzone">
  <div class="cols wide">
    <svg class="gz" data-gz="0" viewBox="0 0 1200 700" width="1150" height="670" aria-label="Grey zone: from a blurry band to a crisp boundary">
      <defs>
        <linearGradient id="bandGrad" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0" stop-color="#6f6e69" stop-opacity="0"/>
          <stop offset=".5" stop-color="#6f6e69" stop-opacity=".45"/>
          <stop offset="1" stop-color="#6f6e69" stop-opacity="0"/>
        </linearGradient>
        <filter id="blur"><feGaussianBlur stdDeviation="28"/></filter>
        <radialGradient id="fade" cx=".5" cy=".5" r=".55"><stop offset=".55" stop-color="#fff"/><stop offset="1" stop-color="#000"/></radialGradient>
        <mask id="fadeMask"><rect x="0" y="0" width="1200" height="700" fill="url(#fade)"/></mask>
      </defs>
      <!-- band along the diagonal -->
      <g mask="url(#fadeMask)"><g transform="rotate(-30 600 350)">
        <rect class="band" x="-900" y="200" width="3000" height="300" fill="url(#bandGrad)" filter="url(#blur)"/>
      </g></g>
      __GZ_DOTS__
      <path class="p p1" d="M 110 650 C 200 520, 300 700, 400 540 S 560 380, 660 420 S 820 300, 900 200 S 1040 120, 1080 60"/>
      <path class="p p2" d="M 60 580 C 180 640, 260 440, 380 470 S 540 560, 640 360 S 800 420, 900 300 S 1060 220, 1140 120"/>
      <path class="p p3" d="M 170 690 C 240 560, 340 600, 440 460 S 600 470, 700 340 S 860 380, 940 180 S 1000 60, 1020 20"/>
      <path class="crisp" d="M 100 620 C 420 500, 680 380, 1100 60"/>
    </svg>
    <div>
      <div class="eyebrow">Naming the problem</div>
      <h2>The grey zone</h2>
      <p class="body" data-step="0" style="opacity:1;transform:none">Every evaluation has one.</p>
      <p class="body" data-step="1">One defensible boundary…</p>
      <p class="body" data-step="2">…several. All plausible. All different.</p>
      <p class="body" data-step="3"><b class="hl">Alignment is how it becomes one line.</b></p>
    </div>
  </div>
</section>

<!-- 7 · Statement -->
<section class="slide statement">
  <div class="eyebrow">The open question</div>
  <h2>Who decides where<br>the boundary goes?</h2>
</section>

<!-- 8 · The agent -->
<section class="slide">
  <div class="eyebrow">Running example</div>
  <h2>A small analytics agent over a business dataset.</h2>
  <p class="body" style="margin-bottom:48px">Writes SQL, runs it against DuckDB, can save an insight. <span class="mono tl">"Month-over-month EMEA revenue growth in Q3?"</span></p>
  <div class="stats">
    <div class="stat"><div class="n hl">1</div><div class="l">Right query,<br>wrong aggregation.</div></div>
    <div class="stat"><div class="n hl">2</div><div class="l">A number,<br>no query behind it.</div></div>
    <div class="stat"><div class="n hl">3</div><div class="l">Right answer,<br>invalid path.</div></div>
    <div class="stat"><div class="n hl">4</div><div class="l">Loses context<br>across turns.</div></div>
  </div>
</section>

<!-- 9 · The corpus -->
<section class="slide">
  <div class="eyebrow">The corpus</div>
  <h2>Fifty conversations. Ten of them deliberately broken.</h2>
  <div class="stats">
    <div class="stat"><div class="n">50</div><div class="l">cases, generated across<br>diversity dimensions, hand-reviewed</div></div>
    <div class="stat"><div class="n">30<span class="tl">/</span>20</div><div class="l">dev / test split,<br>frozen before looking</div></div>
    <div class="stat"><div class="n">8<span class="tl">·</span>22<span class="tl">·</span>20</div><div class="l">one, two, three-turn<br>conversations</div></div>
    <div class="stat"><div class="n hl">10</div><div class="l">behavioural failures<br>kept, not regenerated</div></div>
  </div>
</section>

<!-- 10 · Cheap graders -->
<section class="slide">
  <div class="cols">
    <div>
      <div class="eyebrow">Before any judge</div>
      <h2>If code can grade it, never pay a model to.</h2>
      <p class="body">Stdlib only. AST-checked. No credentials, no network. Runs on every commit.</p>
    </div>
    <div class="checks">
      <div class="check"><i>✓</i><span>Did the SQL parse?</span></div>
      <div class="check"><i>✓</i><span>Did it execute?</span></div>
      <div class="check"><i>✓</i><span>Was the insight actually written?</span></div>
    </div>
  </div>
</section>

<!-- 11 · Rubrics -->
<section class="slide">
  <div class="cols wide">
    <div>
      <div class="eyebrow">Decomposition</div>
      <h2>"Is this correct?" is several questions in one coat.</h2>
      <p class="body" style="margin-bottom:36px">Cut the grey zone into smaller, sharper ones. Align <b>one</b>.</p>
      <blockquote>Do not infer correctness from tool execution. You intentionally cannot see tool calls here.<span class="src">answer_correctness · prompt · evidence-blind by design</span></blockquote>
    </div>
    <svg class="quad" viewBox="0 0 700 700" width="700" height="700" aria-label="Four rubrics">
      <rect class="on" x="20" y="20" width="320" height="320"/>
      <text x="180" y="170" text-anchor="middle">answer</text><text x="180" y="215" text-anchor="middle">correctness</text>
      <rect x="360" y="20" width="320" height="320"/>
      <text x="520" y="170" text-anchor="middle" class="dim">query</text><text x="520" y="215" text-anchor="middle" class="dim">semantics</text>
      <rect x="20" y="360" width="320" height="320"/>
      <text x="180" y="510" text-anchor="middle" class="dim">evidence</text><text x="180" y="555" text-anchor="middle" class="dim">faithfulness</text>
      <rect x="360" y="360" width="320" height="320"/>
      <text x="520" y="510" text-anchor="middle" class="dim">multi-turn</text><text x="520" y="555" text-anchor="middle" class="dim">consistency</text>
    </svg>
  </div>
</section>

<!-- 12 · Protocol -->
<section class="slide">
  <div class="cols">
    <div>
      <div class="eyebrow">The protocol</div>
      <h2>Treat the judge like an annotator you hired.</h2>
      <ul class="plain">
        <li>Binary pass/fail <b>plus a written critique</b>. The critique is the asset.</li>
        <li>Dev/test split — applied to the evaluation itself.</li>
        <li>Iterate on <b>disagreement patterns</b>, never single rows.</li>
      </ul>
    </div>
    <svg viewBox="0 0 800 300" width="800" height="300" aria-label="Dev/test split on the corpus">
      <rect x="20" y="90" width="456" height="120" rx="14" fill="var(--teal-deep)"/>
      <rect x="490" y="90" width="290" height="120" rx="14" fill="none" stroke="var(--teal)" stroke-width="4"/>
      <text x="248" y="162" text-anchor="middle" class="lbl" fill="var(--ink)">30 dev</text>
      <text x="635" y="162" text-anchor="middle" class="lbl">20 test</text>
      <text x="20" y="260" class="lbl small">frozen · before any result was seen</text>
    </svg>
  </div>
</section>

<!-- 13 · Thresholds -->
<section class="slide">
  <div class="eyebrow">When is the judge evidence?</div>
  <h2>Below these, it isn't.</h2>
  <div class="stats">
    <div class="stat"><div class="n">κ ≥ 0.70</div><div class="l">Cohen's kappa<br>agreement beyond chance</div></div>
    <div class="stat"><div class="n">BA ≥ 0.80</div><div class="l">balanced accuracy<br>both classes count</div></div>
    <div class="stat"><div class="n hl">FP ≤ 0.10</div><div class="l">false-pass rate<br><b style="color:var(--ink)">the asymmetric error — a false pass ships</b></div></div>
  </div>
</section>

<!-- 14 · Audience places the boundary (placeholder) -->
<section class="slide">
  <div class="cols wide">
    <div>
      <div class="eyebrow">Your turn</div>
      <h2>Pass or fail?</h2>
      <p class="body"><b>Oracle:</b> EMEA net revenue 10,369,167.91</p>
      <p class="body" style="margin-top:24px"><b>Response:</b> reports 9,801,114.03 as net revenue, and mentions 10,369,167.91 — labelled as gross.</p>
      <blockquote data-step="1" style="margin-top:40px">Reports 9,801,114.03 by subtracting refunds again from the stored net_revenue… incorrectly labels 10,369,167.91 as pre-refund/gross.<span class="src">judge · fail</span></blockquote>
    </div>
    <div class="ph">placeholder<br>3–4 real grey-zone rows<br>to be selected from the joined CSV<br>verdict reveals on keypress</div>
  </div>
</section>

<!-- 15 · 47 / 3 / 10 -->
<section class="slide">
  <div class="cols wide">
    <svg class="dots" viewBox="0 0 1240 620" width="1100" height="550" aria-label="Fifty rows: 47 pass, 3 fail, 10 seeded failures">
      __S15_DOTS__
    </svg>
    <div>
      <div class="eyebrow">One pinned run · answer_correctness@1.0.0</div>
      <div class="stats" style="grid-auto-flow:row;gap:20px;--n:96px">
        <div class="stat"><div class="n">47</div><div class="l">pass</div></div>
        <div class="stat"><div class="n hl">3</div><div class="l">fail</div></div>
        <div class="stat"><div class="n" style="color:var(--ink-2)">10</div><div class="l">seeded failures in the corpus</div></div>
      </div>
      <p class="body" data-step="1" style="margin-top:40px">Zero human labels so far. <b>Which number is lying?</b></p>
      <p class="mono" style="margin-top:28px;font-size:20px;color:var(--ink-3);letter-spacing:.06em">PLACEHOLDER · ring positions are illustrative until seeded rows are mapped</p>
    </div>
  </div>
</section>

<!-- 16 · Trajectory and state -->
<section class="slide">
  <div class="cols">
    <div>
      <div class="eyebrow">Agent-only dimensions</div>
      <h2>Trajectory and state.</h2>
      <ul class="plain">
        <li>Replay the <b>recorded</b> response. Never re-invoke the agent to judge it.</li>
        <li>State: assert the file exists. Don't ask a model whether it does.</li>
        <li>pass@k for capability. pass^k for reliability.</li>
      </ul>
    </div>
    <svg viewBox="0 0 800 400" width="800" height="400" aria-label="Replay without inference">
      <rect x="20" y="60" width="300" height="110" rx="14" fill="var(--bg-2)" stroke="var(--teal)" stroke-width="4"/>
      <text x="170" y="126" text-anchor="middle" class="lbl" fill="var(--ink)">recorded run</text>
      <path d="M 330 115 L 460 115" class="stroke-o"/>
      <path d="M 440 95 L 465 115 L 440 135" class="stroke-o"/>
      <rect x="480" y="60" width="300" height="110" rx="14" fill="var(--bg-2)" stroke="var(--orange)" stroke-width="4"/>
      <text x="630" y="126" text-anchor="middle" class="lbl" fill="var(--ink)">judge</text>
      <text x="400" y="290" text-anchor="middle" class="lbl small">inference = False · reproducible by construction</text>
    </svg>
  </div>
</section>

<!-- 17 · Close -->
<section class="slide">
  <div class="cols wide">
    <div>
      <div class="eyebrow">What to keep</div>
      <h2>The grey zone does not go away.<br><span class="hl">Locate it on purpose.</span></h2>
      <p class="body">Start small. Validate small components. Then increase scope.</p>
      <div class="byline"><span>Bauke Brenninkmeijer</span><span>Orq.ai</span></div>
    </div>
    <svg class="gz" data-gz="3" viewBox="0 0 1200 700" width="760" height="443" aria-label="Crisp boundary">
      __GZ_DOTS__
      <path class="crisp" d="M 100 620 C 420 500, 680 380, 1100 60"/>
    </svg>
  </div>
</section>

</div>

<script>
(() => {
  const stage = document.getElementById('stage');
  const slides = [...document.querySelectorAll('.slide')];
  let i = 0, step = 0;

  const fit = () => {
    const s = Math.min(innerWidth / 1920, innerHeight / 1080);
    stage.style.transform = `translate(-50%,-50%) scale(${s})`;
  };
  addEventListener('resize', fit); fit();

  const maxStep = el => Math.max(0, ...[...el.querySelectorAll('[data-step]')].map(e => +e.dataset.step));
  const render = () => {
    slides.forEach((s, k) => s.classList.toggle('active', k === i));
    const s = slides[i];
    s.querySelectorAll('[data-step]').forEach(e => e.classList.toggle('on', +e.dataset.step <= step));
    const gz = s.querySelector('.gz[data-gz]');
    if (gz && s.id === 'greyzone') gz.dataset.gz = step;
    location.hash = step ? `s${i + 1}.${step}` : `s${i + 1}`;
  };
  const next = () => { if (step < maxStep(slides[i])) step++; else if (i < slides.length - 1) { i++; step = 0; } render(); };
  const prev = () => { if (step > 0) step--; else if (i > 0) { i--; step = maxStep(slides[i]); } render(); };

  addEventListener('keydown', e => {
    if (['ArrowRight', ' ', 'PageDown'].includes(e.key)) { e.preventDefault(); next(); }
    else if (['ArrowLeft', 'PageUp'].includes(e.key)) { e.preventDefault(); prev(); }
    else if (e.key === 'Home') { i = 0; step = 0; render(); }
    else if (e.key === 'End') { i = slides.length - 1; step = 0; render(); }
    else if (e.key.toLowerCase() === 'f') { document.fullscreenElement ? document.exitFullscreen() : document.documentElement.requestFullscreen(); }
  });
  addEventListener('click', e => { if (e.clientX > innerWidth / 2) next(); else prev(); });

  const m = location.hash.match(/^#s(\d+)(?:\.(\d+))?$/);
  if (m) { i = Math.min(slides.length - 1, Math.max(0, +m[1] - 1)); step = Math.min(maxStep(slides[i]), +(m[2] || 0)); }
  render();
})();
</script>
</body>
</html>
'''
for k, v in fonts.items(): html = html.replace(f'__{k}__', v)
html = html.replace('__GZ_DOTS__', gz_dots).replace('__S15_DOTS__', s15_dots)
out = pathlib.Path(__file__).with_name('pydata-2026.html'); out.write_text(html)
print(out, f'{out.stat().st_size/1024:.0f} KB')
