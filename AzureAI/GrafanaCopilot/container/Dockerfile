# VM Reboot Analyzer report service — lightweight Alpine image.
#
# Alpine + system Chromium/Chromedriver + Selenium is the reliable lightweight
# combo for headless browsing on musl (Playwright does not officially support
# Alpine). Pillow comes from the apk package to avoid a C toolchain.
FROM alpine:3.20

# Runtime deps only:
#  - python3 / py3-pip / py3-pillow : app + image cropping
#  - chromium / chromium-chromedriver : headless rendering + screenshots
#  - nss freetype harfbuzz ttf-freefont font-noto-emoji : Chromium fonts/rendering
#  - openssl : self-signed TLS cert at boot
#  - tini : clean PID 1 / signal handling
RUN apk add --no-cache \
        python3 py3-pip py3-pillow \
        chromium chromium-chromedriver \
        nss freetype harfbuzz ttf-freefont font-noto-emoji \
        openssl tini \
    && rm -rf /var/cache/apk/*

ENV CHROME_BIN=/usr/bin/chromium-browser \
    CHROMEDRIVER=/usr/bin/chromedriver \
    PYTHONUNBUFFERED=1 \
    PORT=443 \
    REPORTS_DIR=/reports \
    CERT_DIR=/certs \
    MAX_CONCURRENCY=2

# Install Selenium into the system site-packages (shared with py3-pillow).
# PEP 668: Alpine's python is externally managed, so --break-system-packages.
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --break-system-packages -r /tmp/requirements.txt

COPY app/ /app/
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

VOLUME ["/reports", "/certs"]
EXPOSE 443

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
    CMD wget -qO- --no-check-certificate https://127.0.0.1:${PORT}/health || exit 1

ENTRYPOINT ["/sbin/tini", "--", "/entrypoint.sh"]
