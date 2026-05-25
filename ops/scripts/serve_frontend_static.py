#!/usr/bin/env python3
"""Serve the EMITS React build with SPA fallback.

This is a small fallback server for hosts that expose the frontend directly on
port 3013 instead of serving /var/www/emits through nginx.
"""

from __future__ import annotations

import argparse
import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


class SPAFallbackHandler(SimpleHTTPRequestHandler):
    static_prefixes = (
        "/static/",
        "/asset-manifest.json",
        "/favicon",
        "/manifest.json",
        "/robots.txt",
        "/version.json",
    )

    def send_head(self):
        path = self.translate_path(self.path)
        if not os.path.exists(path) and not self.path.startswith(self.static_prefixes):
            self.path = "/index.html"
        return super().send_head()


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve a React build with SPA fallback")
    parser.add_argument("--root", default=os.environ.get("EMITS_WEB_ROOT", "/var/www/emits"))
    parser.add_argument("--host", default=os.environ.get("EMITS_FRONTEND_HOST", "0.0.0.0"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("EMITS_FRONTEND_PORT", "3013")))
    args = parser.parse_args()

    root = Path(args.root).resolve()
    index = root / "index.html"
    if not index.exists():
        raise SystemExit(f"index.html not found under {root}")

    os.chdir(root)
    print(f"serving static frontend on {args.host}:{args.port} from {root}", flush=True)
    ThreadingHTTPServer((args.host, args.port), SPAFallbackHandler).serve_forever()


if __name__ == "__main__":
    main()
