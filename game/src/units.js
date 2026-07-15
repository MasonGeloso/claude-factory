import * as THREE from 'three';
import { CSS2DObject } from 'three/addons/renderers/CSS2DRenderer.js';
import { SERVICES, UNIT_TYPES, STATUS_COLORS } from './data.js';
import { rng, damp } from './util.js';

const serviceById = Object.fromEntries(SERVICES.map((s) => [s.id, s]));

// ── unit body factories: authored silhouettes per rank ─────────────────
function makeBody(type, tint) {
  const g = new THREE.Group();
  const mat = new THREE.MeshStandardMaterial({ color: 0x93a7d4, roughness: 0.45, metalness: 0.2, emissive: 0x2a3a5e, emissiveIntensity: 0.35 });
  const accent = new THREE.MeshStandardMaterial({ color: 0x10182c, emissive: tint, emissiveIntensity: 2.0, roughness: 0.35 });
  const band = new THREE.MeshStandardMaterial({ color: 0x10182c, emissive: tint, emissiveIntensity: 1.0, roughness: 0.5 });

  if (type === 'session') {
    // command unit: tall hex prism + shoulder cape ring + antenna
    const torso = new THREE.Mesh(new THREE.CylinderGeometry(0.8, 1.0, 2.6, 6), mat);
    torso.position.y = 1.5;
    const shoulder = new THREE.Mesh(new THREE.CylinderGeometry(1.15, 1.25, 0.4, 6), accent);
    shoulder.position.y = 2.55;
    const head = new THREE.Mesh(new THREE.SphereGeometry(0.55, 12, 10), mat);
    head.position.y = 3.35;
    const visor = new THREE.Mesh(new THREE.SphereGeometry(0.3, 10, 8), accent);
    visor.position.set(0, 3.4, 0.35);
    const mast = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.05, 1.4), mat);
    mast.position.y = 4.4;
    const tip = new THREE.Mesh(new THREE.SphereGeometry(0.14, 8, 6), accent);
    tip.position.y = 5.1;
    tip.name = 'antenna-tip';
    g.add(torso, shoulder, head, visor, mast, tip);
  } else if (type === 'agent') {
    // field engineer: capsule + backpack + visor stripe
    const torso = new THREE.Mesh(new THREE.CapsuleGeometry(0.62, 1.5, 6, 12), mat);
    torso.position.y = 1.7;
    const pack = new THREE.Mesh(new THREE.BoxGeometry(0.7, 1.0, 0.4), mat);
    pack.position.set(0, 1.8, -0.62);
    const belt = new THREE.Mesh(new THREE.CylinderGeometry(0.66, 0.66, 0.22, 12), band);
    belt.position.y = 1.15;
    g.add(belt);
    const packLight = new THREE.Mesh(new THREE.BoxGeometry(0.5, 0.15, 0.05), accent);
    packLight.position.set(0, 2.2, -0.84);
    const visor = new THREE.Mesh(new THREE.BoxGeometry(0.7, 0.22, 0.3), accent);
    visor.position.set(0, 2.35, 0.42);
    g.add(torso, pack, packLight, visor);
  } else if (type === 'subagent') {
    // scout drone: floating octahedron + halo
    const core = new THREE.Mesh(new THREE.OctahedronGeometry(0.62), mat);
    core.position.y = 1.6;
    core.name = 'hover-core';
    const halo = new THREE.Mesh(new THREE.TorusGeometry(0.75, 0.06, 6, 24), accent);
    halo.rotation.x = Math.PI / 2;
    halo.position.y = 1.6;
    halo.name = 'hover-halo';
    const eye = new THREE.Mesh(new THREE.SphereGeometry(0.16, 8, 6), accent);
    eye.position.set(0, 1.6, 0.55);
    eye.name = 'hover-eye';
    g.add(core, halo, eye);
  } else {
    // worker bot: squat box + treads + tool light
    const hull = new THREE.Mesh(new THREE.BoxGeometry(0.95, 0.85, 1.1), mat);
    hull.position.y = 0.85;
    const treadL = new THREE.Mesh(new THREE.BoxGeometry(0.28, 0.5, 1.3), new THREE.MeshStandardMaterial({ color: 0x18223c, roughness: 0.9 }));
    treadL.position.set(-0.55, 0.3, 0);
    const treadR = treadL.clone();
    treadR.position.x = 0.55;
    const lamp = new THREE.Mesh(new THREE.BoxGeometry(0.5, 0.18, 0.08), accent);
    lamp.position.set(0, 1.1, 0.58);
    g.add(hull, treadL, treadR, lamp);
  }

  g.traverse((o) => { if (o.isMesh) o.castShadow = true; });
  return g;
}

export class Unit {
  constructor(spec, scene) {
    Object.assign(this, spec); // id, name, type, service, module, task, status, parent, progress
    this.def = UNIT_TYPES[this.type];
    const service = serviceById[this.service];
    this.tint = new THREE.Color(service.color);

    this.group = new THREE.Group();
    this.group.userData = { kind: 'unit', id: this.id };
    this.body = makeBody(this.type, this.tint);
    this.body.scale.setScalar(this.def.scale);
    this.group.add(this.body);

    // status ring at the feet
    this.ring = new THREE.Mesh(
      new THREE.RingGeometry(0.9, 1.15, 24),
      new THREE.MeshBasicMaterial({ color: STATUS_COLORS[this.status], transparent: true, opacity: 0.85, side: THREE.DoubleSide })
    );
    this.ring.rotation.x = -Math.PI / 2;
    this.ring.position.y = 0.08;
    this.ring.scale.setScalar(this.def.scale);
    this.group.add(this.ring);

    // selection halo (hidden until selected)
    this.selRing = new THREE.Mesh(
      new THREE.RingGeometry(1.3, 1.45, 28),
      new THREE.MeshBasicMaterial({ color: 0xffb454, transparent: true, opacity: 0, side: THREE.DoubleSide })
    );
    this.selRing.rotation.x = -Math.PI / 2;
    this.selRing.position.y = 0.1;
    this.selRing.scale.setScalar(this.def.scale);
    this.group.add(this.selRing);

    // picking proxy: invisible cylinder so small units are clickable
    this.hit = new THREE.Mesh(
      new THREE.CylinderGeometry(1.4, 1.4, 5, 8),
      new THREE.MeshBasicMaterial({ visible: false })
    );
    this.hit.position.y = 2;
    this.hit.userData = { kind: 'unit', id: this.id };
    this.group.add(this.hit);

    // nameplate
    this.tagEl = document.createElement('div');
    this.tagEl.className = `tag ${this.status}`;
    this.tagEl.innerHTML = `
      <div class="tag-name"><span class="status-dot status-${this.status}"></span><span class="tag-title">${this.name}</span></div>
      <div class="tag-bar"><div class="tag-bar-fill" style="width:${(this.progress * 100) | 0}%"></div></div>
      <div class="tag-say"></div>`;
    this.tag = new CSS2DObject(this.tagEl);
    this.tag.position.y = 4.8 * this.def.scale + 0.8;
    this.group.add(this.tag);
    this.sayEl = this.tagEl.querySelector('.tag-say');
    this.barEl = this.tagEl.querySelector('.tag-bar-fill');
    this.dotEl = this.tagEl.querySelector('.status-dot');
    this.sayTimer = 0;

    // spawn position: near assigned building, jittered
    this.target = null;
    this.onArrive = null;
    this.selected = false;
    this.chat = [];
    this.unread = 0;
    this.phase = rng() * Math.PI * 2;

    scene.add(this.group);
  }

  get serviceDef() { return serviceById[this.service]; }

  setStatus(status) {
    if (this.status === status) return;
    this.status = status;
    this.ring.material.color.set(STATUS_COLORS[status]);
    this.tagEl.className = `tag ${status}${this.sayTimer > 0 ? ' saying' : ''}`;
    this.dotEl.className = `status-dot status-${status}`;
  }

  setSelected(sel) {
    this.selected = sel;
    this.selRing.material.opacity = sel ? 0.95 : 0;
  }

  say(text, duration = 4) {
    this.sayEl.textContent = text;
    this.sayTimer = duration;
    this.tagEl.classList.add('saying');
  }

  orderMove(x, z, onArrive = null) {
    this.target = new THREE.Vector3(x, 0, z);
    this.onArrive = onArrive;
    this.setStatus('moving');
  }

  update(dt, elapsed) {
    // speech bubble timeout (real time)
    if (this.sayTimer > 0) {
      this.sayTimer -= dt;
      if (this.sayTimer <= 0) this.tagEl.classList.remove('saying');
    }

    // movement
    if (this.target) {
      const p = this.group.position;
      const dx = this.target.x - p.x, dz = this.target.z - p.z;
      const dist = Math.hypot(dx, dz);
      if (dist < 0.4) {
        this.target = null;
        const cb = this.onArrive;
        this.onArrive = null;
        if (cb) cb(); else this.setStatus('idle');
      } else {
        const step = Math.min(dist, this.def.speed * dt);
        p.x += (dx / dist) * step;
        p.z += (dz / dist) * step;
        const yaw = Math.atan2(dx, dz);
        this.body.rotation.y = damp(this.body.rotation.y, yaw, 8, dt);
      }
    }

    // idle/working animation per rank
    const t = elapsed * 2 + this.phase;
    if (this.type === 'subagent') {
      const bob = Math.sin(t * 1.6) * 0.25;
      this.body.position.y = 0.4 + bob;
      const halo = this.body.getObjectByName('hover-halo');
      if (halo) halo.rotation.z = elapsed * 2.2;
      const core = this.body.getObjectByName('hover-core');
      if (core) core.rotation.y = elapsed * 1.4;
    } else if (this.target) {
      this.body.position.y = Math.abs(Math.sin(t * 4)) * 0.18; // walk bounce
    } else if (this.status === 'working') {
      this.body.position.y = Math.abs(Math.sin(t * 2.4)) * 0.06; // work bob
      this.body.rotation.y += Math.sin(t * 0.7) * 0.0015;
    } else {
      this.body.position.y = damp(this.body.position.y, 0, 6, dt);
    }

    // session antenna beacon pulse
    const tip = this.body.getObjectByName('antenna-tip');
    if (tip) tip.material.emissiveIntensity = 1.2 + Math.sin(elapsed * 3 + this.phase) * 0.8;

    // blocked: ring flashes
    if (this.status === 'blocked') {
      this.ring.material.opacity = 0.5 + Math.abs(Math.sin(elapsed * 4)) * 0.5;
    } else {
      this.ring.material.opacity = 0.85;
    }

    // selection ring slow spin
    if (this.selected) this.selRing.rotation.z = elapsed * 0.9;

    // progress bar
    if (this.status === 'working') this.barEl.style.width = `${(this.progress * 100) | 0}%`;
  }
}

export function spawnUnits(specs, scene, buildingByKey) {
  const units = specs.map((s) => new Unit(s, scene));
  for (const u of units) {
    const b = buildingByKey.get(`${u.service}/${u.module}`);
    const base = b ? b.userData.worldPos : new THREE.Vector3();
    const a = rng() * Math.PI * 2;
    const r = 4.5 + rng() * 3.5;
    u.group.position.set(base.x + Math.cos(a) * r, 1.6, base.z + Math.sin(a) * r);
    u.home = { x: u.group.position.x, z: u.group.position.z };
    u.wanderT = 10 + rng() * 35;
    u.body.rotation.y = rng() * Math.PI * 2;
  }
  return units;
}
