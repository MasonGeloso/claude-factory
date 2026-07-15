# AGENT COMMAND

RTS-style ops theater for managing Claude Code agents, built with three.js.
Currently runs on a fully mocked world — the data layer (`src/data.js`) is shaped
so a live Claude Code session feed can replace it later.

## The metaphor

| Game | Reality |
| --- | --- |
| District (island plateau) | Repo / service (`api-gateway`, `web-frontend`, …) |
| Building | Code module (auth, router, warehouse, …) |
| Session unit (tall, antenna) | Top-level Claude Code session |
| Agent unit (capsule) | Agent within a session |
| Subagent drone (floating octahedron) | Spawned subagent |
| Worker bot (treaded box) | Mechanical task runner |
| Comms feed / hail channel | Session transcripts & steering |

## Run

```bash
cd game
npm install
npm run dev      # http://localhost:5173
```

## Controls

- **LMB** select · **drag** box-select · **shift** add to selection
- **RMB click ground** move order · **RMB click building** assign work there
- **RMB / MMB drag** pan · **WASD / arrows / edge** pan · **wheel** zoom · **Q/E** rotate
- **double-click** unit to focus · **H** help · **P** pause · **M** mute · **1/2/4×** sim speed
- Select a single unit to open its hail channel. Orders it understands:
  `status`, `hold`, `resume`, `approve`, `work on <module>`, `move to <service>`

## Playing the ops loop

Operatives work tasks, report on comms, and occasionally **block** on a decision
(red flashing ring + comms ping). Hail them and hit **APPROVE** to unblock —
if you don't, their session lead will eventually make the call without you.
Idle units drift back to work on their own district after a while.

## Architecture

```
src/data.js      mock org: services, modules, units, chatter/reply templates
src/world.js     terrain, districts, buildings, roads, lighting, move marker
src/units.js     unit meshes per rank, nameplates, movement, status rings
src/sim.js       simulation: task progress, blockers, chatter, chat parsing
src/controls.js  RTS camera rig + picking + box select
src/ui.js        HUD: top bar, comms feed, hail panel, selection tray, inspector
src/minimap.js   tacmap canvas
src/audio.js     synthesized WebAudio blips (no assets)
```

All randomness routes through a seeded RNG (`src/util.js`) so visual tests are
reproducible. `window.__game` exposes sim/units/controls hooks for Playwright.

## Hooking up real sessions (later)

Replace `buildUnits()` / `SERVICES` with a live feed, and forward
`Sim.handleMessage` to a real session instead of the template reply engine.
Everything downstream (rendering, selection, chat UI, minimap) reads only that
shape.
