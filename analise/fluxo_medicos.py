"""Fluxo de médicos da SES-DF a partir da folha publicada (Portal da Transparência do DF).
Lê os zips mensais já em cache no saudedf (somente leitura). Nada nominal sai daqui:
a matrícula é usada só em memória para ligar um mês ao seguinte; a saída são contagens."""
import zipfile, io, csv, re, json, statistics, collections, glob, os
RAW = '/home/saudedf/dados/raw/remuneracao'
M = re.compile(r"^\s*(?:M[EÉ]DIC[OA]S?\b|MED\.?\s|MED\.(?=[A-ZÁ-Ú]))", re.I)
R = re.compile(r"\bRESID|\bRES[.\-](?=\s*[A-ZÁ-Ú])", re.I)
MD = re.compile(r'M[EÉ]D', re.I)
SES = 'SECRETARIA DE ESTADO DE SAUDE'
def num(s):
    s = (s or '').strip().replace('.', '').replace(',', '.')
    try: return float(s)
    except ValueError: return None
meses = []
for zp in sorted(glob.glob(f'{RAW}/Remuneracao_*.zip')):
    z = zipfile.ZipFile(zp)
    for n in sorted(z.namelist()):
        m = re.search(r'/Remuneracao_(\d{4})_(\d{2})\.csv$', n)
        if m: meses.append((m.group(1), m.group(2), zp, n))
estado = {}   # competencia -> {matricula: (situacao, tipo, cargo)}
mensal = []
for ano, mes, zp, n in meses:
    cur = {}; basicos = []; brutos = []; brutos_res = []
    with zipfile.ZipFile(zp).open(n) as f:
        tf = io.TextIOWrapper(f, encoding='latin1', newline='')
        hdr = next(csv.reader([tf.readline()], delimiter=';'))
        ix = {h.strip(): i for i, h in enumerate(hdr)}
        iO, iC, iS, iM, iB, iBr = (ix['ÓRGÃO'], ix['CARGO'], ix['SITUAÇÃO'], ix['MATRÍCULA'],
                                    ix['REMUNERAÇÃO BÁSICA'], ix['BRUTO'])
        linhas = (l for l in tf if 'SECRETARIA DE ESTADO DE SAUDE' in l and MD.search(l))
        for row in csv.reader(linhas, delimiter=';'):
            if row[iO].strip().upper() != SES: continue
            c = row[iC].strip()
            res = bool(R.search(c)); med = bool(M.search(c)) and not res
            medres = res and re.search(r'MED', c, re.I)
            if not (med or medres): continue
            sit = row[iS].strip().upper()
            cur[row[iM].strip()] = (sit, 'med' if med else 'res', c)
            if med and sit == 'ATIVO':
                b = num(row[iB]); br = num(row[iBr])
                if b: basicos.append(b)
                if br: brutos.append(br)
            if medres and sit == 'ATIVO':
                br = num(row[iBr])
                if br: brutos_res.append(br)
    cnt = collections.Counter((t, s) for s, t, _ in cur.values())
    sits = collections.Counter(s for s, t, _ in cur.values() if t == 'med')
    res_cargo = collections.Counter(c for s, t, c in cur.values() if t == 'res' and s == 'ATIVO')
    mensal.append({'ano': ano, 'mes': mes,
        'med_ativo': cnt[('med','ATIVO')], 'med_aposentado': cnt[('med','APOSENTADO')],
        'med_pensao': cnt[('med','PENSAO')], 'res_medico_ativo': cnt[('res','ATIVO')],
        'basico_mediana_ativo': statistics.median(basicos) if basicos else None,
        'bruto_mediana_ativo': statistics.median(brutos) if brutos else None,
        'bruto_mediana_residente': statistics.median(brutos_res) if brutos_res else None,
        'situacoes_med': dict(sits), 'residentes_por_cargo': dict(res_cargo)})
    estado[(ano, mes)] = cur
    print(ano, mes, mensal[-1]['med_ativo'], flush=True)
# fluxos mês a mês, somente médicos de carreira ativos.
# Uma matrícula ATIVA que some da folha e REAPARECE depois (em qualquer situação) é afastamento
# temporário, não saída; só conta como saída definitiva a que não volta até o último mês lido.
fluxo = collections.defaultdict(collections.Counter)
esp_saida = collections.defaultdict(collections.Counter)
chaves = sorted(estado)
ultimo = {}
for i, k in enumerate(chaves):
    for mat in estado[k]: ultimo[mat] = i
ja_visto = set()
for i, k in enumerate(chaves):
    cur = estado[k]
    if i == 0:
        ja_visto |= set(cur); continue
    prev = estado[chaves[i-1]]; ano = k[0]
    for mat, (s, t, c) in prev.items():
        if t != 'med' or s != 'ATIVO': continue
        nx = cur.get(mat)
        if nx is None:
            if ultimo[mat] > i: fluxo[ano]['afastamento_temporario'] += 1
            else: fluxo[ano]['saida_definitiva'] += 1; esp_saida[ano][c] += 1
        elif nx[0] == 'APOSENTADO':
            fluxo[ano]['aposentadoria'] += 1
        elif nx[0] == 'PENSAO':
            fluxo[ano]['ativo_para_pensao'] += 1
    for mat, (s, t, c) in cur.items():
        if t == 'med' and s == 'ATIVO':
            p = prev.get(mat)
            if p is None and mat not in ja_visto: fluxo[ano]['entrada_nova'] += 1
            elif p is None: fluxo[ano]['retorno'] += 1
            elif p[0] != 'ATIVO' or p[1] != 'med': fluxo[ano]['entrada_outro_status'] += 1
    ja_visto |= set(cur)
# saídas da folha que voltam depois (lacuna de mês) -- conta como ruído
json.dump({'mensal': mensal, 'fluxo_anual': {a: dict(v) for a, v in sorted(fluxo.items())},
           'saidas_por_cargo': {a: v.most_common(15) for a, v in sorted(esp_saida.items())},
           'meses_lidos': len(chaves)},
          open(os.path.expanduser('~/relatorios/analise/fluxo_medicos.json'), 'w'), ensure_ascii=False, indent=1)
