"""Ordens bancárias pagas pelo GDF ao IGES-DF e ao ICIPE (operador do HCB), por ano, unidade pagadora e
unidade liquidante. Fonte: www.transparencia.df.gov.br/api/despesa/ob-por-credor (host já registrado no
saudedf, leitura). Só credores pessoa jurídica; respeita o limite publicado de 10 req/min."""
import json, time, uuid, urllib.request, urllib.parse
B = 'https://www.transparencia.df.gov.br/api/despesa/ob-por-credor'
CRED = {'IGES-DF': ('GESTAO ESTRAT', '28481233000172'), 'ICIPE (HCB)': ('CANCER INFANTIL', '10942995000163')}
H = {'x-client-id': str(uuid.uuid4()), 'Accept': 'application/json'}
out = []
for ent, (nome, cnpj) in CRED.items():
    for ano in range(2009, 2027):
        page = 0
        while True:
            q = urllib.parse.urlencode({'ano': ano, 'nomeCredor': nome, 'page': page, 'size': 200})
            d = json.load(urllib.request.urlopen(urllib.request.Request(f'{B}?{q}', headers=H), timeout=90))
            time.sleep(7)
            for r in d['content']:
                if r['codigoCredor'] == cnpj:
                    out.append({'entidade': ent, **{k: r[k] for k in ('ano', 'codigoCredor', 'nomeUnidadeGestora',
                               'nomeUnidadeGestoraLiquidante', 'valorEvento', 'valorCancelado', 'valorFinal')}})
            if d.get('last', True): break
            page += 1
        print(ent, ano, round(sum(o['valorFinal'] for o in out if o['entidade'] == ent and o['ano'] == ano)), flush=True)
json.dump({'fonte': B, 'coletado_em': time.strftime('%Y-%m-%d'), 'linhas': out},
          open('repasses.json', 'w'), ensure_ascii=False, indent=1)
