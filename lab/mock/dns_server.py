#!/usr/bin/env python3
"""Authoritative mock DNS with no recursion or upstream forwarding."""
import json
import os
import socket
import struct
import threading
import time
from pathlib import Path

RECORDS = {key.rstrip(".").lower(): value for key, value in json.loads(os.environ["DNS_RECORDS"]).items()}
RUN_ID = os.environ.get("RUN_ID", "unset")
LOG = Path("/telemetry/services/dns.jsonl")
LOG.parent.mkdir(parents=True, exist_ok=True)
LOCK = threading.Lock()
SEQ = 0


def emit(event):
    global SEQ
    with LOCK:
        SEQ += 1
        event.update(seq=SEQ, ts=time.time(), monotonic_ns=time.monotonic_ns(), run_id=RUN_ID, service="dns")
        with LOG.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n")
            stream.flush()


def parse_question(packet):
    if len(packet) < 12:
        raise ValueError("short DNS packet")
    offset = 12
    labels = []
    while True:
        length = packet[offset]
        offset += 1
        if length == 0:
            break
        if length & 0xC0 or length > 63 or offset + length > len(packet):
            raise ValueError("unsupported DNS name")
        labels.append(packet[offset:offset + length].decode("ascii").lower())
        offset += length
    if offset + 4 > len(packet):
        raise ValueError("short DNS question")
    qtype, qclass = struct.unpack("!HH", packet[offset:offset + 4])
    return ".".join(labels), qtype, qclass, packet[12:offset + 4]


def response(packet, peer):
    ident, flags, qdcount, _, _, _ = struct.unpack("!HHHHHH", packet[:12])
    try:
        if qdcount != 1:
            raise ValueError("exactly one question required")
        name, qtype, qclass, question = parse_question(packet)
    except (ValueError, UnicodeError, IndexError):
        emit({"event": "dns_query", "src_ip": peer[0], "response": "FORMERR"})
        return struct.pack("!HHHHHH", ident, 0x8001, 0, 0, 0, 0)
    address = RECORDS.get(name)
    rcode = 0 if address else 3
    answers = b""
    answer_count = 0
    if address and qclass == 1 and qtype in (1, 255):
        answers = question[:len(question) - 4] + struct.pack("!HHIH", 1, 1, 0, 4) + socket.inet_aton(address)
        answer_count = 1
    emit({
        "event": "dns_query", "src_ip": peer[0], "name": name, "qtype": qtype,
        "response": "NXDOMAIN" if rcode == 3 else "NOERROR", "address": address if answer_count else None,
    })
    # AA + requested RD, no RA. TTL=0 prevents the nonce check becoming a cached false pass.
    response_flags = 0x8400 | (flags & 0x0100) | rcode
    return struct.pack("!HHHHHH", ident, response_flags, 1, answer_count, 0, 0) + question + answers


def udp_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("0.0.0.0", 53))
    while True:
        packet, peer = sock.recvfrom(4096)
        try:
            reply = response(packet, peer)
        except Exception as error:
            emit({"event": "dns_error", "src_ip": peer[0], "error": type(error).__name__})
            continue
        sock.sendto(reply, peer)


def tcp_client(client, peer):
    with client:
        client.settimeout(5)
        try:
            header = client.recv(2)
            if len(header) != 2:
                return
            size = struct.unpack("!H", header)[0]
            packet = client.recv(size)
            if len(packet) != size:
                return
            reply = response(packet, peer)
            client.sendall(struct.pack("!H", len(reply)) + reply)
        except (OSError, struct.error):
            return


def tcp_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("0.0.0.0", 53))
    sock.listen()
    while True:
        client, peer = sock.accept()
        threading.Thread(target=tcp_client, args=(client, peer), daemon=True).start()


if __name__ == "__main__":
    threading.Thread(target=tcp_server, daemon=True).start()
    udp_server()
