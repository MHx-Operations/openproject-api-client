# External Integrations

**Analysis Date:** 2026-05-12

## APIs & External Services

**OpenProject REST API v3:**
- This project IS an API client — its sole purpose is integrating with OpenProject instances
- Endpoint base: `{OPENPROJECT_BASEURL}api/v3/`
- Protocol: HTTPS REST/JSON
- SDK/Client: `requests` library — wrapped in `openproject_api_client/apiclient.py`
- Auth: HTTP Basic Auth — username `apikey`, password = user-supplied API key
- Compression: `accept-encoding: identity, gzip` sent on all requests
- Covered API resources: projects, work packages, relations, versions, users, placeholder users, memberships, statuses, grids (boards), queries, types, priorities, time entries, activities, attachments, notifications, categories

## Data Storage

**Databases:**
- None — this is a stateless client library; all data resides on the remote OpenProject server

**File Storage:**
- Local filesystem only — attachment downloads write to local paths via `http_get` responses; no managed storage integration

**Caching:**
- None

## Authentication & Identity

**Auth Provider:**
- OpenProject native API key authentication
  - Implementation: `requests.auth.HTTPBasicAuth('apikey', api_key)` applied to every request in `openproject_api_client/apiclient.py` (`ApiClient.__init__`, `ApiClient.auth` attribute)
  - Key source: constructor parameter or `OPENPROJECT_APIKEY` env var (used in `openproject_api_client/cli.py` and `examples/simple_client.py`)
  - No OAuth, no token refresh, no session management

## Monitoring & Observability

**Error Tracking:**
- None — no Sentry, Datadog, or similar integration

**Logs:**
- Standard Python `logging` module via `logger = logging.getLogger(__name__)` in `openproject_api_client/apiclient.py`
- Log level DEBUG for all HTTP requests and responses (method, URL, status code)
- Caller controls log configuration; library does not configure root logger

## CI/CD & Deployment

**Hosting:**
- PyPI — https://pypi.org/project/openproject-api-client/
- GitHub repository — https://github.com/MHx-Operations/openproject-api-client

**CI Pipeline:**
- GitHub Actions
  - `ci.yml` (`.github/workflows/ci.yml`): Runs `pytest -v` on Python 3.9–3.13 for every push/PR to `main`
  - `publish.yml` (`.github/workflows/publish.yml`): Triggered on version tags (`v*`); runs tests, builds sdist+wheel, verifies tag matches `pyproject.toml` version, publishes to PyPI using OIDC trusted publishing (`pypa/gh-action-pypi-publish@release/v1`)
- PyPI publish uses GitHub OIDC (`id-token: write` permission) — no stored PyPI token required
- GitHub Actions environment named `pypi` with URL https://pypi.org/project/openproject-api-client/

## Environment Configuration

**Required env vars:**
- `OPENPROJECT_BASEURL` — target OpenProject instance URL (e.g. `https://your-instance.openproject.com/`)
- `OPENPROJECT_APIKEY` — API key from OpenProject user settings

**Secrets location:**
- Not stored in repo; gitignored `.env` pattern in `.gitignore`
- CI secrets: PyPI credentials handled via GitHub OIDC (no stored secrets needed for publish)
- `OPENPROJECT_BASEURL` and `OPENPROJECT_APIKEY` must be supplied by the operator at runtime

## Webhooks & Callbacks

**Incoming:**
- None — this is a client library; it does not expose any HTTP endpoints

**Outgoing:**
- None — all HTTP calls are synchronous REST requests to the OpenProject API; no webhook dispatch

---

*Integration audit: 2026-05-12*
