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
/* Histórico de conversa — só em memória (nunca salvo em localStorage,
   banco de dados), para preservar a privacidade da pessoa usuária.
   É zerado ao fechar o chat ou acionar a saída rápida. */
let simpleChatHistory = [];

/* Token de sessão: invalida respostas pendentes ao fechar o chat. */
let chatSession = 0;

function openAssistant() {
  document.getElementById('assistantModal').style.display = 'block';
  setTimeout(() => {
    const i = document.getElementById('simpleUserInput');
    if (i) i.focus();
  }, 100);
}

function closeAssistant() {
  document.getElementById('assistantModal').style.display = 'none';
  pararFala();
  pararEscuta();
  chatSession++;
  simpleChatHistory = [];
  const box = document.getElementById('simpleChatBox');
  if (box) {
    const welcome = box.querySelector('.simple-bot-msg:first-child');
    box.replaceChildren(...(welcome ? [welcome] : []));
  }
}

window.addEventListener('click', function (e) {
  const modal = document.getElementById('assistantModal');
  if (modal && e.target === modal) closeAssistant();
});

function handleSimpleEnter(e) {
  if (e.key === 'Enter') sendSimpleMessage();
}

function addSimpleMsg(text, cls) {
  const box = document.getElementById('simpleChatBox');
  if (!box) return;

  const d = document.createElement('div');
  d.className = cls;
  d.textContent = text;
  box.appendChild(d);
  box.scrollTop = box.scrollHeight;
}

function respostaLocalDeFallback(text, language) {
  const q = (text || '').toLowerCase();
  const idioma = language || (typeof getSiteLanguage === 'function' ? getSiteLanguage() : 'pt');
  if (idioma === 'en') {
    if (/danger|help|threat|attack|hurt/.test(q)) return 'If you are in immediate danger, prioritize your safety. If you can, move to a safe place and call 190. The 180 hotline also provides guidance and information about support services.';
    if (/180|report|complaint|guidance/.test(q)) return 'The 180 hotline is Brazil’s Women’s Support Center. It is free and operates 24 hours a day, providing guidance on rights and support services.';
    if (/police station|deam/.test(q)) return 'A DEAM is a specialized police station for women. Open the Resources tab to find more information about specialized support services.';
    if (/violence|abuse|harassment/.test(q)) return 'Violence against women can be physical, psychological, sexual, financial, or moral. If this is happening to you, contact someone you trust or a specialized support service.';
    if (/afraid|fear|alone|sad|anxious/.test(q)) return 'I am sorry you are going through this. You deserve to be heard and respected. If it is safe, talk to someone you trust. In an emergency, call 190.';
    if (/case|angela|daniella|eloa|eliza|mercia/.test(q)) return 'The “Learn about the Cases” tab presents historical cases for educational purposes: Ângela Diniz, Daniella Perez, Eloá Pimentel, Eliza Samudio, and Mércia Nakashima.';
    if (/law|maria da penha|right/.test(q)) return 'Brazil has specific legislation to protect women, including the Maria da Penha Law. For legal guidance, contact the Public Defender’s Office or a specialized legal service.';
    if (/site|rede violeta|project/.test(q)) return 'Rede Violeta is an academic project by Faculdade Cruzeiro do Sul. It brings together information, awareness, and support options related to violence against women.';
    return 'I can help with information about Rede Violeta resources, emergency contacts, historical cases, or ways to seek support. I am Violeta! 💜';
  }
  if (idioma === 'es') {
    if (/peligro|ayuda|amenaz|agred|violencia/.test(q)) return 'Si estás en peligro inmediato, prioriza tu seguridad. Si puedes, ve a un lugar seguro y llama al 190. La línea 180 también ofrece orientación e información sobre la red de atención.';
    if (/180|denuncia|orienta/.test(q)) return 'La línea 180 es el Centro de Atención a las Mujeres de Brasil. Es gratuita y funciona las 24 horas. Ofrece orientación sobre derechos y servicios de apoyo.';
    if (/comisaría|policia|deam/.test(q)) return 'La DEAM es una comisaría especializada en la atención a las mujeres. Consulta la pestaña Recursos para obtener más información sobre los servicios especializados.';
    if (/acoso|violencia|abuso/.test(q)) return 'La violencia contra las mujeres puede ser física, psicológica, sexual, patrimonial o moral. Si estás viviendo esta situación, busca a alguien de confianza o un servicio especializado.';
    if (/miedo|sola|triste|ansio/.test(q)) return 'Siento mucho que estés pasando por esto. Mereces que te escuchen y te respeten. Si es seguro, habla con alguien de confianza. En una emergencia, llama al 190.';
    if (/caso|angela|daniella|eloa|eliza|mercia/.test(q)) return 'La pestaña “Conoce los casos” presenta casos históricos con fines educativos: Ângela Diniz, Daniella Perez, Eloá Pimentel, Eliza Samudio y Mércia Nakashima.';
    if (/ley|maria da penha|derecho/.test(q)) return 'Brasil cuenta con legislación específica para proteger a las mujeres, incluida la Ley Maria da Penha. Para recibir orientación jurídica, contacta con la Defensoría Pública o un servicio especializado.';
    if (/sitio|rede violeta|proyecto/.test(q)) return 'Rede Violeta es un proyecto académico de la Faculdade Cruzeiro do Sul. Reúne información, concienciación y opciones de apoyo frente a la violencia contra las mujeres.';
    return 'Puedo ayudarte con información sobre los recursos de Rede Violeta, teléfonos de emergencia, casos históricos o formas de buscar apoyo. ¡Soy Violeta! 💜';
  }

  let r = 'Posso ajudar com informações sobre os recursos da Rede Violeta, canais de emergência, casos históricos ou formas de buscar apoio. Sou a Violeta! 💜';

  if (q.includes('perigo') || q.includes('socorro') || q.includes('amea') || q.includes('agredindo') || q.includes('agress')) {
    r = 'Se você estiver em perigo imediato, priorize sua segurança. Se puder, vá para um local seguro e ligue 190. O Ligue 180 também oferece orientação e informações sobre a rede de atendimento.';
  } else if (q.includes('180') || q.includes('denúncia') || q.includes('denuncia') || q.includes('orienta')) {
    r = 'O Ligue 180 é a Central de Atendimento à Mulher. O serviço é gratuito e funciona 24 horas. Ele oferece orientação sobre direitos e serviços da rede de atendimento.';
  } else if (q.includes('delegacia') || q.includes('deam')) {
    r = 'A DEAM é a Delegacia Especializada de Atendimento à Mulher. Ela integra a rede de atendimento especializado. Use a aba Recursos para encontrar mais informações.';
  } else if (q.includes('violênci') || q.includes('violenc')) {
    r = 'Violência contra a mulher pode assumir diferentes formas: física, psicológica, sexual, patrimonial e moral. Se você estiver vivendo isso, procure uma pessoa de confiança ou um serviço especializado.';
  } else if (q.includes('medo') || q.includes('sozinha') || q.includes('triste') || q.includes('ansio')) {
    r = 'Sinto muito que você esteja passando por isso. Você merece ser ouvida e respeitada. Se for seguro, converse com alguém de confiança. Em uma emergência, ligue 190.';
  } else if (q.includes('caso') || q.includes('angela') || q.includes('ângela') || q.includes('daniella') || q.includes('eloá') || q.includes('eloa') || q.includes('eliza') || q.includes('mércia') || q.includes('mercia')) {
    r = 'Na aba “Conheça os Casos”, a Rede Violeta apresenta casos históricos de forma educativa: Ângela Diniz, Daniella Perez, Eloá Pimentel, Eliza Samudio e Mércia Nakashima.';
  } else if (q.includes('lei') || q.includes('maria da penha') || q.includes('direito')) {
    r = 'O Brasil possui legislação específica de proteção às mulheres, incluindo a Lei Maria da Penha. Para orientação jurídica, procure a Defensoria Pública ou serviço jurídico especializado.';
  } else if (q.includes('site') || q.includes('rede violeta') || q.includes('projeto')) {
    r = 'A Rede Violeta é um projeto acadêmico da Faculdade Cruzeiro do Sul. O objetivo é reunir informação, conscientização e caminhos de apoio relacionados à violência contra a mulher.';
  }

  return r;
}

function mostrarDigitando() {
  const box = document.getElementById('simpleChatBox');
  if (!box) return;

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
  const text = inp ? inp.value.trim() : '';

  if (!text) return;

  addSimpleMsg(text, 'simple-user-msg');
  if (inp) inp.value = '';

  mostrarDigitando();

  const sessao = chatSession;
  const historicoEnviado = simpleChatHistory.slice();
  const idioma = typeof getSiteLanguage === 'function' ? getSiteLanguage() : 'pt';
  let resposta = '';
  let timer;

  try {
    const ctrl = new AbortController();
    timer = setTimeout(() => ctrl.abort(), 20000);
    const res = await fetch(window.REDE_VIOLETA_API_BASE + '/chat/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      signal: ctrl.signal,
      body: JSON.stringify({ mensagem: text, historico: historicoEnviado, idioma })
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const dados = await res.json();
    resposta = dados && dados.resposta ? dados.resposta : respostaLocalDeFallback(text, idioma);
  } catch (e) {
    /* Backend indisponível — usa respostas locais para manter o chat acessível. */
    resposta = respostaLocalDeFallback(text, idioma);
  } finally {
    clearTimeout(timer);
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
(function () {
  'use strict';

  const root = typeof window !== 'undefined' ? window : globalThis;
  const doc = typeof document !== 'undefined' ? document : null;
  const A11Y_KEY = 'violeta-a11y-preferencias';
  const VOICE_KEY = 'violeta-voz-resposta';
  const defaults = { fontSize: 100, contrast: false, reducedMotion: false, focus: false, readOnClick: false };
  let recognition = null;
  let listening = false;
  let lastEscape = 0;
  let escapeTimer = null;

  function el(...selectors) {
    if (!doc) return null;
    for (const selector of selectors) {
      const node = doc.querySelector(selector);
      if (node) return node;
    }
    return null;
  }

  function texto(value) {
    return String(value == null ? '' : value).replace(/\s+/g, ' ').trim();
  }

  function idiomaAtual() {
    const language = typeof root.getSiteLanguage === 'function' ? root.getSiteLanguage() : 'pt';
    return language === 'en' ? 'en-US' : language === 'es' ? 'es-ES' : 'pt-BR';
  }

  function vozFeminina() {
    if (!root.speechSynthesis || typeof root.speechSynthesis.getVoices !== 'function') return null;
    const voices = root.speechSynthesis.getVoices();
    const language = idiomaAtual().split('-')[0];
    const languageVoices = voices.filter(function (voice) { return new RegExp('^' + language + '([-_]|$)', 'i').test(voice.lang || ''); });
    const indicadoresFemininos = /\b(female|woman|zira|luciana|francisca|maria|joana|fernanda|camila|helo[ií]sa|helena|vit[oó]ria|bruna|raquel|samantha|susan|karen|ana|aria|jenny|michelle|sara|paulina|monica|elena|laura|sofia|sabina|isabela)\b/i;
    return languageVoices.find(function (voice) { return indicadoresFemininos.test(voice.name || ''); })
      || languageVoices.find(function (voice) { return new RegExp(idiomaAtual().split('-')[1], 'i').test(voice.lang || ''); })
      || voices.find(function (voice) { return indicadoresFemininos.test(voice.name || ''); })
      || null;
  }

  function falarTexto(text) {
    const value = texto(text);
    if (!value || !root.speechSynthesis || typeof root.SpeechSynthesisUtterance !== 'function') return false;
    pararFala();
    const utterance = new root.SpeechSynthesisUtterance(value);
    utterance.lang = idiomaAtual();
    utterance.rate = 1;
    utterance.pitch = 1.08;
    utterance.voice = vozFeminina();
    root.speechSynthesis.speak(utterance);
    return true;
  }

  function falarResposta(text) {
    const source = text || el('[data-violeta-response]', '.mensagem-violeta:last-child', '.message.violeta:last-child', '#simpleChatBox .simple-bot-msg:last-child');
    const value = source && source.textContent != null ? source.textContent : source;
    if (root.localStorage && root.localStorage.getItem(VOICE_KEY) !== 'true') return false;
    return falarTexto(value);
  }

  function pararFala() {
    if (root.speechSynthesis && typeof root.speechSynthesis.cancel === 'function') root.speechSynthesis.cancel();
  }

  function toggleVoiceReply(force) {
    let current = false;
    try { current = root.localStorage && root.localStorage.getItem(VOICE_KEY) === 'true'; } catch (_) {}
    const enabled = typeof force === 'boolean' ? force : !current;
    try { if (root.localStorage) root.localStorage.setItem(VOICE_KEY, String(enabled)); } catch (_) {}
    const button = el('[data-voice-toggle]', '#toggleVoiceReply', '#voiceReplyToggle');
    if (button) {
      button.setAttribute('aria-pressed', String(enabled));
      button.classList.toggle('ativo', enabled);
      button.classList.toggle('active', enabled);
      button.setAttribute('aria-label', enabled
        ? 'Desativar respostas faladas da Violeta'
        : 'Ativar respostas faladas da Violeta');
      button.title = enabled ? 'Desativar respostas em voz alta' : 'Ouvir respostas em voz alta';
    }
    if (!enabled) pararFala();
    return enabled;
  }

  function getSpeechRecognition() {
    if (recognition) return recognition;
    const SpeechRecognition = root.SpeechRecognition || root.webkitSpeechRecognition;
    if (typeof SpeechRecognition !== 'function') return null;
    recognition = new SpeechRecognition();
    recognition.lang = idiomaAtual();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.onstart = function () { listening = true; atualizarMic(true); };
    recognition.onend = function () { listening = false; atualizarMic(false); };
    recognition.onerror = function (event) {
      listening = false;
      atualizarMic(false);
      addSimpleMsg(event && event.error === 'not-allowed'
        ? 'O acesso ao microfone foi bloqueado. Você pode digitar sua mensagem.'
        : 'Não foi possível usar o microfone. Você pode digitar sua mensagem.', 'simple-bot-msg');
    };
    recognition.onresult = function (event) {
      const result = event && event.results && event.results[0] && event.results[0][0];
      const input = el('#simpleUserInput', '#mensagem', '#message', 'textarea[name="message"]', 'input[name="message"]', '[contenteditable="true"]');
      if (input && result && result.transcript) {
        if ('value' in input) input.value = result.transcript;
        else input.textContent = result.transcript;
        input.dispatchEvent(new Event('input', { bubbles: true }));
        if (input.id === 'simpleUserInput') sendSimpleMessage();
      }
    };
    return recognition;
  }

  function atualizarMic(active) {
    const button = el('[data-mic-toggle]', '#toggleMic', '#microfone');
    if (button) {
      button.setAttribute('aria-pressed', String(active));
      button.classList.toggle('ativo', active);
      button.classList.toggle('listening', active);
    }
  }

  function toggleMic() {
    const mic = getSpeechRecognition();
    if (!mic) {
      addSimpleMsg('Seu navegador não oferece entrada por voz. Você pode digitar sua mensagem.', 'simple-bot-msg');
      return false;
    }
    if (listening) pararEscuta();
    else {
      toggleVoiceReply(true);
      mic.lang = idiomaAtual();
      try { mic.start(); }
      catch (error) {
        if (root.console && typeof root.console.warn === 'function') root.console.warn('Não foi possível iniciar o reconhecimento de voz.', error);
        addSimpleMsg('Não foi possível iniciar o microfone. Verifique a permissão do navegador ou digite sua mensagem.', 'simple-bot-msg');
        pararEscuta();
        return false;
      }
    }
    return true;
  }

  function pararEscuta() {
    if (recognition && listening) { try { recognition.stop(); } catch (_) {} }
    listening = false;
    atualizarMic(false);
  }

  function carregarA11y() {
    try { return Object.assign({}, defaults, JSON.parse(root.localStorage && root.localStorage.getItem(A11Y_KEY) || '{}')); }
    catch (_) { return Object.assign({}, defaults); }
  }

  function aplicarA11y(settings) {
    if (!doc || !doc.documentElement) return;
    const s = Object.assign({}, defaults, settings);
    doc.documentElement.style.setProperty('--violeta-font-scale', String(Number(s.fontSize) / 100));
    doc.documentElement.style.fontSize = String(Number(s.fontSize) || 100) + '%';
    doc.documentElement.classList.toggle('alto-contraste', !!s.contrast);
    doc.documentElement.classList.toggle('menos-movimento', !!s.reducedMotion);
    doc.documentElement.classList.toggle('foco-visivel', !!s.focus);
    doc.documentElement.classList.toggle('leitura-clique', !!s.readOnClick);
    if (doc.body) {
      doc.body.classList.toggle('a11y-high-contrast', !!s.contrast);
      doc.body.classList.toggle('a11y-reduce-motion', !!s.reducedMotion);
      doc.body.classList.toggle('a11y-strong-focus', !!s.focus);
    }

    const controls = {
      contrast: '#a11yContrast',
      reducedMotion: '#a11yMotion',
      focus: '#a11yFocus',
      readOnClick: '#a11yReadAloud',
    };
    Object.keys(controls).forEach(function (key) {
      const control = el(controls[key]);
      if (control) control.checked = !!s[key];
    });
  }

  function salvarA11y(settings) {
    const value = Object.assign({}, defaults, settings);
    try {
      if (root.localStorage) root.localStorage.setItem(A11Y_KEY, JSON.stringify(value));
    } catch (error) {
      if (root.console && typeof root.console.warn === 'function') root.console.warn('Não foi possível salvar as preferências de acessibilidade.', error);
    }
    aplicarA11y(value);
    return value;
  }

  function painelAcessibilidade(force) {
    const panel = el('[data-a11y-panel]', '#painelAcessibilidade', '#accessibilityPanel', '#a11yPanel');
    if (!panel) return false;
    const open = typeof force === 'boolean' ? force : !panel.classList.contains('open');
    panel.hidden = !open;
    panel.classList.toggle('open', open);
    panel.setAttribute('aria-hidden', String(!open));
    const button = el('#a11yFab');
    if (button) button.setAttribute('aria-expanded', String(open));
    return open;
  }

  function alterarFonte(delta) {
    const s = carregarA11y();
    s.fontSize = Math.max(80, Math.min(150, Number(s.fontSize) + Number(delta || 0)));
    return salvarA11y(s);
  }

  function definirPreferenciaAcessibilidade(name, enabled) {
    const allowed = ['contrast', 'reducedMotion', 'focus', 'readOnClick'];
    if (allowed.indexOf(name) === -1) throw new Error('Preferência de acessibilidade inválida: ' + name);
    const settings = carregarA11y();
    settings[name] = !!enabled;
    return salvarA11y(settings);
  }

  function resetAcessibilidade() {
    const settings = salvarA11y(Object.assign({}, defaults));
    const panel = el('#a11yPanel');
    if (panel) {
      panel.classList.remove('open');
      panel.hidden = false;
      panel.setAttribute('aria-hidden', 'true');
    }
    const button = el('#a11yFab');
    if (button) button.setAttribute('aria-expanded', 'false');
    return settings;
  }

  function saidaRapida() {
    const desabafo = el('#desabafoText');
    const alerta = el('#alertaDesc');
    const chatInput = el('#simpleUserInput');
    const chatBox = el('#simpleChatBox');
    if (desabafo) desabafo.value = '';
    if (alerta) alerta.value = '';
    if (chatInput) chatInput.value = '';
    if (chatBox) chatBox.replaceChildren();
    chatSession++;
    simpleChatHistory = [];
    pararFala();
    pararEscuta();
    if (root.location) root.location.replace('https://www.google.com/search?q=clima+hoje');
    return true;
  }

  function configurarA11y() {
    aplicarA11y(carregarA11y());
    if (!doc) return;
    let voiceEnabled = false;
    try { voiceEnabled = root.localStorage && root.localStorage.getItem(VOICE_KEY) === 'true'; } catch (_) {}
    toggleVoiceReply(voiceEnabled);
    doc.addEventListener('click', function (event) {
      const target = event.target && event.target.closest
        ? event.target.closest('[data-read-aloud], .ler-por-clique, .tab-pane p, .tab-pane h2, .tab-pane h3, .tab-pane li')
        : null;
      if (target && !target.closest('#a11yPanel, #assistantModal') && carregarA11y().readOnClick) falarTexto(target.textContent);
    });
    doc.addEventListener('keydown', function (event) {
      if (event.key !== 'Escape') return;
      const now = Date.now();
      if (now - lastEscape < 600) { clearTimeout(escapeTimer); lastEscape = 0; pararFala(); pararEscuta(); painelAcessibilidade(false); }
      else { lastEscape = now; clearTimeout(escapeTimer); escapeTimer = setTimeout(function () { lastEscape = 0; }, 600); }
    });
  }

  Object.assign(root, { A11Y_KEY, toggleVoiceReply, falarResposta, falarTexto, pararFala, getSpeechRecognition, toggleMic, pararEscuta, painelAcessibilidade, alterarFonte, definirPreferenciaAcessibilidade, aplicarA11y, resetAcessibilidade, saidaRapida });
  if (doc) {
    if (doc.readyState === 'loading') doc.addEventListener('DOMContentLoaded', configurarA11y, { once: true });
    else configurarA11y();
  }
}());