#!/bin/sh
set -eu
: "${ALLOWED_SOURCE:?missing ALLOWED_SOURCE}"
nft -f - <<EOF
table inet mock_target {
  chain input {
    type filter hook input priority filter; policy accept;
    iifname "lo" accept
    ct state established,related accept
    ip saddr ${ALLOWED_SOURCE} tcp dport 8080 accept
    ip saddr 10.77.0.0/24 tcp dport 8080 reject with icmpx type admin-prohibited
  }
}
EOF
exec python /opt/lab/mock_service.py "$@"
