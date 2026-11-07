FROM python:3.12-alpine
RUN apk add --no-cache nftables iproute2
WORKDIR /opt/lab
COPY lab/proxy/app.py lab/proxy/entrypoint.sh /opt/lab/
COPY lab/sandbox/seal_verify.py /opt/lab/seal_verify.py
RUN chmod 0555 /opt/lab/entrypoint.sh
EXPOSE 11434
ENTRYPOINT ["/opt/lab/entrypoint.sh"]
