"""Botão de reportar erro/sugestão, comum a todos os relatórios.
O e-mail de destino é definido aqui, num só lugar; vazio, o botão abre o cliente de e-mail
sem destinatário (o assunto e o corpo já vêm preenchidos)."""
from urllib.parse import quote
EMAIL = ''   # a definir

CSS = '''.rep{display:flex;justify-content:flex-end;margin:12px 0 20px}
.rep a{display:inline-flex;align-items:center;gap:8px;background:#c8102e;color:#fff;text-decoration:none;
font:600 14px/1 var(--sans,system-ui);padding:11px 16px;border-radius:6px;border:2px solid #c8102e}
.rep a:hover,.rep a:focus-visible{background:#fff;color:#c8102e;outline:none}
.rep.fim{justify-content:center;margin:36px 0 8px}'''

def botao(relatorio, url, fim=False):
    assunto = f'[{relatorio}] erro / sugestão'
    corpo = (f'Relatório: {relatorio}\nPágina: {url}\n\nTipo (erro ou sugestão):\n'
             'Seção ou número em questão:\nDescrição:\n')
    href = f'mailto:{EMAIL}?subject={quote(assunto)}&body={quote(corpo)}'
    return (f'<div class="rep{" fim" if fim else ""}"><a href="{href}">'
            '<span aria-hidden="true">⚑</span> Reportar erro ou sugestão</a></div>')
