// Minimal WebAudio feedback — synthesized blips, no assets. Muted with M.
let ctx = null;
let muted = false;

function ensureCtx() {
  if (!ctx) {
    try { ctx = new (window.AudioContext || window.webkitAudioContext)(); }
    catch { return null; }
  }
  if (ctx.state === 'suspended') ctx.resume().catch(() => {});
  return ctx;
}

// resume on first gesture (autoplay policy)
window.addEventListener('pointerdown', ensureCtx, { once: true });
window.addEventListener('keydown', (e) => {
  if (e.key === 'm' || e.key === 'M') {
    if (e.target.tagName === 'INPUT') return;
    muted = !muted;
  }
});

function tone(freq, dur = 0.07, type = 'square', gain = 0.045, slide = 0) {
  const c = ensureCtx();
  if (!c || muted || c.state !== 'running') return;
  const osc = c.createOscillator();
  const g = c.createGain();
  osc.type = type;
  osc.frequency.setValueAtTime(freq, c.currentTime);
  if (slide) osc.frequency.exponentialRampToValueAtTime(Math.max(40, freq + slide), c.currentTime + dur);
  g.gain.setValueAtTime(gain, c.currentTime);
  g.gain.exponentialRampToValueAtTime(0.0004, c.currentTime + dur);
  osc.connect(g).connect(c.destination);
  osc.start();
  osc.stop(c.currentTime + dur + 0.02);
}

export const sfx = {
  select: () => tone(720, 0.05, 'square', 0.035),
  order: () => tone(430, 0.08, 'square', 0.045, 90),
  assign: () => { tone(430, 0.06, 'square', 0.04); setTimeout(() => tone(650, 0.07, 'square', 0.04), 70); },
  done: () => { tone(660, 0.07, 'triangle', 0.05); setTimeout(() => tone(990, 0.1, 'triangle', 0.05), 90); },
  blocked: () => { tone(220, 0.12, 'sawtooth', 0.04, -60); },
  message: () => tone(880, 0.04, 'sine', 0.03),
};
