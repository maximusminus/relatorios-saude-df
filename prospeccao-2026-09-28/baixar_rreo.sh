#!/usr/bin/env bash
# Baixa o RREO de dezembro (6º bimestre) do DF, 2023-2025, e confere o sha256
# contra os arquivos obtidos em 28/09/2026. Roda em macOS ou Linux (curl + shasum).
# Uso: bash baixar_rreo.sh [pasta_destino]   (padrão: ./brutos)
set -euo pipefail
DEST="${1:-brutos}"; mkdir -p "$DEST"
B=https://www.economia.df.gov.br/documents/d/seec
API="https://apidatalake.tesouro.gov.br/ords/siconfi/tt/rreo?nr_periodo=6&co_tipo_demonstrativo=RREO&id_ente=53&no_anexo=RREO-Anexo%2002&an_exercicio"
UA="Mozilla/5.0"

baixa() {  # url arquivo
  echo "-> $2"
  curl -fsSL --retry 3 --max-time 300 -A "$UA" -o "$DEST/$2" "$1" || { echo "   FALHOU: $1"; return 0; }
}
baixa "$B/01-a-03-balanco-orcamentario-ate-dezembro-de-2023-anexo-1-novo-xlsx-pdf" rreo_dez_2023.pdf
baixa "$B/rreodezembro2024" rreo_dez_2024.pdf
baixa "$B/rreodezembro2025" rreo_dez_2025.pdf
for y in 2023 2024 2025; do baixa "$API=$y" "rreo_${y}_02.json"; done

# sha256 de 28/09/2026. O JSON do Siconfi muda se o DF retificar o relatório,
# então só os PDFs são conferidos; diferença = arquivo republicado, investigar.
cat > "$DEST/SHA256SUMS.pdf" <<'SUMS'
fcf8f1631a9625e7b3e357f28b87639ee2f3a90f2adf2507dd56be48a328e934  rreo_dez_2023.pdf
b32b7d5ef037eee5f7adb8170b9890e2407e71d19ec94b21660f0e63bda7d0af  rreo_dez_2024.pdf
cfd43aa6309de1e283afdc63ded8503867d3bddb61c67759f84a1baf3a9de588  rreo_dez_2025.pdf
SUMS
(cd "$DEST" && if command -v shasum >/dev/null; then shasum -a 256 -c SHA256SUMS.pdf; else sha256sum -c SHA256SUMS.pdf; fi) || echo "ATENÇÃO: algum PDF difere do baixado em 28/09/2026"

# --- Prospecção 28/09/2026: FCDF, emendas federais e distritais, RREO 2026 parcial ---
mkdir -p "$DEST/federal" "$DEST/df"
baixa https://portaldatransparencia.gov.br/download-de-dados/emendas-parlamentares/UNICO federal/emendas_fed.zip
for y in 2023 2024 2025 2026; do
  baixa "https://portaldatransparencia.gov.br/download-de-dados/orcamento-despesa/$y" "federal/orc_fed_$y.zip"
done
baixa "https://apidatalake.tesouro.gov.br/ords/siconfi/tt/rreo?an_exercicio=2026&nr_periodo=3&co_tipo_demonstrativo=RREO&no_anexo=RREO-Anexo%2002&id_ente=53" df/rreo_2026_p3.json
CID=$(uuidgen 2>/dev/null || python3 -c 'import uuid;print(uuid.uuid4())')
for y in 2023 2024 2025 2026; do
  echo "-> df/dfem_$y.json"
  curl -fsSL --max-time 120 -A "$UA" -H "x-client-id: $CID" -H "Accept: application/json" \
    -o "$DEST/df/dfem_$y.json" \
    "https://www.transparencia.df.gov.br/api/despesa/emendas-parlamentares?anoExercicio=$y&codigoFuncao=10&page=0&size=500" || echo "   FALHOU"
done

# --- Pagamentos do Fundo de Saúde ao IGES-DF e ao HCB (ICIPE), por ano ---
for y in 2023 2024 2025 2026; do
  for n in "GESTAO%20ESTRAT" "PEDIATRIA%20ESPECIALI"; do
    echo "-> df/ob_${y}_${n%%%*}.json"
    curl -fsSL --max-time 120 -A "$UA" -H "x-client-id: $CID" -H "Accept: application/json" \
      -o "$DEST/df/ob_${y}_${n%%%*}.json" \
      "https://www.transparencia.df.gov.br/api/despesa/ob-por-credor?ano=$y&nomeCredor=$n&page=0&size=50" || echo "   FALHOU"
  done
done
