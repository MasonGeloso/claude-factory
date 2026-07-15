import { SERVICES, CHATTER, REPLIES, EVENT_LINES, TASK_POOL, UNIT_TYPES } from './data.js';
import { rng, pick, fill, clamp } from './util.js';
import { terrainHeight } from './world.js';
import { sfx } from './audio.js';

const serviceById = Object.fromEntries(SERVICES.map((s) => [s.id, s]));

export class Sim {
  constructor(units, world, bus) {
    this.units = units;
    this.world = world;
    this.bus = bus;           // { comms(line), chatMessage(unit, msg), statsDirty() }
    this.speed = 1;
    this.paused = false;
    this.tasksDone = 0;
    this.tokensPerMin = 8200;
    this.clock = 0;           // shift time in game seconds
    this.chatterTimer = 4;
    this.eventTimer = 11;
    this.blockTimer = 30;
    this.byId = new Map(units.map((u) => [u.id, u]));
  }

  unitCtx(u) {
    return {
      name: u.name, module: this.moduleName(u), service: serviceById[u.service].name,
      task: u.task, status: u.status.toUpperCase(), progress: Math.round(u.progress * 100),
      target: '', ...{},
    };
  }

  moduleName(u) {
    const svc = serviceById[u.service];
    return svc.modules.find((m) => m.id === u.module)?.name ?? u.module;
  }

  // ── orders from the player ─────────────────────────────────────────
  orderMoveTo(u, x, z) {
    u.away = false;
    u.orderMove(x, z);
    u.say(fill(pick(REPLIES.move), { ...this.unitCtx(u), target: 'position' }), 2.5);
  }

  assignToBuilding(u, building) {
    const { service, module } = building.userData;
    const svc = serviceById[service];
    const mod = svc.modules.find((m) => m.id === module);
    const wp = building.userData.worldPos;
    const a = rng() * Math.PI * 2, r = 5 + rng() * 3;
    u.service = service;
    u.module = module;
    u.task = pick(TASK_POOL[service]);
    u.progress = 0;
    u.away = false;
    const tx = wp.x + Math.cos(a) * r, tz = wp.z + Math.sin(a) * r;
    u.orderMove(tx, tz, () => {
      u.home = { x: tx, z: tz };
      u.setStatus('working');
      this.bus.comms({ who: u, text: `On station at ${mod.name}. Starting: ${u.task}` });
    });
    u.say(fill(pick(REPLIES.assign), { ...this.unitCtx(u), target: mod.name }), 3);
  }

  moveToService(u, svc) {
    const a = rng() * Math.PI * 2, r = 10 + rng() * 8;
    u.orderMove(svc.pos[0] + Math.cos(a) * r, svc.pos[1] + Math.sin(a) * r, () => u.setStatus('idle'));
  }

  // ── player chat → unit reply ───────────────────────────────────────
  handleMessage(u, text) {
    u.chat.push({ from: 'you', text, t: this.clock });
    const lower = text.toLowerCase().trim();
    const ctx = this.unitCtx(u);
    let reply = null;
    let after = null;

    if (/\b(status|sitrep|report|how('s| is) it going|update)\b/.test(lower)) {
      reply = fill(pick(REPLIES.status), ctx);
    } else if (/\b(hold|stop|halt|pause|stand down)\b/.test(lower)) {
      reply = pick(REPLIES.hold);
      after = () => { u.target = null; u.setStatus('idle'); };
    } else if (/\b(resume|continue|back to work|go ahead|proceed)\b/.test(lower) && u.status !== 'blocked') {
      reply = fill(pick(REPLIES.resume), ctx);
      after = () => u.setStatus('working');
    } else if (/\b(approve|approved|unblock|proceed|yes do it|ship it|lgtm)\b/.test(lower)) {
      if (u.status === 'blocked') {
        reply = pick(REPLIES.approve);
        after = () => {
          u.setStatus('working');
          this.bus.comms({ who: u, text: `Unblocked by overseer, resuming ${ctx.task}.`, event: true });
          this.bus.statsDirty();
        };
      } else reply = pick(REPLIES.approveNoop);
    } else if (/work on (\w+)/.test(lower)) {
      const want = lower.match(/work on (\w+)/)[1];
      const found = this.findModule(want);
      if (found) {
        reply = fill(pick(REPLIES.assign), { ...ctx, target: found.mod.name });
        after = () => this.assignToBuilding(u, found.building);
      } else {
        reply = `No module "${want}" on my charts. Districts carry: ${SERVICES.map((s) => s.modules.map((m) => m.id).join('/')).join(', ')}.`;
      }
    } else if (/move to (\w+)/.test(lower)) {
      const want = lower.match(/move to (\w+)/)[1];
      const svc = SERVICES.find((s) => s.id.startsWith(want) || s.name.toLowerCase().includes(want));
      if (svc) {
        reply = fill(pick(REPLIES.move), { ...ctx, target: svc.name });
        after = () => this.moveToService(u, svc);
      } else {
        reply = `Unknown sector "${want}". I know: ${SERVICES.map((s) => s.id).join(', ')}.`;
      }
    } else if (/\b(hi|hello|hey|yo|o7)\b/.test(lower)) {
      reply = pick(REPLIES.greeting);
    } else {
      reply = pick(REPLIES.unknown);
    }

    // typing delay then reply
    const delay = 0.7 + rng() * 1.1;
    u.pendingReply = { text: reply, in: delay, after };
    return delay;
  }

  greet(u) {
    if (u.pendingReply) return;
    u.pendingReply = { text: pick(REPLIES.greeting), in: 0.6 + rng() * 0.6, after: null };
  }

  findModule(want) {
    for (const svc of SERVICES) {
      const mod = svc.modules.find((m) => m.id.startsWith(want) || m.name.toLowerCase().includes(want));
      if (mod) {
        const building = this.world.buildingByKey.get(`${svc.id}/${mod.id}`);
        if (building) return { svc, mod, building };
      }
    }
    return null;
  }

  deliverReply(u) {
    const { text, after } = u.pendingReply;
    u.pendingReply = null;
    u.chat.push({ from: 'them', text, t: this.clock });
    u.say(text.length > 90 ? text.slice(0, 88) + '…' : text, 4);
    after?.();
    sfx.message();
    this.bus.chatMessage(u);
  }

  // ── ambient behavior ───────────────────────────────────────────────
  tick(dt) {
    if (this.paused) return;
    const gdt = dt * this.speed;
    this.clock += gdt;

    for (const u of this.units) {
      // typing replies run on real-ish time scaled a bit
      if (u.pendingReply) {
        u.pendingReply.in -= dt;
        if (u.pendingReply.in <= 0) this.deliverReply(u);
      }

      if (u.status === 'working') {
        const rate = u.type === 'worker' ? 0.022 : u.type === 'subagent' ? 0.018 : 0.013;
        u.progress += rate * gdt * (0.7 + rng() * 0.6);
        if (u.progress >= 1) this.completeTask(u);
      }
    }

    // foot traffic: working units stroll to a neighboring building, dwell,
    // then walk home — the city reads as a place where people move around
    for (const u of this.units) {
      if (u.type === 'session' || u.status !== 'working' || u.target || u.pendingReply) continue;
      if (u.away) {
        u.dwellT -= gdt;
        if (u.dwellT <= 0) {
          u.away = false;
          u.orderMove(u.home.x, u.home.z, () => u.setStatus('working'));
        }
        continue;
      }
      u.wanderT = (u.wanderT ?? 20) - gdt;
      if (u.wanderT <= 0) {
        u.wanderT = 22 + rng() * 40;
        const svc = serviceById[u.service];
        const others = svc.modules.filter((m) => m.id !== u.module);
        if (!others.length) continue;
        const dest = pick(others);
        const b = this.world.buildingByKey.get(`${svc.id}/${dest.id}`);
        if (!b) continue;
        const wp = b.userData.worldPos;
        const a = rng() * Math.PI * 2, r = 4.5 + rng() * 2.5;
        u.orderMove(wp.x + Math.cos(a) * r, wp.z + Math.sin(a) * r, () => {
          u.setStatus('working');
          u.away = true;
          u.dwellT = 3 + rng() * 5;
          if (rng() < 0.3) u.say(`Syncing with the ${dest.name} crew.`, 3);
        });
      }
    }

    // sessions eventually unblock their crew if the overseer doesn't
    for (const u of this.units) {
      if (u.status === 'blocked') {
        u.blockedFor = (u.blockedFor ?? 0) + gdt;
        if (u.blockedFor > 75 + rng() * 30) {
          u.blockedFor = 0;
          u.setStatus('working');
          const boss = this.byId.get(u.parent);
          this.bus.comms({
            who: boss ?? u,
            text: boss ? `Made the call for ${u.name} — proceeding.` : 'Resolved my own blocker. Moving on.',
            event: true,
          });
          this.bus.statsDirty();
        }
      } else u.blockedFor = 0;
    }

    // idle hands find work: after a while, pick a module in the current district
    for (const u of this.units) {
      if (u.status === 'idle' && !u.target) {
        u.idleFor = (u.idleFor ?? 0) + gdt;
        if (u.idleFor > 18 + rng() * 20) {
          u.idleFor = 0;
          const svc = serviceById[u.service];
          const mod = pick(svc.modules);
          const building = this.world.buildingByKey.get(`${svc.id}/${mod.id}`);
          if (building) this.assignToBuilding(u, building);
        }
      } else u.idleFor = 0;
    }

    // ambient radio chatter
    this.chatterTimer -= gdt;
    if (this.chatterTimer <= 0) {
      this.chatterTimer = 5 + rng() * 9;
      const candidates = this.units.filter((u) => !u.pendingReply);
      const u = pick(candidates);
      const lines = CHATTER[u.status] ?? CHATTER.working;
      const text = fill(pick(lines), this.unitCtx(u));
      u.say(text, 3.5);
      this.bus.comms({ who: u, text });
    }

    // org events
    this.eventTimer -= gdt;
    if (this.eventTimer <= 0) {
      this.eventTimer = 14 + rng() * 18;
      const u = pick(this.units.filter((x) => x.type !== 'worker'));
      const text = fill(pick(EVENT_LINES), { name: u.name, service: serviceById[u.service].repo });
      this.bus.comms({ who: null, text, event: true });
      this.tokensPerMin = clamp(this.tokensPerMin + (rng() - 0.5) * 900, 4000, 16000);
    }

    // occasional blocker to give the player something to do
    this.blockTimer -= gdt;
    if (this.blockTimer <= 0) {
      this.blockTimer = 45 + rng() * 40;
      const workers = this.units.filter((u) => u.status === 'working' && u.type !== 'session');
      if (workers.length) {
        const u = pick(workers);
        u.setStatus('blocked');
        const text = fill(pick(CHATTER.blocked), this.unitCtx(u));
        u.say(text, 6);
        u.chat.push({ from: 'them', text, t: this.clock });
        u.unread++;
        sfx.blocked();
        this.bus.comms({ who: u, text, event: true });
        this.bus.chatMessage(u);
        this.bus.statsDirty();
      }
    }
  }

  completeTask(u) {
    this.tasksDone++;
    sfx.done();
    const doneLine = fill(pick(CHATTER.done), this.unitCtx(u));
    u.say(doneLine, 4);
    this.bus.comms({ who: u, text: doneLine, event: true });
    // brief review, then new task from the district pool
    u.setStatus('reviewing');
    u.progress = 0;
    setTimeout(() => {
      if (u.status !== 'reviewing') return;
      u.task = pick(TASK_POOL[u.service]);
      u.setStatus('working');
      this.bus.statsDirty();
    }, (2500 + rng() * 3500) / this.speed);
    this.bus.statsDirty();
  }

  // called every frame regardless of pause (visuals)
  updateUnits(dt, elapsed) {
    const gdt = this.paused ? 0 : dt * this.speed;
    for (const u of this.units) {
      u.update(gdt, elapsed);
      // settle onto plateaus / ground
      const targetY = terrainHeight(u.group.position.x, u.group.position.z);
      u.group.position.y += (targetY - u.group.position.y) * Math.min(1, dt * 10);
    }
  }

  stats() {
    let working = 0, blocked = 0;
    for (const u of this.units) {
      if (u.status === 'working') working++;
      if (u.status === 'blocked') blocked++;
    }
    return { agents: this.units.length, working, blocked, tasks: this.tasksDone, tokens: this.tokensPerMin };
  }
}
