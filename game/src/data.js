// Mock org: districts are repos/services, buildings are code modules,
// units are sessions/agents/subagents/workers. Swap this file for a live
// Claude Code session feed later — everything downstream reads this shape.

export const SERVICES = [
  {
    id: 'core', name: 'CORE PLATFORM', repo: 'factory',
    color: 0x5fd9e7, css: '#5fd9e7', pos: [8, -4], radius: 31, elev: 1.6,
    desc: 'Orchestration heart of the org. Session routing, agent lifecycle, billing.',
    modules: [
      { id: 'orchestrator', name: 'Orchestrator', loc: 18400, health: 0.94, desc: 'Session scheduling and agent dispatch loops.' },
      { id: 'auth', name: 'Auth', loc: 9200, health: 0.88, desc: 'Token issuance, refresh, scoped credentials.' },
      { id: 'sessions', name: 'Sessions', loc: 12750, health: 0.91, desc: 'Conversation state, resume, context windows.' },
      { id: 'billing', name: 'Billing', loc: 6100, health: 0.72, desc: 'Token metering and usage rollups.' },
      { id: 'agents', name: 'Agents', loc: 15300, health: 0.9, desc: 'Agent runtime: spawning, tool loops, teardown.' },
      { id: 'tools', name: 'Tool Registry', loc: 8700, health: 0.86, desc: 'Tool schemas, permissions, dispatch.' },
      { id: 'hooks', name: 'Hooks', loc: 4200, health: 0.82, desc: 'Lifecycle hooks and event interception.' },
      { id: 'memory', name: 'Memory', loc: 7600, health: 0.89, desc: 'Persistent memory store and recall ranking.' },
      { id: 'search', name: 'Search', loc: 6900, health: 0.84, desc: 'Code and transcript search backends.' },
      { id: 'indexer', name: 'Indexer', loc: 5800, health: 0.87, desc: 'Repo graph and symbol indexing.' },
      { id: 'telemetry', name: 'Telemetry', loc: 5100, health: 0.78, desc: 'Client metrics, spans, crash reports.' },
      { id: 'queue', name: 'Job Queue', loc: 4900, health: 0.92, desc: 'Background jobs, retries, dead letters.' },
      { id: 'scheduler', name: 'Scheduler', loc: 3800, health: 0.9, desc: 'Cron routines and wakeup timers.' },
      { id: 'sandbox', name: 'Sandbox', loc: 9800, health: 0.93, desc: 'Isolated execution: fs, net, process jails.' },
      { id: 'permissions', name: 'Permissions', loc: 5400, health: 0.88, desc: 'Grants, allowlists, approval flows.' },
      { id: 'transcripts', name: 'Transcripts', loc: 6300, health: 0.85, desc: 'Conversation logs, replay, export.' },
      { id: 'artifacts', name: 'Artifacts', loc: 4600, health: 0.91, desc: 'Published artifacts and version history.' },
      { id: 'cache', name: 'Cache', loc: 3400, health: 0.95, desc: 'Prompt cache and warm context reuse.' },
      { id: 'migrations', name: 'Migrations', loc: 2900, health: 0.8, desc: 'Schema evolution and backfills.' },
      { id: 'notifications', name: 'Notifications', loc: 3100, health: 0.83, desc: 'Push, email, and webhook fan-out.' },
      { id: 'webhooks', name: 'Webhooks', loc: 2700, health: 0.86, desc: 'Inbound event endpoints and signatures.' },
      { id: 'admin', name: 'Admin Console', loc: 7200, health: 0.77, desc: 'Internal ops surface and feature flags.' },
    ],
  },
  {
    id: 'gateway', name: 'API GATEWAY', repo: 'api-gateway',
    color: 0xffb454, css: '#ffb454', pos: [-76, -64], radius: 21, elev: 2.4,
    desc: 'Northern edge. Every request enters the theater through here.',
    modules: [
      { id: 'router', name: 'Router', loc: 7300, health: 0.96, desc: 'Route tables, versioning, canary splits.' },
      { id: 'ratelimit', name: 'Rate Limiter', loc: 3900, health: 0.83, desc: 'Sliding-window quotas per org and key.' },
      { id: 'proxy', name: 'Proxy', loc: 5200, health: 0.9, desc: 'Upstream fan-out and retry policy.' },
    ],
  },
  {
    id: 'webapp', name: 'WEB FRONTEND', repo: 'web-frontend',
    color: 0xb593e6, css: '#b593e6', pos: [97, -33], radius: 26, elev: 1.1,
    desc: 'The glass city. Everything the customer actually sees.',
    modules: [
      { id: 'dashboard', name: 'Dashboard', loc: 14100, health: 0.87, desc: 'Live ops view, charts, fleet status.' },
      { id: 'editor', name: 'Editor', loc: 21500, health: 0.79, desc: 'In-browser code editing surface.' },
      { id: 'design', name: 'Design System', loc: 8800, health: 0.95, desc: 'Tokens, primitives, dark mode.' },
    ],
  },
  {
    id: 'data', name: 'DATA PIPELINE', repo: 'data-pipeline',
    color: 0x7bd88f, css: '#7bd88f', pos: [-94, 36], radius: 24, elev: 1.9,
    desc: 'Southern lowlands. Events flow in, insight flows out.',
    modules: [
      { id: 'ingest', name: 'Ingest', loc: 6700, health: 0.92, desc: 'Event intake, dedupe, schema checks.' },
      { id: 'warehouse', name: 'Warehouse', loc: 11300, health: 0.85, desc: 'Column store, partitions, retention.' },
      { id: 'analytics', name: 'Analytics', loc: 9400, health: 0.68, desc: 'Aggregation jobs and usage reports.' },
    ],
  },
  {
    id: 'infra', name: 'INFRA & DEPLOY', repo: 'infra',
    color: 0xff8f6b, css: '#ff8f6b', pos: [50, 89], radius: 18, elev: 2.8,
    desc: 'The forge. CI, fleets, terraform, the pager.',
    modules: [
      { id: 'ci', name: 'CI Rig', loc: 4800, health: 0.9, desc: 'Build matrix, caching, flaky-test triage.' },
      { id: 'deploy', name: 'Deploy', loc: 5600, health: 0.93, desc: 'Rollouts, canaries, instant rollback.' },
      { id: 'observability', name: 'Observability', loc: 7200, health: 0.81, desc: 'Metrics, traces, alert routing.' },
    ],
  },
];

// type: session > agent > subagent | worker
export const UNIT_TYPES = {
  session:  { glyph: '⬢', label: 'SESSION',  scale: 1.35, speed: 9 },
  agent:    { glyph: '⬡', label: 'AGENT',    scale: 1.0,  speed: 11 },
  subagent: { glyph: '◇', label: 'SUBAGENT', scale: 0.78, speed: 13 },
  worker:   { glyph: '▪', label: 'WORKER',   scale: 0.66, speed: 14 },
};

export const STATUS_COLORS = {
  working: 0x7bd88f, idle: 0x66779c, moving: 0x5fd9e7,
  blocked: 0xff6b6b, reviewing: 0xb593e6,
};

let uid = 0;
const U = (name, type, service, module, task, status, parent = null) =>
  ({ id: `u${uid++}`, name, type, service, module, task, status, parent, progress: Math.random() });

export function buildUnits() {
  uid = 0;
  return [
    // ── core ──
    U('MAINLINE', 'session', 'core', 'orchestrator', 'Coordinating the platform milestone', 'working'),
    U('ADA', 'agent', 'core', 'auth', 'Refactor token refresh race', 'working', 'u0'),
    U('GRACE', 'agent', 'core', 'sessions', 'Context compaction on resume', 'working', 'u0'),
    U('ADA-S1', 'subagent', 'core', 'auth', 'Audit refresh call sites', 'working', 'u1'),
    U('ADA-S2', 'subagent', 'core', 'billing', 'Trace double-count in metering', 'blocked', 'u1'),
    U('BOLT', 'worker', 'core', 'sessions', 'Run session-restore test matrix', 'working', 'u2'),
    U('EDSGER', 'agent', 'core', 'billing', 'Invoice rollup correctness pass', 'reviewing', 'u0'),

    // ── gateway ──
    U('NIGHTWATCH', 'session', 'gateway', 'router', 'Own the edge during the migration', 'working'),
    U('LIN', 'agent', 'gateway', 'ratelimit', 'Sliding-window off-by-one at burst', 'working', 'u7'),
    U('KAY', 'agent', 'gateway', 'proxy', 'Retry storm dampening', 'idle', 'u7'),
    U('LIN-S1', 'subagent', 'gateway', 'ratelimit', 'Repro burst pattern in staging', 'working', 'u8'),
    U('PATCH', 'worker', 'gateway', 'router', 'Regenerate route-table fixtures', 'working', 'u7'),

    // ── webapp ──
    U('STOREFRONT', 'session', 'webapp', 'dashboard', 'Ship the fleet-status dashboard', 'working'),
    U('IVY', 'agent', 'webapp', 'editor', 'Editor latency: input to paint', 'working', 'u12'),
    U('MARGO', 'agent', 'webapp', 'design', 'Dark-mode token sweep', 'working', 'u12'),
    U('IVY-S1', 'subagent', 'webapp', 'editor', 'Profile keystroke hot path', 'working', 'u13'),
    U('PIXEL', 'worker', 'webapp', 'dashboard', 'Screenshot-diff the chart pack', 'reviewing', 'u12'),

    // ── data ──
    U('UNDERTOW', 'session', 'data', 'warehouse', 'Quarter-close data integrity', 'working'),
    U('HOPPER', 'agent', 'data', 'ingest', 'Dedupe window misses late events', 'working', 'u17'),
    U('TESS', 'agent', 'data', 'analytics', 'Usage report drift vs billing', 'blocked', 'u17'),
    U('CRUNCH', 'worker', 'data', 'warehouse', 'Backfill March partitions', 'working', 'u17'),

    // ── infra ──
    U('FORGE', 'session', 'infra', 'deploy', 'Keep the trains running', 'working'),
    U('WRENCH', 'agent', 'infra', 'ci', 'Flaky-test quarantine automation', 'working', 'u21'),
    U('SIREN', 'agent', 'infra', 'observability', 'Alert dedupe before the pager melts', 'working', 'u21'),
    U('RIVET', 'worker', 'infra', 'deploy', 'Canary bake-time tuning', 'idle', 'u21'),

    // ── core reinforcements (the big city gets a big crew) ──
    U('VOSS', 'agent', 'core', 'tools', 'Tool schema versioning', 'working', 'u0'),
    U('NOOR', 'agent', 'core', 'memory', 'Recall ranking regression', 'working', 'u0'),
    U('GRACE-S1', 'subagent', 'core', 'transcripts', 'Replay long sessions for repro', 'working', 'u2'),
    U('TINKER', 'worker', 'core', 'cache', 'Warm-cache hit-rate sweep', 'working', 'u0'),
    U('JUNO', 'agent', 'core', 'sandbox', 'Network jail escape audit', 'reviewing', 'u0'),
    U('SPROCKET', 'worker', 'core', 'queue', 'Dead-letter replay tooling', 'idle', 'u0'),
  ];
}

// Task pool drawn from when a unit finishes its current task.
export const TASK_POOL = {
  core: [
    'Harden session handoff between agents', 'Kill the N+1 in agent lookup',
    'Snapshot/restore for long-running sessions', 'Rotate signing keys without downtime',
    'Batch billing events before flush', 'Instrument orchestrator queue depth',
  ],
  gateway: [
    'Add hedged requests to slow upstreams', 'Version-pin the public API surface',
    'Zero-downtime route table reload', 'Per-org burst credit ledger',
    'TLS session resumption at the edge',
  ],
  webapp: [
    'Virtualize the fleet table', 'Optimistic UI for agent commands',
    'Keyboard palette for ops actions', 'Streaming render for long transcripts',
    'Contrast pass on status colors',
  ],
  data: [
    'Late-event watermark tuning', 'Compact small warehouse partitions',
    'Anomaly flags on usage curves', 'Schema registry for event types',
    'Replay tooling for bad batches',
  ],
  infra: [
    'Cache the build graph across PRs', 'One-click env clone for repro',
    'SLO burn-rate alerts', 'Terraform drift detector',
    'Rollback rehearsal automation',
  ],
};

// ── Radio voice. Each unit type has a register; lines are picked seeded. ──
export const CHATTER = {
  working: [
    'Tests green on {module}, pushing on.', 'Diff is getting big — will split before review.',
    'Found the culprit in {module}. Patching.', '{module} building clean. ETA holding.',
    'Two call sites left to migrate.', 'Refactor landed local, running the suite.',
    'Tracing through {module} — signal is good.', 'Benchmarks improving. 12% so far.',
  ],
  idle: [
    'Standing by for tasking.', 'Queue empty on my end. Point me somewhere.',
    'Holding position at {module}.', 'Awaiting orders, overseer.',
  ],
  moving: [
    'En route to {module}.', 'Relocating. Give me a minute.', 'Crossing to {service} now.',
  ],
  blocked: [
    'Blocked: need a decision on {task}.', 'Requesting approval to proceed — flagging you.',
    'Hit a wall on {module}. Two options, need your call.', 'CI is red upstream of me. Holding.',
  ],
  reviewing: [
    'Reviewing the diff now. Few nits so far.', 'Re-checking my own work before handoff.',
    'Second pass on {module} looks clean.',
  ],
  done: [
    'Task complete. {task} is in.', 'Shipped. Marking {task} done.', 'Done and verified. Next?',
  ],
};

export const REPLIES = {
  status: [
    '{status}. On "{task}" — {progress}% through. Morale high.',
    'Sitrep: {status} at {module}, {progress}% on "{task}".',
    'Holding {progress}% on "{task}". No surprises since last check.',
  ],
  hold: ['Copy, holding position.', 'Standing down. Say resume when ready.', 'Pausing work, staying warm.'],
  resume: ['Back on it.', 'Resuming "{task}".', 'Copy, spinning back up.'],
  approve: ['Approval received — proceeding.', 'Copy that, unblocked. Moving.', 'That was the call I needed. Executing.'],
  approveNoop: ['Nothing pending approval on my end.', 'No blockers here, but appreciated.'],
  assign: ['Copy, retasking to {target}.', 'New orders received: {target}. Moving.', 'On my way to {target}.'],
  move: ['Repositioning to {target}.', 'Copy, heading to {target}.'],
  unknown: [
    'Say again? I parse: status / hold / resume / approve / work on <module> / move to <service>.',
    'Didn\'t catch that, overseer. Try "status" or "work on <module>".',
  ],
  greeting: ['Overseer on the line. Go ahead.', 'Reading you loud and clear.', 'Channel open. What do you need?'],
};

export const EVENT_LINES = [
  '{name} opened a PR against {service}.', 'CI run for {service} finished: green.',
  'Nightly backup for {service} verified.', '{name} merged to main in {service}.',
  'Canary for {service} at 25%, error budget intact.',
];
