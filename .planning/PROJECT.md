# openproject-api-client

## What This Is

A Python client and CLI for the OpenProject REST API v3, providing read/write/delete access to projects, work packages, relations, time entries, notifications, and related resources. Used as a library (`from openproject_api_client import ApiClient`) and as a CLI (`openproject-cli`) by developers and operations folks who automate OpenProject workflows.

## Core Value

A correct, predictable, safe-by-default Python wrapper for OpenProject v3 — callers should be able to script against it without worrying about hung connections, dropped pages, or surprising parsing edge cases.

## Requirements

### Validated

<!-- Shipped and confirmed valuable. -->

- Full coverage of the OpenProject v3 resource surface (projects, work packages, relations, versions, users, memberships, statuses, grids, queries, types, priorities, time entries, activities, attachments, notifications, categories)
- HTTP Basic auth with API key (env vars `OPENPROJECT_BASEURL` / `OPENPROJECT_APIKEY` or constructor args)
- CLI entry point `openproject-cli` with text and JSON output modes
- Pytest suite on Python 3.9 – 3.13 via GitHub Actions CI

### Active — v0.3 Hardening Milestone

<!-- Current scope. Building toward these. -->

- [ ] **Security baseline**: configurable request timeout, SSL verify toggle, private apikey attribute, no secret leakage in DEBUG logs
- [ ] **Performance baseline**: `requests.Session` reuse, sensible `page_size` defaults, fix O(n²) project hierarchy builder
- [ ] **Latent-bug fixes**: `Collection._items` default to `[]`, guarded href-id parsing, remove `Query` `debug=True` hardcode, well-defined behavior for unknown `status` strings
- [ ] **Test gap closure**: cover the gaps enumerated in `.planning/codebase/CONCERNS.md` (missing-`_embedded`, URN hrefs, unknown `_type`, pageSize edge cases)

### Out of Scope

<!-- Explicit boundaries. Includes reasoning to prevent re-adding. -->

- Async / `httpx` rewrite — out of scope for this milestone; would be a major version bump and a separate effort
- Live integration tests against a real OpenProject server — infra cost too high; mocked HTTP via `responses` remains the standard
- New API surface area (e.g. budgets, news, forums) — deferred until hardening lands
- Breaking changes to method signatures, attribute names, or default behavior — see Key Decisions
- Replacing the argparse CLI with `click` / `typer` — not justified by the hardening goal
- Linter / formatter introduction (`ruff`, `black`) — out of scope; would touch every file and bury the hardening diff

## Context

This is a brownfield Python library at v0.2.0 with a complete codebase map under `.planning/codebase/`. The library has ~2.2k lines of source across `apiclient.py`, `resources.py`, `cli.py`, and a comparable amount of pytest coverage using `responses` for HTTP mocking. CI runs `pytest -v` across Python 3.9 – 3.13.

The hardening focus is driven entirely by `.planning/codebase/CONCERNS.md`, which catalogs concrete issues found during the codebase map: missing request timeouts, no `requests.Session` reuse, an O(n²) hierarchy builder, several latent bugs around resource parsing, and identifiable test gaps. The work is not exploratory — it's executing on a known punch list.

## Constraints

- **Compatibility**: Non-breaking changes only — keep the v0.2.x public API (method names, signatures, attribute names) intact. New behavior must opt in via kwargs with backward-compatible defaults.
- **Python support**: Must continue to support Python 3.9 – 3.13 (CI matrix). No 3.10+-only syntax.
- **Dependencies**: Single runtime dep (`requests`). Do not add new runtime deps in this milestone.
- **Tech stack**: Python 3.9+, `requests`, `pytest` + `responses`. Argparse for CLI.
- **Style**: No linter / formatter is currently configured; do not introduce one as part of this work.

## Key Decisions

<!-- Decisions that constrain future work. Add throughout project lifecycle. -->

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Non-breaking hardening (v0.2.x → v0.3.0 minor bump, no API breakage) | Library is already in use externally; can't justify forcing a rewrite on consumers for a hardening pass | — Pending |
| New behaviors opt in via kwargs with backward-compatible defaults (e.g. `timeout=None` default; user passes `timeout=30` to enable) | Lets users adopt hardening when they're ready, without surprise behavior changes | — Pending |
| Coarse phase granularity (3–5 phases) for this milestone | Hardening is well-scoped; coarse phases reduce orchestration overhead | — Pending |
| Skip `/gsd-plan-phase` research subagent for these phases | CONCERNS.md and the codebase itself are sufficient context; research would be busywork | — Pending |
| Keep `responses`-based mocking as the only test mode (no live integration tests) | Cost/benefit doesn't justify infra for a client library | ✓ Good |

---
*Last updated: 2026-05-12 after /gsd-new-project initialization*
