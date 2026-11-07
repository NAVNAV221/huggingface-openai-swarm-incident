FROM alpine:3.20
RUN apk add --no-cache python3 tcpdump nftables
WORKDIR /opt/lab
COPY lab/telemetry/capture.py lab/telemetry/entrypoint.sh /opt/lab/
RUN chmod 0555 /opt/lab/entrypoint.sh
ENTRYPOINT ["/opt/lab/entrypoint.sh"]
