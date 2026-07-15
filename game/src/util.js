// Seeded RNG (mulberry32) — all gameplay randomness routes through this so
// screenshots and bot playtests stay reproducible.
export function createSeededRandom(seed = 1337) {
  let a = seed >>> 0;
  return function () {
    a |= 0; a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export const rng = createSeededRandom(20260714);

export const pick = (arr) => arr[Math.floor(rng() * arr.length)];

export const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));
export const lerp = (a, b, t) => a + (b - a) * t;

// Exponential smoothing that is frame-rate independent.
export const damp = (a, b, lambda, dt) => lerp(a, b, 1 - Math.exp(-lambda * dt));

export const easeOutCubic = (t) => 1 - Math.pow(1 - t, 3);
export const easeOutBack = (t) => {
  const c1 = 1.70158, c3 = c1 + 1;
  return 1 + c3 * Math.pow(t - 1, 3) + c1 * Math.pow(t - 1, 2);
};

export class TweenManager {
  constructor() { this.tweens = []; }
  tween(duration, onUpdate, easing = easeOutCubic, onComplete) {
    this.tweens.push({ elapsed: 0, duration, easing, onUpdate, onComplete });
  }
  update(delta) {
    for (let i = this.tweens.length - 1; i >= 0; i--) {
      const t = this.tweens[i];
      t.elapsed += delta;
      const k = Math.min(t.elapsed / t.duration, 1);
      t.onUpdate(t.easing(k));
      if (t.elapsed >= t.duration) { t.onComplete?.(); this.tweens.splice(i, 1); }
    }
  }
}

export function fill(template, ctx) {
  return template.replace(/\{(\w+)\}/g, (_, k) => (ctx[k] ?? `{${k}}`));
}
