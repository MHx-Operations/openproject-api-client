# Project Status

## v0.3 Release Notes

### Breaking / Behavior Changes

**Query.json removed (intentional cleanup)**

`Query` instances no longer carry a `Query.json` attribute holding the raw API
JSON payload. The raw `_links` and `_embedded` keys are also no longer set as
lowercased attributes (e.g. `query.links`, `query.embedded`) on `Query` instances.
This was an unintentional debug leak introduced in v0.2 (`debug=True` was passed to
`GenericType.__init__` during development and never removed).

Callers that relied on `Query.json` to access the raw API response must instead call
`ApiClient.get("queries/{id}")` directly and inspect the returned object, or use
`ApiClient.http_get()` to get the raw `requests.Response`.

**`get_workpackages(status=...)` — unknown status values are silently ignored**

Passing an unrecognised status string (anything other than `'all'`, `'open'`, or
`'closed'`) now emits a DEBUG-level log entry and applies no filter, returning all
work packages. A matching `else` clause was added to `get_workpackages_by_project_id`
for consistency. See `get_workpackages` docstring for details.

**`get_workpackages_by_query_id` — None pagesize/offset handled gracefully**

The pagination termination condition now falls back to local `page_size` / `offset`
values when the API omits `pageSize` or `offset` from the `WorkPackageCollection`
envelope, mirroring the existing `get_paged_collection` behavior.

**`get_paged_collection` default `page_size` raised from 5 to 100 (PERF-02)**

The default `page_size` argument of `get_paged_collection` has been increased from `5` to
`100`, reducing the number of HTTP roundtrips by up to 20x for large collections. This change
is non-breaking — callers that pass an explicit `page_size` argument are unaffected; only
callers relying on the default benefit from the new value.

---

## Current State (v0.2.0)

Read-only Python client for the OpenProject API v3. Supports pagination, typed
resource models, and automatic JSON-to-object mapping.

### What works

- **HTTP GET** against all major endpoints (projects, work packages, relations,
  versions, users, placeholder users, memberships, statuses, grids, queries)
- **Pagination** via `get_paged_collection()`
- **Typed models** — API responses are mapped to Python classes (`Project`,
  `WorkPackage`, `Relation`, etc.)
- **Project hierarchy** — parent/child resolution with `fullname` and `path`
- **Relation support** — inbound/outbound relation dicts on `WorkPackage`
- **Filter support** — status filters (open/closed/all) and status ID filters

### Known Issues

- ~~**Bug:** `_calculate_relations_inout()` checks `r.type` but creates the key
  with `r.reversetype`.~~ **Resolved** — code was correct; added regression
  tests to verify multiple relations of the same type accumulate properly.

---

## Backlog

### 1. Tests ✅

Unit tests with pytest + responses for HTTP mocking (86 tests).

- [x] Resource model tests — JSON in, correct attributes out
- [x] `decode()` / `decode_response()` tests
- [x] Pagination tests (`get_paged_collection`)
- [x] Relations regression tests (multiple same-type, mixed directions)
- [x] CLI tests (arg parsing, env vars, json_out)
- [x] Project hierarchy tests (`get_projects_dict`)
- [x] Endpoint convenience method tests (all endpoints covered)

### 2. Write Support

The client is currently read-only. Add:

- [ ] `http_post()` / `http_patch()` / `http_delete()` on `ApiClient`
- [ ] Create/update work packages (`POST` / `PATCH`)
- [ ] Status transitions
- [ ] Add comments (Activities endpoint)
- [ ] File attachments

### 3. CLI (JSON output)

`cli.py` has the skeleton but does nothing yet. Plan:

- [ ] Subcommands: `projects`, `workpackages`, `users`, `versions`, `statuses`
- [ ] `--json` flag → structured JSON output (already wired, needs implementation)
- [ ] Filtering flags (`--status`, `--project`)
- [ ] Exit codes for scripting

### 4. Housekeeping ✅

- [x] Type hints cleanup — replaced `typing.List` with `from __future__ import annotations` + `list`
- [x] Consistent `__str__` on all models (already present)
- [x] Logging improvements — debug logging for HTTP requests and pagination
- [x] CI pipeline (GitHub Actions — Python 3.9–3.13 matrix)
