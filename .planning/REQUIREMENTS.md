# Requirements: openproject-api-client v0.3 Hardening

**Defined:** 2026-05-12
**Core Value:** A correct, predictable, safe-by-default Python wrapper for OpenProject v3.

## v0.3 Requirements

Requirements for the hardening milestone. All changes must be non-breaking with respect to the v0.2.x public API.

### Security (SEC)

- [x] **SEC-01**: `ApiClient.__init__` accepts an optional `timeout` kwarg (seconds). Default `None` preserves current behavior (no timeout). When set, `timeout` is passed on every `requests.*` call.
- [x] **SEC-02**: `ApiClient.__init__` accepts an optional `verify_ssl` kwarg (`True` | `False` | path to CA bundle). Default `True` (current behavior). Passed to every `requests.*` call.
- [x] **SEC-03**: The API key is stored on a private attribute (e.g. `self._apikey`) instead of `self.apikey`. A public `self.apikey` accessor remains for backwards compatibility but does not appear in `repr()` / `vars()` output for casual logging.
- [x] **SEC-04**: DEBUG-level logging never includes the `Authorization` header or any rendered form of the API key. A regression test asserts that `caplog` output from a known request contains no substring of the test key.

### Performance (PERF)

- [x] **PERF-01**: `ApiClient` uses a single `requests.Session` for the lifetime of the instance. Session is constructed lazily and reused across all HTTP methods.
- [x] **PERF-02**: `get_paged_collection` default `page_size` is raised from `5` to a sensible value (target: `100`) without changing the function signature in a breaking way. Existing callers that pass explicit `page_size` are unaffected.
- [x] **PERF-03**: `get_projects_dict` builds the parent/child hierarchy in O(n) (single pass with an index dict) instead of the current O(n²) re-scan. Same output shape.

### Latent Bugs (BUG)

- [x] **BUG-01**: `Collection._items` defaults to `[]` (not `None`). Iterating an empty `Collection` is safe (`for x in collection: ...` raises nothing).
- [x] **BUG-02**: Resource-class href parsing tolerates `None`, empty strings, and URN-style hrefs (e.g. `urn:openproject:work_packages:42`). When an ID cannot be parsed, the relevant `*_id` attribute is `None`, never a `ValueError`.
- [x] **BUG-03**: `Query.__init__` no longer forces `debug=True` to its base constructor. Callers may opt in to `debug=True` explicitly. CLI `json_out` no longer emits raw `_links`/`_embedded` blobs for queries by default.
- [x] **BUG-04**: `get_workpackages(status=...)` (and analogues) have well-defined behavior for unknown `status` strings — either a documented passthrough or a `ValueError`. Behavior is covered by a test.
- [x] **BUG-05**: `get_workpackages_by_query_id` shares the same `None`-guard / empty-collection handling as `get_paged_collection`.

### Test Coverage (TEST)

- [x] **TEST-01**: Test for `Collection` constructed from a response missing `_embedded.elements` — iterates safely (covers BUG-01).
- [x] **TEST-02**: Test for resource href parsing with `None`, empty, and URN-style hrefs (covers BUG-02).
- [x] **TEST-03**: Test for unknown `_type` strings in `decode` — well-defined fallback behavior.
- [x] **TEST-04**: Test for `pageSize: null` in a paged response — pagination loop terminates correctly.
- [x] **TEST-05**: Test for unknown `status=` strings in `get_workpackages` (covers BUG-04).
- [x] **TEST-06**: Test asserting no API-key substring appears in DEBUG log output (covers SEC-04).
- [x] **TEST-07**: Test asserting `Session` reuse across two sequential calls (covers PERF-01).
- [x] **TEST-08**: Test asserting `timeout` and `verify` kwargs are propagated to `requests` (covers SEC-01, SEC-02).

## v0.4+ Requirements

Deferred to future milestones. Tracked but not in the current roadmap.

### Async / Streaming

- **ASYNC-01**: Async variant of `ApiClient` (likely via `httpx`)
- **STREAM-01**: Streaming attachment downloads for large files

### API surface

- **API-01**: Budgets, news, forums, custom-action endpoints
- **API-02**: Webhook helpers

### Developer Experience

- **DX-01**: Snake-case attribute names on resource models (breaking — would be a v1.0 change)
- **DX-02**: Adopt `ruff` + a formatter
- **DX-03**: Replace argparse CLI with `click` or `typer`

## Out of Scope

Explicitly excluded for v0.3. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Async / httpx rewrite | Major effort; would be a v1.0 candidate, not a hardening pass |
| Live integration tests against a real OpenProject server | Infra cost; mocked HTTP via `responses` remains the standard |
| Breaking changes to method signatures or attribute names | Milestone is explicitly non-breaking (v0.3.0 minor bump) |
| Linter / formatter rollout | Would bury the hardening diff under style churn |
| New API resources (budgets, news, forums) | Deferred until hardening lands |
| Retries / backoff | Could land in a follow-up; not required for this milestone |
| Replacing argparse CLI | Not justified by the hardening goal |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| BUG-01 | Phase 1 | Complete |
| BUG-02 | Phase 1 | Complete |
| BUG-03 | Phase 1 | Complete |
| BUG-04 | Phase 1 | Complete |
| BUG-05 | Phase 1 | Complete |
| SEC-01 | Phase 2 | Complete |
| SEC-02 | Phase 2 | Complete |
| SEC-03 | Phase 2 | Complete |
| SEC-04 | Phase 2 | Complete |
| PERF-01 | Phase 3 | Complete |
| PERF-02 | Phase 3 | Pending |
| PERF-03 | Phase 3 | Complete |
| TEST-01 | Phase 4 | Complete |
| TEST-02 | Phase 4 | Complete |
| TEST-03 | Phase 4 | Complete |
| TEST-04 | Phase 4 | Complete |
| TEST-05 | Phase 4 | Complete |
| TEST-06 | Phase 4 | Complete |
| TEST-07 | Phase 4 | Complete |
| TEST-08 | Phase 4 | Complete |

**Coverage:**
- v0.3 requirements: 20 total
- Mapped to phases: 20
- Unmapped: 0

---
*Requirements defined: 2026-05-12*
*Last updated: 2026-05-12 after /gsd-new-project initialization*
