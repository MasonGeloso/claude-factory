# -*- coding: utf-8 -*-
"""Serve the demo directory over HTTP. file:// silently blocks the cast fetch and the
webfonts, and the failure looks like a content bug rather than a transport one."""
import functools, http.server, socketserver, sys
from _config import load

cfg = load()
port = int(sys.argv[1]) if len(sys.argv) > 1 else cfg["port"]
handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=cfg["_dir"])
socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(("127.0.0.1", port), handler) as httpd:
    print(f"serving {cfg['_dir']} on http://127.0.0.1:{port}", flush=True)
    httpd.serve_forever()
