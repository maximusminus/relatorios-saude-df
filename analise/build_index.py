"""Página inicial dos relatórios avulsos. Para incluir um relatório, acrescente uma linha em RELATORIOS."""
import os
from html import escape as E
from reportar import CSS as REP_CSS, botao, modal
BASE = os.path.expanduser('~/relatorios')

RELATORIOS = [
    # (nº, pasta, título, recorte, fonte e período, data)
    ('01', 'medicos', 'O médico da Secretaria de Saúde do DF',
     'Quantos são, quanto ganham, quem está saindo, formação e residência médica.',
     'Folha da SES-DF, 01/2013 a 07/2026', '09/2026'),
]

cards = '\n'.join(f'''<a class="card" href="{p}/">
<span class="num">Relatório {n}</span>
<h2>{E(t)}</h2>
<p>{E(r)}</p>
<span class="meta">{E(f)} · publicado em {E(d)}</span>
<span class="ir" aria-hidden="true">Ler relatório →</span>
</a>''' for n, p, t, r, f, d in RELATORIOS)

html = f'''<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Relatórios Saúde DF</title>
<meta name="description" content="Relatórios avulsos sobre a saúde pública no Distrito Federal, feitos só com dados públicos e com a fonte de cada número.">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Newsreader:opsz,wght@6..72,500;6..72,650&family=Public+Sans:wght@400;600;700&family=JetBrains+Mono:wght@400;600&display=swap">
<style>
:root{{--bg:#f5f6f3;--fg:#17211d;--mut:#56645e;--rule:#d5dbd6;--card:#ffffff;--a1:#11614f;--hl:#e5efe9;
--serif:"Newsreader",Georgia,serif;--sans:"Public Sans",system-ui,sans-serif;--mono:"JetBrains Mono",ui-monospace,monospace}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{color-scheme:dark;--bg:#111714;--fg:#e4ebe7;--mut:#9aaaa2;--rule:#2b3632;--card:#18201d;--a1:#4fc0a2;--hl:#1b2a25}}}}
:root[data-theme="dark"]{{color-scheme:dark;--bg:#111714;--fg:#e4ebe7;--mut:#9aaaa2;--rule:#2b3632;--card:#18201d;--a1:#4fc0a2;--hl:#1b2a25}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--fg);font:16px/1.6 var(--sans)}}
.wrap{{max-width:980px;margin:0 auto;padding-inline:16px;padding-block:40px 64px}}
.kick{{font:600 12px/1 var(--mono);letter-spacing:.12em;text-transform:uppercase;color:var(--a1)}}
h1{{font:650 clamp(36px,6vw,60px)/1.02 var(--serif);margin:.35em 0 .3em;text-wrap:balance;letter-spacing:-.01em}}
.lede{{font-size:19px;max-width:62ch;color:var(--mut);margin:0 0 8px}}
.principios{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:1px;background:var(--rule);border:1px solid var(--rule);margin:32px 0 40px}}
.principios div{{background:var(--card);padding:16px 18px;font-size:14px;color:var(--mut)}}
.principios b{{display:block;color:var(--fg);font-size:15px;margin-bottom:4px}}
h3{{font:700 13px/1.3 var(--sans);letter-spacing:.08em;text-transform:uppercase;color:var(--mut);margin:0 0 12px}}
.lista{{display:grid;grid-template-columns:repeat(auto-fill,minmax(290px,1fr));gap:16px}}
.card{{display:flex;flex-direction:column;gap:8px;background:var(--card);border:1px solid var(--rule);border-top:4px solid var(--a1);
padding:20px;color:inherit;text-decoration:none;transition:background .15s}}
.card:hover,.card:focus-visible{{background:var(--hl);outline:none}}
.card .num{{font:600 12px/1 var(--mono);letter-spacing:.1em;text-transform:uppercase;color:var(--a1)}}
.card h2{{font:650 25px/1.15 var(--serif);margin:0;text-wrap:balance}}
.card p{{margin:0;color:var(--mut);font-size:15px}}
.card .meta{{font:12px/1.4 var(--mono);color:var(--mut);margin-top:auto;padding-top:8px}}
.card .ir{{font-weight:600;font-size:14px;color:var(--a1)}}
footer{{border-top:1px solid var(--rule);margin-top:48px;padding-top:20px;font-size:13px;color:var(--mut)}}
footer p{{max-width:68ch}}
a{{color:var(--a1)}}
{REP_CSS}
</style>
<div class="wrap">
{botao()}
<div class="kick">Saúde no DF · relatórios avulsos</div>
<h1>Relatórios sobre a saúde pública no Distrito Federal</h1>
<p class="lede">Cada relatório faz um recorte sobre um tema e usa só dados públicos. A fonte de cada número está no próprio texto.</p>
<div class="principios">
<div><b>Dados públicos</b>Só bases oficiais já publicadas: folha de pagamento, DATASUS, IBGE, portais de transparência.</div>
<div><b>Fonte em cada número</b>Cada número traz a base e o período de onde saiu.</div>
<div><b>Nada estimado</b>Quando a fonte não publica um dado, o relatório diz que ele falta e não preenche o buraco.</div>
<div><b>Sem dado pessoal</b>Só contagens e medianas. Nenhum nome, CPF ou matrícula é publicado.</div>
</div>
<h3>Relatórios publicados · {len(RELATORIOS)}</h3>
<div class="lista">
{cards}
</div>
<footer>
<p>O código que gera cada número está em
<a href="https://github.com/maximusminus/relatorios-saude-df/tree/main/analise">relatorios-saude-df/analise</a>.
Achou um erro ou tem uma sugestão? Use o botão vermelho.</p>
{botao(fim=True)}
</footer>
</div>
{modal("Página inicial")}'''
open(f'{BASE}/index.html', 'w').write(html)
print('ok', len(html))
