import './styles.css';
import * as THREE from 'three';
import { CSS2DRenderer } from 'three/addons/renderers/CSS2DRenderer.js';
import { buildWorld } from './world.js';
import { buildUnits } from './data.js';
import { spawnUnits } from './units.js';
import { RTSControls } from './controls.js';
import { Sim } from './sim.js';
import { UI } from './ui.js';
import { Minimap } from './minimap.js';
import { sfx } from './audio.js';

// ── renderer ─────────────────────────────────────────────────────────
const canvas = document.getElementById('gl');
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
renderer.setPixelRatio(Math.min(devicePixelRatio, 1.75));
renderer.setSize(innerWidth, innerHeight);
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.5;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;

const labelRenderer = new CSS2DRenderer({ element: document.getElementById('labels') });
labelRenderer.setSize(innerWidth, innerHeight);

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(42, innerWidth / innerHeight, 1, 2000);

// ── world / units / systems ──────────────────────────────────────────
const world = buildWorld(scene);
const units = spawnUnits(buildUnits(), scene, world.buildingByKey);
const unitById = new Map(units.map((u) => [u.id, u]));

const controls = new RTSControls(camera, canvas);

let ui; // forward ref for sim bus
const sim = new Sim(units, world, {
  comms: (line) => ui.comms(line),
  chatMessage: (u) => ui.chatMessage(u),
  statsDirty: () => ui.renderStats(),
});

ui = new UI(
  sim,
  (unit) => selectUnits([unit], true),
  (x, z) => controls.jumpTo(x, z)
);

const minimap = new Minimap(document.getElementById('minimap'), controls, units);

// ── selection ────────────────────────────────────────────────────────
let selected = [];

function selectUnits(list, focusCamera = false) {
  if (list.length) sfx.select();
  for (const u of selected) u.setSelected(false);
  selected = list;
  for (const u of selected) u.setSelected(true);
  ui.renderSelection(selected);
  if (selected.length === 1) ui.openChat(selected[0]);
  else ui.closeChat();
  if (focusCamera && selected.length === 1) {
    const p = selected[0].group.position;
    controls.jumpTo(p.x, p.z);
  }
}

const pickables = [];
for (const u of units) pickables.push(u.hit);
for (const b of world.buildings) pickables.push(b);

function findUnitHit(hits) {
  for (const h of hits) {
    let o = h.object;
    while (o) {
      if (o.userData?.kind === 'unit') return unitById.get(o.userData.id);
      o = o.parent;
    }
  }
  return null;
}

function findBuildingHit(hits) {
  for (const h of hits) {
    let o = h.object;
    while (o) {
      if (o.userData?.kind === 'building') return o;
      o = o.parent;
    }
  }
  return null;
}

controls.onSelectPoint = (e, additive) => {
  const hits = controls.raycast(pickables, e.clientX, e.clientY);
  const unit = findUnitHit(hits);
  if (unit) {
    if (additive) {
      selectUnits(selected.includes(unit) ? selected.filter((u) => u !== unit) : [...selected, unit]);
    } else selectUnits([unit]);
    return;
  }
  const building = findBuildingHit(hits);
  if (building) {
    selectUnits([]);
    ui.openInspector(building, units);
    return;
  }
  if (!additive) selectUnits([]);
  ui.closeInspector();
};

controls.onBoxSelect = (x0, y0, x1, y1, additive) => {
  const minX = Math.min(x0, x1), maxX = Math.max(x0, x1);
  const minY = Math.min(y0, y1), maxY = Math.max(y0, y1);
  const v = new THREE.Vector3();
  const boxed = units.filter((u) => {
    v.copy(u.group.position).project(camera);
    const sx = (v.x + 1) / 2 * innerWidth;
    const sy = (-v.y + 1) / 2 * innerHeight;
    return sx >= minX && sx <= maxX && sy >= minY && sy <= maxY && v.z < 1;
  });
  selectUnits(additive ? [...new Set([...selected, ...boxed])] : boxed);
};

controls.onCommand = (e) => {
  if (!selected.length) return;
  const hits = controls.raycast(pickables, e.clientX, e.clientY);
  const building = findBuildingHit(hits);
  if (building) {
    const wp = building.userData.worldPos;
    world.marker.ping(wp.x, wp.z, 0x5fd9e7);
    sfx.assign();
    for (const u of selected) sim.assignToBuilding(u, building);
    ui.toast(`${selected.length} unit${selected.length > 1 ? 's' : ''} → ${building.userData.module.toUpperCase()}`);
    return;
  }
  const p = controls.groundPoint(e.clientX, e.clientY);
  if (!p) return;
  world.marker.ping(p.x, p.z);
  sfx.order();
  selected.forEach((u, i) => {
    const a = (i / Math.max(1, selected.length)) * Math.PI * 2;
    const r = selected.length > 1 ? 3 + selected.length * 0.4 : 0;
    sim.orderMoveTo(u, p.x + Math.cos(a) * r, p.z + Math.sin(a) * r);
  });
};

controls.onDoubleClick = (e) => {
  const hits = controls.raycast(pickables, e.clientX, e.clientY);
  const unit = findUnitHit(hits);
  if (unit) selectUnits([unit], true);
};

// hover cursor + building highlight
let hoverBuilding = null;
controls.onHoverMove = (e) => {
  const hits = controls.raycast(pickables, e.clientX, e.clientY);
  const unit = findUnitHit(hits);
  const building = unit ? null : findBuildingHit(hits);
  canvas.style.cursor = unit || building ? 'pointer' : 'default';
  if (hoverBuilding && hoverBuilding !== building) {
    hoverBuilding.userData.trim.material.emissiveIntensity = hoverBuilding.userData.trimBase;
  }
  hoverBuilding = building;
  if (building) building.userData.trim.material.emissiveIntensity = 2.4;
};

// ── resize ───────────────────────────────────────────────────────────
addEventListener('resize', () => {
  camera.aspect = innerWidth / innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(innerWidth, innerHeight);
  labelRenderer.setSize(innerWidth, innerHeight);
});

// ── loop ─────────────────────────────────────────────────────────────
const clock = new THREE.Clock();
let statTimer = 0;
let uiTimer = 0;

function frame() {
  requestAnimationFrame(frame);
  const dt = Math.min(clock.getDelta(), 0.05);
  const elapsed = clock.elapsedTime;

  controls.update(dt);
  sim.tick(dt);
  sim.updateUnits(dt, elapsed);
  world.update(dt, elapsed);

  statTimer -= dt;
  if (statTimer <= 0) {
    statTimer = 0.5;
    ui.renderStats();
    minimap.render();
    document.getElementById('labels').classList.toggle('far', controls._dist > 110);
  }
  uiTimer -= dt;
  if (uiTimer <= 0) {
    uiTimer = 1.2;
    ui.refreshSelectionCards();
    if (ui.chatUnit) ui.renderChatMeta();
  }

  renderer.render(scene, camera);
  labelRenderer.render(scene, camera);
}
frame();

// opening comms
setTimeout(() => ui.comms({ who: null, text: 'Theater online. 25 operatives across 5 districts.', event: true }), 400);
setTimeout(() => ui.toast('OVERSEER ON DECK'), 600);

// ── deterministic test hooks for playwright ──────────────────────────
window.__game = {
  sim, units, controls, camera, selectUnits,
  unitByName: (name) => units.find((u) => u.name === name),
  stats: () => sim.stats(),
  renderer,
};
