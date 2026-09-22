"""Gera relatorios/iges-hcb/index.html — IGES-DF × HCB, dois modelos de gestão pagos pela SES-DF.
Entradas: iges_hcb.json (agregados dos microdados CNES e SIH, gerados por iges_hcb.py) e o banco do
saudedf aberto SOMENTE LEITURA. Nada nominal: só contagens, somas e razões."""
import json, sqlite3, os, collections as C
from comum import br, rs, E, linhas, barras, legenda, tabela, CSS
from reportar import CSS as REP_CSS, botao, modal
BASE = os.path.expanduser('~/relatorios')
c = sqlite3.connect('file:/home/saudedf/dados/database/saudedf.sqlite?mode=ro', uri=True)
REL = 'Relatório 02 — IGES-DF × HCB'
D = json.load(open(f'{BASE}/analise/iges_hcb.json'))
ST, SIH, PF = D['st'], D['sih'], D['pf']

HBDF, HRSM, HCB = '0010456', '5717515', '6876617'
RAIZ_IGES, RAIZ_SES = '28481233', '00394700'
NOME = {HBDF: 'Hospital de Base (HBDF)', HRSM: 'Hospital Regional de Santa Maria (HRSM)', HCB: 'Hospital da Criança de Brasília (HCB)'}

def st(ano): return ST.get(f'{ano}12') or ST.get('202608')
def raiz(ano, cnes):
    r = st(ano).get(cnes)
    return r['cnpj'][:8] if r else None
def ano_iges(cnes):
    return min(int(k[:4]) for k, s in ST.items() if s.get(cnes, {}).get('cnpj', '')[:8] == RAIZ_IGES)
A_HBDF, A_HRSM = ano_iges(HBDF), ano_iges(HRSM)

# ---------- SIH: por ano e grupo ----------
anos_sih = sorted({int(k[:4]) for k in SIH})
def grupo(cnes):
    return {HBDF: 'hbdf', HRSM: 'hrsm', HCB: 'hcb'}.get(cnes, 'resto')
S = C.defaultdict(lambda: [0, 0, 0, 0.0, 0, 0])
for k, v in SIH.items():
    a, cn = k.split('|'); g = grupo(cn)
    for gg in (g, 'df'):
        acc = S[(int(a), gg)]
        for i in range(6): acc[i] += v[i]
def m(a, g, q):
    n, mo, dias, val, uti_d, uti_n = S[(a, g)]
    if not n: return None
    return {'n': n, 'mort': mo / n * 100, 'perm': dias / n, 'val': val / n,
            'uti': uti_n / n * 100, 'uti_d': uti_d}[q]
for a in anos_sih:  # reconciliação com a série do próprio saudedf
    tot = c.execute('select sum(internacoes) from sih_uti_serie where ano=?', (str(a),)).fetchone()[0]
    assert tot == S[(a, 'df')][0], (a, tot, S[(a, 'df')][0])

# ---------- leitos ----------
leitos = C.defaultdict(lambda: [0, 0])
for ano, cn, cat, n in c.execute('select ano, co_cnes, categoria, leitos_sus from leitos_serie_cnes where co_cnes in (?,?,?)', (HBDF, HRSM, HCB)):
    leitos[(int(ano), cn)][0] += n or 0
    if cat.startswith('UTI'): leitos[(int(ano), cn)][1] += n or 0
anos_l = sorted({a for a, _ in leitos})

# ---------- pronto atendimento público (UPA) e médicos ----------
anos_st = sorted(int(k[:4]) for k in ST if k.endswith('12'))
def upas(comp):
    return [cn for cn, r in ST[comp].items() if r['tp'] == '73' and (r['nj'][:1] == '1' or (not r['nj'] and r['esf'] in ('E', 'M')))]
upa_n = {a: len(upas(f'{a}12')) for a in anos_st}
def medicos(comp, cns): return sum(PF.get(comp, {}).get(x, [0])[0] for x in cns)
med = {a: {cn: medicos(f'{a}12', [cn]) for cn in (HBDF, HRSM, HCB)} for a in anos_st}
med_upa = {a: medicos(f'{a}12', upas(f'{a}12')) for a in anos_st}
upa_ult = upas('202608')
nomes_upa = dict(c.execute('select co_cnes, no_fantasia from cnes_estabelecimentos'))
contratos_upa = [t for (t,) in c.execute("select titulo from igesdf_contratos_gestao where tipo='upa' order by titulo")]

# ---------- contratos, transparência, auditoria ----------
iges_tipos = dict(c.execute('select tipo, count(*) from igesdf_contratos_gestao group by tipo'))
iges_ta_max = max(int(x) for (t,) in c.execute("select titulo from igesdf_contratos_gestao where tipo='termo_aditivo'")
                  for x in __import__('re').findall(r'(\d+)º', t))
hcb_docs = [d for (d,) in c.execute('select documento from hcb_contratos')]
hcb_ta = [d for d in hcb_docs if ' ta ' in f' {d} ']
hcb_ta_max = max(int(d.split()[1]) for d in hcb_ta if d.split()[1].isdigit())
hcb_emendas = sum('emenda parlamentar' in d for d in hcb_docs)
tri = {e: (p, t) for e, p, t in c.execute('select entidade, celulas_publicadas, celulas_totais from transparencia_indice_publicacao')}
matriz = list(c.execute('select tipo_documento, entidade, publicado from transparencia_matriz order by tipo_documento, entidade'))
opin = {}
for ex, op, base in c.execute('select exercicio, opiniao, coalesce(trecho_base, "") from opinioes_auditoria order by exercicio'):
    mot = []
    if 'Medusa' in base: mot.append('Operação Medusa (Polícia Civil do DF), contratos de 2018')
    if 'Escudeiro' in base: mot.append('Operação Escudeiro (Polícia Civil do DF), renovação de contrato')
    if 'nvent' in base: mot.append('estoques sem inventário físico')
    opin[ex] = (op, mot)
dem = {(l, ex): v for l, ex, v in c.execute("select linha, exercicio, valor from demonstracoes_serie where publicavel='sim'")}
orc = dict((int(a), v) for a, v in c.execute('select ano, liquidado from orcamento_saude'))

LAB_T = {'contrato_gestao': 'Contrato de gestão', 'prestacao_contas_periodica': 'Prestação de contas periódica',
         'demonstracoes_contabeis': 'Demonstrações contábeis'}
SIHSRC = 'DATASUS, SIH/SUS, AIH reduzida (RD), DF, arquivos RDDF&lt;aamm&gt;.dbc de 01/2008 a 12/2024, agregados por CNES do estabelecimento'
CNESSRC = 'DATASUS, CNES, arquivos ST (estabelecimentos) e PF (profissionais) do DF, competência de dezembro de cada ano (2026: agosto)'

# ---------- gráficos ----------
G = [('hbdf', 's1', 'HBDF'), ('hrsm', 's2', 'HRSM'), ('hcb', 's3', 'HCB')]
lab_s = [str(a) for a in anos_sih]
tx = list(range(0, len(lab_s), 2))
g_n = linhas([{'v': [m(a, g, 'n') for a in anos_sih], 'cls': cls} for g, cls, _ in G], lab_s, ticks_x=tx, titulo='Internações SUS por ano')
g_uti = linhas([{'v': [m(a, g, 'uti') for a in anos_sih], 'cls': cls} for g, cls, _ in G] + [{'v': [m(a, 'df', 'uti') for a in anos_sih], 'cls': 's4'}],
               lab_s, fmt=lambda v: br(v) + '%', ticks_x=tx, titulo='Internações com uso de UTI')
lab_l = [str(a) for a in anos_l]
g_leitos = linhas([{'v': [leitos[(a, cn)][0] or None for a in anos_l], 'cls': cls} for cn, cls in ((HBDF, 's1'), (HRSM, 's2'), (HCB, 's3'))],
                  lab_l, ticks_x=list(range(0, len(lab_l), 3)), titulo='Leitos SUS por hospital')
lab_u = [str(a)[2:] for a in anos_st]
g_upa = barras(None, lab_u, [{'v': [upa_n[a] for a in anos_st], 'cls': 's1'}], titulo='Unidades públicas de pronto atendimento no CNES')

def cel(v, f=br, d=0): return '—' if v is None else f(v, d)
U = max(anos_sih)

out = []; w = out.append
w(f'''<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>IGES-DF e HCB</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Newsreader:opsz,wght@6..72,500;6..72,650&family=Public+Sans:wght@400;600;700&family=JetBrains+Mono:wght@400;600&display=swap">
<style>{CSS}
polyline.s4{{stroke:var(--mut);stroke-dasharray:4 4}} .dot.s4{{fill:var(--mut);stroke:none}} .sw.s4{{background:var(--mut)}}
{REP_CSS}</style>
<div class="wrap">
{botao()}
<div class="kick">Relatório 02 · Saúde no DF · dois modelos de gestão</div>
<h1>IGES-DF e Hospital da Criança: dois modelos pagos pela SES</h1>
<p class="lede">O Instituto de Gestão Estratégica de Saúde (IGES-DF) e o Hospital da Criança de Brasília (HCB) recebem recursos
da Secretaria de Saúde para operar hospitais públicos fora da administração direta. Este relatório põe lado a lado o que os
dados públicos já coletados pelo projeto saudedf mostram sobre os dois: tamanho, produção, contas, auditoria e transparência.
Onde a fonte não publica o dado, a lacuna fica declarada e não é estimada.</p>
<div class="kpis">
<div class="kpi"><b>{sum(1 for o in opin.values() if o[0]=="com_ressalva")} de {sum(1 for e in opin if e >= "2019")}</b><span>balanços do IGES-DF (2019–2023) com opinião <b>com ressalva</b> do auditor independente</span><small>2018 (IHBDF): sem ressalva</small></div>
<div class="kpi"><b>{iges_ta_max}º</b><span>termo aditivo ao contrato de gestão 001/2018 do IGES-DF, o mais alto publicado</span><small>HCB: {hcb_ta_max}º termo aditivo ao contrato 076/2019</small></div>
<div class="kpi"><b>{upa_n[2020]} → {upa_n[2022]}</b><span>unidades públicas de pronto atendimento no CNES, dez/2020 → dez/2022</span><small>{upa_n[2012]} em 2012; {len(upa_ult)} em ago/2026</small></div>
<div class="kpi"><b>{tri["IGES-DF"][0]}/{tri["IGES-DF"][1]} · {tri["HCB"][0]}/{tri["HCB"][1]}</b><span>tipos de documento de prestação de contas localizados: IGES-DF · HCB</span><small>medida própria, não índice oficial</small></div>
</div>
''')

# 1 — os dois modelos
w(f'''<section id="modelos"><h2>1. Os dois modelos</h2>
<p>O <b>HBDF</b> passou a ser gerido pelo Instituto Hospital de Base, depois IGES-DF, e o CNES registra a troca: até {A_HBDF - 1}
o hospital constava sob a raiz de CNPJ da Secretaria de Saúde; a partir de dezembro de {A_HBDF}, sob a raiz {RAIZ_IGES[:2]}.{RAIZ_IGES[2:5]}.{RAIZ_IGES[5:]}
(IGES-DF), natureza jurídica 3077, serviço social autônomo. O <b>HRSM</b> fez a mesma passagem em {A_HRSM}. O <b>HCB</b> continua
cadastrado no CNES sob a raiz de CNPJ da Secretaria ({RAIZ_SES[:2]}.{RAIZ_SES[2:5]}.{RAIZ_SES[5:]}), natureza 1023, embora seja
operado por contrato de gestão (076/2019).</p>
{tabela(['Unidade', 'Natureza jurídica no CNES (ago/2026)', 'Raiz do CNPJ no CNES', 'Desde'],
  [[NOME[HBDF], '3077 — serviço social autônomo', f'{RAIZ_IGES} (IGES-DF)', str(A_HBDF)],
   [NOME[HRSM], '3077 — serviço social autônomo', f'{RAIZ_IGES} (IGES-DF)', str(A_HRSM)],
   [NOME[HCB], '1023 — órgão público do Poder Executivo estadual/DF', f'{RAIZ_SES} (SES-DF)', '—']], ())}
<p class="src">Fonte: {CNESSRC}; campos CNES, CPF_CNPJ e NAT_JUR. “Desde” = primeiro dezembro em que a raiz 28481233 aparece.</p>
<div class="lac"><b>Lacuna declarada — governança</b>A composição dos conselhos de administração do IGES-DF e do HCB, os estatutos e
o assento do secretário de Saúde em cada conselho não estão entre os dados coletados pelo saudedf. A diferença de governança entre
os dois modelos, central na pergunta, não pode ser medida aqui.</div>
<div class="lac"><b>Lacuna declarada — trânsito de dirigentes</b>A passagem de dirigentes entre o IGES-DF e cargos de secretário ou
subsecretário da SES exigiria nomes e datas de nomeação. O Diário Oficial (DODF) foi coletado só como índice, e este relatório não
publica nomes. Não há medida possível com os dados disponíveis.</div>
</section>''')

# 2 — tamanho
lu = max(a for a in anos_l if leitos[(a, HBDF)][0])
w(f'''<section id="tamanho"><h2>2. Tamanho: leitos e médicos</h2>
<figure>{legenda([('s1','HBDF'),('s2','HRSM'),('s3','HCB')])}{g_leitos}
<figcaption>Leitos SUS por hospital (enfermaria, cuidados intermediários e UTI somados), {anos_l[0]}–{anos_l[-1]}.</figcaption></figure>
{tabela(['Ano', 'HBDF leitos', 'HBDF UTI', 'HRSM leitos', 'HRSM UTI', 'HCB leitos', 'HCB UTI'],
  [[str(a)] + [cel(leitos[(a, cn)][i] or None) for cn in (HBDF, HRSM, HCB) for i in (0, 1)] for a in anos_l if a >= 2012], (1,2,3,4,5,6))}
<p class="src">Fonte: tabela leitos_serie_cnes do saudedf (DATASUS, CNES, arquivos LT do DF). “—” = sem leito SUS registrado no ano.</p>
<h3>Médicos com vínculo registrado no CNES</h3>
{tabela(['Dezembro de', 'HBDF', 'HRSM', 'HCB', 'Pronto atendimento público (soma)'],
  [[str(a), br(med[a][HBDF]), br(med[a][HRSM]), br(med[a][HCB]), br(med_upa[a])] for a in anos_st if a >= 2012], (1,2,3,4))}
<p class="src">Fonte: {CNESSRC}; profissionais com CBO 225 (médicos), contados por CNS distinto em cada estabelecimento.
Um médico com vínculo em duas unidades conta nas duas. Nenhum nome sai da análise.</p>
<div class="lac"><b>Lacuna declarada — tempo de formado</b>O CNES não registra o ano de formatura, e os empregados do IGES-DF não
estão na folha do GDF que o saudedf coleta. Se as unidades geridas pelo IGES-DF são ocupadas por médicos recém-formados não é
mensurável com estes dados.</div>
</section>''')

# 3 — produção
w(f'''<section id="producao"><h2>3. Produção e desfecho das internações</h2>
<p>O SIH registra cada internação paga pelo SUS, com o CNES do hospital. Em {U}, o HBDF fez <b>{br(m(U,'hbdf','n'))}</b>
internações, o HRSM <b>{br(m(U,'hrsm','n'))}</b> e o HCB <b>{br(m(U,'hcb','n'))}</b>, de {br(m(U,'df','n'))} no DF.
O HBDF fez {br(m(A_HBDF-1,'hbdf','n'))} internações em {A_HBDF-1}, último ano sob gestão direta.</p>
<figure>{legenda([('s1','HBDF'),('s2','HRSM'),('s3','HCB')])}{g_n}
<figcaption>Internações SUS (AIH) por ano de competência, {anos_sih[0]}–{U}.</figcaption></figure>
<figure>{legenda([('s1','HBDF'),('s2','HRSM'),('s3','HCB'),('s4','DF, todas as unidades')])}{g_uti}
<figcaption>Percentual das internações com uso de UTI (campo MARCA_UTI diferente de 00).</figcaption></figure>
{tabela(['Ano', 'Unidade', 'Internações', 'Óbitos (%)', 'Permanência média (dias)', 'Com UTI (%)', 'Valor médio da AIH (R$ nominais)'],
  [[str(a), lb, br(m(a,g,'n')), br(m(a,g,'mort'),1), br(m(a,g,'perm'),1), br(m(a,g,'uti'),1), rs(m(a,g,'val'))]
   for a in (2012, 2017, 2019, 2022, U) for g, _, lb in G + [('resto','','Demais do DF')] if m(a, g, 'n')], (2,3,4,5,6))}
<p class="src">Fonte: {SIHSRC}. Campos MORTE, DIAS_PERM, MARCA_UTI e VAL_TOT. O total do DF por ano bate, internação por
internação, com a tabela sih_uti_serie do saudedf. Valores nominais, sem correção.</p>
<div class="lac"><b>Leia com cuidado</b>Mortalidade e permanência não comparam a qualidade dos hospitais entre si: o HCB atende
crianças em alta complexidade, o HBDF é referência em trauma e alta complexidade adulta, e o perfil dos pacientes muda cada
número. A comparação que o dado sustenta é a do mesmo hospital antes e depois da troca de gestão.</div>
<div class="lac"><b>Lacuna declarada — fila de UTI</b>A lista de espera por leito de UTI do DF é publicada pela SES num painel
(InfoSaúde) que o projeto não conseguiu extrair. Se a gestão das UPAs pressiona essa fila não é mensurável com estes dados.</div>
</section>''')

# 4 — UPAs
w(f'''<section id="upas"><h2>4. As UPAs</h2>
<p>O CNES tinha <b>{upa_n[2012]}</b> unidades públicas de pronto atendimento no DF em 2012, <b>{upa_n[2020]}</b> em 2020 e
<b>{upa_n[2022]}</b> em 2022, número que se mantém em {len(upa_ult)} em agosto de 2026. O índice de contratos do IGES-DF publica
contratos de gestão para {len(contratos_upa)} UPAs, assinados em 2021.</p>
<figure>{legenda([('s1','Unidades públicas de pronto atendimento')])}{g_upa}
<figcaption>Estabelecimentos do tipo 73 (pronto atendimento) com natureza jurídica pública, dezembro de cada ano.</figcaption></figure>
{tabela(['Contrato de gestão do IGES-DF (título publicado)'], [[E(t)] for t in contratos_upa])}
<p class="src">Fontes: {CNESSRC}, campo TP_UNID; tabela igesdf_contratos_gestao do saudedf (índice de documentos de igesdf.org.br).</p>
<div class="lac"><b>Lacuna declarada — quem gere cada UPA</b>No CNES, as UPAs continuam cadastradas sob a raiz de CNPJ da SES, e
não sob a do IGES-DF. O cadastro não diz qual UPA é operada pelo instituto; a única fonte é o título dos contratos acima.</div>
</section>''')

# 5 — contas e auditoria
w(f'''<section id="contas"><h2>5. Contas e auditoria</h2>
<p>O IGES-DF publica demonstrações contábeis e relatórios de auditor independente. Desde o exercício de 2019, <b>todos</b> os
pareceres localizados são <b>com ressalva</b>. As razões abaixo são as que o próprio auditor escreveu na base da ressalva.</p>
{tabela(['Exercício', 'Opinião do auditor', 'Base da ressalva (resumo das palavras do auditor)'],
  [[ex, 'com ressalva' if op == 'com_ressalva' else 'sem ressalva', '; '.join(mot) or '—'] for ex, (op, mot) in sorted(opin.items())])}
<p class="src">Fonte: tabela opinioes_auditoria do saudedf; relatórios de auditor independente publicados em igesdf.org.br
(2018: Instituto Hospital de Base). A ressalva registra uma limitação do auditor, não uma conclusão de irregularidade.</p>
{tabela(['Exercício', 'Patrimônio líquido', 'Estoques'],
  [[ex, cel(dem.get(('patrimonio_liquido', ex)), lambda v, d: rs(v)), cel(dem.get(('estoques', ex)), lambda v, d: rs(v))] for ex in ('2018','2019','2020','2021','2022','2023')], (1,2))}
<p class="src">Fonte: tabela demonstracoes_serie do saudedf, lida dos balanços do IGES-DF. “—” = os documentos divergem entre si
para aquele exercício, e o valor não é publicado.</p>
<div class="lac"><b>Lacuna declarada — demonstrações do HCB</b>O saudedf não localizou demonstrações contábeis do HCB na página
de transparência que lê (hcb.org.br). Não há como comparar o balanço dos dois.</div>
<div class="lac"><b>Lacuna declarada — quanto a SES repassa a cada um</b>O saudedf tem o gasto liquidado da função saúde do GDF
(R$ {br(orc[2019]/1e9,2)} bilhões em 2019, R$ {br(orc[max(orc)]/1e9,2)} bilhões em {max(orc)}), mas não o repasse a cada contrato
de gestão. Custo por leito e por internação de cada entidade ficam sem medida.</div>
<div class="lac"><b>Fora do alcance — desvio de recursos</b>Desvio é uma conclusão de investigação ou de julgamento, não um dado.
Este relatório não o mede. O que os documentos públicos mostram está acima: as ressalvas do auditor e as operações que ele cita.</div>
</section>''')

# 6 — transparência e contratos
w(f'''<section id="transparencia"><h2>6. Transparência e contratos</h2>
<p>O projeto procurou os mesmos três tipos de documento nas páginas de transparência de cada entidade.</p>
{tabela(['Documento', 'IGES-DF', 'HCB'],
  [[LAB_T.get(t, t), *[('localizado' if dict(((e, p) for tt, e, p in matriz if tt == t)).get(ent) == 'sim' else 'não localizado') for ent in ('IGES-DF', 'HCB')]]
   for t in dict.fromkeys(t for t, _, _ in matriz)])}
<p class="src">Fonte: tabelas transparencia_matriz e transparencia_indice_publicacao do saudedf. Medida própria do projeto,
não um índice oficial. “Não localizado” quer dizer ausente nas páginas que o projeto lê, não prova de que o documento não existe.</p>
<h3>Aditivos</h3>
<p>O contrato de gestão 001/2018 do IGES-DF chegou ao <b>{iges_ta_max}º termo aditivo</b> publicado; o índice do instituto tem
{iges_tipos.get('termo_aditivo', 0)} termos aditivos, {iges_tipos.get('apostilamento', 0)} apostilamentos e {iges_tipos.get('extrato', 0)} extratos.
O HCB publica {len(hcb_ta)} documentos de termo aditivo, até o <b>{hcb_ta_max}º</b>, {hcb_emendas} deles vinculados a emendas
parlamentares.</p>
<p class="src">Fontes: tabelas igesdf_contratos_gestao e hcb_contratos do saudedf (índices de documentos das duas páginas de transparência).</p>
</section>''')

w(f'''<section id="metodo"><h2>Método e limites</h2>
<p>Este relatório é independente do dossiê do projeto saudedf e usa só dados que o projeto já coletou, lidos sem alteração.
Os microdados do SIH e do CNES foram descompactados numa pasta temporária e agregados por estabelecimento; nenhum arquivo do
saudedf foi alterado. Nenhum nome, CPF ou CNS sai da análise.</p>
<p>A pergunta que motivou o relatório inclui pontos que os dados públicos não alcançam: governança dos conselhos, trânsito de
dirigentes, perfil de formação dos médicos, fila de UTI e desvio de recursos. Cada um aparece acima como lacuna, com o motivo.
Nada é estimado. O código que gera cada número está em
<a href="https://github.com/maximusminus/relatorios-saude-df/tree/main/analise">relatorios-saude-df/analise</a>.</p>
</section>
{botao(fim=True)}
</div>''')
w(modal(REL))

os.makedirs(f'{BASE}/iges-hcb', exist_ok=True)
open(f'{BASE}/iges-hcb/index.html', 'w').write('\n'.join(out))
print('ok', len('\n'.join(out)))
