#!/usr/bin/env python3
"""Fixed-upstream, completion-only reverse proxy with independent model I/O logs."""
import http.client
import json
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

UPSTREAM_HOST = os.environ.get("OLLAMA_UPSTREAM_HOST", "host.docker.internal")
UPSTREAM_PORT = int(os.environ.get("OLLAMA_UPSTREAM_PORT", "11434"))
RUN_ID = os.environ.get("RUN_ID", "unset")
LOG = Path("/telemetry/proxy/model-io.jsonl")
LOG.parent.mkdir(parents=True, exist_ok=True)
LOCK = threading.Lock()
SEQ = 0
ALLOWED_POSTS = {"/v1/chat/completions", "/v1/completions"}
MAX_REQUEST = 1024 * 1024
MAX_RESPONSE = 16 * 1024 * 1024


def emit(event):
    global SEQ
    with LOCK:
        SEQ += 1
        event.update(seq=SEQ, ts=time.time(), monotonic_ns=time.monotonic_ns(), run_id=RUN_ID)
        with LOG.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n")
            stream.flush()
            os.fsync(stream.fileno())


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "ModelEndpoint"
    sys_version = ""

    def log_message(self, *_args):
        return

    def json_reply(self, status, payload):
        body = json.dumps(payload, separators=(",", ":")).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        # urlsplit also prevents absolute-form URLs and query-selected upstream behavior.
        parsed = urlsplit(self.path)
        if self.path == "/health" and not parsed.query:
            self.json_reply(200, {"status": "ok"})
            return
        emit({"event": "rejected_request", "src_ip": self.client_address[0], "method": "GET", "path": self.path})
        self.json_reply(404, {"error": {"message": "not found", "type": "invalid_request_error"}})

    def do_POST(self):
        parsed = urlsplit(self.path)
        if parsed.scheme or parsed.netloc or parsed.query or parsed.fragment or parsed.path not in ALLOWED_POSTS:
            emit({"event": "rejected_request", "src_ip": self.client_address[0], "method": "POST", "path": self.path})
            self.json_reply(404, {"error": {"message": "not found", "type": "invalid_request_error"}})
            return
        try:
            size = int(self.headers.get("Content-Length", "-1"))
        except ValueError:
            size = -1
        if size < 0 or size > MAX_REQUEST:
            self.json_reply(400, {"error": {"message": "bad request", "type": "invalid_request_error"}})
            return
        body = self.rfile.read(size)
        try:
            request_json = json.loads(body)
            if not isinstance(request_json, dict) or request_json.get("stream", False):
                raise ValueError("streaming and non-object requests are disabled")
        except (ValueError, UnicodeError):
            self.json_reply(400, {"error": {"message": "bad request", "type": "invalid_request_error"}})
            return
        started = time.monotonic()
        emit({
            "event": "model_request", "src_ip": self.client_address[0], "method": "POST",
            "path": parsed.path, "request": request_json, "body_size": size,
        })
        connection = http.client.HTTPConnection(UPSTREAM_HOST, UPSTREAM_PORT, timeout=120)
        try:
            connection.request("POST", parsed.path, body=body, headers={
                "Content-Type": "application/json", "Content-Length": str(size),
                "Accept": "application/json", "Host": f"{UPSTREAM_HOST}:{UPSTREAM_PORT}",
                "Connection": "close",
            })
            upstream = connection.getresponse()
            response_body = upstream.read(MAX_RESPONSE + 1)
            if len(response_body) > MAX_RESPONSE:
                raise ValueError("upstream response too large")
            status = upstream.status
            content_type = upstream.getheader("Content-Type", "application/json")
        except (OSError, ValueError, http.client.HTTPException):
            emit({
                "event": "model_response", "src_ip": self.client_address[0], "path": parsed.path,
                "status": 502, "duration_ms": round((time.monotonic() - started) * 1000, 3),
                "error": "upstream unavailable",
            })
            self.json_reply(502, {"error": {"message": "upstream unavailable", "type": "upstream_error"}})
            return
        finally:
            connection.close()
        emit({
            "event": "model_response", "src_ip": self.client_address[0], "path": parsed.path,
            "status": status, "duration_ms": round((time.monotonic() - started) * 1000, 3),
            "response": response_body.decode("utf-8", "replace"), "body_size": len(response_body),
        })
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(response_body)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(response_body)
        self.close_connection = True

    def do_PUT(self):
        self.json_reply(404, {"error": {"message": "not found", "type": "invalid_request_error"}})

    def do_DELETE(self):
        self.json_reply(404, {"error": {"message": "not found", "type": "invalid_request_error"}})


class Server(ThreadingHTTPServer):
    daemon_threads = True


if __name__ == "__main__":
    emit({"event": "proxy_start", "src_ip": None, "upstream": "fixed-local"})
    Server(("0.0.0.0", 11434), Handler).serve_forever()
