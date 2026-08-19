/* ── Navegação de abas ── */
const TAB_MAP = { desabafo: 0, identificar: 1, quiz: 2, recursos: 3, faq: 4, alertas: 5 };

/* ── Backend ── */
const API_BASE = '/api/v1';

async function apiFetch(path, options = {}) {
  try {
    const ctrl  = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), 3000);
    const res = await fetch(API_BASE + path, {
      headers: { 'Content-Type': 'application/json' },
      signal: ctrl.signal,
      ...options,
    });
    clearTimeout(timer);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch { return null; }
}

function switchTab(tab) {
  document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(b => { b.classList.remove('active'); b.setAttribute('aria-selected', 'false'); });
  document.getElementById('tab-' + tab).classList.add('active');
  const idx = TAB_MAP[tab];
  if (idx !== undefined) {
    const btns = document.querySelectorAll('.tab-btn');
    btns[idx].classList.add('active');
    btns[idx].setAttribute('aria-selected', 'true');
  }
  window.scrollTo({ top: 0, behavior: 'smooth' });
  if (tab === 'identificar' && !mapInitialized) setTimeout(initMap, 120);
  if (tab === 'identificar') initTimeline();
  if (tab === 'recursos')    initRecursos();
  if (tab === 'faq')         initFAQ();
  if (tab === 'alertas')     renderFeed();
}

/* ── Acordeão ── */
function toggleAcc(btn) {
  const item = btn.closest('.acc-item');
  const isOpen = item.classList.contains('open');
  document.querySelectorAll('.acc-item').forEach(i => i.classList.remove('open'));
  if (!isOpen) item.classList.add('open');
}

/* ── Contador de caracteres ── */
function updateCharCount(el, countId, max) {
  document.getElementById(countId).textContent = el.value.length;
}

/* ── Mood ── */
const moodMessages = {
  'triste':           'É normal sentir tristeza. Permita-se sentir, mas lembre-se de buscar apoio. Você não está sozinha/o.',
  'com raiva':        'Raiva é uma resposta legítima à injustiça. Canalize essa energia para buscar ajuda e tomar medidas seguras.',
  'com medo':         'O medo protege, mas não precisa paralisá-la/lo. Há pessoas e canais prontos para te apoiar com segurança.',
  'perdida/o':        'Está tudo bem não saber por onde começar. Dê um passo de cada vez — estamos aqui para ajudar.',
  'envergonhada/o':   'A vergonha não é sua — ela pertence a quem praticou o assédio. Você foi corajosa/o ao vir até aqui.',
  'aliviada/o':       'Dar nome ao que aconteceu já é um grande passo. Continue e busque o suporte que merece.',
  'esperançosa/o':    'Essa esperança é real. Com apoio certo, a situação pode mudar. Você está no caminho certo.',
};

document.getElementById('moodRow').addEventListener('click', e => {
  const btn = e.target.closest('.mood-btn');
  if (!btn) return;
  document.querySelectorAll('.mood-btn').forEach(b => b.classList.remove('selected'));
  btn.classList.add('selected');
  const mood = btn.dataset.mood;
  const fb = document.getElementById('moodFeedback');
  document.getElementById('moodFeedbackText').textContent = moodMessages[mood] || '';
  fb.style.display = 'flex';
});

/* ── Desabafo ── */
async function enviarDesabafo() {
  const txt = document.getElementById('desabafoText').value.trim();
  if (!txt) { alert('Escreva algo antes de registrar seu desabafo. 💙'); return; }

  apiFetch('/desabafos/', { method: 'POST', body: JSON.stringify({ texto: txt, anonimo: true }) });

  const classifEl = document.getElementById('assedioClassif');
  classifEl.dataset.texto = txt;

  document.getElementById('desabafoText').closest('.card').style.display = 'none';
  document.getElementById('desabafoSuccess').style.display = 'block';

  const classif = await apiFetch('/identificar-assedio/', {
    method: 'POST',
    body: JSON.stringify({ descricao_situacao: txt }),
  });
  if (classif?.resultado) {
    classifEl.innerHTML = `<span><i class="fa-solid fa-robot"></i></span><span>${classif.resultado}</span>`;
    classifEl.classList.remove('is-hidden');
    document.getElementById('btnFormalizar').classList.remove('is-hidden');
  }
}

function limparDesabafo() {
  document.getElementById('desabafoText').value = '';
  document.getElementById('desabafoCount').textContent = '0';
  document.querySelectorAll('.mood-btn').forEach(b => b.classList.remove('selected'));
  document.getElementById('moodFeedback').style.display = 'none';
}

function novoDesabafo() {
  document.getElementById('desabafoSuccess').style.display = 'none';
  document.querySelector('#tab-desabafo .card').style.display = '';
  const classifEl = document.getElementById('assedioClassif');
  classifEl.classList.add('is-hidden');
  classifEl.dataset.texto = '';
  document.getElementById('btnFormalizar').classList.add('is-hidden');
  document.getElementById('btnFormalizar').disabled = false;
  document.getElementById('formalizarConfirm').classList.add('is-hidden');
  limparDesabafo();
}

async function formalizarDenuncia() {
  const txt = document.getElementById('assedioClassif').dataset.texto || '';
  if (!txt) return;
  const btn = document.getElementById('btnFormalizar');
  btn.disabled = true;
  const result = await apiFetch('/denuncias/', {
    method: 'POST',
    body: JSON.stringify({ descricao: txt, anonimo: true }),
  });
  if (result?.id) {
    document.getElementById('formalizarConfirm').classList.remove('is-hidden');
    btn.classList.add('is-hidden');
  } else {
    btn.disabled = false;
  }
}

/* ── Quiz ── */
let qCurrent = 0;
const qTotal  = 8;
const qScores = [];

function quizNav(dir) {
  const questions = document.querySelectorAll('.quiz-question');
  const radios    = document.querySelectorAll(`input[name="q${qCurrent}"]`);
  const answered  = Array.from(radios).some(r => r.checked);

  if (dir === 1 && !answered) { alert('Selecione uma opção antes de avançar.'); return; }

  if (dir === 1) {
    const val = parseInt(document.querySelector(`input[name="q${qCurrent}"]:checked`).value);
    qScores[qCurrent] = val;
  }

  questions[qCurrent].style.display = 'none';
  qCurrent += dir;
  if (qCurrent < 0) qCurrent = 0;

  if (qCurrent >= qTotal) {
    mostrarResultadoQuiz();
    return;
  }

  questions[qCurrent].style.display = 'block';
  document.getElementById('qProgressLabel').textContent = `Pergunta ${qCurrent + 1} de ${qTotal}`;
  const pct = Math.round((qCurrent / qTotal) * 100);
  document.getElementById('qProgressPct').textContent = pct + '%';
  document.getElementById('qProgressBar').style.width = pct + '%';
  document.getElementById('qBtnBack').style.visibility = qCurrent === 0 ? 'hidden' : 'visible';
  document.getElementById('qBtnNext').textContent = qCurrent === qTotal - 1 ? 'Ver Resultado ✓' : 'Próxima →';
}

function mostrarResultadoQuiz() {
  document.getElementById('quizQuestions').style.display = 'none';
  document.getElementById('quizNav').style.display = 'none';
  document.getElementById('qProgressBar').style.width = '100%';
  document.getElementById('qProgressPct').textContent = '100%';

  const total  = qScores.reduce((a, b) => a + (b || 0), 0);
  const result = document.getElementById('quizResult');
  const circle = document.getElementById('resultCircle');
  const title  = document.getElementById('resultTitle');
  const desc   = document.getElementById('resultDesc');
  const alerta = document.getElementById('resultAlerta');

  if (total <= 3) {
    circle.className = 'result-circle result-ok';
    circle.textContent = '✅';
    title.textContent = 'Situação aparentemente segura';
    desc.textContent = 'Suas respostas não indicam sinais fortes de assédio no momento. Continue atenta/o e lembre-se: qualquer desconforto merece atenção. Fique segura/o e cuide-se!';
    alerta.style.display = 'none';
  } else if (total <= 9) {
    circle.className = 'result-circle result-atencao';
    circle.textContent = '⚠️';
    title.textContent = 'Sinal de atenção — fique alerta';
    desc.textContent = 'Suas respostas indicam situações que merecem atenção. Algumas experiências que você relatou podem configurar assédio. Conversar com alguém de confiança ou um profissional pode ajudar a esclarecer a situação.';
    alerta.style.display = 'none';
  } else {
    circle.className = 'result-circle result-alerta';
    circle.textContent = '🆘';
    title.textContent = 'Indicadores de assédio ou violência';
    desc.textContent = 'Suas respostas indicam que você pode estar em situação de assédio ou violência. Você não está sozinha/o e há apoio disponível. Busque ajuda agora — use os canais abaixo ou a aba Fazer Denúncia.';
    alerta.style.display = 'flex';
  }

  result.style.display = 'block';
  apiFetch('/quiz/resultado', { method: 'POST', body: JSON.stringify({ respostas: [...qScores] }) });
}

function resetQuiz() {
  qCurrent = 0;
  qScores.length = 0;
  document.querySelectorAll('.quiz-question').forEach((q, i) => {
    q.style.display = i === 0 ? '' : 'none';
    q.querySelectorAll('input[type=radio]').forEach(r => r.checked = false);
  });
  document.getElementById('quizResult').style.display = 'none';
  document.getElementById('quizQuestions').style.display = '';
  document.getElementById('quizNav').style.display = '';
  document.getElementById('qProgressLabel').textContent = 'Pergunta 1 de 8';
  document.getElementById('qProgressPct').textContent = '0%';
  document.getElementById('qProgressBar').style.width = '0%';
  document.getElementById('qBtnBack').style.visibility = 'hidden';
  document.getElementById('qBtnNext').textContent = 'Próxima →';
}

/* ── FAQ Search ── */
function filtrarFAQ(termo) {
  const t = termo.toLowerCase().trim();
  let visible = 0;
  document.querySelectorAll('.faq-item').forEach(item => {
    const txt = (item.dataset.text + ' ' + item.textContent).toLowerCase();
    const show = !t || txt.includes(t);
    item.classList.toggle('hidden', !show);
    if (show) visible++;
  });
  document.getElementById('faqEmpty').style.display = visible === 0 ? 'flex' : 'none';
}

/* ── Alertas ── */
const ALERTAS_KEY = 'fs_alertas';
const ALERTAS_VER = 2; // incrementar quando o seed mudar

const alertasSeed = [
  { id: 1,  tipo: 'Importunação Sexual',             cidade: 'São Paulo',        uf: 'SP', local: 'Metrô Linha 2-Verde',              desc: 'Relatos recorrentes de importunação sexual nos vagões entre as estações Paraíso e Ana Rosa nos horários de pico.',                                                urgencia: 'alta',  ts: Date.now() - 3600000,    confirmacoes: 18 },
  { id: 2,  tipo: 'Assédio Virtual / Cyberbullying', cidade: 'Rio de Janeiro',   uf: 'RJ', local: 'Instagram / WhatsApp',              desc: 'Perfis falsos criados para assediar mulheres com mensagens íntimas não solicitadas. Múltiplas vítimas relataram o mesmo padrão.',                                urgencia: 'media', ts: Date.now() - 18000000,   confirmacoes: 11 },
  { id: 3,  tipo: 'Violência Doméstica',              cidade: 'Belo Horizonte',   uf: 'MG', local: 'Bairro Santa Efigênia',             desc: 'Situação de violência doméstica em andamento relatada por vizinhas. Pedido de apoio e orientação à comunidade.',                                                 urgencia: 'alta',  ts: Date.now() - 7200000,    confirmacoes: 7  },
  { id: 4,  tipo: 'Perseguição (Stalking)',           cidade: 'Curitiba',         uf: 'PR', local: 'Bairro Água Verde',                 desc: 'Homem seguindo mulheres que saem do trabalho no período noturno. Comportamento identificado em mais de uma ocasião.',                                           urgencia: 'alta',  ts: Date.now() - 5400000,    confirmacoes: 9  },
  { id: 5,  tipo: 'Assédio Moral',                    cidade: 'Porto Alegre',     uf: 'RS', local: 'Centro Comercial Iguatemi',          desc: 'Funcionárias relatam assédio moral sistemático por parte de gerência. Situação já reportada ao RH sem resolução.',                                            urgencia: 'media', ts: Date.now() - 86400000,   confirmacoes: 5  },
  { id: 6,  tipo: 'Assédio Sexual',                   cidade: 'Salvador',         uf: 'BA', local: 'Orla de Ondina',                    desc: 'Grupo de homens abordando mulheres de forma agressiva na orla. Situação especialmente intensa nos finais de semana.',                                          urgencia: 'media', ts: Date.now() - 43200000,   confirmacoes: 14 },
  { id: 7,  tipo: 'Assédio Moral',                    cidade: 'Brasília',         uf: 'DF', local: 'Setor Bancário Sul — empresa privada', desc: 'Supervisora humilha funcionárias publicamente em reuniões, atribui erros alheios a elas e ameaça demissão sem justificativa. Pelo menos 5 relatos confirmados.', urgencia: 'media', ts: Date.now() - 10800000,   confirmacoes: 8  },
  { id: 8,  tipo: 'Importunação Sexual',              cidade: 'Recife',           uf: 'PE', local: 'Terminal Integrado de Passageiros',  desc: 'Homem encosta e faz comentários obscenos em mulheres que aguardam ônibus no período da tarde. Relatado por passageiras em diferentes dias.',                    urgencia: 'alta',  ts: Date.now() - 21600000,   confirmacoes: 12 },
  { id: 9,  tipo: 'Assédio Virtual / Cyberbullying',  cidade: 'Fortaleza',        uf: 'CE', local: 'TikTok / Telegram',                  desc: 'Grupo no Telegram compartilha fotos e vídeos íntimos de mulheres sem consentimento. Vítimas identificadas já acionaram a SaferNet.',                            urgencia: 'alta',  ts: Date.now() - 14400000,   confirmacoes: 22 },
  { id: 10, tipo: 'Violência Física',                 cidade: 'Manaus',           uf: 'AM', local: 'Bairro Compensa',                    desc: 'Mulher agredida fisicamente por parceiro em via pública. Vizinhos chamaram a PM. Vítima está em abrigo. Caso em acompanhamento pela Delegacia da Mulher.',    urgencia: 'alta',  ts: Date.now() - 28800000,   confirmacoes: 6  },
  { id: 11, tipo: 'Perseguição (Stalking)',            cidade: 'Campinas',         uf: 'SP', local: 'Universidade Estadual de Campinas',  desc: 'Ex-aluno persegue estudante dentro do campus, manda mensagens ameaçadoras e aparece em locais que ela frequenta. Caso registrado na ouvidoria da universidade.', urgencia: 'alta',  ts: Date.now() - 36000000,   confirmacoes: 17 },
  { id: 12, tipo: 'Assédio Sexual',                   cidade: 'Florianópolis',    uf: 'SC', local: 'Praia de Jurerê',                    desc: 'Homens abordam mulheres que estão sozinhas na praia, fazem comentários sexuais e seguem mesmo após pedido de afastamento. Situações repetidas nos fins de semana.', urgencia: 'media', ts: Date.now() - 50400000,   confirmacoes: 10 },
  { id: 13, tipo: 'Violência Doméstica',              cidade: 'Goiânia',          uf: 'GO', local: 'Setor Jardim América',               desc: 'Moradora relata agressões verbais e físicas frequentes. Tentou registrar BO, mas se sentiu intimidada. Vizinhos solicitam apoio de assistência social.',      urgencia: 'alta',  ts: Date.now() - 72000000,   confirmacoes: 4  },
  { id: 14, tipo: 'Assédio Moral',                    cidade: 'São Luís',         uf: 'MA', local: 'Hospital público regional',           desc: 'Enfermeiras relatam chefia que distribui tarefas degradantes apenas para mulheres, faz piadas sexistas e pune quem reclama com escalas piores.',              urgencia: 'media', ts: Date.now() - 93600000,   confirmacoes: 9  },
  { id: 15, tipo: 'Assédio Virtual / Cyberbullying',  cidade: 'Porto Velho',      uf: 'RO', local: 'Facebook / grupos escolares',         desc: 'Grupo de alunos cria memes ofensivos com fotos de colegas do sexo feminino e circula em grupos de turma. Direção da escola foi comunicada.',                   urgencia: 'baixa', ts: Date.now() - 108000000,  confirmacoes: 3  },
  { id: 16, tipo: 'Importunação Sexual',              cidade: 'Belém',            uf: 'PA', local: 'Ver-o-Peso — feira popular',          desc: 'Mulheres relatam apalpamentos e comentários sexuais na feira, especialmente em dias de maior movimento. Policiamento pedido por feirantes.',                  urgencia: 'media', ts: Date.now() - 57600000,   confirmacoes: 7  },
  { id: 17, tipo: 'Violência Física',                 cidade: 'Natal',            uf: 'RN', local: 'Bairro Lagoa Nova',                   desc: 'Mulher foi agredida com socos pelo companheiro após tentar terminar o relacionamento. Filho menor de idade presenciou. Medida protetiva solicitada.',         urgencia: 'alta',  ts: Date.now() - 45000000,   confirmacoes: 11 },
  { id: 18, tipo: 'Assédio Sexual',                   cidade: 'Vitória',          uf: 'ES', local: 'Escritório de advocacia — Centro',    desc: 'Advogada relata que sócio faz comentários sobre seu corpo e envia mensagens com conotação sexual. Dois outros funcionários testemunharam situações.',       urgencia: 'media', ts: Date.now() - 64800000,   confirmacoes: 8  },
];

function loadAlertas() {
  try {
    const ver   = parseInt(localStorage.getItem(ALERTAS_KEY + '_v') || '0');
    const saved = localStorage.getItem(ALERTAS_KEY);
    if (saved && ver === ALERTAS_VER) return JSON.parse(saved);
    localStorage.removeItem(ALERTAS_KEY);
    localStorage.setItem(ALERTAS_KEY + '_v', String(ALERTAS_VER));
    return alertasSeed.map(a => ({ ...a }));
  } catch { return alertasSeed.map(a => ({ ...a })); }
}

function saveAlertas(lista) {
  try {
    localStorage.setItem(ALERTAS_KEY, JSON.stringify(lista));
    localStorage.setItem(ALERTAS_KEY + '_v', String(ALERTAS_VER));
  } catch {}
}

function timeAgo(ts) {
  const diff = Date.now() - ts;
  const m = Math.floor(diff / 60000);
  if (m < 60)  return m <= 1 ? 'agora mesmo' : `${m} min atrás`;
  const h = Math.floor(m / 60);
  if (h < 24)  return `${h}h atrás`;
  return `${Math.floor(h / 24)}d atrás`;
}

const urgenciaLabel = { alta: 'Alta', media: 'Média', baixa: 'Baixa' };
const urgenciaClass = { alta: 'urgencia-tag-alta', media: 'urgencia-tag-media', baixa: 'urgencia-tag-baixa' };

let filtroAtivo = 'todos';

/* renderiza a lista atual de alertas no DOM (síncrono) */
function _paintFeed(lista) {
  const feed  = document.getElementById('alertaFeed');
  const vazio = document.getElementById('alertaVazio');
  if (!feed) return;
  const filtrados = lista.filter(a => {
    if (filtroAtivo === 'todos')    return true;
    if (filtroAtivo === '__alta__') return a.urgencia === 'alta';
    return a.tipo.toLowerCase().includes(filtroAtivo.toLowerCase());
  });
  vazio.classList.toggle('is-hidden', filtrados.length > 0);
  feed.innerHTML = filtrados.map(a => `
    <div class="alerta-card urgencia-borda-${a.urgencia}">
      <div class="alerta-header">
        <span class="alerta-tipo">${a.tipo}</span>
        <span class="urgencia-tag ${urgenciaClass[a.urgencia]}">
          <i class="fa-solid fa-circle"></i> ${urgenciaLabel[a.urgencia]}
        </span>
      </div>
      <div class="alerta-local">
        <i class="fa-solid fa-location-dot"></i>
        <strong>${a.cidade}, ${a.uf}</strong>${a.local ? ` — ${a.local}` : ''}
      </div>
      <p class="alerta-desc">${a.desc}</p>
      <div class="alerta-footer">
        <span class="alerta-ts"><i class="fa-regular fa-clock"></i> ${timeAgo(a.ts)}</span>
        <button class="alerta-confirmar" onclick="confirmarAlerta(${typeof a.id === 'string' ? `'${a.id}'` : a.id})" aria-label="Confirmar alerta">
          <i class="fa-solid fa-triangle-exclamation"></i> Confirmar <span class="conf-count">${a.confirmacoes}</span>
        </button>
      </div>
    </div>`).join('');
}

async function renderFeed() {
  let lista = loadAlertas().sort((a, b) => b.ts - a.ts);

  _paintFeed(lista); // renderiza imediatamente sem esperar o backend

  const backendData = await apiFetch('/alertas/');
  if (backendData?.length) {
    const backendAlertas = backendData
      .filter(a => !lista.some(l => l.desc === a.descricao))
      .map(a => {
        const loc = a.localizacao || '';
        const dashIdx = loc.indexOf('—');
        const cidadeUf = dashIdx >= 0 ? loc.slice(0, dashIdx).trim() : loc;
        const local    = dashIdx >= 0 ? loc.slice(dashIdx + 1).trim() : '';
        const commaIdx = cidadeUf.lastIndexOf(',');
        const cidade   = commaIdx >= 0 ? cidadeUf.slice(0, commaIdx).trim() : cidadeUf;
        const uf       = commaIdx >= 0 ? cidadeUf.slice(commaIdx + 1).trim().substring(0, 2) : '—';
        return {
          id: 'be_' + a.id, tipo: a.titulo,
          cidade, uf, local, desc: a.descricao,
          urgencia: 'media', ts: new Date(a.criado_em).getTime(), confirmacoes: 0,
        };
      });
    if (backendAlertas.length) {
      lista = [...backendAlertas, ...lista].sort((a, b) => b.ts - a.ts);
      _paintFeed(lista);
    }
  }
}

function filtrarAlertas(filtro) {
  filtroAtivo = filtro;
  document.querySelectorAll('.filter-btn').forEach(b =>
    b.classList.toggle('active', b.textContent.trim().toLowerCase().includes(
      filtro === '__alta__' ? 'urgente' : filtro === 'todos' ? 'todo' : filtro.toLowerCase()
    ))
  );
  renderFeed();
}

function confirmarAlerta(id) {
  const lista = loadAlertas();
  const a = lista.find(x => x.id === id);
  if (a) { a.confirmacoes++; saveAlertas(lista); renderFeed(); }
}

async function criarAlerta(e) {
  e.preventDefault();
  const tipo     = document.getElementById('alertaTipo').value;
  const cidade   = document.getElementById('alertaCidade').value.trim();
  const uf       = document.getElementById('alertaEstado').value;
  const local    = document.getElementById('alertaLocal').value.trim();
  const desc     = document.getElementById('alertaDesc').value.trim();
  const urgencia = document.querySelector('input[name="urgencia"]:checked')?.value || 'media';

  if (!tipo)   { alert('Selecione o tipo de abuso.'); return; }
  if (!cidade) { alert('Informe a cidade.'); return; }
  if (!uf)     { alert('Selecione o estado.'); return; }
  if (!desc)   { alert('Descreva a situação.'); return; }

  apiFetch('/alertas/', {
    method: 'POST',
    body: JSON.stringify({
      titulo: tipo, descricao: desc,
      localizacao: `${cidade}, ${uf}${local ? ' — ' + local : ''}`,
    }),
  });

  const lista = loadAlertas();
  lista.unshift({ id: Date.now(), tipo, cidade, uf, local, desc, urgencia, ts: Date.now(), confirmacoes: 1 });
  saveAlertas(lista);
  document.getElementById('alertaForm').reset();
  document.getElementById('alertaCount').textContent = '0';
  filtroAtivo = 'todos';
  document.querySelectorAll('.filter-btn').forEach((b, i) => b.classList.toggle('active', i === 0));
  renderFeed();
  document.getElementById('alertaFeed').scrollIntoView({ behavior: 'smooth' });
}

function resetAlertaForm() {
  document.getElementById('alertaForm').reset();
  document.getElementById('alertaCount').textContent = '0';
}

/* ── Linha do tempo ── */
let timelineLoaded = false;
async function initTimeline() {
  if (timelineLoaded) return;
  const data = await apiFetch('/linha-do-tempo/');
  if (!data?.length) return;
  timelineLoaded = true;
  const list = document.getElementById('timelineList');
  list.innerHTML = data
    .sort((a, b) => new Date(a.data_evento) - new Date(b.data_evento))
    .map(e => {
      const year = new Date(e.data_evento).getFullYear();
      return `<div class="tl-item">
        <div class="tl-dot"></div>
        <div class="tl-year">${year}</div>
        <div class="tl-title">${e.titulo}</div>
        ${e.descricao ? `<div class="tl-desc">${e.descricao}</div>` : ''}
      </div>`;
    }).join('');
  document.getElementById('timelineCard').classList.remove('is-hidden');
}

/* ── Recursos ── */
let recursosLoaded = false;
async function initRecursos() {
  if (recursosLoaded) return;
  const data = await apiFetch('/recursos/');
  if (!data?.length) return;
  recursosLoaded = true;
  const cats = {};
  data.forEach(r => { const c = r.categoria || 'Outros'; (cats[c] = cats[c] || []).push(r); });
  document.getElementById('recursosBackend').innerHTML = Object.entries(cats).map(([cat, items]) => `
    <div class="card">
      <h2><i class="fa-solid fa-link"></i> ${cat}</h2>
      <div class="resource-grid">
        ${items.map(r => {
          const tag  = r.link ? 'a' : 'div';
          const href = r.link ? ` href="${r.link}" target="_blank" rel="noopener"` : '';
          return `<${tag}${href} class="resource-card${r.link ? '' : ' no-cursor'}">
            <span class="rc-icon"><i class="fa-solid fa-circle-info"></i></span>
            <strong>${r.titulo}</strong>
            ${r.descricao ? `<span>${r.descricao}</span>` : ''}
            <span class="rc-badge">${cat}</span>
          </${tag}>`;
        }).join('')}
      </div>
    </div>`).join('');
}

/* ── FAQ dinâmico ── */
let faqLoaded = false;
async function initFAQ() {
  if (faqLoaded) return;
  const data = await apiFetch('/faq/');
  if (!data?.length) return;
  faqLoaded = true;
  const accordion = document.getElementById('faqAccordion');
  accordion.insertAdjacentHTML('beforeend',
    data
      .sort((a, b) => a.ordem - b.ordem)
      .map(f => `
        <div class="acc-item faq-item" data-text="${f.pergunta.toLowerCase()}">
          <button class="acc-header" onclick="toggleAcc(this)">
            <span class="acc-icon"><i class="fa-solid fa-circle-question"></i></span> ${f.pergunta}
            <span class="acc-chevron">▼</span>
          </button>
          <div class="acc-body"><p>${f.resposta}</p></div>
        </div>`).join('')
  );
}

/* ── Mapa ── */
let mapInitialized = false;
let leafletMap, markersLayer, heatLayer;
let currentMapMode = 'delegacias';

const deams = [
  { lat:-23.5505, lng:-46.6333, name:'DEAM – São Paulo Centro',    tel:'(11) 3392-9100', end:'Av. Paulista, 900 – Bela Vista' },
  { lat:-23.6273, lng:-46.6566, name:'DEAM – Santo André',         tel:'(11) 4438-1200', end:'R. Senador Fláquer, 452' },
  { lat:-22.9068, lng:-43.1729, name:'DEAM – Rio de Janeiro',      tel:'(21) 2332-2408', end:'R. Dom Manuel, 15 – Centro' },
  { lat:-22.8683, lng:-43.2785, name:'DEAM – Niterói',             tel:'(21) 2620-0748', end:'R. Visconde de Sepetiba, 990' },
  { lat:-19.9191, lng:-43.9386, name:'DEAM – Belo Horizonte',      tel:'(31) 3261-3197', end:'R. Guajajaras, 40 – Centro' },
  { lat:-15.7801, lng:-47.9292, name:'DEAM – Brasília',            tel:'(61) 3362-4563', end:'SCS Qd. 6 – Asa Sul' },
  { lat:-12.9714, lng:-38.5014, name:'DEAM – Salvador',            tel:'(71) 3116-0800', end:'Av. Oscar Pontes, 1247' },
  { lat: -3.7172, lng:-38.5433, name:'DEAM – Fortaleza',           tel:'(85) 3101-7300', end:'R. 24 de Maio, 860 – Centro' },
  { lat: -8.0476, lng:-34.8770, name:'DEAM – Recife',              tel:'(81) 3184-3500', end:'R. do Imperador, 209 – Boa Vista' },
  { lat:-30.0346, lng:-51.2177, name:'DEAM – Porto Alegre',        tel:'(51) 3289-2930', end:'R. dos Andradas, 1355 – Centro' },
  { lat:-25.4284, lng:-49.2733, name:'DEAM – Curitiba',            tel:'(41) 3233-9060', end:'R. Mar. Floriano Peixoto, 141' },
  { lat: -2.5307, lng:-44.3068, name:'DEAM – São Luís',            tel:'(98) 3212-2160', end:'Pça. João Lisboa, 10 – Centro' },
  { lat: -1.4558, lng:-48.4902, name:'DEAM – Belém',               tel:'(91) 3202-0610', end:'R. João Diogo, 100 – Cidade Velha' },
  { lat: -3.1190, lng:-60.0217, name:'DEAM – Manaus',              tel:'(92) 3212-4870', end:'Av. Ephigênio Salles, 1100' },
  { lat:-20.3155, lng:-40.3128, name:'DEAM – Vitória',             tel:'(27) 3636-0840', end:'R. Sete de Setembro, 490 – Centro' },
  { lat: -5.7793, lng:-35.2009, name:'DEAM – Natal',               tel:'(84) 3232-5999', end:'Av. Deodoro, 600 – Centro' },
  { lat: -7.1150, lng:-34.8641, name:'DEAM – João Pessoa',         tel:'(83) 3218-4000', end:'R. da República, 70 – Centro' },
  { lat: -9.6658, lng:-35.7350, name:'DEAM – Maceió',              tel:'(82) 3315-1800', end:'R. Sá e Albuquerque, 60' },
  { lat:-10.9111, lng:-37.0717, name:'DEAM – Aracaju',             tel:'(79) 3179-3800', end:'Av. Barão de Maruim, 867' },
  { lat: -5.0892, lng:-42.8019, name:'DEAM – Teresina',            tel:'(86) 3215-5400', end:'R. 24 de Janeiro, 165 – Centro' },
  { lat: -4.9609, lng:-37.3631, name:'DEAM – Mossoró',             tel:'(84) 3315-2200', end:'R. Felipe Camarão, 1177' },
  { lat:-29.6868, lng:-53.8023, name:'DEAM – Santa Maria (RS)',    tel:'(55) 3220-1940', end:'R. Floriano Peixoto, 1670' },
  { lat:-27.5954, lng:-48.5480, name:'DEAM – Florianópolis',       tel:'(48) 3665-4500', end:'R. Esteves Júnior, 68 – Centro' },
  { lat:-23.9035, lng:-46.1800, name:'DEAM – Santos',              tel:'(13) 3232-6060', end:'R. General Câmara, 23 – Centro' },
];

/* gera pontos dispersos para simular heatmap de ocorrências */
function spreadHeat(lat, lng, n, r, w) {
  const pts = [];
  for (let i = 0; i < n; i++) {
    const a = Math.random() * 2 * Math.PI;
    const d = Math.random() * r;
    pts.push([lat + d * Math.cos(a), lng + d * Math.sin(a), w * (.4 + Math.random() * .6)]);
  }
  return pts;
}

const heatData = [
  ...spreadHeat(-23.55, -46.63, 120, 1.8, 1.0),   // São Paulo
  ...spreadHeat(-22.91, -43.17, 100, 1.5, 0.9),   // Rio de Janeiro
  ...spreadHeat(-19.92, -43.94,  70, 1.2, 0.75),  // BH
  ...spreadHeat(-15.78, -47.93,  60, 1.0, 0.7),   // Brasília
  ...spreadHeat(-12.97, -38.50,  65, 1.0, 0.8),   // Salvador
  ...spreadHeat( -3.72, -38.54,  55, 0.9, 0.72),  // Fortaleza
  ...spreadHeat( -8.05, -34.88,  55, 0.8, 0.7),   // Recife
  ...spreadHeat(-30.03, -51.22,  50, 0.9, 0.68),  // Porto Alegre
  ...spreadHeat(-25.43, -49.27,  50, 0.9, 0.66),  // Curitiba
  ...spreadHeat( -1.46, -48.49,  40, 0.8, 0.6),   // Belém
  ...spreadHeat( -3.12, -60.02,  38, 0.8, 0.58),  // Manaus
  ...spreadHeat( -5.09, -42.80,  30, 0.7, 0.55),  // Teresina
  ...spreadHeat( -2.53, -44.31,  30, 0.7, 0.55),  // São Luís
  ...spreadHeat( -5.78, -35.20,  28, 0.6, 0.52),  // Natal
  ...spreadHeat(-27.60, -48.55,  30, 0.7, 0.5),   // Florianópolis
  ...spreadHeat(-20.32, -40.31,  28, 0.6, 0.5),   // Vitória
];

const deamIcon = L.divIcon({
  className: '',
  html: '<div style="width:20px;height:20px;background:#7b2d8b;border:3px solid #fff;border-radius:50%;box-shadow:0 2px 6px rgba(0,0,0,.4)"></div>',
  iconSize: [20, 20],
  iconAnchor: [10, 10],
  popupAnchor: [0, -12],
});

async function initMap() {
  if (mapInitialized) return;
  mapInitialized = true;

  leafletMap = L.map('mapContainer').setView([-14.24, -51.93], 4);

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    maxZoom: 18,
  }).addTo(leafletMap);

  markersLayer = L.layerGroup();

  let delegaciasData = deams;
  const backendDeams = await apiFetch('/delegacias/?apenas_especializadas=true');
  if (backendDeams?.length) {
    const mapped = backendDeams
      .filter(d => d.latitude && d.longitude)
      .map(d => ({ lat: d.latitude, lng: d.longitude, name: d.nome, tel: d.telefone || 'N/D', end: d.endereco }));
    if (mapped.length) delegaciasData = mapped;
  }

  delegaciasData.forEach(d => {
    const popup = `<strong>${d.name}</strong><br>${d.end}<br>
      <a href="tel:${d.tel.replace(/\D/g,'')}" style="color:#7b2d8b;font-weight:700">${d.tel}</a>`;
    L.marker([d.lat, d.lng], { icon: deamIcon }).bindPopup(popup).addTo(markersLayer);
  });
  markersLayer.addTo(leafletMap);

  heatLayer = L.heatLayer(heatData, { radius: 35, blur: 25, maxZoom: 8,
    gradient: { 0.3: '#22c55e', 0.6: '#f59e0b', 1.0: '#ef4444' } });
}

function switchMapTab(mode) {
  if (!leafletMap) return;
  if (mode === 'delegacias') {
    if (leafletMap.hasLayer(heatLayer)) leafletMap.removeLayer(heatLayer);
    markersLayer.addTo(leafletMap);
  } else {
    if (leafletMap.hasLayer(markersLayer)) leafletMap.removeLayer(markersLayer);
    heatLayer.addTo(leafletMap);
  }
  leafletMap.invalidateSize();
}

/* popula o feed na carga inicial sem esperar clique na aba */
document.addEventListener('DOMContentLoaded', () => renderFeed());
