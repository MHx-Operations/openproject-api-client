# Technology Stack

**Analysis Date:** 2026-05-12

## Languages

**Primary:**
- Python 3.9+ - All source code, CLI, tests, and examples

**Secondary:**
- None

## Runtime

**Environment:**
- CPython 3.9, 3.10, 3.11, 3.12, 3.13 (all supported and tested in CI)

**Package Manager:**
- pip (standard Python tooling)
- Lockfile: Not present (library project — intentionally no lockfile)

## Frameworks

**Core:**
- None — pure Python library with no application framework

**Testing:**
- pytest >= 7.0 — test runner and assertions (`pyproject.toml`)
- responses >= 0.23 — HTTP mocking for requests-based tests (`pyproject.toml`)

**Build/Dev:**
- setuptools >= 68.0, < 77.0 — build backend (`pyproject.toml`)
- wheel — packaging (`pyproject.toml`)
- python-build — used in CI to build sdist/wheel (`python -m build`)

## Key Dependencies

**Critical:**
- requests >= 2.25.1 — sole runtime dependency; used for all HTTP communication with the OpenProject API (`requirements.txt`, `pyproject.toml`)

**Infrastructure:**
- None — no database, no ORM, no web server dependency

## Configuration

**Environment:**
- Runtime configuration via environment variables:
  - `OPENPROJECT_BASEURL` — base URL of the OpenProject instance (e.g. `https://openproject.example.com/`)
  - `OPENPROJECT_APIKEY` — API key for HTTP Basic Auth (username `apikey`, password = key value)
- Alternatively passed as `--baseurl` and `--apikey` CLI flags or directly to `ApiClient(base_url, apikey)` constructor
- `.env` file is gitignored; no `.env` file present in repo

**Build:**
- `pyproject.toml` — PEP 517/518 build config, project metadata, optional deps
- `setup.py` — minimal shim (`setup()`) for editable installs
- `openproject-api-client.iml` — IntelliJ IDEA module file (not used in build)

## Platform Requirements

**Development:**
- Python >= 3.9
- Install: `pip install -e ".[test]"` installs package + test extras
- Run tests: `pytest -v`

**Production:**
- Distributed as a Python package on PyPI: https://pypi.org/project/openproject-api-client/
- Installs CLI entry point `openproject-cli` via `openproject_api_client.cli:main`
- Requires network access to a running OpenProject instance (version 10+)
- No server-side deployment — client library only

---

*Stack analysis: 2026-05-12*
