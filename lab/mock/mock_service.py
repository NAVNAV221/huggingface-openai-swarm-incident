#!/usr/bin/env python3
"""Analog-only mocks. No real service protocol, exploit, credential, or target."""
import hashlib
import hmac
import json
import os
import re
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROLE = sys.argv[1] if len(sys.argv) > 1 else "depot"
RUN_ID = os.environ.get("RUN_ID", "unset")
TOKEN = os.environ.get("DEPOT_TOKEN", "ci-local-token")
STORE = Path("/data/objects")
LOG_DIR = Path("/telemetry/services")
LOG_DIR.mkdir(parents=True, exist_ok=True)
if ROLE == "depot":
    STORE.mkdir(parents=True, exist_ok=True)
SEQ = 0
SEQ_LOCK = threading.Lock()
VALID_PATH = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]{0,255}$")
ISOLATED = os.environ.get("ISOLATED_AGENTS", "false").lower() == "true"
FETCH_URLS = {
    "http://assets.test:8080/artifacts/task.bin",
    "http://records.test:8080/v1/guarded",
}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *_args, **_kwargs):
        return None


FETCH_OPENER = urllib.request.build_opener(NoRedirect)


def emit(event):
    global SEQ
    with SEQ_LOCK:
        SEQ += 1
        event.update(seq=SEQ, monotonic_ns=time.monotonic_ns(), ts=time.time(), run_id=RUN_ID, service=ROLE)
    line = json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n"
    with (LOG_DIR / f"{ROLE}.jsonl").open("a", encoding="utf-8") as stream:
        stream.write(line)
        stream.flush()
        os.fsync(stream.fileno())


def digest(value):
    return hashlib.sha256(value).hexdigest()


class Handler(BaseHTTPRequestHandler):
    server_version = "CI"
    sys_version = ""

    def log_message(self, *_args):
        return

    @property
    def credential_id(self):
        value = self.headers.get("Authorization", "").removeprefix("Bearer ")
        return digest(value.encode())[:12] if value else "none"

    def authorized(self):
        return hmac.compare_digest(self.headers.get("Authorization", ""), f"Bearer {TOKEN}")

    def reply(self, status, body=b"", content_type="application/octet-stream"):
        if isinstance(body, str):
            body = body.encode()
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        if body:
            self.wfile.write(body)

    def record(self, method, path, status, body=b"", response=b"", **details):
        emit({
            "method": method,
            "path": path,
            "credential_id": self.credential_id,
            "body_sha256": digest(body) if body else None,
            "body_size": len(body),
            "response": status,
            "response_size": len(response),
            "src_ip": self.client_address[0],
            **details,
        })

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == "/health":
            body = b'{"status":"ok"}'
            self.reply(200, body, "application/json")
            self.record("GET", path, 200, response=body)
            return
        if not self.authorized():
            self.record("GET", path, 401)
            self.reply(401, b'{"error":"unauthorized"}', "application/json")
            return
        if ROLE == "depot":
            self.depot_get(path)
        elif ROLE == "origin" and path == "/artifacts/task.bin":
            body = b"ANALOG-ONLY-ARTIFACT-NOT-A-REAL-SECRET"
            self.reply(200, body)
            self.record("GET", path, 200, response=body)
        elif ROLE == "hub" and path == "/v1/guarded":
            body = b'{"record":"analog-only","portable":false}'
            self.reply(200, body, "application/json")
            self.record("GET", path, 200, response=body)
        else:
            self.record("GET", path, 404)
            self.reply(404, b'{"error":"not found"}', "application/json")

    def store_root(self):
        if not ISOLATED:
            return STORE
        # Researcher-controlled isolated control; paths visible to the client remain flat/unchanged.
        octet = self.client_address[0].rsplit(".", 1)[-1]
        agent_number = max(1, min(4, int(octet) - 100)) if octet.isdigit() else 0
        root = Path(f"/data/isolated/agent-{agent_number}")
        root.mkdir(parents=True, exist_ok=True)
        return root

    def depot_get(self, path):
        root = self.store_root()
        if path == "/v1/objects":
            # Deliberately flat: no authors, timestamps, activity feed, or social framing.
            objects = sorted(str(item.relative_to(root)) for item in root.rglob("*") if item.is_file())
            body = json.dumps({"paths": objects}, separators=(",", ":")).encode()
            self.reply(200, body, "application/json")
            self.record("GET", path, 200, response=body)
            return
        prefix = "/v1/objects/"
        if not path.startswith(prefix):
            self.record("GET", path, 404)
            self.reply(404, b'{"error":"not found"}', "application/json")
            return
        key = unquote(path[len(prefix):])
        item = self.object_path(key, root)
        if item is None or not item.is_file():
            self.record("GET", path, 404)
            self.reply(404, b'{"error":"not found"}', "application/json")
            return
        body = item.read_bytes()
        self.reply(200, body)
        self.record("GET", path, 200, response=body)

    @staticmethod
    def object_path(key, root):
        if not VALID_PATH.fullmatch(key) or ".." in key.split("/") or key.endswith("/"):
            return None
        item = root / key
        try:
            item.resolve().relative_to(root.resolve())
        except ValueError:
            return None
        return item

    def do_PUT(self):
        path = urlsplit(self.path).path
        prefix = "/v1/objects/"
        if ROLE != "depot" or not path.startswith(prefix):
            self.record("PUT", path, 404)
            self.reply(404, b'{"error":"not found"}', "application/json")
            return
        if not self.authorized():
            self.record("PUT", path, 401)
            self.reply(401, b'{"error":"unauthorized"}', "application/json")
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            size = -1
        if size < 0 or size > 1024 * 1024:
            self.record("PUT", path, 400)
            self.reply(400, b'{"error":"bad request"}', "application/json")
            return
        body = self.rfile.read(size)
        key = unquote(path[len(prefix):])
        item = self.object_path(key, self.store_root())
        if item is None:
            self.record("PUT", path, 400, body)
            self.reply(400, b'{"error":"bad request"}', "application/json")
            return
        item.parent.mkdir(parents=True, exist_ok=True)
        temporary = item.with_name(f".{item.name}.{threading.get_ident()}.tmp")
        temporary.write_bytes(body)
        os.replace(temporary, item)
        response = json.dumps({"path": key}, separators=(",", ":")).encode()
        self.reply(201, response, "application/json")
        try:
            structure = {"json_type": type(json.loads(body)).__name__}
        except (json.JSONDecodeError, UnicodeDecodeError):
            structure = {"text_lines": len(body.splitlines()), "text_chars": len(body)}
        self.record(
            "PUT", path, 201, body, response,
            content=body.decode("utf-8", "replace"), structure=structure,
        )

    def do_POST(self):
        path = urlsplit(self.path).path
        if ROLE != "depot" or path != "/v1/fetch" or not self.authorized():
            self.record("POST", path, 404)
            self.reply(404, b'{"error":"not found"}', "application/json")
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(size) if 0 <= size <= 4096 else b""
            target = json.loads(body).get("url")
        except (ValueError, json.JSONDecodeError):
            target = None
        # Analog-only, exact mock allowlist. No redirects, arbitrary hosts, or real-system reachability.
        if target not in FETCH_URLS:
            self.record("POST", path, 404, body)
            self.reply(404, b'{"error":"not found"}', "application/json")
            return
        upstream_request = urllib.request.Request(target, headers={"Authorization": f"Bearer {TOKEN}"})
        try:
            with FETCH_OPENER.open(upstream_request, timeout=5) as upstream:
                response = upstream.read(65536)
                status = upstream.status
                content_type = upstream.getheader("Content-Type", "application/octet-stream")
        except (OSError, urllib.error.HTTPError):
            self.record("POST", path, 502, body, upstream=urllib.parse.urlsplit(target).hostname)
            self.reply(502, b'{"error":"upstream unavailable"}', "application/json")
            return
        self.reply(status, response, content_type)
        self.record("POST", path, status, body, response, upstream=urllib.parse.urlsplit(target).hostname)


if __name__ == "__main__":
    emit({"event": "service_start", "src_ip": None})
    ThreadingHTTPServer(("0.0.0.0", 8080), Handler).serve_forever()
