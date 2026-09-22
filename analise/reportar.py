"""Botão de relatar problema ou sugestão, comum a todos os relatórios.
Copiado do Observatório CLDF (sinapseagentes/cldf-observatorio, OS-145): um formulário que a
PRÓPRIA PÁGINA envia ao Web3Forms, direto ao operador. Nenhum código deste repositório faz o
envio; é o navegador de quem lê. O campo `estado` diz de qual relatório e seção veio o relato."""
from html import escape
CHAVE_WEB3FORMS = '596b7023-f2a3-4f29-8f0b-fb446fad4664'   # a mesma chave pública do Observatório CLDF

CSS = '''.rep{display:flex;justify-content:flex-end;margin:12px 0 20px}
.rep.fim{justify-content:center;margin:36px 0 8px}
.rep button{display:inline-flex;align-items:center;gap:8px;background:#c8102e;color:#fff;cursor:pointer;
font:600 14px/1 var(--sans,system-ui);padding:11px 16px;border-radius:6px;border:2px solid #c8102e}
.rep button:hover,.rep button:focus-visible{background:#fff;color:#c8102e;outline:none}
.modal{position:fixed;inset:0;background:rgba(10,15,30,.55);display:grid;place-items:center;z-index:20;padding:16px}
.modal[hidden]{display:none}
.modal-caixa{background:var(--card);color:var(--fg);border-radius:14px;max-width:560px;width:100%;
max-height:88vh;overflow:auto;padding:24px;position:relative;box-shadow:0 20px 60px rgba(0,0,0,.35)}
.modal-caixa h3{margin:0 0 8px}
.fechar{position:absolute;top:10px;right:12px;font-size:26px;line-height:1;border:0;background:none;color:var(--mut);cursor:pointer}
.form-relatar label{display:block;margin:12px 0;font-size:13px;color:var(--mut)}
.form-relatar textarea,.form-relatar input[type=email]{width:100%;box-sizing:border-box;font:inherit;color:inherit;
background:var(--card);border:1px solid var(--rule);border-radius:8px;padding:8px 10px;margin-top:4px;resize:vertical}
.form-relatar button[type=submit]{background:#c8102e;color:#fff;border:2px solid #c8102e;border-radius:6px;
padding:9px 16px;font:600 14px/1 var(--sans,system-ui);cursor:pointer}
.form-relatar button[type=submit]:disabled{opacity:.6;cursor:wait}
.nota{font-size:13px;color:var(--mut)}
.campo-oculto{position:absolute;left:-9999px;width:1px;height:1px;overflow:hidden}
@media print{.rep,.modal{display:none!important}}'''

def botao(fim=False):
    return (f'<div class="rep{" fim" if fim else ""}"><button type="button" data-relatar>'
            '<span aria-hidden="true">⚑</span> Relatar problema ou sugestão</button></div>')

def modal(relatorio):
    r = escape(relatorio, quote=True)
    return f'''<div id="modal-relatar" class="modal" hidden>
<div class="modal-caixa" role="dialog" aria-modal="true" aria-labelledby="modal-titulo">
<button type="button" class="fechar" id="modal-fechar" aria-label="Fechar">×</button>
<h3 id="modal-titulo">Relatar problema ou sugestão</h3>
<p class="nota">Sua mensagem é enviada por um serviço de terceiros (Web3Forms) direto ao operador do projeto;
esta página não guarda nem lê o que você escrever.</p>
<form id="form-relatar" class="form-relatar">
<label for="relatar-mensagem">Mensagem<textarea id="relatar-mensagem" name="message" required rows="5"></textarea></label>
<label for="relatar-email">Seu e-mail (opcional, para resposta)<input id="relatar-email" name="email" type="email"></label>
<input type="hidden" name="subject" value="Relatórios Saúde DF — {r} — relato ou sugestão">
<input type="hidden" name="from_name" value="Relatórios Saúde DF">
<input type="checkbox" name="botcheck" class="campo-oculto" tabindex="-1" autocomplete="off" aria-hidden="true">
<p><button type="submit">Enviar</button></p>
<p id="relatar-status" class="nota" role="status"></p>
</form></div></div>
<script>
(function () {{
  var CHAVE = "{CHAVE_WEB3FORMS}", RELATORIO = "{r}";
  var m = document.getElementById('modal-relatar'), f = document.getElementById('form-relatar'),
      st = document.getElementById('relatar-status'), origem = null;
  function secao() {{
    var s = [].slice.call(document.querySelectorAll('section[id]')), y = window.scrollY + 120, a = '';
    s.forEach(function (e) {{ if (e.offsetTop <= y) {{ a = e.id; }} }});
    return a;
  }}
  function abrir(ev) {{ origem = ev.currentTarget; st.textContent = ''; m.hidden = false;
    document.getElementById('relatar-mensagem').focus(); }}
  function fechar() {{ m.hidden = true; if (origem) {{ origem.focus(); }} }}
  [].forEach.call(document.querySelectorAll('[data-relatar]'), function (b) {{ b.addEventListener('click', abrir); }});
  document.getElementById('modal-fechar').addEventListener('click', fechar);
  m.addEventListener('click', function (ev) {{ if (ev.target === m) {{ fechar(); }} }});
  document.addEventListener('keydown', function (ev) {{ if (ev.key === 'Escape' && !m.hidden) {{ fechar(); }} }});
  f.addEventListener('submit', function (ev) {{
    ev.preventDefault();
    var bt = f.querySelector('button[type=submit]');
    if (f.botcheck.checked) {{ st.textContent = 'Mensagem enviada. Obrigado.'; f.reset(); return; }}
    var corpo = {{access_key: CHAVE, message: f.message.value, email: f.email.value,
      subject: f.subject.value, from_name: f.from_name.value,
      estado: JSON.stringify({{relatorio: RELATORIO, secao: secao(), pagina: location.href}})}};
    bt.disabled = true; st.textContent = 'Enviando…';
    fetch('https://api.web3forms.com/submit', {{method: 'POST',
      headers: {{'Content-Type': 'application/json', Accept: 'application/json'}}, body: JSON.stringify(corpo)}})
      .then(function (r) {{ return r.json(); }})
      .then(function (j) {{ bt.disabled = false;
        if (j.success) {{ st.textContent = 'Mensagem enviada. Obrigado.'; f.reset(); }}
        else {{ st.textContent = 'Não foi possível enviar: ' + (j.message || 'erro desconhecido') + '. Tente novamente.'; }} }})
      .catch(function (e) {{ bt.disabled = false;
        st.textContent = 'Não foi possível enviar: ' + e.message + '. Tente novamente.'; }});
  }});
}})();
</script>'''
