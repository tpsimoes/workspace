# VM Reboot Analyzer — containerized report service

A lightweight Linux container that hosts an HTTPS server on **port 443**. POST a
Grafana *Virtual Machine Reboot Analyzer* dashboard URL and it immediately
returns a link where the generated HTML report will appear once ready (report
generation runs in the background and usually outlasts the HTTP request).

## How it works

```
POST /                 body = dashboard URL (raw text / form `url` / JSON {"url":...})
  -> 202  "Your report will soon be available at https://<host>/reports/<random>.html"
     (a background worker scrapes the dashboard and writes that file)

GET  /reports/<file>   downloads the report when ready
  -> 200 html          (Content-Disposition: attachment)
  -> 202               while still generating
  -> 404               unknown token
GET  /health           -> 200 ok
```

Reports are stored in the container's **ephemeral** storage (`/reports`), no
persistence required.

## Build & run

```bash
cd container
docker build -t vmrca .

docker run --rm -p 8443:443 \
  -e PUBLIC_BASE_URL=https://localhost:8443 \
  -e GRAFANA_COOKIES="$(cat cookies.json)" \
  vmrca
```

Then:

```bash
curl -sk -X POST https://localhost:8443/ \
  -d 'https://asw-main-....grafana.azure.com/d/tictrm7/virtual-machine-reboot-analyzer?...&var-_id=%2Fsubscriptions%2F...%2FvirtualMachines%2Fazlsapkaqdb06'
# -> Your report will soon be available at https://localhost:8443/reports/ab12cd34....html

# poll until 200
curl -sk https://localhost:8443/reports/ab12cd34....html -o report.html
```

## Authentication

Azure Managed Grafana requires a signed-in session. Provide one via the
`GRAFANA_COOKIES` env var — a JSON array of cookie objects exported from an
authenticated browser session:

```json
[{"name":"grafana_session","value":"...","domain":"asw-main-....grafana.azure.com","path":"/"}]
```

Without valid cookies the scrape still runs but will capture the login page; the
report then contains an explanatory error note (the pre-announced URL always
resolves to *something*).

## Configuration (env vars)

| Var | Default | Purpose |
|-----|---------|---------|
| `PORT` | `443` | Listen port |
| `PUBLIC_BASE_URL` | (from `Host` header) | Base URL used in the announced link |
| `REPORTS_DIR` | `/reports` | Ephemeral report output dir |
| `GRAFANA_COOKIES` | — | JSON cookie array for the Grafana session |
| `MAX_CONCURRENCY` | `2` | Max simultaneous report generations |
| `CERT_CN` | `localhost` | CN for the auto self-signed cert |
| `TLS_CERT` / `TLS_KEY` | `/certs/server.*` | Provide your own cert to skip self-signing |

## Image

`alpine:3.20` + system `chromium`/`chromium-chromedriver` + `selenium` +
`py3-pillow`. Alpine + Selenium is used because Playwright does not officially
support musl. The browser is the only heavy component; everything else is
stdlib.

## Files

| File | Role |
|------|------|
| `app/server.py` | stdlib HTTPS server: POST → announce URL + async, GET → serve |
| `app/generate.py` | Orchestrates one report (scrape → build), lazy browser import |
| `app/scrape.py` | Headless-Chromium (Selenium) panel capture + manifest |
| `app/report.py` | Manifest → self-contained dark-theme HTML RCA report |
| `entrypoint.sh` | Generates the self-signed cert then runs the server |
