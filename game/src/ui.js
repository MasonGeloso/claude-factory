import { SERVICES, UNIT_TYPES } from './data.js';

const $ = (id) => document.getElementById(id);
const serviceById = Object.fromEntries(SERVICES.map((s) => [s.id, s]));

export class UI {
  constructor(sim, onSelectUnit, onJump) {
    this.sim = sim;
    this.onSelectUnit = onSelectUnit; // (unit) -> select + focus chat
    this.onJump = onJump;             // (x, z) -> camera jump
    this.chatUnit = null;
    this.selected = [];
    this.commsLines = [];

    // top bar
    this.el = {
      agents: $('stat-agents'), working: $('stat-working'), blocked: $('stat-blocked'),
      tasks: $('stat-tasks'), tokens: $('stat-tokens'), clock: $('stat-clock'),
      comms: $('comms-lines'),
      chat: $('chat'), chatName: $('chat-name'), chatMeta: $('chat-meta'),
      chatTask: $('chat-task'), chatLog: $('chat-log'), chatText: $('chat-text'),
      chatPortrait: $('chat-portrait'),
      selection: $('selection'), cards: $('selection-cards'),
      inspector: $('inspector'), inspKicker: $('insp-kicker'), inspName: $('insp-name'),
      inspDesc: $('insp-desc'), inspRows: $('insp-rows'), inspCrew: $('insp-crew'),
      hint: $('hint'), help: $('help'), toasts: $('toasts'),
    };

    $('chat-close').addEventListener('click', () => this.closeChat());
    $('insp-close').addEventListener('click', () => this.closeInspector());
    $('chat-form').addEventListener('submit', (e) => {
      e.preventDefault();
      this.sendChat(this.el.chatText.value);
      this.el.chatText.value = '';
    });
    $('chat-quick').addEventListener('click', (e) => {
      const cmd = e.target.dataset?.cmd;
      if (cmd) this.sendChat(cmd);
    });

    // speed controls
    document.querySelectorAll('.spd[data-speed]').forEach((btn) => {
      btn.addEventListener('click', () => {
        sim.speed = Number(btn.dataset.speed);
        sim.paused = false;
        this.syncSpeedButtons();
      });
    });
    $('btn-pause').addEventListener('click', () => { sim.paused = !sim.paused; this.syncSpeedButtons(); });
    $('btn-help').addEventListener('click', () => this.toggleHelp());
    $('help').addEventListener('click', () => this.toggleHelp(false));
    window.addEventListener('keydown', (e) => {
      if (e.target.tagName === 'INPUT') {
        if (e.key === 'Escape') { e.target.blur(); this.closeChat(); }
        return;
      }
      if (e.key === 'h' || e.key === 'H') this.toggleHelp();
      if (e.key === 'p' || e.key === 'P') { sim.paused = !sim.paused; this.syncSpeedButtons(); }
      if (e.key === 'Escape') { this.closeChat(); this.closeInspector(); }
    });

    setTimeout(() => this.el.hint.classList.add('gone'), 14000);
  }

  syncSpeedButtons() {
    document.querySelectorAll('.spd[data-speed]').forEach((b) => {
      b.classList.toggle('active', !this.sim.paused && Number(b.dataset.speed) === this.sim.speed);
    });
    $('btn-pause').classList.toggle('active', this.sim.paused);
    $('btn-pause').textContent = this.sim.paused ? '▶' : '❚❚';
  }

  toggleHelp(force) {
    const show = force ?? this.el.help.classList.contains('hidden');
    this.el.help.classList.toggle('hidden', !show);
  }

  toast(text, ms = 2600) {
    const el = document.createElement('div');
    el.className = 'toast';
    el.textContent = text;
    this.el.toasts.appendChild(el);
    setTimeout(() => el.classList.add('fade'), ms);
    setTimeout(() => el.remove(), ms + 600);
  }

  // ── stats ──
  renderStats() {
    const s = this.sim.stats();
    this.el.agents.textContent = s.agents;
    this.el.working.textContent = s.working;
    this.el.blocked.textContent = s.blocked;
    this.el.tasks.textContent = s.tasks;
    this.el.tokens.textContent = (s.tokens / 1000).toFixed(1) + 'k';
    const mins = Math.floor(this.sim.clock / 60), secs = Math.floor(this.sim.clock % 60);
    this.el.clock.textContent = `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
  }

  // ── comms feed ──
  comms({ who, text, event = false }) {
    const line = document.createElement('div');
    line.className = `comms-line${event ? ' event' : ''}`;
    const mins = Math.floor(this.sim.clock / 60), secs = Math.floor(this.sim.clock % 60);
    const time = `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
    const whoHtml = who
      ? `<span class="comms-who" data-unit="${who.id}" style="color:${serviceById[who.service].css}">${who.name}</span>`
      : `<span class="comms-who" style="color:var(--faint)">OPS</span>`;
    line.innerHTML = `<span class="comms-time">${time}</span>${whoHtml}<span class="comms-text">${text}</span>`;
    const whoEl = line.querySelector('[data-unit]');
    if (whoEl) whoEl.addEventListener('click', () => {
      const u = this.sim.byId.get(whoEl.dataset.unit);
      if (u) this.onSelectUnit(u);
    });
    this.el.comms.appendChild(line);
    this.commsLines.push(line);
    while (this.commsLines.length > 7) this.commsLines.shift().remove();
  }

  // ── chat panel ──
  openChat(unit) {
    this.chatUnit = unit;
    unit.unread = 0;
    this.el.chat.classList.remove('hidden');
    this.closeInspector();
    const svc = serviceById[unit.service];
    this.el.chatName.textContent = unit.name;
    this.el.chatPortrait.textContent = UNIT_TYPES[unit.type].glyph;
    this.el.chatPortrait.style.color = svc.css;
    this.renderChatMeta();
    this.renderChatLog();
    if (unit.chat.length === 0) {
      unit.chat.push({ from: 'sys', text: `channel open — ${unit.name} / ${svc.repo}`, t: this.sim.clock });
      this.sim.greet(unit);
      this.renderChatLog();
    }
  }

  closeChat() {
    this.chatUnit = null;
    this.el.chat.classList.add('hidden');
  }

  renderChatMeta() {
    const u = this.chatUnit;
    if (!u) return;
    const svc = serviceById[u.service];
    this.el.chatMeta.innerHTML = `${UNIT_TYPES[u.type].label} · ${svc.name} · <span style="color:${statusCss(u.status)}">${u.status.toUpperCase()}</span>`;
    this.el.chatTask.textContent = `▸ TASK: ${u.task} — ${Math.round(u.progress * 100)}%`;
  }

  renderChatLog() {
    const u = this.chatUnit;
    if (!u) return;
    const log = this.el.chatLog;
    log.innerHTML = '';
    for (const m of u.chat.slice(-60)) {
      const div = document.createElement('div');
      div.className = `msg ${m.from}`;
      const who = m.from === 'you' ? 'OVERSEER' : m.from === 'them' ? u.name : '';
      div.innerHTML = m.from === 'sys'
        ? `<div class="msg-body">${m.text}</div>`
        : `<div class="msg-head">${who}</div><div class="msg-body">${m.text}</div>`;
      log.appendChild(div);
    }
    if (u.pendingReply) {
      const div = document.createElement('div');
      div.className = 'msg them msg-typing';
      div.innerHTML = `<div class="msg-head">${u.name}</div><div class="msg-body"></div>`;
      log.appendChild(div);
    }
    log.scrollTop = log.scrollHeight;
  }

  sendChat(text) {
    if (!text.trim() || !this.chatUnit) return;
    this.sim.handleMessage(this.chatUnit, text.trim());
    this.renderChatLog();
  }

  // called by sim when any unit's chat gets a new message
  chatMessage(unit) {
    if (this.chatUnit === unit) {
      this.renderChatLog();
      this.renderChatMeta();
    }
  }

  // ── selection tray ──
  renderSelection(units) {
    this.selected = units;
    this.el.hint.classList.toggle('gone', units.length > 0);
    if (!units.length) {
      this.el.selection.classList.add('hidden');
      return;
    }
    this.el.selection.classList.remove('hidden');
    this.el.cards.innerHTML = '';
    for (const u of units.slice(0, 12)) {
      const svc = serviceById[u.service];
      const card = document.createElement('div');
      card.className = 'ucard' + (units.length === 1 ? ' primary' : '');
      card.innerHTML = `
        <div class="ucard-top">
          <span class="ucard-glyph" style="color:${svc.css}">${UNIT_TYPES[u.type].glyph}</span>
          <span class="ucard-name">${u.name}</span>
          <span class="status-dot status-${u.status}"></span>
        </div>
        <div class="ucard-type">${UNIT_TYPES[u.type].label} · ${svc.id.toUpperCase()}</div>
        <div class="ucard-task">${u.task}</div>
        <div class="ucard-bar"><div class="ucard-fill" style="width:${Math.round(u.progress * 100)}%"></div></div>`;
      card.addEventListener('click', () => this.onSelectUnit(u));
      this.el.cards.appendChild(card);
    }
    if (units.length > 12) {
      const more = document.createElement('div');
      more.className = 'ucard';
      more.innerHTML = `<div class="ucard-name">+${units.length - 12} more</div>`;
      this.el.cards.appendChild(more);
    }
  }

  refreshSelectionCards() {
    if (this.selected.length) this.renderSelection(this.selected);
  }

  // ── inspector ──
  openInspector(building, units) {
    this.closeChat();
    const { service, module } = building.userData;
    const svc = serviceById[service];
    const mod = svc.modules.find((m) => m.id === module);
    this.el.inspector.classList.remove('hidden');
    this.el.inspKicker.textContent = `MODULE · ${svc.repo}`;
    this.el.inspKicker.style.color = svc.css;
    this.el.inspName.textContent = mod.name.toUpperCase();
    this.el.inspDesc.textContent = mod.desc;
    const crew = units.filter((u) => u.service === service && u.module === module);
    this.el.inspRows.innerHTML = `
      <div class="insp-row"><span>DISTRICT</span><b>${svc.name}</b></div>
      <div class="insp-row"><span>LINES OF CODE</span><b>${mod.loc.toLocaleString()}</b></div>
      <div class="insp-row"><span>HEALTH</span><b style="color:${mod.health > 0.85 ? 'var(--green)' : mod.health > 0.75 ? 'var(--amber)' : 'var(--red)'}">${Math.round(mod.health * 100)}%</b></div>
      <div class="insp-row"><span>CREW</span><b>${crew.length}</b></div>`;
    this.el.inspCrew.innerHTML = crew.length ? '' : '<div class="crew-line" style="color:var(--faint)">no one on site — RMB with units selected to assign</div>';
    for (const u of crew) {
      const line = document.createElement('div');
      line.className = 'crew-line';
      line.innerHTML = `<span class="status-dot status-${u.status}"></span><b>${u.name}</b><span class="crew-task">${u.task}</span>`;
      line.addEventListener('click', () => this.onSelectUnit(u));
      this.el.inspCrew.appendChild(line);
    }
  }

  closeInspector() {
    this.el.inspector.classList.add('hidden');
  }
}

function statusCss(status) {
  return {
    working: 'var(--green)', idle: 'var(--dim)', moving: 'var(--cyan)',
    blocked: 'var(--red)', reviewing: 'var(--violet)',
  }[status];
}
