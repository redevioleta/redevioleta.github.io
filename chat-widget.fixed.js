/* ── Mensagem rotativa ── */
const comfortMessages = [
  "Você merece viver com paz, respeito, segurança e liberdade.",
  "Buscar ajuda não é sinal de fraqueza. É um passo de proteção.",
  "Você não precisa enfrentar uma situação de violência sozinha.",
  "Informação pode ajudar você a conhecer caminhos de apoio.",
  "Nenhuma forma de violência deve ser normalizada ou justificada."
];
let comfortIdx = 0;
setInterval(() => {
  comfortIdx = (comfortIdx + 1) % comfortMessages.length;
  const el = document.getElementById('comfortMessage');
  if (el) el.textContent = '\u201c' + comfortMessages[comfortIdx] + '\u201d';
}, 6500);

/* ── Chat simples ── */
/* Histórico de conversa — só em memória (nunca salvo em localStorage/
   banco de dados), para preservar a privacidade da pessoa usuária.
   É zerado ao fechar o chat ou acionar a saída rápida. */
let simpleChatHistory = [];
/* Token de sessão: invalida respostas pendentes ao fechar o chat. */
let chatSession = 0;

function openAssistant() {
  document.getElementById('assistantModal').style.display = 'block';
  setTimeout(() => { const i = document.getElementById('simpleUserInput'); if (i) i.focus(); }, 100);
}
function closeAssistant() {
  document.getElementById('assistantModal').style.display = 'none';
  pararFala();
  pararEscuta();
  chatSession++;
  simpleChatHistory = [];
}
window.addEventListener('click', function(e) {
  if (e.target === document.getElementById('assistantModal')) closeAssistant();
});
function handleSimpleEnter(e) {
  if (e.key === 'Enter') sendSimpleMessage();
}
function addSimpleMsg(text, cls) {
  const box = document.getElementById('simpleChatBox');
  const d = document.createElement('div');
  d.className = cls;
  d.textContent = text;
  box.appendChild(d);
  box.scrollTop = box.scrollHeight;
}

function respostaLocalDeFallback(text) {
  const q = text.toLowerCase();
  let r = 'Posso ajudar com informações sobre os recursos da Rede Violeta, canais de emergência, casos históricos ou formas de buscar apoio. Sou a Violeta! 💜';
  if (q.includes('perigo') || q.includes('socorro') || q.includes('amea') || q.includes('agredindo') || q.includes('agress'))
    r = 'Se você estiver em perigo imediato, priorize sua segurança. Se puder, vá para um local seguro e ligue 190. O Ligue 180 também oferece orientação e informações sobre a rede de atendimento.';
  else if (q.includes('180') || q.includes('denúncia') || q.includes('denuncia') || q.includes('orienta'))
    r = 'O Ligue 180 é a Central de Atendimento à Mulher. O serviço é gratuito e funciona 24 horas. Ele oferece orientação sobre direitos e serviços da rede de atendimento.';
  else if (q.includes('delegacia') || q.includes('deam'))
    r = 'A DEAM é a Delegacia Especializada de Atendimento à Mulher. Ela integra a rede de atendimento especializado. Use a aba Recursos para encontrar mais informações.';
  else if (q.includes('violênci') || q.includes('violenc'))
    r = 'Violência contra a mulher pode assumir diferentes formas: física, psicológica, sexual, patrimonial e moral. Se você estiver vivendo isso, procure uma pessoa de confiança ou um serviço especializado.';
  else if (q.includes('medo') || q.includes('sozinha') || q.includes('triste') || q.includes('ansio'))
    r = 'Sinto muito que você esteja passando por isso. Você merece ser ouvida e respeitada. Se for seguro, converse com alguém de confiança. Em uma emergência, ligue 190.';
  else if (q.includes('caso') || q.includes('angela') || q.includes('ângela') || q.includes('daniella') || q.includes('eloá') || q.includes('eloa') || q.includes('eliza') || q.includes('mércia') || q.includes('mercia'))
    r = 'Na aba “Conheça os Casos”, a Rede Violeta apresenta casos históricos de forma educativa: Ângela Diniz, Daniella Perez, Eloá Pimentel, Eliza Samudio e Mércia Nakashima.';
  else if (q.includes('lei') || q.includes('maria da penha') || q.includes('direito'))
    r = 'O Brasil possui legislação específica de proteção às mulheres, incluindo a Lei Maria da Penha. Para orientação jurídica, procure a Defensoria Pública ou serviço jurídico especializado.';
  else if (q.includes('site') || q.includes('rede violeta') || q.includes('projeto'))
    r = 'A Rede Violeta é um projeto acadêmico da Faculdade Cruzeiro do Sul. O objetivo é reunir informação, conscientização e caminhos de apoio relacionados à violência contra a mulher.';
  return r;
}

function mostrarDigitando() {
  const box = document.getElementById('simpleChatBox');
  const d = document.createElement('div');
  d.className = 'simple-bot-msg simple-typing';
  d.id = 'simpleTypingIndicator';
  d.textContent = 'Violeta está digitando…';
  box.appendChild(d);
  box.scrollTop = box.scrollHeight;
}
function removerDigitando() {
  const d = document.getElementById('simpleTypingIndicator');
  if (d) d.remove();
}

async function sendSimpleMessage() {
  const inp = document.getElementById('simpleUserInput');
  const text = inp.value.trim();
  if (!text) return;
  addSimpleMsg(text, 'simple-user-msg');
  inp.value = '';
  mostrarDigitando();
  const sessao = chatSession;
  const historicoEnviado = simpleChatHistory.slice();

  let resposta;
  try {
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), 20000);
    const res = await fetch('/api/v1/chat/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      signal: ctrl.signal,
      body: JSON.stringify({ mensagem: text, historico: historicoEnviado }),
    });
    clearTimeout(timer);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const dados = await res.json();
    resposta = dados.resposta;
  } catch (e) {
    /* Backend indisponível (ex.: site aberto via file://, sem servidor,
       ou falha de rede) — cai para as respostas locais por palavra-chave,
       para que o chat continue funcional mesmo offline. */
    resposta = respostaLocalDeFallback(text);
  }

  removerDigitando();
  if (sessao !== chatSession) return;
  addSimpleMsg(resposta, 'simple-bot-msg');
  falarResposta(resposta);

  simpleChatHistory.push({ role: 'user', content: text });
  simpleChatHistory.push({ role: 'assistant', content: resposta });
  if (simpleChatHistory.length > 16) simpleChatHistory = simpleChatHistory.slice(-16);
}

/* ════════════════════════════════════════════
   🔊 Voz: ouvir respostas da Violeta
   ════════════════════════════════════════════ */
let vozAtivada = false;

function toggleVoiceReply() {
  vozAtivada = !vozAtivada;
  const btn = document.getElementById('voiceReplyToggle');
  btn.classList.toggle('active', vozAtivada);
  btn.setAttribute('aria-pressed', String(vozAtivada));
  if (!vozAtivada) pararFala();
}

function falarResposta(texto) {
  if (!vozAtivada) return;
  falarTexto(texto);
}

function falarTexto(texto) {
  if (!('speechSynthesis' in window)) return;
  window.speechSynthesis.cancel();
  const utter = new SpeechSynthesisUtterance(texto);
  utter.lang = 'pt-BR';
  utter.rate = 1;
  window.speechSynthesis.speak(utter);
}

function pararFala() {
  if ('speechSynthesis' in window) window.speechSynthesis.cancel();
}

/* ════════════════════════════════════════════
   🎙️ Voz: falar com a Violeta (microfone)
   ════════════════════════════════════════════ */
let reconhecimento = null;
let escutando = false;

function getSpeechRecognition() {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  return SR ? new SR() : null;
}

function toggleMic() {
  if (escutando) { pararEscuta(); return; }
  if (!reconhecimento) reconhecimento = getSpeechRecognition();
  if (!reconhecimento) {
    addSimpleMsg('Seu navegador não suporta entrada por voz. Tente usar o Google Chrome ou digite sua mensagem.', 'simple-bot-msg');
    return;
  }
  reconhecimento.lang = 'pt-BR';
  reconhecimento.interimResults = false;
  reconhecimento.maxAlternatives = 1;

  reconhecimento.onstart = () => {
    escutando = true;
    document.getElementById('micBtn').classList.add('listening');
    document.getElementById('micBtn').setAttribute('aria-pressed', 'true');
    document.getElementById('voiceHint').style.display = 'block';
  };
  reconhecimento.onresult = (event) => {
    const texto = event.results[0][0].transcript;
    const inp = document.getElementById('simpleUserInput');
    inp.value = texto;
    sendSimpleMessage();
  };
  reconhecimento.onerror = () => { pararEscuta(); };
  reconhecimento.onend = () => { pararEscuta(); };

  try { reconhecimento.start(); } catch (e) { pararEscuta(); }
}

function pararEscuta() {
  escutando = false;
  if (reconhecimento) { try { reconhecimento.stop(); } catch (e) {} }
  const micBtn = document.getElementById('micBtn');
  const hint = document.getElementById('voiceHint');
  if (micBtn) { micBtn.classList.remove('listening'); micBtn.setAttribute('aria-pressed', 'false'); }
  if (hint) hint.style.display = 'none';
}

/* ════════════════════════════════════════════
   ♿ Acessibilidade
   ════════════════════════════════════════════ */
const A11Y_KEY = 'redeVioleta_a11y_prefs';
const A11Y_FONT_STEP = 2; /* px por nível */
const A11Y_FONT_MIN  = -2;
const A11Y_FONT_MAX  = 4;
let a11yFontLevel = 0;

function a11yLoadPrefs() {
  let prefs = {};
  try { prefs = JSON.parse(localStorage.getItem(A11Y_KEY) || '{}'); } catch (e) { prefs = {}; }

  a11yFontLevel = Number(prefs.fontLevel) || 0;
  document.documentElement.style.fontSize = (16 + a11yFontLevel * A11Y_FONT_STEP) + 'px';

  document.body.classList.toggle('a11y-high-contrast', !!prefs.highContrast);
  document.body.classList.toggle('a11y-reduce-motion', !!prefs.reduceMotion);
  document.body.classList.toggle('a11y-strong-focus', !!prefs.strongFocus);

  const elContrast = document.getElementById('a11yContrast');
  const elMotion    = document.getElementById('a11yMotion');
  const elFocus     = document.getElementById('a11yFocus');
  const elRead      = document.getElementById('a11yReadAloud');
  if (elContrast) elContrast.checked = !!prefs.highContrast;
  if (elMotion)   elMotion.checked   = !!prefs.reduceMotion;
  if (elFocus)    elFocus.checked    = !!prefs.strongFocus;
  if (elRead)     elRead.checked     = !!prefs.readAloud;
  if (prefs.readAloud) a11yAtivarLeituraClique(true);
}

function a11ySavePrefs(partial) {
  let prefs = {};
  try { prefs = JSON.parse(localStorage.getItem(A11Y_KEY) || '{}'); } catch (e) { prefs = {}; }
  prefs = Object.assign(prefs, partial);
  try { localStorage.setItem(A11Y_KEY, JSON.stringify(prefs)); } catch (e) {}
}

function toggleA11yPanel(force) {
  const panel = document.getElementById('a11yPanel');
  const fab   = document.getElementById('a11yFab');
  const abrir = typeof force === 'boolean' ? force : !panel.classList.contains('open');
  panel.classList.toggle('open', abrir);
  fab.setAttribute('aria-expanded', String(abrir));
}
window.addEventListener('click', function (e) {
  const panel = document.getElementById('a11yPanel');
  const fab   = document.getElementById('a11yFab');
  if (panel && panel.classList.contains('open') && !panel.contains(e.target) && e.target !== fab && !fab.contains(e.target)) {
    toggleA11yPanel(false);
  }
});

function a11yFont(direcao) {
  if (direcao === 0) a11yFontLevel = 0;
  else a11yFontLevel = Math.max(A11Y_FONT_MIN, Math.min(A11Y_FONT_MAX, a11yFontLevel + direcao));
  document.documentElement.style.fontSize = (16 + a11yFontLevel * A11Y_FONT_STEP) + 'px';
  a11ySavePrefs({ fontLevel: a11yFontLevel });
}

function a11yToggle(className, ativo) {
  document.body.classList.toggle(className, ativo);
  const map = { 'a11y-high-contrast': 'highContrast', 'a11y-reduce-motion': 'reduceMotion', 'a11y-strong-focus': 'strongFocus' };
  a11ySavePrefs({ [map[className]]: ativo });
}

function a11yReadAloudToggle(ativo) {
  a11ySavePrefs({ readAloud: ativo });
  a11yAtivarLeituraClique(ativo);
}

let a11yLeituraHandler = null;
function a11yAtivarLeituraClique(ativo) {
  if (ativo && !a11yLeituraHandler) {
    a11yLeituraHandler = function (e) {
      const alvo = e.target.closest('p, h1, h2, h3, li, span, button, a, label');
      if (!alvo) return;
      const texto = alvo.innerText && alvo.innerText.trim();
      if (texto) falarTexto(texto);
    };
    document.addEventListener('click', a11yLeituraHandler, true);
  } else if (!ativo && a11yLeituraHandler) {
    document.removeEventListener('click', a11yLeituraHandler, true);
    a11yLeituraHandler = null;
    pararFala();
  }
}

function a11yReset() {
  try { localStorage.removeItem(A11Y_KEY); } catch (e) {}
  a11yAtivarLeituraClique(false);
  document.body.classList.remove('a11y-high-contrast', 'a11y-reduce-motion', 'a11y-strong-focus');
  document.documentElement.style.fontSize = '';
  a11yFontLevel = 0;
  ['a11yContrast', 'a11yMotion', 'a11yFocus', 'a11yReadAloud'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.checked = false;
  });
}

document.addEventListener('DOMContentLoaded', a11yLoadPrefs);

/* ════════════════════════════════════════════
   ↗ Saída rápida
   ════════════════════════════════════════════ */
function saidaRapida() {
  /* Nunca mantemos o desabafo ou o histórico do chat salvos no navegador,
     mas por segurança limpamos qualquer conteúdo sensível visível antes de sair. */
  try {
    const desabafo = document.getElementById('desabafoText');
    if (desabafo) desabafo.value = '';
    const chatBox = document.getElementById('simpleChatBox');
    if (chatBox) chatBox.innerHTML = '';
    const chatInput = document.getElementById('simpleUserInput');
    if (chatInput) chatInput.value = '';
    chatSession++;
    simpleChatHistory = [];
    pararFala();
    pararEscuta();
  } catch (e) {}
  window.location.replace('https://www.google.com/search?q=clima+hoje');
}

let ultimoEscape = 0;
document.addEventListener('keydown', function (e) {
  if (e.key !== 'Escape') return;
  const modalAberto = document.getElementById('assistantModal') && document.getElementById('assistantModal').style.display === 'block';
  const painelAberto = document.getElementById('a11yPanel') && document.getElementById('a11yPanel').classList.contains('open');
  if (modalAberto) { closeAssistant(); return; }
  if (painelAberto) { toggleA11yPanel(false); return; }
  /* Segundo Escape em até 2s confirma a saída rápida */
  const agora = Date.now();
  if (agora - ultimoEscape <= 2000) { ultimoEscape = 0; saidaRapida(); return; }
  ultimoEscape = agora;
});
