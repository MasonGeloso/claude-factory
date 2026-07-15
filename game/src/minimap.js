import { SERVICES, STATUS_COLORS } from './data.js';
import { WORLD_RADIUS } from './world.js';

const CSS_STATUS = Object.fromEntries(
  Object.entries(STATUS_COLORS).map(([k, v]) => [k, '#' + v.toString(16).padStart(6, '0')])
);

export class Minimap {
  constructor(canvas, controls, units) {
    this.canvas = canvas;
    this.g = canvas.getContext('2d');
    this.controls = controls;
    this.units = units;
    this.scale = canvas.width / ((WORLD_RADIUS + 40) * 2);

    canvas.addEventListener('pointerdown', (e) => {
      const rect = canvas.getBoundingClientRect();
      const { x, z } = this.toWorld(e.clientX - rect.left, e.clientY - rect.top);
      controls.jumpTo(x, z);
      this.dragging = true;
    });
    window.addEventListener('pointermove', (e) => {
      if (!this.dragging) return;
      const rect = canvas.getBoundingClientRect();
      const { x, z } = this.toWorld(e.clientX - rect.left, e.clientY - rect.top);
      controls.jumpTo(x, z);
    });
    window.addEventListener('pointerup', () => { this.dragging = false; });
  }

  toPx(x, z) {
    const c = this.canvas.width / 2;
    return [c + x * this.scale, c + z * this.scale];
  }

  toWorld(px, py) {
    const c = this.canvas.width / 2;
    return { x: (px - c) / this.scale, z: (py - c) / this.scale };
  }

  render() {
    const { g, canvas } = this;
    const w = canvas.width, h = canvas.height;
    g.clearRect(0, 0, w, h);

    // world disc
    g.fillStyle = '#0d1526';
    g.beginPath();
    g.arc(w / 2, h / 2, WORLD_RADIUS * this.scale + 8, 0, Math.PI * 2);
    g.fill();
    g.strokeStyle = '#24334f';
    g.stroke();

    // roads
    g.strokeStyle = 'rgba(74, 98, 143, 0.4)';
    g.lineWidth = 1.5;
    const core = SERVICES[0];
    for (let i = 1; i < SERVICES.length; i++) {
      const [x0, y0] = this.toPx(core.pos[0], core.pos[1]);
      const [x1, y1] = this.toPx(SERVICES[i].pos[0], SERVICES[i].pos[1]);
      g.beginPath(); g.moveTo(x0, y0); g.lineTo(x1, y1); g.stroke();
    }

    // districts
    for (const s of SERVICES) {
      const [x, y] = this.toPx(s.pos[0], s.pos[1]);
      g.fillStyle = s.css + '22';
      g.strokeStyle = s.css + '88';
      g.beginPath();
      g.arc(x, y, s.radius * this.scale, 0, Math.PI * 2);
      g.fill(); g.stroke();
    }

    // units
    for (const u of this.units) {
      const [x, y] = this.toPx(u.group.position.x, u.group.position.z);
      g.fillStyle = u.selected ? '#ffb454' : CSS_STATUS[u.status];
      const r = u.type === 'session' ? 3 : 2;
      g.beginPath(); g.arc(x, y, r, 0, Math.PI * 2); g.fill();
      if (u.selected) { g.strokeStyle = '#ffb454'; g.beginPath(); g.arc(x, y, r + 2, 0, Math.PI * 2); g.stroke(); }
    }

    // camera focus reticle
    const f = this.controls.focus;
    const [cx, cy] = this.toPx(f.x, f.z);
    g.strokeStyle = 'rgba(217, 228, 247, 0.8)';
    g.lineWidth = 1;
    const s = 7;
    g.strokeRect(cx - s, cy - s, s * 2, s * 2);
  }
}
