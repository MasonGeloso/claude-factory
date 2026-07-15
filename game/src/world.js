import * as THREE from 'three';
import { CSS2DObject } from 'three/addons/renderers/CSS2DRenderer.js';
import { SERVICES } from './data.js';
import { rng } from './util.js';

export const WORLD_RADIUS = 150;

const blinkers = [];   // { mat, phase } — pulsed in world.update

// ── shared canvas textures ─────────────────────────────────────────────
function makeWindowTexture(litRatio, cellW, cellH) {
  const c = document.createElement('canvas');
  c.width = 64; c.height = 128;
  const g = c.getContext('2d');
  g.fillStyle = '#0a0f1d';
  g.fillRect(0, 0, 64, 128);
  for (let y = 6; y < 122; y += cellH) {
    for (let x = 5; x < 58; x += cellW) {
      const lit = rng() < litRatio;
      g.fillStyle = lit ? (rng() < 0.75 ? '#ffc978' : '#9fe8f0') : '#141d33';
      g.fillRect(x, y, cellW - 4, cellH - 5);
    }
  }
  const tex = new THREE.CanvasTexture(c);
  tex.colorSpace = THREE.SRGBColorSpace;
  return tex;
}

function makeGroundTexture() {
  const c = document.createElement('canvas');
  c.width = c.height = 512;
  const g = c.getContext('2d');
  g.fillStyle = '#1a2742';
  g.fillRect(0, 0, 512, 512);
  for (let i = 0; i < 2600; i++) {
    const x = rng() * 512, y = rng() * 512, r = 4 + rng() * 22;
    const shade = 26 + rng() * 24;
    g.fillStyle = `rgba(${shade + 8}, ${shade + 18}, ${shade + 40}, ${0.06 + rng() * 0.1})`;
    g.beginPath(); g.arc(x, y, r, 0, Math.PI * 2); g.fill();
  }
  g.strokeStyle = 'rgba(110, 145, 200, 0.12)';
  g.lineWidth = 1;
  for (let i = 0; i <= 512; i += 32) {
    g.beginPath(); g.moveTo(i, 0); g.lineTo(i, 512); g.stroke();
    g.beginPath(); g.moveTo(0, i); g.lineTo(512, i); g.stroke();
  }
  const tex = new THREE.CanvasTexture(c);
  tex.wrapS = tex.wrapT = THREE.RepeatWrapping;
  tex.repeat.set(8, 8);
  tex.colorSpace = THREE.SRGBColorSpace;
  return tex;
}

function makeSky() {
  const c = document.createElement('canvas');
  c.width = 16; c.height = 256;
  const g = c.getContext('2d');
  const grad = g.createLinearGradient(0, 0, 0, 256);
  grad.addColorStop(0.0, '#05070f');
  grad.addColorStop(0.45, '#0c1226');
  grad.addColorStop(0.72, '#1a2848');
  grad.addColorStop(1.0, '#2c3f66');
  g.fillStyle = grad;
  g.fillRect(0, 0, 16, 256);
  for (let i = 0; i < 90; i++) {
    const y = rng() * 130;
    g.fillStyle = `rgba(220, 235, 255, ${0.25 + rng() * 0.6})`;
    g.fillRect(rng() * 16, y, 1, 1);
  }
  const tex = new THREE.CanvasTexture(c);
  tex.colorSpace = THREE.SRGBColorSpace;
  return new THREE.Mesh(
    new THREE.SphereGeometry(900, 24, 16),
    new THREE.MeshBasicMaterial({ map: tex, side: THREE.BackSide, fog: false })
  );
}

// ── small material helpers ─────────────────────────────────────────────
const std = (color, o = {}) => new THREE.MeshStandardMaterial({ color, roughness: 0.85, ...o });
const glow = (tint, intensity) =>
  new THREE.MeshStandardMaterial({ color: 0x10182c, emissive: tint, emissiveIntensity: intensity, roughness: 0.4 });

function addBlinker(group, x, y, z, color = 0xff6b6b) {
  const mat = new THREE.MeshStandardMaterial({ color: 0x10182c, emissive: color, emissiveIntensity: 2, roughness: 0.3 });
  const bulb = new THREE.Mesh(new THREE.SphereGeometry(0.16, 8, 6), mat);
  bulb.position.set(x, y, z);
  group.add(bulb);
  blinkers.push({ mat, phase: rng() * Math.PI * 2 });
}

function addRoofClutter(group, w, d, topY, tint) {
  const mat = std(0x1e2a4a, { roughness: 0.9 });
  const n = 2 + Math.floor(rng() * 3);
  for (let i = 0; i < n; i++) {
    const bw = 0.7 + rng() * 1.1, bh = 0.5 + rng() * 0.8, bd = 0.7 + rng() * 1.1;
    const box = new THREE.Mesh(new THREE.BoxGeometry(bw, bh, bd), mat);
    box.position.set((rng() - 0.5) * (w - bw - 0.6), topY + bh / 2, (rng() - 0.5) * (d - bd - 0.6));
    box.castShadow = true;
    group.add(box);
  }
  if (rng() < 0.75) {
    const mastH = 1.8 + rng() * 2.2;
    const mast = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.07, mastH, 5), mat);
    const mx = (rng() - 0.5) * (w * 0.5), mz = (rng() - 0.5) * (d * 0.5);
    mast.position.set(mx, topY + mastH / 2, mz);
    group.add(mast);
    addBlinker(group, mx, topY + mastH + 0.1, mz);
  }
  if (rng() < 0.5) {
    // rooftop vent pipe
    const pipe = new THREE.Mesh(new THREE.CylinderGeometry(0.16, 0.16, 1.1, 6), std(0x2a3a5e, { metalness: 0.5, roughness: 0.6 }));
    pipe.position.set((rng() - 0.5) * w * 0.5, topY + 0.55, (rng() - 0.5) * d * 0.5);
    group.add(pipe);
  }
}

function addPlinth(group, w, d) {
  const plinth = new THREE.Mesh(new THREE.BoxGeometry(w, 0.7, d), std(0x16203a, { roughness: 0.95 }));
  plinth.position.y = 0.35;
  plinth.receiveShadow = true;
  group.add(plinth);
}

function finishBuilding(group, service, module, topY, trim, trimBase) {
  const label = document.createElement('div');
  label.className = 'blab';
  label.textContent = module.name.toUpperCase();
  const tag = new CSS2DObject(label);
  tag.position.set(0, topY + 2.4, 0);
  group.add(tag);
  group.traverse((o) => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
  group.userData = { kind: 'building', service: service.id, module: module.id, trim, trimBase, height: topY };
  return group;
}

// ── building archetypes ────────────────────────────────────────────────

// stepped office tower — orchestration & state modules
function makeTower(service, module, tex) {
  const group = new THREE.Group();
  const tint = new THREE.Color(service.color);
  const h = 5 + Math.sqrt(module.loc) / 18;
  const w = 4.6 + rng() * 2.2;
  const d = 4.6 + rng() * 2.2;

  const bodyMat = new THREE.MeshStandardMaterial({
    color: 0x27314f, roughness: 0.85, metalness: 0.15,
    map: tex, emissive: 0xffffff, emissiveMap: tex, emissiveIntensity: 0.5,
  });
  const body = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), bodyMat);
  body.position.y = h / 2;
  group.add(body);

  // dark corner columns give the box an authored edge
  const colMat = std(0x131c31);
  for (const [sx, sz] of [[-1, -1], [-1, 1], [1, -1], [1, 1]]) {
    const col = new THREE.Mesh(new THREE.BoxGeometry(0.42, h + 0.2, 0.42), colMat);
    col.position.set(sx * (w / 2), (h + 0.2) / 2, sz * (d / 2));
    group.add(col);
  }

  let topY = h;
  if (h > 8) {
    const h2 = h * 0.45;
    const upper = new THREE.Mesh(new THREE.BoxGeometry(w * 0.62, h2, d * 0.62), bodyMat);
    upper.position.y = h + h2 / 2;
    group.add(upper);
    const trim2 = new THREE.Mesh(new THREE.BoxGeometry(w * 0.66, 0.3, d * 0.66), glow(tint, 0.4));
    trim2.position.y = h + h2 + 0.1;
    group.add(trim2);
    addRoofClutter(group, w * 0.6, d * 0.6, h + h2 + 0.25, tint);
    topY = h + h2;
  } else {
    addRoofClutter(group, w, d, h + 0.28, tint);
  }

  const trim = new THREE.Mesh(new THREE.BoxGeometry(w * 1.04, 0.35, d * 1.04), glow(tint, 0.4));
  trim.position.y = h + 0.1;
  group.add(trim);

  addPlinth(group, w * 1.35, d * 1.35);
  return finishBuilding(group, service, module, topY, trim, 0.4);
}

// wide glass slab — frontend & design modules
function makeSlab(service, module, tex) {
  const group = new THREE.Group();
  const tint = new THREE.Color(service.color);
  const w = 9 + rng() * 2.5;
  const h = 4.2 + Math.sqrt(module.loc) / 40;
  const d = 6.5 + rng() * 1.5;

  const glassMat = new THREE.MeshStandardMaterial({
    color: 0x2c3c66, roughness: 0.25, metalness: 0.55,
    map: tex, emissive: 0xffffff, emissiveMap: tex, emissiveIntensity: 0.42,
  });
  const body = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), glassMat);
  body.position.y = h / 2 + 0.4;
  group.add(body);

  // horizontal floor bands
  const bandMat = std(0x131c31);
  const floors = Math.max(2, Math.round(h / 1.6));
  for (let i = 1; i < floors; i++) {
    const band = new THREE.Mesh(new THREE.BoxGeometry(w + 0.12, 0.14, d + 0.12), bandMat);
    band.position.y = 0.4 + (h / floors) * i;
    group.add(band);
  }

  // dark roof caps hide the stretched window texture on top faces
  const roof = new THREE.Mesh(new THREE.BoxGeometry(w + 0.1, 0.16, d + 0.1), bandMat);
  roof.position.y = h + 0.4;
  group.add(roof);

  // offset penthouse block
  const ph = 1.6 + rng() * 1.2;
  const pent = new THREE.Mesh(new THREE.BoxGeometry(w * 0.42, ph, d * 0.7), glassMat);
  pent.position.set((rng() < 0.5 ? -1 : 1) * w * 0.22, h + 0.4 + ph / 2, 0);
  group.add(pent);
  const pentRoof = new THREE.Mesh(new THREE.BoxGeometry(w * 0.42 + 0.1, 0.14, d * 0.7 + 0.1), bandMat);
  pentRoof.position.set(pent.position.x, h + 0.4 + ph, 0);
  group.add(pentRoof);

  // entrance canopy strip, service-tinted
  const trim = new THREE.Mesh(new THREE.BoxGeometry(w * 0.55, 0.28, 1.4), glow(tint, 0.7));
  trim.position.set(0, 1.5, d / 2 + 0.55);
  group.add(trim);

  addRoofClutter(group, w * 0.8, d * 0.8, h + 0.42, tint);
  addPlinth(group, w * 1.2, d * 1.3);
  return finishBuilding(group, service, module, h + 0.4 + ph, trim, 0.7);
}

// silo cluster — data & billing modules
function makeSilo(service, module) {
  const group = new THREE.Group();
  const tint = new THREE.Color(service.color);
  const tankMat = std(0x3d5183, { metalness: 0.5, roughness: 0.42 });
  const n = 3;
  let maxH = 0;
  const positions = [[-2.2, -1], [2.2, -0.6], [0.2, 2]];
  positions.forEach(([x, z], i) => {
    const r = 1.5 + rng() * 0.7;
    const th = 4.5 + rng() * 3 + (module.loc / 6000);
    maxH = Math.max(maxH, th);
    const tank = new THREE.Mesh(new THREE.CylinderGeometry(r, r, th, 14), tankMat);
    tank.position.set(x, th / 2 + 0.7, z);
    group.add(tank);
    const cap = new THREE.Mesh(new THREE.SphereGeometry(r, 14, 8, 0, Math.PI * 2, 0, Math.PI / 2), tankMat);
    cap.position.set(x, th + 0.7, z);
    group.add(cap);
    // data stripe
    const stripe = new THREE.Mesh(new THREE.CylinderGeometry(r + 0.04, r + 0.04, 0.3, 14), glow(tint, i === 0 ? 0.9 : 0.5));
    stripe.position.set(x, th * (0.55 + rng() * 0.25), z);
    group.add(stripe);
    if (i === 0) group.userData_trim = stripe;
  });

  // connecting pipes
  const pipeMat = std(0x1e2a4a, { metalness: 0.5, roughness: 0.6 });
  const pipe1 = new THREE.Mesh(new THREE.CylinderGeometry(0.18, 0.18, 4.4, 6), pipeMat);
  pipe1.rotation.z = Math.PI / 2;
  pipe1.position.set(0, 2.6, -0.8);
  group.add(pipe1);
  const pipe2 = new THREE.Mesh(new THREE.CylinderGeometry(0.14, 0.14, 3.4, 6), pipeMat);
  pipe2.rotation.set(Math.PI / 2, 0, Math.PI / 6);
  pipe2.position.set(1.2, 1.6, 0.6);
  group.add(pipe2);

  // pump house
  const pump = new THREE.Mesh(new THREE.BoxGeometry(2.2, 1.4, 1.8), std(0x1e2a4a));
  pump.position.set(-0.2, 1.4, -2.6);
  group.add(pump);
  addBlinker(group, 0.2, maxH + 1.5, 2, 0xffb454);

  addPlinth(group, 8.2, 7.6);
  const trim = group.userData_trim;
  delete group.userData_trim;
  return finishBuilding(group, service, module, maxH + 1.4, trim, 0.9);
}

// comms spire — edge & observability modules
function makeSpire(service, module) {
  const group = new THREE.Group();
  const tint = new THREE.Color(service.color);
  const mastH = 9 + Math.sqrt(module.loc) / 25;

  const base = new THREE.Mesh(new THREE.BoxGeometry(3.4, 2.6, 3.4), std(0x27314f));
  base.position.y = 1.3 + 0.5;
  group.add(base);
  const baseTrim = new THREE.Mesh(new THREE.BoxGeometry(3.5, 0.24, 3.5), glow(tint, 0.5));
  baseTrim.position.y = 3.2;
  group.add(baseTrim);

  // lattice mast: outer thin + inner core
  const mast = new THREE.Mesh(new THREE.CylinderGeometry(0.34, 0.6, mastH, 6, 1, true), std(0x1e2a4a, { side: THREE.DoubleSide }));
  mast.position.y = 3.3 + mastH / 2;
  group.add(mast);
  const core = new THREE.Mesh(new THREE.CylinderGeometry(0.1, 0.1, mastH + 0.8, 5), std(0x131c31));
  core.position.y = 3.3 + mastH / 2;
  group.add(core);

  // crossbars
  for (let i = 1; i <= 3; i++) {
    const bar = new THREE.Mesh(new THREE.BoxGeometry(1.7, 0.1, 0.1), std(0x1e2a4a));
    bar.position.y = 3.3 + (mastH / 4) * i;
    bar.rotation.y = i * 1.1;
    group.add(bar);
  }

  // dishes
  for (let i = 0; i < 2; i++) {
    const dishGroup = new THREE.Group();
    const dish = new THREE.Mesh(
      new THREE.SphereGeometry(0.9, 12, 8, 0, Math.PI * 2, 0, Math.PI / 3),
      std(0x93a7d4, { metalness: 0.4, roughness: 0.5, side: THREE.DoubleSide })
    );
    dish.rotation.x = Math.PI / 2.3;
    dishGroup.add(dish);
    const yy = 3.3 + mastH * (0.45 + i * 0.28);
    dishGroup.position.set(i === 0 ? 0.75 : -0.7, yy, i === 0 ? 0.3 : -0.25);
    dishGroup.rotation.y = i === 0 ? 0.6 : 3.6;
    group.add(dishGroup);
  }

  // emissive ring near top + blinker at tip
  const halo = new THREE.Mesh(new THREE.TorusGeometry(0.62, 0.07, 6, 18), glow(tint, 1.2));
  halo.rotation.x = Math.PI / 2;
  halo.position.y = 3.3 + mastH * 0.9;
  group.add(halo);
  addBlinker(group, 0, 3.3 + mastH + 0.55, 0);

  addPlinth(group, 4.6, 4.6);
  return finishBuilding(group, service, module, 3.3 + mastH, halo, 1.2);
}

// fab hall — CI & deploy modules
function makeWorks(service, module, tex) {
  const group = new THREE.Group();
  const tint = new THREE.Color(service.color);
  const w = 9.5, d = 6.4, h = 3.4;

  const hallMat = new THREE.MeshStandardMaterial({
    color: 0x27314f, roughness: 0.8, metalness: 0.2,
    map: tex, emissive: 0xffffff, emissiveMap: tex, emissiveIntensity: 0.35,
  });
  const hall = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), hallMat);
  hall.position.y = h / 2 + 0.5;
  group.add(hall);

  // barrel-vault roof segments
  const vaultMat = std(0x1e2a4a, { metalness: 0.35, roughness: 0.6 });
  for (let i = -1; i <= 1; i++) {
    const vault = new THREE.Mesh(
      new THREE.CylinderGeometry(d / 6.2, d / 6.2, w * 0.94, 12, 1, false, 0, Math.PI),
      vaultMat
    );
    vault.rotation.set(0, 0, Math.PI / 2);
    vault.position.set(0, h + 0.5, i * (d / 3.1));
    group.add(vault);
  }

  // chimneys with warm emissive collars
  for (let i = 0; i < 2; i++) {
    const ch = 2.6 + rng() * 1.4;
    const x = -w / 2 + 1.3, z = i === 0 ? -d / 4 : d / 4;
    const chimney = new THREE.Mesh(new THREE.CylinderGeometry(0.42, 0.5, ch, 8), std(0x1e2a4a));
    chimney.position.set(x, h + 0.5 + ch / 2, z);
    group.add(chimney);
    const collar = new THREE.Mesh(new THREE.CylinderGeometry(0.46, 0.46, 0.22, 8), glow(0xffb454, 1.2));
    collar.position.set(x, h + 0.5 + ch - 0.2, z);
    group.add(collar);
  }

  // side gantry crane arm
  const gantry = new THREE.Mesh(new THREE.BoxGeometry(0.24, 4.4, 0.24), std(0x131c31));
  gantry.position.set(w / 2 + 1.1, 2.7, -1);
  group.add(gantry);
  const arm = new THREE.Mesh(new THREE.BoxGeometry(3.2, 0.2, 0.2), std(0x131c31));
  arm.position.set(w / 2 - 0.2, 4.8, -1);
  group.add(arm);

  // service-tinted door
  const trim = new THREE.Mesh(new THREE.BoxGeometry(2.6, 2.1, 0.18), glow(tint, 0.55));
  trim.position.set(1.6, 1.55, d / 2 + 0.1);
  group.add(trim);

  addBlinker(group, w / 2 + 1.1, 5.1, -1, 0xffb454);
  addPlinth(group, w * 1.18, d * 1.3);
  return finishBuilding(group, service, module, h + 1.6, trim, 0.55);
}

const ARCHETYPES = {
  warehouse: makeSilo, ingest: makeSilo, billing: makeSilo,
  cache: makeSilo, queue: makeSilo, memory: makeSilo, artifacts: makeSilo,
  router: makeSpire, proxy: makeSpire, ratelimit: makeSpire, observability: makeSpire,
  telemetry: makeSpire, search: makeSpire, webhooks: makeSpire, notifications: makeSpire,
  dashboard: makeSlab, editor: makeSlab, design: makeSlab,
  admin: makeSlab, transcripts: makeSlab,
  ci: makeWorks, deploy: makeWorks, sandbox: makeWorks, migrations: makeWorks,
};

function makeBuilding(service, module, texPool) {
  const builder = ARCHETYPES[module.id] ?? makeTower;
  const tex = texPool[Math.floor(rng() * texPool.length)];
  return builder(service, module, tex);
}

// ── plaza props ────────────────────────────────────────────────────────
function addPlazaProps(group, tint, R, E) {
  // lamp posts around the plaza — count scales with district size
  const poleMat = std(0x223050, { metalness: 0.4, roughness: 0.6 });
  const nLamps = Math.max(3, Math.round(R / 7));
  for (let i = 0; i < nLamps; i++) {
    const a = (i / nLamps) * Math.PI * 2 + 1.2 + (rng() - 0.5) * 0.4;
    const r = R * (0.3 + rng() * 0.1);
    const pole = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.12, 3.2, 6), poleMat);
    pole.position.set(Math.cos(a) * r, E + 1.6, Math.sin(a) * r);
    group.add(pole);
    const bulb = new THREE.Mesh(
      new THREE.SphereGeometry(0.22, 8, 6),
      new THREE.MeshStandardMaterial({ color: 0x10182c, emissive: 0xffc978, emissiveIntensity: 1.6, roughness: 0.3 })
    );
    bulb.position.set(Math.cos(a) * r, E + 3.3, Math.sin(a) * r);
    group.add(bulb);
  }

  // supply crates
  const crateMat = std(0x2a3a5e, { roughness: 0.9 });
  const crateTint = glow(tint, 0.35);
  const nCrates = Math.max(4, Math.round(R / 5));
  for (let i = 0; i < nCrates; i++) {
    const a = rng() * Math.PI * 2;
    const r = R * (0.72 + rng() * 0.16);
    const s = 0.6 + rng() * 0.7;
    const crate = new THREE.Mesh(new THREE.BoxGeometry(s, s, s), rng() < 0.3 ? crateTint : crateMat);
    crate.position.set(Math.cos(a) * r, E + s / 2, Math.sin(a) * r);
    crate.rotation.y = rng() * Math.PI;
    crate.castShadow = true;
    group.add(crate);
  }
}

// ── district layout ────────────────────────────────────────────────────
const PLAZA_R = 8;

function layoutBuildings(n, R) {
  const golden = Math.PI * (3 - Math.sqrt(5));
  const start = rng() * Math.PI * 2;
  const pts = [];
  for (let i = 0; i < n; i++) {
    const t = (i + 0.6) / n;
    const r = PLAZA_R + (R * 0.84 - PLAZA_R) * Math.sqrt(t);
    const a = start + i * golden + (rng() - 0.5) * 0.4;
    pts.push({ x: Math.cos(a) * r, z: Math.sin(a) * r });
  }
  // relax overlaps apart, keep everything on the plateau and off the plaza
  const minD = 13;
  for (let iter = 0; iter < 60; iter++) {
    for (let i = 0; i < n; i++) {
      for (let j = i + 1; j < n; j++) {
        const dx = pts[j].x - pts[i].x, dz = pts[j].z - pts[i].z;
        const d = Math.hypot(dx, dz) || 0.01;
        if (d < minD) {
          const push = ((minD - d) / 2) / d;
          pts[i].x -= dx * push; pts[i].z -= dz * push;
          pts[j].x += dx * push; pts[j].z += dz * push;
        }
      }
    }
    for (const p of pts) {
      const r = Math.hypot(p.x, p.z) || 0.01;
      const rMax = R * 0.86 - 3.5;
      if (r > rMax) { p.x *= rMax / r; p.z *= rMax / r; }
      if (r < PLAZA_R) { const k = PLAZA_R / r; p.x *= k; p.z *= k; }
    }
  }
  return pts;
}

// ── districts ──────────────────────────────────────────────────────────
function makeDistrict(service, texPool) {
  const group = new THREE.Group();
  group.position.set(service.pos[0], 0, service.pos[1]);
  const tint = new THREE.Color(service.color);
  const R = service.radius, E = service.elev;

  const plate = new THREE.Mesh(
    new THREE.CylinderGeometry(R, R + 1.5 + E, E, 48),
    std(0x223252, { roughness: 0.9 })
  );
  plate.position.y = E / 2;
  plate.receiveShadow = true;
  group.add(plate);

  const rim = new THREE.Mesh(
    new THREE.TorusGeometry(R - 0.3, 0.18, 8, 64),
    glow(tint, 0.65)
  );
  rim.rotation.x = -Math.PI / 2;
  rim.position.y = E + 0.02;
  group.add(rim);

  // buildings packed on a jittered golden-angle spiral, relaxed apart —
  // scales from 3 modules to 20+ without two districts sharing a layout
  const buildings = [];
  const spots = layoutBuildings(service.modules.length, R);
  service.modules.forEach((module, i) => {
    const p = spots[i];
    const b = makeBuilding(service, module, texPool);
    b.position.set(p.x, E, p.z);
    const facing = Math.atan2(p.z, p.x);
    b.rotation.y = -facing + Math.PI / 2 + (rng() - 0.5) * 0.5;
    group.add(b);
    buildings.push(b);
  });

  const pylon = new THREE.Mesh(
    new THREE.CylinderGeometry(0.35, 0.55, 7, 6),
    std(0x3a4f78, { roughness: 0.6, metalness: 0.4 })
  );
  pylon.position.y = E + 3.5;
  group.add(pylon);

  const beacon = new THREE.Mesh(new THREE.OctahedronGeometry(0.9), glow(tint, 1.6));
  beacon.position.y = E + 8;
  group.add(beacon);

  addPlazaProps(group, tint, R, E);

  const el = document.createElement('div');
  el.className = 'dlab';
  el.innerHTML = `${service.name}<small>${service.repo}</small>`;
  el.style.color = service.css;
  const title = new CSS2DObject(el);
  title.position.y = E + 19.5;
  group.add(title);

  group.userData = { kind: 'district', service: service.id, beacon, beaconBaseY: E + 8 };
  return { group, buildings };
}

// ── roads ──────────────────────────────────────────────────────────────
function makeRoad(from, to) {
  const ax = from[0], az = from[1], bx = to[0], bz = to[1];
  const len = Math.hypot(bx - ax, bz - az);
  const angle = Math.atan2(bz - az, bx - ax);
  const group = new THREE.Group();
  group.position.set((ax + bx) / 2, 0, (az + bz) / 2);
  group.rotation.y = -angle;

  const road = new THREE.Mesh(new THREE.PlaneGeometry(len, 5.5), std(0x131c31, { roughness: 0.95 }));
  road.rotation.x = -Math.PI / 2;
  road.position.y = 0.06;
  road.receiveShadow = true;
  group.add(road);

  const line = new THREE.Mesh(
    new THREE.PlaneGeometry(len, 0.3),
    new THREE.MeshBasicMaterial({ color: 0x4a628f, transparent: true, opacity: 0.5 })
  );
  line.rotation.x = -Math.PI / 2;
  line.position.y = 0.08;
  group.add(line);

  return group;
}

// ── scatter props (instanced) ──────────────────────────────────────────
function scatterProps(scene) {
  const inDistrict = (x, z) =>
    SERVICES.some((s) => Math.hypot(x - s.pos[0], z - s.pos[1]) < s.radius + 8);

  const rockGeo = new THREE.ConeGeometry(1, 3.2, 5);
  const rockMat = std(0x1d2946, { roughness: 0.7, metalness: 0.3, emissive: 0x2b4a6e, emissiveIntensity: 0.15 });
  const rocks = new THREE.InstancedMesh(rockGeo, rockMat, 160);
  const m = new THREE.Matrix4();
  let placed = 0, guard = 0;
  while (placed < 160 && guard++ < 3000) {
    const a = rng() * Math.PI * 2;
    const r = 30 + rng() * (WORLD_RADIUS - 34);
    const x = Math.cos(a) * r, z = Math.sin(a) * r;
    if (inDistrict(x, z)) continue;
    const s = 0.5 + rng() * 1.8;
    m.makeRotationY(rng() * Math.PI * 2);
    m.setPosition(x, s * 1.6 * 0.5, z);
    m.scale(new THREE.Vector3(s, s * (0.7 + rng()), s));
    rocks.setMatrixAt(placed++, m);
  }
  rocks.count = placed;
  rocks.castShadow = true;
  scene.add(rocks);
}

// ── move order marker ──────────────────────────────────────────────────
export class MoveMarker {
  constructor(scene) {
    this.ring = new THREE.Mesh(
      new THREE.RingGeometry(0.6, 0.9, 32),
      new THREE.MeshBasicMaterial({ color: 0xffb454, transparent: true, opacity: 0, side: THREE.DoubleSide })
    );
    this.ring.rotation.x = -Math.PI / 2;
    this.ring.position.y = 0.15;
    this.t = 1;
    scene.add(this.ring);
  }
  ping(x, z, color = 0xffb454) {
    this.ring.position.set(x, terrainHeight(x, z) + 0.15, z);
    this.ring.material.color.set(color);
    this.t = 0;
  }
  update(dt) {
    if (this.t >= 1) { this.ring.material.opacity = 0; return; }
    this.t = Math.min(1, this.t + dt * 1.6);
    const s = 0.5 + this.t * 3.2;
    this.ring.scale.set(s, s, 1);
    this.ring.material.opacity = 0.9 * (1 - this.t);
  }
}

export function terrainHeight(x, z) {
  for (const s of SERVICES) {
    if (Math.hypot(x - s.pos[0], z - s.pos[1]) < s.radius) return s.elev;
  }
  return 0;
}

// ── build world ────────────────────────────────────────────────────────
export function buildWorld(scene) {
  blinkers.length = 0;

  // a district must be big enough to seat all its modules — grow radius
  // with module count so a 20-module monorepo becomes a true city
  for (const s of SERVICES) {
    const needed = Math.ceil((Math.sqrt(PLAZA_R * PLAZA_R + s.modules.length * 50) + 3.5) / 0.86);
    s.radius = Math.max(s.radius, needed);
  }
  scene.fog = new THREE.Fog(0x0c1226, 160, 520);
  scene.add(makeSky());

  scene.add(new THREE.HemisphereLight(0x4d6ea6, 0x131c30, 1.6));
  scene.add(new THREE.AmbientLight(0x2a3a5e, 0.35));

  const key = new THREE.DirectionalLight(0xffd9a0, 2.0);
  key.position.set(90, 130, 60);
  key.castShadow = true;
  key.shadow.mapSize.set(2048, 2048);
  key.shadow.camera.left = -170; key.shadow.camera.right = 170;
  key.shadow.camera.top = 170; key.shadow.camera.bottom = -170;
  key.shadow.camera.far = 420;
  key.shadow.bias = -0.0004;
  scene.add(key);

  const rim = new THREE.DirectionalLight(0x5fd9e7, 0.8);
  rim.position.set(-120, 60, -90);
  scene.add(rim);

  const ground = new THREE.Mesh(
    new THREE.CircleGeometry(WORLD_RADIUS + 60, 64),
    new THREE.MeshStandardMaterial({ map: makeGroundTexture(), roughness: 1 })
  );
  ground.rotation.x = -Math.PI / 2;
  ground.receiveShadow = true;
  ground.userData = { kind: 'ground' };
  scene.add(ground);

  const edge = new THREE.Mesh(
    new THREE.TorusGeometry(WORLD_RADIUS + 30, 0.5, 8, 96),
    new THREE.MeshBasicMaterial({ color: 0x2b4a6e, transparent: true, opacity: 0.6 })
  );
  edge.rotation.x = -Math.PI / 2;
  edge.position.y = 0.3;
  scene.add(edge);

  // window texture variants for visual diversity
  const texPool = [
    makeWindowTexture(0.55, 10, 12),
    makeWindowTexture(0.4, 8, 10),
    makeWindowTexture(0.68, 12, 16),
  ];

  const core = SERVICES[0];
  for (let i = 1; i < SERVICES.length; i++) scene.add(makeRoad(core.pos, SERVICES[i].pos));
  scene.add(makeRoad(SERVICES[1].pos, SERVICES[3].pos));
  scene.add(makeRoad(SERVICES[2].pos, SERVICES[4].pos));

  const districts = [];
  const buildings = [];
  const buildingByKey = new Map();
  for (const service of SERVICES) {
    const { group, buildings: bs } = makeDistrict(service, texPool);
    scene.add(group);
    districts.push(group);
    for (const b of bs) {
      buildings.push(b);
      const wp = new THREE.Vector3();
      b.getWorldPosition(wp);
      b.userData.worldPos = wp;
      buildingByKey.set(`${service.id}/${b.userData.module}`, b);
    }
  }

  scatterProps(scene);

  const marker = new MoveMarker(scene);

  return {
    districts, buildings, buildingByKey, marker,
    update(dt, elapsed) {
      marker.update(dt);
      for (const d of districts) {
        d.userData.beacon.rotation.y = elapsed * 0.8;
        d.userData.beacon.position.y = d.userData.beaconBaseY + Math.sin(elapsed * 1.5 + d.position.x) * 0.35;
      }
      for (const b of blinkers) {
        b.mat.emissiveIntensity = Math.sin(elapsed * 2.6 + b.phase) > 0.2 ? 2.2 : 0.15;
      }
    },
  };
}
