"""Agrega, só leitura, microdados do saudedf para o Relatório 02 (IGES-DF × HCB).
Saída: iges_hcb.json. Nenhum nome, CPF ou CNS sai daqui — só contagens."""
import glob, json, os, re, collections as C
from dbf_ro import ler
R = '/home/saudedf/dados/raw'
out = {'st': {}, 'sih': {}, 'pf': {}}

# CNES ST: dezembro de cada ano + último
for f in sorted(glob.glob(f'{R}/cnes_historico_st/STDF*.dbc')):
    comp = re.search(r'STDF(\d{6})', f).group(1)
    if comp[4:] != '12' and comp != '202608': continue
    d = {}
    for r in ler(f):
        d[r['CNES']] = dict(nj=r.get('NAT_JUR') or '', cnpj=r['CPF_CNPJ'], man=r['CNPJ_MAN'],
                            tp=r['TP_UNID'], esf=r['ESFERA_A'])
    out['st'][comp] = d
    print('st', comp, len(d), flush=True)

# SIH RD: por ano de competência e CNES
for f in sorted(glob.glob(f'{R}/sih_microdados/RDDF*.dbc')):
    agg = out['sih']
    for r in ler(f):
        k = f"{r['ANO_CMPT']}|{r['CNES']}"
        a = agg.setdefault(k, [0, 0, 0, 0.0, 0, 0])
        a[0] += 1; a[1] += int(r['MORTE'] or 0); a[2] += int(r['DIAS_PERM'] or 0)
        a[3] += float(r['VAL_TOT'] or 0); a[4] += int(r['UTI_MES_TO'] or 0)
        a[5] += 1 if (r['MARCA_UTI'] or '00') not in ('00', '') else 0
    print('sih', os.path.basename(f), flush=True)

# CNES PF: médicos (CBO 225*) distintos por CNES, e por vínculo (2 primeiros dígitos)
for f in sorted(glob.glob(f'{R}/cnes_historico_pf/PFDF*.dbc')):
    comp = re.search(r'PFDF(\d{6})', f).group(1)
    if comp[4:] != '12' and comp != '202608': continue
    med = C.defaultdict(set); vin = C.defaultdict(C.Counter)
    for r in ler(f):
        if not (r['CBO'] or '').startswith('225'): continue
        med[r['CNES']].add(r['CNS_PROF'])
        vin[r['CNES']][r['VINCULAC'][:4]] += 1
    out['pf'][comp] = {c: [len(s), dict(vin[c])] for c, s in med.items()}
    print('pf', comp, flush=True)

json.dump(out, open('iges_hcb.json', 'w'))
