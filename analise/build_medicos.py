"""Gera relatorios/medicos/index.html — corte sobre a figura do médico da SES-DF.
Entradas: fluxo_medicos.json (agregados da folha, gerados por fluxo_medicos.py) e o banco do
saudedf aberto SOMENTE LEITURA. Nada nominal: só contagens e medianas."""
import json, sqlite3, statistics, collections, os, html
BASE = os.path.expanduser('~/relatorios')
DB = 'file:/home/saudedf/dados/database/saudedf.sqlite?mode=ro'
c = sqlite3.connect(DB, uri=True)
F = json.load(open(f'{BASE}/analise/fluxo_medicos.json'))
mensal = F['mensal']

def br(x, d=0):
    s = f'{x:,.{d}f}'
    return s.replace(',', '§').replace('.', ',').replace('§', '.')
def rs(x): return 'R$ ' + br(x, 2)
E = html.escape

# ---------- IPCA: fator para levar um mês a preços de dez/2025 ----------
ipca = dict(c.execute('select periodo, variacao_mensal from ipca_mensal'))
IPCA_FIM = max(ipca)
def fator(aaaamm):
    f = 1.0
    for p in sorted(ipca):
        if p > aaaamm and p <= IPCA_FIM: f *= 1 + ipca[p] / 100
    return f

# ---------- séries ----------
lab = [f"{m['ano']}-{m['mes']}" for m in mensal]
ativos = [m['med_ativo'] for m in mensal]
apos = [m['med_aposentado'] for m in mensal]
pens = [m['med_pensao'] for m in mensal]
resid = [m['res_medico_ativo'] for m in mensal]
ult, pri = mensal[-1], mensal[0]
pico_i = max(range(len(ativos)), key=lambda i: ativos[i])

cv = [(r[0], r[1], r[2], r[3]) for r in c.execute(
    "select data_referencia,total,vagos,ocupados from cargos_vagos where carreira like 'M%DIC%'")]
cv = sorted(cv, key=lambda r: r[0][3:] + r[0][:2])
cv_pico = max(cv, key=lambda r: r[3]); cv_ult = cv[-1]

pop = {int(a): p for a, p in c.execute('select ano, populacao from populacao_df_serie')}
cnes = list(c.execute('select ano, competencia, vinculos_medicos_proxy, medicos_deduplicados_proxy, estado, motivo from vinculos_medicos_ses order by ano'))

# remuneração: mediana anual das medianas mensais, em R$ de dez/2025 (2026 fica nominal)
por_ano = collections.defaultdict(lambda: {'bruto': [], 'bas': [], 'res': [], 'nominal': False})
for m in mensal:
    k = f"{m['ano']}{m['mes']}"; a = int(m['ano'])
    real = k <= IPCA_FIM
    f = fator(k) if real else 1.0
    if not real: por_ano[a]['nominal'] = True
    if m['bruto_mediana_ativo']: por_ano[a]['bruto'].append(m['bruto_mediana_ativo'] * f)
    if m['basico_mediana_ativo']: por_ano[a]['bas'].append(m['basico_mediana_ativo'] * f)
    if m['bruto_mediana_residente']: por_ano[a]['res'].append(m['bruto_mediana_residente'] * f)
anos_rem = sorted(por_ano)
rem = {a: {k: statistics.median(v) for k, v in por_ano[a].items() if isinstance(v, list) and v}
       for a in anos_rem}

venc = list(c.execute('select vigencia, jornada_horas, classe, padrao, vencimento_basico, norma, fonte from vencimento_medico'))
def faixa(vig, jor):
    v = [r[4] for r in venc if r[0] == vig and r[1] == jor]
    return min(v), max(v)
lac_venc = list(c.execute('select intervalo, motivo from vencimento_medico_lacunas'))

amb = {r[0]: r for r in c.execute('select uf, medicos, populacao, razao_por_1000, nota, fonte from demografia_medica_amb')}
emec = c.execute('select motivo from cursos_medicina_df').fetchone()[0]
inep = c.execute('select motivo from medicina_ingressantes_egressos').fetchone()[0]

fl = F['fluxo_anual']
anos_fl = sorted(fl)

# ---------- gráficos SVG ----------
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

jan_idx = [i for i, l in enumerate(lab) if l.endswith('-01') and int(l[:4]) % 2 == 1]
g_folha = linhas([{'v': ativos, 'cls': 's1'}, {'v': apos, 'cls': 's2'}, {'v': pens, 'cls': 's3'}],
                 lab, ticks_x=jan_idx, titulo='Médicos na folha da SES-DF por situação, mensal')
cv_lab = [r[0] for r in cv]
cv_jan = [i for i, l in enumerate(cv_lab) if l.startswith('01/')]
g_cargos = linhas([{'v': [r[3] for r in cv], 'cls': 's1'}, {'v': [r[2] for r in cv], 'cls': 's2'}],
                  [l[3:] for l in cv_lab], ticks_x=cv_jan, titulo='Cargos de médico ocupados e vagos')
anos_r = [a for a in anos_rem if 'bruto' in rem[a]]
g_rem = linhas([{'v': [rem[a].get('bruto') for a in anos_r], 'cls': 's1'},
                {'v': [rem[a].get('bas') for a in anos_r], 'cls': 's2'}],
               [str(a) for a in anos_r], fmt=lambda v: br(v / 1000) + ' mil',
               ticks_x=list(range(0, len(anos_r), 2)), titulo='Remuneração mediana real do médico ativo')
anos_fc = [a for a in anos_fl]
g_fluxo = barras(None, [a[2:] for a in anos_fc],
                 [{'v': [fl[a].get('entrada_nova', 0) for a in anos_fc], 'cls': 's1'},
                  {'v': [fl[a].get('aposentadoria', 0) for a in anos_fc], 'cls': 's2'},
                  {'v': [fl[a].get('saida_definitiva', 0) for a in anos_fc], 'cls': 's3'}],
                 titulo='Entradas e saídas de médicos ativos por ano')
g_res = linhas([{'v': resid, 'cls': 's1'}], lab, ticks_x=jan_idx, titulo='Médicos residentes na folha')

# ---------- números-chave ----------
def ano_de(l): return int(l[:4])
por100k = [(a, ativos[max(i for i, l in enumerate(lab) if ano_de(l) == a and l.endswith('-12')) ] / pop[a] * 1e5)
           for a in sorted({ano_de(l) for l in lab}) if a in pop and any(l == f'{a}-12' for l in lab)]
res_ult = sorted(ult['residentes_por_cargo'].items(), key=lambda kv: -kv[1])

tot_fl = collections.Counter()
for a in anos_fl: tot_fl.update(fl[a])
saidas_esp = collections.Counter()
for a, lst in F['saidas_por_cargo'].items():
    for cg, n in lst: saidas_esp[cg] += n

a06 = faixa('2006-07', 20); a25 = faixa('2025-07', 20); b06 = faixa('2006-07', 40); b25 = faixa('2025-07', 40)
f06 = fator('200607'); f25 = fator('202507')

def tabela(cab, linhas_, num_cols=()):
    h = ''.join(f'<th{" class=n" if i in num_cols else ""}>{E(x)}</th>' for i, x in enumerate(cab))
    b = ''.join('<tr>' + ''.join(f'<td{" class=n" if i in num_cols else ""}>{x}</td>' for i, x in enumerate(r)) + '</tr>' for r in linhas_)
    return f'<div class="tw"><table><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table></div>'

FOLHA = 'Portal da Transparência do DF — folha de remuneração dos servidores (Remuneracao_&lt;ano&gt;.zip, arquivos mensais), órgão SECRETARIA DE ESTADO DE SAUDE'
LBL = lambda l: f'{l[5:]}/{l[:4]}'

out = []
w = out.append
w(f'''<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>O Médico da SES-DF</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Newsreader:opsz,wght@6..72,500;6..72,650&family=Public+Sans:wght@400;600;700&family=JetBrains+Mono:wght@400;600&display=swap">
<style>
:root{{--bg:#f5f6f3;--fg:#17211d;--mut:#56645e;--rule:#d5dbd6;--card:#ffffff;
--a1:#11614f;--a2:#b4621c;--a3:#7a3b8f;--hl:#e5efe9;--warn:#fbf1e4;
--serif:"Newsreader",Georgia,serif;--sans:"Public Sans",system-ui,sans-serif;--mono:"JetBrains Mono",ui-monospace,monospace}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{color-scheme:dark;--bg:#111714;--fg:#e4ebe7;--mut:#9aaaa2;--rule:#2b3632;--card:#18201d;
--a1:#4fc0a2;--a2:#e59a55;--a3:#c68ad8;--hl:#1b2a25;--warn:#2b2217}}}}
:root[data-theme="dark"]{{color-scheme:dark;--bg:#111714;--fg:#e4ebe7;--mut:#9aaaa2;--rule:#2b3632;--card:#18201d;
--a1:#4fc0a2;--a2:#e59a55;--a3:#c68ad8;--hl:#1b2a25;--warn:#2b2217}}
body{{background:var(--bg);color:var(--fg);font:16px/1.6 var(--sans)}}
.wrap{{max-width:980px;margin:0 auto;padding-inline:16px;padding-block:40px 64px}}
.kick{{font:600 12px/1 var(--mono);letter-spacing:.12em;text-transform:uppercase;color:var(--a1)}}
h1{{font:650 clamp(36px,6vw,60px)/1.02 var(--serif);margin:.35em 0 .3em;text-wrap:balance;letter-spacing:-.01em}}
.lede{{font-size:19px;max-width:62ch;color:var(--mut)}}
h2{{font:650 30px/1.15 var(--serif);margin:0 0 .4em;text-wrap:balance}}
h3{{font:700 13px/1.3 var(--sans);letter-spacing:.08em;text-transform:uppercase;color:var(--mut);margin:28px 0 8px}}
section{{border-top:1px solid var(--rule);padding-block:40px 8px}}
p{{max-width:68ch}}
.kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:1px;background:var(--rule);border:1px solid var(--rule);margin:32px 0 8px}}
.kpi{{background:var(--card);padding:18px}}
.kpi b{{display:block;font:600 34px/1.1 var(--mono);font-variant-numeric:tabular-nums;letter-spacing:-.02em}}
.kpi span{{font-size:14px;color:var(--mut);display:block;margin-top:6px}}
.kpi small{{display:block;font-size:12px;color:var(--mut);margin-top:6px;font-family:var(--mono)}}
figure{{margin:16px 0 8px;background:var(--card);border:1px solid var(--rule);padding:16px}}
figure svg{{width:100%;height:auto;display:block}}
figcaption{{font-size:13px;color:var(--mut);margin-top:8px}}
.grid{{stroke:var(--rule);stroke-width:1}}
.tk{{fill:var(--mut);font:11px var(--mono)}}
polyline{{stroke-width:2.2;stroke-linejoin:round}}
polyline.s1,.dot.s1{{stroke:var(--a1)}} polyline.s2{{stroke:var(--a2)}} polyline.s3{{stroke:var(--a3)}}
.dot.s1{{fill:var(--a1)}} .dot.s2{{fill:var(--a2);stroke:none}} .dot.s3{{fill:var(--a3);stroke:none}}
rect.s1{{fill:var(--a1)}} rect.s2{{fill:var(--a2)}} rect.s3{{fill:var(--a3)}}
.leg{{display:flex;flex-wrap:wrap;gap:6px 18px;font-size:13px;color:var(--mut);margin-bottom:6px}}
.sw{{display:inline-block;width:14px;height:4px;margin-right:6px;vertical-align:middle}}
.sw.s1{{background:var(--a1)}} .sw.s2{{background:var(--a2)}} .sw.s3{{background:var(--a3)}}
.tw{{overflow-x:auto;margin:12px 0}}
table{{border-collapse:collapse;font-size:14px;min-width:100%}}
th,td{{text-align:left;padding:7px 10px;border-bottom:1px solid var(--rule);vertical-align:top}}
th{{font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:var(--mut);font-weight:600}}
td.n,th.n{{text-align:right;font-family:var(--mono);font-variant-numeric:tabular-nums;white-space:nowrap}}
.lac{{background:var(--warn);border-left:3px solid var(--a2);padding:12px 16px;margin:16px 0;font-size:14px;max-width:none}}
.lac b{{font-family:var(--mono);font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--a2);display:block;margin-bottom:4px}}
.src{{font-size:12.5px;color:var(--mut);font-family:var(--mono);max-width:none;word-break:break-word}}
.two{{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:16px}}
a{{color:var(--a1)}}
</style>
<div class="wrap">
<div class="kick">Relatório 01 · Saúde no DF · corte sobre a figura do médico</div>
<h1>O médico da Secretaria de Saúde do DF</h1>
<p class="lede">Quantos médicos a SES-DF tem de fato, quanto eles recebem, quem está saindo, de onde vem a formação e quantos
residentes a rede sustenta. Todos os números abaixo vêm de dados públicos já coletados pelo projeto saudedf, com a fonte ao lado.
Onde a fonte não publica o dado, a lacuna fica declarada e não é estimada.</p>
<div class="kpis">
<div class="kpi"><b>{br(ult['med_ativo'])}</b><span>médicos de carreira ativos na folha em {LBL(lab[-1])}</span><small>pico: {br(ativos[pico_i])} em {LBL(lab[pico_i])}</small></div>
<div class="kpi"><b>{br(cv_ult[2])}</b><span>cargos de médico vagos, de {br(cv_ult[1])} autorizados ({cv_ult[0]})</span><small>{br(cv_ult[2]/cv_ult[1]*100,1)}% da carreira desocupada</small></div>
<div class="kpi"><b>{br(ult['med_aposentado'])}</b><span>médicos aposentados na folha em {LBL(lab[-1])}</span><small>eram {br(pri['med_aposentado'])} em {LBL(lab[0])}</small></div>
<div class="kpi"><b>{br(ult['res_medico_ativo'])}</b><span>médicos residentes na folha em {LBL(lab[-1])}</span><small>eram {br(pri['res_medico_ativo'])} em {LBL(lab[0])}</small></div>
</div>
''')

# 1 — quantos são
rel_apos_ult = ult['med_aposentado'] / ult['med_ativo']; rel_apos_pri = pri['med_aposentado'] / pri['med_ativo']
w(f'''<section id="quantos"><h2>1. Quantos são</h2>
<p>Em {LBL(lab[0])} a folha da SES-DF tinha <b>{br(pri['med_ativo'])}</b> médicos de carreira ativos. O número chegou a
<b>{br(ativos[pico_i])}</b> em {LBL(lab[pico_i])} e fechou {LBL(lab[-1])} em <b>{br(ult['med_ativo'])}</b>. No mesmo intervalo,
os aposentados passaram de {br(pri['med_aposentado'])} para <b>{br(ult['med_aposentado'])}</b> e as pensões de {br(pri['med_pensao'])}
para {br(ult['med_pensao'])}. Havia {br(rel_apos_pri*100)} aposentados para cada 100 ativos em {lab[0][:4]}; em {lab[-1][:4]} são
<b>{br(rel_apos_ult*100)}</b>.</p>
<figure>{legenda([('s1','Ativos'),('s2','Aposentados'),('s3','Pensões')])}{g_folha}
<figcaption>Médicos de carreira (cargos “MÉDICO …” e “MED. …”, residentes excluídos) por situação, mês a mês, {LBL(lab[0])}–{LBL(lab[-1])}. Contagem de matrículas distintas.</figcaption></figure>
<p class="src">Fonte: {FOLHA}. Agregação: relatorios/analise/fluxo_medicos.py.</p>
<h3>Cargos autorizados, ocupados e vagos</h3>
<p>A lei autoriza <b>{br(cv_ult[1])}</b> cargos de médico. A ocupação chegou a {br(cv_pico[3])} em {cv_pico[0]} e estava em
<b>{br(cv_ult[3])}</b> em {cv_ult[0]}, com <b>{br(cv_ult[2])}</b> cargos vagos.</p>
<figure>{legenda([('s1','Ocupados'),('s2','Vagos')])}{g_cargos}
<figcaption>Cargo “Médico”, carreira médica da SES-DF, mensal, {cv[0][0]}–{cv_ult[0]}.</figcaption></figure>
<p class="src">Fonte: tabela cargos_vagos do saudedf (Portal da Transparência do DF, cargos vagos e ocupados por carreira).</p>
<h3>Médicos ativos por 100 mil habitantes</h3>
{tabela(['Ano (dez.)','Médicos ativos','População DF','Por 100 mil'],
        [[str(a), br(ativos[lab.index(f"{a}-12")]), br(pop[a]), br(v,1)] for a, v in por100k], (1,2,3))}
<p class="src">Fontes: folha (dezembro de cada ano); população: IBGE SIDRA tabela 6579 (estimativa). Anos sem estimativa publicada
na série do saudedf ({", ".join(str(a) for a in range(2013, 2027) if a not in pop)}) ficam fora da tabela; nada é interpolado.</p>
<h3>Outra medida: vínculos no CNES</h3>
<p>O CNES registra vínculos de profissionais em estabelecimentos, não servidores. A série abaixo cobre hospitais regionais e UBS,
com CNS deduplicado como aproximação do número de pessoas. Não é comparável à folha ponto a ponto. É uma segunda leitura, com
seus próprios limites.</p>
{tabela(['Ano','Competência','Vínculos (proxy)','Médicos deduplicados (proxy)','Estado'],
        [[str(r[0]), r[1], br(r[2]) if r[2] is not None else '—', br(r[3]) if r[3] is not None else '—', E(r[4])] for r in cnes], (2,3))}
<p class="src">Fonte: DATASUS, CNES, arquivos PF do DF (ftp.datasus.gov.br/dissemin/publicos/CNES), tabela vinculos_medicos_ses do saudedf.
2005–2006: lacuna, porque a classificação de ocupação desses arquivos não é a CBO-2002.</p>
</section>''')

# 2 — quanto ganham
anos_tab = [a for a in anos_r]
w(f'''<section id="remuneracao"><h2>2. Quanto ganham</h2>
<p>O vencimento básico da tabela da carreira em julho de 2006 ia de <b>{rs(a06[0])}</b> a <b>{rs(a06[1])}</b> para 20 horas.
Corrigido pelo IPCA até julho de 2025, isso equivale a {rs(a06[0]*f06/f25)} a {rs(a06[1]*f06/f25)}. A tabela vigente em julho de
2025 paga <b>{rs(a25[0])}</b> a <b>{rs(a25[1])}</b>. As tabelas intermediárias não estão publicadas em nenhuma fonte que o
projeto alcança; por isso só estes dois pontos da tabela são comparáveis.</p>
{tabela(['Jornada','Tabela 07/2006','07/2006 a preços de 07/2025 (IPCA)','Tabela 07/2025'],
 [['20 h', f'{rs(a06[0])} – {rs(a06[1])}', f'{rs(a06[0]*f06/f25)} – {rs(a06[1]*f06/f25)}', f'{rs(a25[0])} – {rs(a25[1])}'],
  ['40 h', f'{rs(b06[0])} – {rs(b06[1])}', f'{rs(b06[0]*f06/f25)} – {rs(b06[1]*f06/f25)}', f'{rs(b25[0])} – {rs(b25[1])}']], (1,2,3))}
<p class="src">Fontes: tabela 07/2006 — Lei 3.323/2004, Anexos II e III (SINJ-DF); tabela 07/2025 — SEEC-DF, tabela da carreira médica
com base na Lei 7.253/2023; IPCA — IBGE SIDRA 1737. Tabela vencimento_medico do saudedf. Faixa = do menor ao maior padrão da tabela.</p>
<div class="lac"><b>Lacuna declarada</b>Tabela de vencimentos de 08/2006 a 06/2025: {E(lac_venc[0][1][:330])}…</div>
<h3>O que a folha efetivamente paga</h3>
<p>A folha dá o valor pago de fato, mês a mês. O gráfico mostra a mediana anual das medianas mensais do médico ativo, em reais de
{IPCA_FIM[4:]}/{IPCA_FIM[:4]}. A remuneração bruta inclui gratificações, adicionais, horas extras e parcelas eventuais. A folha
não informa a jornada, então médicos de 20 h e de 40 h entram juntos.</p>
<figure>{legenda([('s1','Bruto (mediana)'),('s2','Remuneração básica (mediana)')])}{g_rem}
<figcaption>Médicos de carreira ativos, SES-DF, {anos_r[0]}–{anos_r[-1]}. R$ de {IPCA_FIM[4:]}/{IPCA_FIM[:4]} pelo IPCA; {", ".join(str(a) for a in anos_r if por_ano[a]['nominal'])} em valores nominais (IPCA da série termina em {IPCA_FIM[4:]}/{IPCA_FIM[:4]}).</figcaption></figure>
{tabela(['Ano','Bruto mediano','Básico mediano','Residente: bruto mediano'],
        [[str(a) + (' (nominal)' if por_ano[a]['nominal'] else ''), rs(rem[a]['bruto']), rs(rem[a]['bas']) if 'bas' in rem[a] else '—', rs(rem[a]['res']) if 'res' in rem[a] else '—'] for a in anos_tab], (1,2,3))}
<p class="src">Fonte: {FOLHA}. Colunas REMUNERAÇÃO BÁSICA e BRUTO. Deflator: IPCA, IBGE SIDRA 1737 (tabela ipca_mensal do saudedf).</p>
</section>''')

# 3 — quem está saindo
anos_tb = anos_fc
saldo = lambda a: fl[a].get('entrada_nova',0) + fl[a].get('retorno',0) + fl[a].get('entrada_outro_status',0) - fl[a].get('aposentadoria',0) - fl[a].get('saida_definitiva',0) - fl[a].get('ativo_para_pensao',0) - fl[a].get('afastamento_temporario',0)
w(f'''<section id="saidas"><h2>3. Quem está dando baixa</h2>
<p>Ligando cada mês ao seguinte pela matrícula, a folha mostra quem entra e quem sai da ativa. De {LBL(lab[1])} a {LBL(lab[-1])}
houve <b>{br(tot_fl['aposentadoria'])}</b> aposentadorias e <b>{br(tot_fl['saida_definitiva'])}</b> saídas definitivas da folha
(exoneração, demissão, óbito, redistribuição: a folha não diz o motivo). Entraram <b>{br(tot_fl['entrada_nova'])}</b> médicos
novos. A matrícula é usada só em memória, para ligar os meses, e nenhuma sai da análise.</p>
<figure>{legenda([('s1','Entradas novas'),('s2','Aposentadorias'),('s3','Saídas definitivas da folha')])}{g_fluxo}
<figcaption>Médicos de carreira ativos, SES-DF. {lab[0][:4]} começa em fevereiro (o primeiro mês lido é a base); {lab[-1][:4]} vai até {LBL(lab[-1])}.</figcaption></figure>
{tabela(['Ano','Entradas novas','Retornos','Aposentadorias','Saídas definitivas','Afastamentos temporários','Saldo'],
 [[a, br(fl[a].get('entrada_nova',0)), br(fl[a].get('retorno',0)+fl[a].get('entrada_outro_status',0)), br(fl[a].get('aposentadoria',0)),
   br(fl[a].get('saida_definitiva',0)), br(fl[a].get('afastamento_temporario',0)), ('+' if saldo(a)>0 else '') + br(saldo(a))] for a in anos_tb], (1,2,3,4,5,6))}
<p class="src">Fonte: {FOLHA}. Método:
<b>entrada nova</b> é uma matrícula de médico ativo nunca vista antes na série. Em {lab[0][:4]} isso inclui quem já estava na
rede e só apareceu depois de janeiro, então as entradas desse ano são infladas.
<b>Aposentadoria</b> é a passagem de ATIVO para APOSENTADO na mesma matrícula.
<b>Saída definitiva</b> é uma matrícula ativa que some e não volta até {LBL(lab[-1])}.
<b>Afastamento temporário</b> é a matrícula que some e volta depois, e não conta como saída.
Nos meses finais da série, uma saída ainda pode ser um afastamento que não teve tempo de voltar.
<b>Saldo</b> = entradas + retornos − aposentadorias − saídas definitivas − afastamentos − passagens a pensão, e reproduz a variação do número de ativos no ano (diferença de até 2 em 2014–2016, por matrículas que mudaram de cargo para residência).</p>
<h3>Especialidades que mais perderam médicos por saída definitiva</h3>
{tabela(['Cargo na folha','Saídas definitivas, ' + lab[1][:4] + '–' + lab[-1][:4]], [[E(cg), br(n)] for cg, n in saidas_esp.most_common(12)], (1,))}
<p class="src">Soma das 15 maiores por ano; o rótulo é o cargo publicado na folha.</p>
</section>''')

# 4 — formação
w(f'''<section id="formacao"><h2>4. Formação médica</h2>
<p>A única medida de estoque de médicos formados que o projeto alcança é a <i>Demografia Médica no Brasil 2025</i> (AMB/CFM/USP).
O DF tem <b>{br(amb['Distrito Federal'][3],2)}</b> registros médicos por mil habitantes, mais que o dobro da média nacional
(<b>{br(amb['Brasil'][3],2)}</b>). Essa densidade não chega à folha da SES: o DF tem médicos, e a rede pública não os fixa.</p>
{tabela(['Recorte','Registros médicos','População','Por 1.000 hab.'],
 [[E(k), br(amb[k][1]), br(amb[k][2]), br(amb[k][3],2)] for k in ('Distrito Federal','Região Centro-Oeste','Brasil')], (1,2,3))}
<p class="src">Fonte: AMB, Demografia Médica no Brasil 2025, Tabela 3, p. 49 (amb.org.br). São inscrições nos CRMs, não pessoas:
56.517 médicos têm registro em mais de uma UF.</p>
<div class="lac"><b>Lacuna declarada — cursos de medicina no DF</b>O cadastro e-MEC (cursos autorizados e ano de autorização) recusa o
acesso automatizado: HTTP 403 mesmo para um navegador real. É um controle do publicador, que o projeto não contorna.</div>
<div class="lac"><b>Lacuna declarada — ingressantes e egressos</b>Os microdados do Censo da Educação Superior (INEP) não aparecem no
índice do próprio publicador (download.inep.gov.br) nas medições do projeto. Nenhum espelho de terceiros é usado como fonte.</div>
</section>''')

# 5 — residência
pico_r = max(range(len(resid)), key=lambda i: resid[i])
w(f'''<section id="residencia"><h2>5. Residência médica</h2>
<p>Os médicos residentes pagos pela SES-DF aparecem na folha com cargos “MED.RESID …”. Eram <b>{br(pri['res_medico_ativo'])}</b>
em {LBL(lab[0])}, chegaram a {br(resid[pico_r])} em {LBL(lab[pico_r])} e somavam <b>{br(ult['res_medico_ativo'])}</b> em {LBL(lab[-1])}.
A bolsa segue valor nacional, e o bruto mediano do residente em {lab[-1][:4]} foi de {rs(rem[int(lab[-1][:4])]['res'])} (nominal).</p>
<figure>{legenda([('s1','Médicos residentes ativos')])}{g_res}
<figcaption>Residentes médicos na folha da SES-DF, mensal. Residências de outras profissões (enfermagem, farmácia, multiprofissional)
excluídas. A oscilação anual acompanha a entrada e a saída das turmas em fevereiro e março.</figcaption></figure>
<h3>Residentes por programa, {LBL(lab[-1])}</h3>
{tabela(['Cargo na folha','Residentes'], [[E(k), br(v)] for k, v in res_ult[:20]], (1,))}
<p class="src">Fonte: {FOLHA}. {len(res_ult)} rótulos de programa distintos no mês; os 20 maiores acima. A folha não informa o ano
de residência (R1, R2, R3) nem o hospital.</p>
</section>''')

w(f'''<section id="metodo"><h2>Método e limites</h2>
<p>Este relatório é independente do dossiê do projeto saudedf e usa só dados que o projeto já coletou, lidos sem alteração.
A folha foi lida em {F['meses_lidos']} arquivos mensais ({LBL(lab[0])} a {LBL(lab[-1])}), órgão SECRETARIA DE ESTADO DE SAUDE.
Um médico de carreira é quem tem cargo que começa por “MÉDICO”/“MED.”. Residentes, identificados por “RESID”, ficam em separado.
Nenhum nome, CPF ou matrícula sai da análise: o código publica só contagens e medianas.</p>
<p>Não há estimativa em lugar nenhum. Onde a fonte não publica, a lacuna aparece como lacuna. O código que gera cada número
está em <a href="https://github.com/maximusminus/relatorios-saude-df/tree/main/analise">relatorios-saude-df/analise</a>.</p>
</section>
</div>''')

os.makedirs(f'{BASE}/medicos', exist_ok=True)
open(f'{BASE}/medicos/index.html', 'w').write('\n'.join(out))
print('ok', len('\n'.join(out)))
