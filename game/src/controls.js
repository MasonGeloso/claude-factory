import * as THREE from 'three';
import { clamp, damp } from './util.js';
import { WORLD_RADIUS } from './world.js';

const EDGE = 14;          // px from viewport edge that triggers edge-pan
const DRAG_THRESHOLD = 6; // px before a click becomes a box-select

export class RTSControls {
  constructor(camera, dom) {
    this.camera = camera;
    this.dom = dom;

    // camera rig state (target values; actuals damp toward them)
    this.focus = new THREE.Vector3(0, 0, 20);
    this.yaw = Math.PI * 0.0;
    this.dist = 95;
    this._focus = this.focus.clone();
    this._yaw = this.yaw;
    this._dist = this.dist;
    this.pitch = 0.92; // radians above horizon

    this.keys = new Set();
    this.mouse = new THREE.Vector2();       // NDC
    this.mousePx = { x: -1, y: -1 };
    this.raycaster = new THREE.Raycaster();
    this.groundPlane = new THREE.Plane(new THREE.Vector3(0, 1, 0), 0);

    // interaction callbacks (wired by main)
    this.onSelectPoint = null;   // (event) left click
    this.onBoxSelect = null;     // (x0,y0,x1,y1, additive)
    this.onCommand = null;       // (event) right click
    this.onDoubleClick = null;
    this.onHoverMove = null;

    this.drag = null;   // {x0,y0, box:boolean}
    this.midPan = null;

    this.edgePanEnabled = true;

    dom.addEventListener('contextmenu', (e) => e.preventDefault());
    dom.addEventListener('pointerdown', (e) => this.pointerDown(e));
    window.addEventListener('pointermove', (e) => this.pointerMove(e));
    window.addEventListener('pointerup', (e) => this.pointerUp(e));
    dom.addEventListener('wheel', (e) => this.wheel(e), { passive: false });
    dom.addEventListener('dblclick', (e) => this.onDoubleClick?.(e));
    window.addEventListener('keydown', (e) => {
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
      this.keys.add(e.code);
    });
    window.addEventListener('keyup', (e) => this.keys.delete(e.code));
    window.addEventListener('blur', () => this.keys.clear());

    this.boxEl = document.getElementById('boxsel');
  }

  // ── input handlers ──
  pointerDown(e) {
    if (e.button === 0) {
      this.drag = { x0: e.clientX, y0: e.clientY, box: false, additive: e.shiftKey };
    } else if (e.button === 1) {
      e.preventDefault();
      this.midPan = { x: e.clientX, y: e.clientY };
    } else if (e.button === 2) {
      // RMB: drag pans, clean click issues a command (resolved on pointerup)
      this.rmb = { x: e.clientX, y: e.clientY, moved: false };
    }
  }

  pointerMove(e) {
    this.mousePx.x = e.clientX;
    this.mousePx.y = e.clientY;
    this.mouse.x = (e.clientX / window.innerWidth) * 2 - 1;
    this.mouse.y = -(e.clientY / window.innerHeight) * 2 + 1;

    if (this.midPan) {
      const dx = e.clientX - this.midPan.x, dy = e.clientY - this.midPan.y;
      this.panScreen(-dx, -dy, 0.14 * (this.dist / 95));
      this.midPan = { x: e.clientX, y: e.clientY };
      return;
    }

    if (this.rmb) {
      const dx = e.clientX - this.rmb.x, dy = e.clientY - this.rmb.y;
      if (!this.rmb.moved && Math.hypot(e.clientX - this.rmb.x, e.clientY - this.rmb.y) > DRAG_THRESHOLD) {
        this.rmb.moved = true;
        this.dom.style.cursor = 'grabbing';
      }
      if (this.rmb.moved) {
        this.panScreen(-dx, -dy, 0.14 * (this.dist / 95));
        this.rmb.x = e.clientX; this.rmb.y = e.clientY;
      }
      return;
    }

    if (this.drag) {
      const dx = e.clientX - this.drag.x0, dy = e.clientY - this.drag.y0;
      if (!this.drag.box && Math.hypot(dx, dy) > DRAG_THRESHOLD) this.drag.box = true;
      if (this.drag.box) {
        const x = Math.min(this.drag.x0, e.clientX), y = Math.min(this.drag.y0, e.clientY);
        Object.assign(this.boxEl.style, {
          left: `${x}px`, top: `${y}px`,
          width: `${Math.abs(dx)}px`, height: `${Math.abs(dy)}px`,
        });
        this.boxEl.classList.remove('hidden');
      }
    } else {
      this.onHoverMove?.(e);
    }
  }

  pointerUp(e) {
    if (e.button === 1) { this.midPan = null; return; }
    if (e.button === 2) {
      const wasPan = this.rmb?.moved;
      this.rmb = null;
      this.dom.style.cursor = 'default';
      if (!wasPan) this.onCommand?.(e);
      return;
    }
    if (e.button !== 0 || !this.drag) return;
    const d = this.drag;
    this.drag = null;
    this.boxEl.classList.add('hidden');
    if (d.box) this.onBoxSelect?.(d.x0, d.y0, e.clientX, e.clientY, d.additive);
    else this.onSelectPoint?.(e, d.additive);
  }

  wheel(e) {
    e.preventDefault();
    this.dist = clamp(this.dist * (e.deltaY > 0 ? 1.12 : 0.89), 26, 240);
  }

  panScreen(dxPx, dyPx, scale = 0.1) {
    const sin = Math.sin(this._yaw), cos = Math.cos(this._yaw);
    // screen right = (cos, -sin), screen forward/up = (-sin, -cos) in xz;
    // dyPx is screen-down, so it moves along -forward
    this.focus.x += (dxPx * cos + dyPx * sin) * scale;
    this.focus.z += (-dxPx * sin + dyPx * cos) * scale;
    this.clampFocus();
  }

  clampFocus() {
    const r = Math.hypot(this.focus.x, this.focus.z);
    const max = WORLD_RADIUS + 20;
    if (r > max) {
      this.focus.x *= max / r;
      this.focus.z *= max / r;
    }
  }

  jumpTo(x, z) {
    this.focus.set(x, 0, z);
    this.clampFocus();
  }

  // ── picking helpers ──
  raycast(objects, clientX, clientY) {
    const ndc = new THREE.Vector2(
      (clientX / window.innerWidth) * 2 - 1,
      -(clientY / window.innerHeight) * 2 + 1
    );
    this.raycaster.setFromCamera(ndc, this.camera);
    return this.raycaster.intersectObjects(objects, true);
  }

  groundPoint(clientX, clientY) {
    const ndc = new THREE.Vector2(
      (clientX / window.innerWidth) * 2 - 1,
      -(clientY / window.innerHeight) * 2 + 1
    );
    this.raycaster.setFromCamera(ndc, this.camera);
    const out = new THREE.Vector3();
    return this.raycaster.ray.intersectPlane(this.groundPlane, out) ? out : null;
  }

  // ── per-frame ──
  update(dt) {
    const panSpeed = 55 * (this._dist / 95);
    let px = 0, py = 0;
    if (this.keys.has('KeyW') || this.keys.has('ArrowUp')) py -= 1;
    if (this.keys.has('KeyS') || this.keys.has('ArrowDown')) py += 1;
    if (this.keys.has('KeyA') || this.keys.has('ArrowLeft')) px -= 1;
    if (this.keys.has('KeyD') || this.keys.has('ArrowRight')) px += 1;

    // edge pan (only when pointer inside window and no drag in progress)
    if (this.edgePanEnabled && !this.drag && this.mousePx.x >= 0) {
      if (this.mousePx.x < EDGE) px -= 1;
      else if (this.mousePx.x > window.innerWidth - EDGE) px += 1;
      if (this.mousePx.y < EDGE) py -= 1;
      else if (this.mousePx.y > window.innerHeight - EDGE) py += 1;
    }

    if (px || py) {
      const len = Math.hypot(px, py) || 1;
      this.panScreen((px / len) * panSpeed * dt / 0.1, (py / len) * panSpeed * dt / 0.1, 0.1);
    }

    if (this.keys.has('KeyQ')) this.yaw += 1.6 * dt;
    if (this.keys.has('KeyE')) this.yaw -= 1.6 * dt;

    // damp actuals toward targets
    this._yaw = damp(this._yaw, this.yaw, 8, dt);
    this._dist = damp(this._dist, this.dist, 8, dt);
    this._focus.x = damp(this._focus.x, this.focus.x, 10, dt);
    this._focus.z = damp(this._focus.z, this.focus.z, 10, dt);

    const cp = this.camera.position;
    cp.x = this._focus.x + Math.sin(this._yaw) * Math.cos(this.pitch) * this._dist;
    cp.z = this._focus.z + Math.cos(this._yaw) * Math.cos(this.pitch) * this._dist;
    cp.y = Math.sin(this.pitch) * this._dist;
    this.camera.lookAt(this._focus.x, 0, this._focus.z);
  }
}
