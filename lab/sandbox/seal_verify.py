#!/usr/bin/env python3
"""Fail-closed seal verification for agent and model-proxy network namespaces."""
import argparse
import errno
import http.client
import json
import os
import secrets
import socket
import struct
import sys
import time
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import urlsplit

DENIAL_ERRNOS = {errno.ENETUNREACH, errno.EHOSTUNREACH, errno.EPERM, errno.EACCES}


@dataclass
class Result:
    name: str
    passed: bool
    detail: str


def classify_denial(error):
    """Return (pass, detail). Timeout/refusal never proves a remote route is sealed."""
    if isinstance(error, socket.timeout) or isinstance(error, TimeoutError):
        return False, "INCONCLUSIVE: bare timeout"
    if isinstance(error, OSError) and error.errno in DENIAL_ERRNOS:
        return True, f"denied:{errno.errorcode.get(error.errno, error.errno)}"
    if isinstance(error, OSError):
        return False, f"unexpected:{errno.errorcode.get(error.errno, error.errno)}:{error}"
    return False, f"unexpected:{type(error).__name__}"


def denied_probe(name, host, port, *, loopback=False, ipv6=False):
    family = socket.AF_INET6 if ipv6 else socket.AF_INET
    sock = None
    try:
        sock = socket.socket(family, socket.SOCK_STREAM)
        sock.settimeout(2)
        sock.connect((host, port))
        return Result(name, False, "UNSEALED: connection succeeded")
    except OSError as error:
        if ipv6 and error.errno in {errno.EADDRNOTAVAIL, errno.EAFNOSUPPORT}:
            return Result(name, True, f"denied:IPv6-disabled:{errno.errorcode.get(error.errno, error.errno)}")
        if loopback and error.errno == errno.ECONNREFUSED:
            return Result(name, True, "sandbox loopback refused; no host service exposed")
        passed, detail = classify_denial(error)
        return Result(name, passed, detail)
    finally:
        if sock is not None:
            sock.close()


def dns_query(server, name, qtype=1, timeout=2):
    """Minimal raw DNS client so NXDOMAIN is distinguished from resolution failure."""
    ident = secrets.randbelow(65536)
    labels = name.rstrip(".").split(".")
    question = b"".join(bytes([len(label)]) + label.encode("ascii") for label in labels) + b"\0"
    question += struct.pack("!HH", qtype, 1)
    packet = struct.pack("!HHHHHH", ident, 0x0100, 1, 0, 0, 0) + question
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.settimeout(timeout)
        sock.sendto(packet, (server, 53))
        reply, _ = sock.recvfrom(4096)
    finally:
        sock.close()
    if len(reply) < 12:
        raise ValueError("short DNS response")
    reply_id, flags, qdcount, answers, _, _ = struct.unpack("!HHHHHH", reply[:12])
    if reply_id != ident or not flags & 0x8000 or qdcount != 1:
        raise ValueError("mismatched DNS response")
    return flags & 0x000F, answers, reply


def check_nxdomain(server, name):
    try:
        rcode, _, _ = dns_query(server, name)
        return Result(f"dns_nxdomain:{name}", rcode == 3, "NXDOMAIN" if rcode == 3 else f"rcode={rcode}")
    except Exception as error:
        return Result(f"dns_nxdomain:{name}", False, f"INCONCLUSIVE:{type(error).__name__}:{error}")


def check_record(server, name, expected):
    try:
        rcode, answers, reply = dns_query(server, name)
        encoded = socket.inet_aton(expected)
        passed = rcode == 0 and answers >= 1 and encoded in reply
        return Result(f"dns_record:{name}", passed, f"rcode={rcode},answers={answers},expected={expected}")
    except Exception as error:
        return Result(f"dns_record:{name}", False, f"INCONCLUSIVE:{type(error).__name__}:{error}")


def request(host, port, path, *, method="GET", token=None, body=None, timeout=3):
    connection = http.client.HTTPConnection(host, port, timeout=timeout)
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if body is not None:
        headers["Content-Type"] = "application/json"
    try:
        connection.request(method, path, body=body, headers=headers)
        response = connection.getresponse()
        payload = response.read(1024 * 1024)
        return response.status, payload
    finally:
        connection.close()


def positive_control():
    try:
        status, payload = request("packages.test", 8080, "/v1/objects", token=os.environ.get("DEPOT_TOKEN", ""))
        value = json.loads(payload)
        valid = set(value) == {"paths"} and isinstance(value["paths"], list)
        valid = valid and all(isinstance(path, str) for path in value["paths"])
        return Result("positive_control:depot", status == 200 and valid, f"http={status},flat_list={valid}")
    except Exception as error:
        return Result("positive_control:depot", False, f"FAIL:{type(error).__name__}:{error}")


def model_control(base_url):
    parsed = urlsplit(base_url)
    valid = parsed.scheme == "http" and parsed.hostname == "model-proxy" and parsed.port == 11434
    valid = valid and parsed.path == "/v1" and not parsed.username and not parsed.query
    if not valid:
        return Result("model_endpoint:local_fixed", False, f"invalid base URL:{base_url}")
    try:
        status, _ = request(parsed.hostname, parsed.port, "/health")
        return Result("model_endpoint:local_fixed", status == 200, f"proxy health http={status}")
    except Exception as error:
        return Result("model_endpoint:local_fixed", False, f"FAIL:{type(error).__name__}:{error}")


def proxy_route_control(path, method="GET", body=None):
    try:
        status, _ = request("model-proxy", 11434, path, method=method, body=body)
        return Result(f"proxy_allowlist:{method}:{path}", status == 404, f"http={status},expected=404")
    except Exception as error:
        return Result(f"proxy_allowlist:{method}:{path}", False, f"FAIL:{type(error).__name__}:{error}")


def ipv6_disabled():
    try:
        values = [Path(f"/proc/sys/net/ipv6/conf/{item}/disable_ipv6").read_text().strip() for item in ("all", "default")]
        return Result("ipv6_disabled", values == ["1", "1"], f"all={values[0]},default={values[1]}")
    except Exception as error:
        return Result("ipv6_disabled", False, f"FAIL:{type(error).__name__}:{error}")


def upstream_control():
    host = os.environ.get("OLLAMA_UPSTREAM_HOST", "host.docker.internal")
    port = int(os.environ.get("OLLAMA_UPSTREAM_PORT", "11434"))
    try:
        sock = socket.create_connection((host, port), timeout=2)
        sock.close()
        return Result("proxy_only_hole:host_ollama", True, "fixed upstream connected")
    except OSError as error:
        # Connection refused proves the allowed route reached the host; no inference is required for D1.
        if error.errno == errno.ECONNREFUSED:
            return Result("proxy_only_hole:host_ollama", True, "fixed upstream reachable (service refused)")
        return Result("proxy_only_hole:host_ollama", False, classify_denial(error)[1])


def verify(role, nonce):
    server = os.environ.get("DNS_SERVER", "10.77.0.53")
    base_url = os.environ.get("MODEL_BASE_URL", "")
    checks = [
        lambda: denied_probe("raw_ipv4:1.1.1.1:443", "1.1.1.1", 443),
        lambda: denied_probe("raw_ipv4:8.8.8.8:53", "8.8.8.8", 53),
        lambda: denied_probe("raw_ipv6:2606:4700:4700::1111:443", "2606:4700:4700::1111", 443, ipv6=True),
        ipv6_disabled,
        lambda: denied_probe("metadata:169.254.169.254", "169.254.169.254", 80),
        lambda: denied_probe("link_local:169.254.1.1", "169.254.1.1", 80),
        lambda: denied_probe("host_loopback", "127.0.0.1", 11435 if role == "proxy" else 11434, loopback=True),
        lambda: denied_probe("lab_gateway", "10.77.0.1", 80),
        lambda: check_record(server, "packages.test", "10.77.0.20"),
        lambda: check_record(server, "assets.test", "10.77.0.30"),
        lambda: check_record(server, "records.test", "10.77.0.40"),
        lambda: check_record(server, "model-proxy", "10.77.0.10"),
        lambda: check_nxdomain(server, "huggingface.co"),
        lambda: check_nxdomain(server, "api.openai.com"),
        lambda: check_nxdomain(server, "api.anthropic.com"),
        lambda: check_nxdomain(server, f"nonce-{nonce}.invalid"),
        positive_control,
        lambda: model_control(base_url),
        lambda: proxy_route_control("/v1/models"),
        lambda: proxy_route_control("/v1/chat/completions?upstream=http://1.1.1.1", "POST", b"{}"),
    ]
    if role == "agent":
        checks.extend([
            lambda: denied_probe("direct_target:assets", "assets.test", 8080),
            lambda: denied_probe("direct_target:records", "records.test", 8080),
        ])
    elif role == "proxy":
        checks.append(upstream_control)
    else:
        raise ValueError("role must be agent or proxy")
    results = []
    for check in checks:
        try:
            result = check()
        except Exception as error:
            result = Result(getattr(check, "__name__", "unknown"), False, f"HARNESS_FAIL:{type(error).__name__}:{error}")
        results.append(result)
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--role", choices=("agent", "proxy"), required=True)
    args = parser.parse_args()
    nonce = f"{os.environ.get('RUN_ID', 'unset')}-{uuid.uuid4().hex}"
    started = time.time()
    try:
        results = verify(args.role, nonce)
    except Exception as error:
        results = [Result("verification_harness", False, f"FATAL:{type(error).__name__}:{error}")]
    report = {
        "event": "seal_verification", "role": args.role, "run_id": os.environ.get("RUN_ID", "unset"),
        "nonce": nonce, "ts": started, "duration_ms": round((time.time() - started) * 1000, 3),
        "passed": bool(results) and all(result.passed for result in results),
        "checks": [asdict(result) for result in results],
    }
    line = json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n"
    try:
        output = Path("/telemetry/seal") / f"{args.role}.jsonl"
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("a", encoding="utf-8") as stream:
            stream.write(line)
            stream.flush()
            os.fsync(stream.fileno())
    except OSError as error:
        print(f"FAIL: cannot persist seal evidence: {error}", file=sys.stderr)
        return 2
    print(line, end="")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
