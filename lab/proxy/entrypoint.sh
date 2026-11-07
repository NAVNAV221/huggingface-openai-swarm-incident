#!/bin/sh
set -eu
: "${OLLAMA_UPSTREAM_HOST:?missing upstream host}"
: "${OLLAMA_UPSTREAM_PORT:?missing upstream port}"
UPSTREAM_IP="$(python -c 'import os,socket; print(socket.gethostbyname(os.environ["OLLAMA_UPSTREAM_HOST"]))')"
export OLLAMA_UPSTREAM_IP="$UPSTREAM_IP"
nft -f - <<EOF
table inet hf_proxy {
  chain input {
    type filter hook input priority filter; policy drop;
    ct state established,related accept
    iifname "lo" accept
    ip saddr 10.77.0.0/24 tcp dport 11434 accept
    log prefix "HF_PROXY_INPUT_DROP " level warn
    reject with icmpx type admin-prohibited
  }
  chain forward {
    type filter hook forward priority filter; policy drop;
  }
  chain output {
    type filter hook output priority filter; policy drop;
    ct state established,related accept
    oifname "lo" accept
    ip daddr 10.77.0.1 reject with icmpx type admin-prohibited
    ip daddr 10.77.0.0/24 accept
    ip daddr ${UPSTREAM_IP} tcp dport ${OLLAMA_UPSTREAM_PORT} accept
    log prefix "HF_PROXY_OUTPUT_DROP " level warn
    reject with icmpx type admin-prohibited
  }
}
EOF
python /opt/lab/app.py &
APP_PID=$!
cleanup() {
  kill "$APP_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM
attempt=0
until python -c 'import urllib.request; urllib.request.urlopen("http://127.0.0.1:11434/health", timeout=1).read()' 2>/dev/null; do
  attempt=$((attempt + 1))
  if [ "$attempt" -ge 30 ]; then
    echo "model proxy failed to become healthy" >&2
    exit 1
  fi
  sleep 0.2
done
# Startup is fail-closed: the service exits if its own namespace is not sealed.
python /opt/lab/seal_verify.py --role proxy
wait "$APP_PID"
