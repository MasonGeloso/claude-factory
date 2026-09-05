# -*- coding: utf-8 -*-
"""Stage 1 — record a REAL interactive session in a PTY to an asciinema v2 cast.

Nothing is reconstructed: every byte in the cast is what the program actually printed.
Driven entirely by demo.json; see SKILL.md for the config shape.
"""
import codecs, json, os, re, sys, time
import pexpect
from _config import load, rel

cfg = load()
COLS, ROWS = cfg["cols"], cfg["rows"]
CWD = rel(cfg, cfg["cwd"])
OUT = rel(cfg, cfg.get("cast_raw", "session.cast"))
PROMPT = open(rel(cfg, cfg["prompt_file"]), encoding="utf-8").read().strip()

# A multi-line prompt is the single most expensive mistake in this stage: sending it with
# \n -> \r submits every line as its own message. Fail here rather than on camera.
assert "\n" not in PROMPT and "\r" not in PROMPT, (
    "prompt must be a single line — use bracketed paste if you need real newlines")

env = dict(os.environ, TERM="xterm-256color", COLUMNS=str(COLS), LINES=str(ROWS),
           COLORTERM="truecolor")
# Parent-session markers can make a child CLI print a warning across its status line,
# which would then be on camera. The consuming project names the prefixes to drop.
for pref in cfg["env_unset_prefixes"]:
    for k in [k for k in list(env) if k.startswith(pref)]:
        env.pop(k, None)

child = pexpect.spawn(cfg["command"], list(cfg["args"]), cwd=CWD, env=env,
                      dimensions=(ROWS, COLS), encoding=None, timeout=None)

t0 = time.time()
events = []
_dec = codecs.getincrementaldecoder("utf-8")("replace")   # never splits a multibyte char

def pump(seconds):
    """Read whatever the program emits for `seconds`, timestamping each chunk."""
    end = time.time() + seconds
    while time.time() < end:
        try:
            b = child.read_nonblocking(size=65536, timeout=0.05)
        except pexpect.TIMEOUT:
            continue
        except (pexpect.EOF, OSError):
            return False
        if b:
            txt = _dec.decode(b)
            if txt:
                events.append([round(time.time() - t0, 6), "o", txt])
    return True

def seen():
    t = "".join(e[2] for e in events)
    t = re.sub(r"\x1b\[[0-9;?]*[a-zA-Z]", "", t)
    return re.sub(r"\x1b\][^\x07]*\x07", "", t)

ready = cfg.get("ready_when", {})
blockers = ready.get("blocked_on", [])
markers  = ready.get("markers", [])

print("booting…", flush=True)
boot = time.time()
while time.time() - boot < ready.get("timeout_s", 45):
    pump(1.0)
    t = seen()
    if any(b in t for b in blockers):
        # e.g. a "do you trust this folder?" dialog, which eats the typed prompt.
        # Pre-accept it in the tool's own config before recording; don't script past it.
        sys.exit(f"BLOCKED: a startup dialog is showing ({blockers})")
    if not markers or any(m in t for m in markers):
        break
pump(1.6)
print("input ready", flush=True)

print("entering prompt…", flush=True)
CH = cfg.get("type_chunk", 6)
for i in range(0, len(PROMPT), CH):
    child.send(PROMPT[i:i + CH].encode())
    pump(cfg.get("type_delay", 0.05))
pump(1.4)
child.send(b"\r")                      # the only Enter in the whole run
print("submitted; following the run…", flush=True)

# Completion is decided by the ARTEFACT, never by the program's prose. Matching a sentence
# in which an agent SAYS it is about to write a file interrupts the run mid-work.
dw = cfg.get("done_when", {})
artefact = rel(cfg, dw["file"]) if dw.get("file") else None
min_bytes = dw.get("min_bytes", 1)
need_stable = dw.get("stable_polls", 4)
tail_abort = dw.get("abort_on_tail", [])

deadline = time.time() + cfg["timeout_s"]
alive, stable, last = True, 0, -1
while alive and time.time() < deadline:
    alive = pump(3.0)
    if artefact and os.path.exists(artefact):
        sz = os.path.getsize(artefact)
        stable = stable + 1 if (sz == last and sz >= min_bytes) else 0
        last = sz
        if stable >= need_stable:
            print(f"artefact stable at {sz} bytes; letting the answer render", flush=True)
            pump(cfg.get("settle_s", 30.0))
            break
    if tail_abort:
        tail = "".join(e[2] for e in events[-10:])
        if any(x in tail for x in tail_abort):
            break

pump(3.0)
try:
    child.sendcontrol("c"); pump(0.6)
    child.sendcontrol("c"); pump(0.6)
    child.close(force=True)
except Exception:
    pass

hdr = {"version": 2, "width": COLS, "height": ROWS, "timestamp": int(t0),
       "env": {"TERM": "xterm-256color", "SHELL": os.environ.get("SHELL", "/bin/bash")}}
with open(OUT, "w", encoding="utf-8") as f:
    f.write(json.dumps(hdr) + "\n")
    for e in events:
        f.write(json.dumps(e, ensure_ascii=False) + "\n")
print(f"wrote {OUT}: {len(events)} events, {events[-1][0]:.1f}s" if events else "NO EVENTS")
