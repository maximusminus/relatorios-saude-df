#!/usr/bin/env python3
"""Pagamentos do FCDF (órgão 73901 e UGs 1703xx/1704xx) por favorecido, 2023-2026.

Baixa os arquivos diários de despesas do Portal da Transparência federal, guarda só
as linhas do FCDF agregadas por UG + favorecido + elemento, e apaga o zip. Retoma de
onde parou: dias já em fcdf_out/ são pulados. Só biblioteca padrão (macOS: python3).
Uso:  python3 fcdf_pagamentos.py            # baixa o que falta, 1 dia por vez
      python3 fcdf_pagamentos.py --resumo   # soma por ano: IGES-DF, HCB, total UG 170397
O servidor da CGU bloqueia com 405 quem baixa rápido demais; por isso há pausa entre dias.
"""
import csv, datetime, glob, io, json, os, sys, time, urllib.request, zipfile, collections
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fcdf_out")
os.makedirs(OUT, exist_ok=True)
PAUSA = 4  # segundos entre dias

def dia(d):
    out = f"{OUT}/{d}.json"
    if os.path.exists(out):
        return "já"
    req = urllib.request.Request(
        f"https://portaldatransparencia.gov.br/download-de-dados/despesas/{d}",
        headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=300) as r:
        zf = zipfile.ZipFile(io.BytesIO(r.read()))
    nome = [n for n in zf.namelist() if n.endswith("_Despesas_Pagamento.csv")][0]
    agg = {}
    for row in csv.DictReader(io.TextIOWrapper(zf.open(nome), encoding="latin1"), delimiter=";"):
        ug = row["Código Unidade Gestora"]
        if row["Código Órgão"] != "73901" and not ug.startswith(("1703", "1704")):
            continue
        fav = row["Código Favorecido"].replace(".", "").replace("/", "").replace("-", "")
        k = f"{ug}|{row['Unidade Gestora']}|{fav}|{row['Favorecido']}|{row['Código Elemento de Despesa']}"
        v = float(row["Valor do Pagamento Convertido pra R$"].replace(".", "").replace(",", ".") or 0)
        agg[k] = agg.get(k, 0) + v
    json.dump(agg, open(out, "w"))
    return "ok"

def resumo():
    alvo = {"28481233000172": "IGES-DF", "10942995000163": "HCB (ICIPE)"}
    t = collections.defaultdict(float); dias = collections.Counter()
    for f in sorted(glob.glob(f"{OUT}/*.json")):
        y = os.path.basename(f)[:4]; dias[y] += 1
        for k, v in json.load(open(f)).items():
            ug, _, fav, _, _ = k.split("|")
            if fav in alvo: t[(y, alvo[fav])] += v
            if ug == "170397": t[(y, "UG 170397 total")] += v
    for (y, n), v in sorted(t.items()):
        print(f"{y}  {n:18s} R$ {v/1e6:10.1f} mi   ({dias[y]} dias)")

if __name__ == "__main__":
    if "--resumo" in sys.argv:
        resumo(); sys.exit()
    d, fim = datetime.date(2023, 1, 1), datetime.date.today()
    while d <= fim:
        s = d.strftime("%Y%m%d")
        try:
            r = dia(s)
            if r == "ok": print(s, "ok"); time.sleep(PAUSA)
        except Exception as e:
            print(s, "FALHOU:", e); time.sleep(30)
        d += datetime.timedelta(1)
    resumo()
