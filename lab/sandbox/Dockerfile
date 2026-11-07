FROM python:3.12-alpine
RUN apk add --no-cache iproute2
WORKDIR /opt/lab
COPY lab/sandbox/seal_verify.py lab/sandbox/canary.py /opt/lab/
COPY agents /opt/lab/agent
RUN adduser -D -H -u 65532 lab
USER 65532:65532
