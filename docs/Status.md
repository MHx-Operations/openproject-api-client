# Project Status

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

- **Bug:** `_calculate_relations_inout()` checks `r.type` but creates the key
  with `r.reversetype` — the `not in` guard is against the wrong key, so
  inbound relation lists can get silently overwritten.

---

## Backlog

### 1. Tests (in progress)

Unit tests with pytest + responses for HTTP mocking.

- [ ] Resource model tests — JSON in, correct attributes out
- [ ] `decode()` / `decode_response()` tests
- [ ] Pagination tests (`get_paged_collection`)
- [ ] Relations bug regression test
- [ ] CLI tests

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

### 4. Housekeeping

- [ ] Type hints cleanup (some `List` imports from `typing` — use `list` for 3.9+)
- [ ] Consistent `__str__` on all models
- [ ] Logging improvements
- [ ] CI pipeline (GitHub Actions)
