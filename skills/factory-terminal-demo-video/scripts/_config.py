# -*- coding: utf-8 -*-
"""Shared config loader. Every stage reads the same demo.json so a re-run of one
stage can never disagree with the others about geometry, paths or timing."""
import json, os, sys

def load(path=None):
    path = path or os.environ.get("DEMO_CONFIG", "demo.json")
    if not os.path.exists(path):
        sys.exit(f"no config at {path} — see the skill's SKILL.md for the shape")
    cfg = json.load(open(path, encoding="utf-8"))
    cfg.setdefault("cols", 92)
    cfg.setdefault("rows", 30)
    cfg.setdefault("cwd", ".")
    cfg.setdefault("args", [])
    cfg.setdefault("env_unset_prefixes", [])
    cfg.setdefault("timeout_s", 780)
    cfg.setdefault("dwells", [])
    cfg.setdefault("port", 8791)
    cfg.setdefault("width", 2560)
    cfg.setdefault("height", 1440)
    cfg.setdefault("end_hold_s", 9.5)
    cfg.setdefault("out_basename", "out/demo")
    cfg["_dir"] = os.path.dirname(os.path.abspath(path)) or "."
    return cfg

def rel(cfg, p):
    return p if os.path.isabs(p) else os.path.join(cfg["_dir"], p)
