#!/bin/sh
set -eu
: "${LAB_BRIDGE:?missing LAB_BRIDGE}"
: "${LAB_GATEWAY:?missing LAB_GATEWAY}"
mkdir -p /telemetry/network
nft -f - <<EOF
table inet hf_lab {
  chain input {
    type filter hook input priority 10; policy accept;
    iifname "${LAB_BRIDGE}" ip daddr ${LAB_GATEWAY} counter log prefix "HF_LAB_DROP " level warn reject with icmpx type admin-prohibited
  }
  chain forward {
    type filter hook forward priority 10; policy accept;
    iifname "${LAB_BRIDGE}" oifname != "${LAB_BRIDGE}" counter log prefix "HF_LAB_DROP " level warn drop
  }
}
EOF
TCPDUMP_PID=""
LOGGER_PID=""
# shellcheck disable=SC2329
cleanup() {
  [ -z "$TCPDUMP_PID" ] || kill "$TCPDUMP_PID" 2>/dev/null || true
  [ -z "$LOGGER_PID" ] || kill "$LOGGER_PID" 2>/dev/null || true
  nft delete table inet hf_lab 2>/dev/null || true
}
trap cleanup EXIT INT TERM
tcpdump -i "$LAB_BRIDGE" -nn -s0 -U -w /telemetry/network/labnet.pcap &
TCPDUMP_PID=$!
python3 /opt/lab/capture.py &
LOGGER_PID=$!
while kill -0 "$TCPDUMP_PID" 2>/dev/null && kill -0 "$LOGGER_PID" 2>/dev/null; do
  sleep 1
done
echo "telemetry capture process exited; failing closed" >&2
exit 1
