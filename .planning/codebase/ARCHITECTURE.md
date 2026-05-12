# Architecture

**Analysis Date:** 2026-05-12

## Pattern

**Style:** Thin client / wrapper library around a single REST API.

- One stateless `ApiClient` class wraps `requests` and exposes typed read/write/delete methods for each OpenProject resource.
- Response JSON is decoded into typed resource model classes (`Project`, `WorkPackage`, `Relation`, …) that all inherit from `GenericType`.
- CLI is a thin argparse dispatcher that constructs an `ApiClient` and forwards parsed args to client methods.

There is no service layer, no DI, no ORM, no event/queue layer — the library is intentionally a flat call-through to the HTTP API.

## Layers

1. **HTTP transport layer** — `openproject_api_client/apiclient.py:65-115` (`http_get`, `http_post`, `http_patch`, `http_delete`). Raw `requests` calls with shared header + auth handling. Centralized in `_endpoint()` (`apiclient.py:51`) and `_headers()` (`apiclient.py:55`).
2. **Decoding layer** — `apiclient.py:198` (`decode_response`) and `apiclient.py:208` (`decode`). Maps JSON `_type` field to a resource class via a hardcoded dispatch table; raises `ApiError` on non-2xx responses.
3. **Resource API layer** — `apiclient.py:227-756`. ~50 methods named `get_*`, `create_*`, `update_*`, `delete_*`, `mark_*`. Each builds a resource path, calls the transport layer, and returns either a typed object, a list, or `bool`.
4. **Model layer** — `openproject_api_client/resources.py`. 21 resource classes that parse JSON into Python attributes (camelCase → lowercase), expand `_links` into `*_id`/`*_href`, and recursively decode `_embedded`.
5. **CLI layer** — `openproject_api_client/cli.py`. Argparse subcommand tree; `dispatch()` (`cli.py`) maps subcommands to `ApiClient` methods; output formatters `text_out`/`json_out`.

## Data Flow

**Read path:**

```
CLI args / Python caller
  → ApiClient.get_<resource>(...)        # apiclient.py
  → http_get(resource, payload)          # builds URL via _endpoint, adds auth
  → requests.get(...)                    # HTTPBasicAuth('apikey', key)
  → decode_response(resp)                # apiclient.py:198
  → decode(json)                         # dispatch on json['_type']
  → ResourceClass(json)                  # resources.py
  → return typed object or list
```

**Write path:**

```
caller → create_workpackage(...) / update_*(...) / delete_*(...)
       → assembles `_links` JSON body
       → http_post / http_patch / http_delete
       → decode_response → typed object (or bool for delete)
```

**Pagination:** `get_paged_collection` (`apiclient.py:163`) loops with `offset`/`pageSize` params until `total` is reached, decoding each page through `Collection` (`resources.py:817`) and accumulating `_embedded.elements`. Default `page_size=5` for the generic helper; callers like `get_workpackages` pass `page_size=100`.

## Key Abstractions

- **`ApiClient`** (`apiclient.py:25`) — single entry point. Holds `base_url`, `apikey`, `HTTPBasicAuth`. All API methods are instance methods.
- **`GenericType`** (`resources.py:22`) — base for every resource model. Subclasses follow a 3-step `__init__`: declare attribute defaults → call `super().__init__()` → parse `_links` / `_embedded`. Provides `__parse_datetime` and `__parse_date` helpers.
- **`Collection`** (`resources.py:817`) and **`WorkPackageCollection`** (`resources.py:849`) — wrap paged API responses (`total`, `count`, `pageSize`, `offset`, `_items`).
- **Decode dispatch** (`apiclient.py:208`) — central map of `_type` string → class constructor. Adding a new resource requires (1) a class in `resources.py`, (2) an entry in `decode`, (3) `__all__` updates in both modules.
- **`ApiError` / `RequestError`** (`apiclient.py`) — explicit exception types for HTTP failures vs. transport/decoding failures.

## Entry Points

- **Python library:** `from openproject_api_client import ApiClient` — re-exported by `openproject_api_client/__init__.py:1-8`.
- **CLI:** `openproject-cli` console script → `openproject_api_client.cli:main` (`pyproject.toml` `[project.scripts]`).
- **Tests:** `pytest -v` (configured implicitly; no `pytest.ini`).
- **No HTTP server, no background worker, no scheduled job** — purely synchronous client.

## Anti-Patterns / Notable Decisions

- **Module-level circular import shim:** `resources.py:11` does `from openproject_api_client import apiclient` (used only for type hints / nothing significant). Works because the import is at module top and not re-entered.
- **Attribute name munging:** JSON keys are forced to `.lower()` (`resources.py:47-52`), so `createdAt` becomes `createdat`. This is consistent but unidiomatic Python (snake_case would be `created_at`).
- **`debug=True` hardcoded for `Query`:** `Query.__init__` always passes `debug=True` to `super()`, attaching raw JSON onto every instance. Probably unintentional — see `.planning/codebase/CONCERNS.md`.
- **Collection items typed as `None` when `_embedded` absent:** `Collection._items = None` (`resources.py:817`) → iterating before items load raises `TypeError`. Most call paths populate it first.
- **No `requests.Session`:** every call opens a new TCP connection. Fine for CLI use, suboptimal for bulk scripting.
- **No retry / no timeout:** `requests.get/post/...` calls omit `timeout=` — a hung server will block forever.

---

*Architecture analysis: 2026-05-12*
