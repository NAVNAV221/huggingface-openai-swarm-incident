FROM python:3.12-alpine
RUN apk add --no-cache nftables
WORKDIR /opt/lab
COPY lab/mock/dns_server.py lab/mock/mock_service.py lab/mock/target-entrypoint.sh /opt/lab/
RUN chmod 0555 /opt/lab/target-entrypoint.sh && adduser -D -H -u 65532 lab
USER root
