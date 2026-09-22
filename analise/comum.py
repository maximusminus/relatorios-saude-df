"""Helpers e estilo compartilhados pelos relatórios (copiados de build_medicos.py)."""
import html, math
def br(x, d=0):
    s = f'{x:,.{d}f}'
    return s.replace(',', '§').replace('.', ',').replace('§', '.')
def rs(x): return 'R$ ' + br(x, 2)
E = html.escape

W, H, PL, PR, PT, PB = 720, 260, 56, 16, 16, 34
def eixo_y(vmax, vmin=0, n=4):
    import math
    passo = (vmax - vmin) / n
    mag = 10 ** math.floor(math.log10(passo)); passo = math.ceil(passo / mag) * mag
    top = vmin + passo * n
    while top < vmax: top += passo
    return [vmin + passo * i for i in range(int(round((top - vmin) / passo)) + 1)], top
def linhas(series, labels, fmt=lambda v: br(v), vmin=0, ticks_x=None, titulo=''):
    vals = [v for s in series for v in s['v'] if v is not None]
    ticks, top = eixo_y(max(vals), vmin)
    n = len(labels)
    X = lambda i: PL + (W - PL - PR) * i / max(n - 1, 1)
    Y = lambda v: PT + (H - PT - PB) * (1 - (v - vmin) / (top - vmin))
    o = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="{E(titulo)}">']
    for t in ticks:
        o.append(f'<line class="grid" x1="{PL}" x2="{W-PR}" y1="{Y(t):.1f}" y2="{Y(t):.1f}"/>'
                 f'<text class="tk" x="{PL-6}" y="{Y(t)+4:.1f}" text-anchor="end">{fmt(t)}</text>')
    for i in (ticks_x or []):
        o.append(f'<text class="tk" x="{X(i):.1f}" y="{H-12}" text-anchor="middle">{E(labels[i][:4])}</text>')
    for s in series:
        pts, seg = [], []
        for i, v in enumerate(s['v']):
            if v is None:
                if seg: pts.append(seg); seg = []
            else: seg.append(f'{X(i):.1f},{Y(v):.1f}')
        if seg: pts.append(seg)
        for sg in pts:
            o.append(f'<polyline class="{s["cls"]}" fill="none" points="{" ".join(sg)}"/>')
        li = max(i for i, v in enumerate(s['v']) if v is not None)
        o.append(f'<circle class="{s["cls"]} dot" cx="{X(li):.1f}" cy="{Y(s["v"][li]):.1f}" r="3.5"/>')
    o.append('</svg>')
    return ''.join(o)
def barras(grupos, labels, series, fmt=lambda v: br(v), titulo=''):
    vals = [v for s in series for v in s['v']]
    ticks, top = eixo_y(max(vals))
    n = len(labels); k = len(series)
    gw = (W - PL - PR) / n; bw = gw * 0.78 / k
    Y = lambda v: PT + (H - PT - PB) * (1 - v / top)
    o = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="{E(titulo)}">']
    for t in ticks:
        o.append(f'<line class="grid" x1="{PL}" x2="{W-PR}" y1="{Y(t):.1f}" y2="{Y(t):.1f}"/>'
                 f'<text class="tk" x="{PL-6}" y="{Y(t)+4:.1f}" text-anchor="end">{fmt(t)}</text>')
    for i, l in enumerate(labels):
        x0 = PL + gw * i + gw * 0.11
        for j, s in enumerate(series):
            v = s['v'][i]
            o.append(f'<rect class="{s["cls"]}" x="{x0 + j*bw:.1f}" y="{Y(v):.1f}" width="{bw-1:.1f}" height="{Y(0)-Y(v):.1f}"/>')
        o.append(f'<text class="tk" x="{PL + gw*i + gw/2:.1f}" y="{H-12}" text-anchor="middle">{E(l)}</text>')
    o.append('</svg>')
    return ''.join(o)
def legenda(itens):
    return '<div class="leg">' + ''.join(f'<span><i class="sw {c}"></i>{E(t)}</span>' for c, t in itens) + '</div>'

def tabela(cab, linhas_, num_cols=()):
    h = ''.join(f'<th{" class=n" if i in num_cols else ""}>{E(x)}</th>' for i, x in enumerate(cab))
    b = ''.join('<tr>' + ''.join(f'<td{" class=n" if i in num_cols else ""}>{x}</td>' for i, x in enumerate(r)) + '</tr>' for r in linhas_)
    return f'<div class="tw"><table><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table></div>'

CSS = r"""
:root{--bg:#f5f6f3;--fg:#17211d;--mut:#56645e;--rule:#d5dbd6;--card:#ffffff;
--a1:#11614f;--a2:#b4621c;--a3:#7a3b8f;--hl:#e5efe9;--warn:#fbf1e4;
--serif:"Newsreader",Georgia,serif;--sans:"Public Sans",system-ui,sans-serif;--mono:"JetBrains Mono",ui-monospace,monospace}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){color-scheme:dark;--bg:#111714;--fg:#e4ebe7;--mut:#9aaaa2;--rule:#2b3632;--card:#18201d;
--a1:#4fc0a2;--a2:#e59a55;--a3:#c68ad8;--hl:#1b2a25;--warn:#2b2217}}
:root[data-theme="dark"]{color-scheme:dark;--bg:#111714;--fg:#e4ebe7;--mut:#9aaaa2;--rule:#2b3632;--card:#18201d;
--a1:#4fc0a2;--a2:#e59a55;--a3:#c68ad8;--hl:#1b2a25;--warn:#2b2217}
body{background:var(--bg);color:var(--fg);font:16px/1.6 var(--sans)}
.wrap{max-width:980px;margin:0 auto;padding-inline:16px;padding-block:40px 64px}
.kick{font:600 12px/1 var(--mono);letter-spacing:.12em;text-transform:uppercase;color:var(--a1)}
h1{font:650 clamp(36px,6vw,60px)/1.02 var(--serif);margin:.35em 0 .3em;text-wrap:balance;letter-spacing:-.01em}
.lede{font-size:19px;max-width:62ch;color:var(--mut)}
h2{font:650 30px/1.15 var(--serif);margin:0 0 .4em;text-wrap:balance}
h3{font:700 13px/1.3 var(--sans);letter-spacing:.08em;text-transform:uppercase;color:var(--mut);margin:28px 0 8px}
section{border-top:1px solid var(--rule);padding-block:40px 8px}
p{max-width:68ch}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:1px;background:var(--rule);border:1px solid var(--rule);margin:32px 0 8px}
.kpi{background:var(--card);padding:18px}
.kpi b{display:block;font:600 34px/1.1 var(--mono);font-variant-numeric:tabular-nums;letter-spacing:-.02em}
.kpi span{font-size:14px;color:var(--mut);display:block;margin-top:6px}
.kpi small{display:block;font-size:12px;color:var(--mut);margin-top:6px;font-family:var(--mono)}
figure{margin:16px 0 8px;background:var(--card);border:1px solid var(--rule);padding:16px}
figure svg{width:100%;height:auto;display:block}
figcaption{font-size:13px;color:var(--mut);margin-top:8px}
.grid{stroke:var(--rule);stroke-width:1}
.tk{fill:var(--mut);font:11px var(--mono)}
polyline{stroke-width:2.2;stroke-linejoin:round}
polyline.s1,.dot.s1{stroke:var(--a1)} polyline.s2{stroke:var(--a2)} polyline.s3{stroke:var(--a3)}
.dot.s1{fill:var(--a1)} .dot.s2{fill:var(--a2);stroke:none} .dot.s3{fill:var(--a3);stroke:none}
rect.s1{fill:var(--a1)} rect.s2{fill:var(--a2)} rect.s3{fill:var(--a3)}
.leg{display:flex;flex-wrap:wrap;gap:6px 18px;font-size:13px;color:var(--mut);margin-bottom:6px}
.sw{display:inline-block;width:14px;height:4px;margin-right:6px;vertical-align:middle}
.sw.s1{background:var(--a1)} .sw.s2{background:var(--a2)} .sw.s3{background:var(--a3)}
.tw{overflow-x:auto;margin:12px 0}
table{border-collapse:collapse;font-size:14px;min-width:100%}
th,td{text-align:left;padding:7px 10px;border-bottom:1px solid var(--rule);vertical-align:top}
th{font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:var(--mut);font-weight:600}
td.n,th.n{text-align:right;font-family:var(--mono);font-variant-numeric:tabular-nums;white-space:nowrap}
.lac{background:var(--warn);border-left:3px solid var(--a2);padding:12px 16px;margin:16px 0;font-size:14px;max-width:none}
.lac b{font-family:var(--mono);font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--a2);display:block;margin-bottom:4px}
.src{font-size:12.5px;color:var(--mut);font-family:var(--mono);max-width:none;word-break:break-word}
.two{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:16px}
a{color:var(--a1)}
"""
