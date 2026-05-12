# Roadmap: openproject-api-client v0.3 Hardening

**Milestone:** v0.3 Hardening
**Created:** 2026-05-12
**Granularity:** Coarse (4 phases)
**Strategy:** Bug fixes first (no new API), then opt-in security knobs, then performance, then test gap closure to lock in everything.

## Phase Sequencing

```
Phase 1 (Latent bugs) ──► Phase 2 (Security knobs) ──► Phase 3 (Performance)
                                                            │
                                                            ▼
                                                   Phase 4 (Test gap closure)
```

Phase 4 lands last so its tests can reference behavior introduced in Phases 1–3.

## Phase 1 — Latent Bug Fixes

**Goal:** Eliminate the known latent bugs in resource parsing and collection iteration without changing any public API behavior in the common path.

**Requirements covered:** BUG-01, BUG-02, BUG-03, BUG-04, BUG-05

**Success criteria:**
- `Collection._items` defaults to `[]`; iteration of an empty collection is safe.
- Resource href parsing returns `None` for unparseable hrefs instead of raising.
- `Query` instances no longer carry a `json` attribute by default.
- `get_workpackages(status=...)` has documented, tested behavior for unknown statuses.
- `get_workpackages_by_query_id` uses the same empty-handling as `get_paged_collection`.
- All existing tests still pass on the Python 3.9 – 3.13 matrix.

**Out of scope for this phase:** Any new constructor kwargs, performance changes.

## Phase 2 — Security Baseline

**Goal:** Make safe-by-default behavior reachable for callers via opt-in kwargs; eliminate the API-key leakage risk in logs.

**Requirements covered:** SEC-01, SEC-02, SEC-03, SEC-04

**Success criteria:**
- `ApiClient(..., timeout=None, verify_ssl=True)` accepted; defaults preserve current behavior.
- `timeout` and `verify_ssl` propagated to all `requests.*` calls.
- `self._apikey` is the canonical storage; `self.apikey` remains as a property for backwards compatibility but doesn't surface the value in `repr()` casually.
- `caplog`-based test confirms no substring of the API key appears in DEBUG log output for a representative GET / POST call.

**Out of scope for this phase:** Retry / backoff, session reuse (lands in Phase 3).

## Phase 3 — Performance Baseline

**Goal:** Eliminate the three performance footguns: per-request TCP reconnects, undersized default `page_size`, and the O(n²) project hierarchy builder.

**Requirements covered:** PERF-01, PERF-02, PERF-03

**Success criteria:**
- A single `requests.Session` is reused for the lifetime of each `ApiClient` instance.
- `get_paged_collection` default `page_size` raised to `100` (or comparable sensible value); explicit callers unaffected.
- `get_projects_dict` runs in O(n) — single pass + index dict. Same output shape; output verified against the existing tests + a new test on a 1000-node synthetic input.

**Out of scope for this phase:** Streaming downloads, connection pooling beyond the defaults `requests.Session` provides.

## Phase 4 — Test Gap Closure

**Goal:** Close the test coverage gaps catalogued in `.planning/codebase/CONCERNS.md` and lock in the behavior introduced by Phases 1–3.

**Requirements covered:** TEST-01 through TEST-08

**Success criteria:**
- New tests for `Collection` without `_embedded`, URN/empty hrefs, unknown `_type`, `pageSize: null`, unknown `status=`, no-key-in-logs, `Session` reuse, and `timeout` / `verify` propagation.
- All new tests pass on Python 3.9 – 3.13.
- CI green on `main` after merge.

**Out of scope for this phase:** Coverage tooling rollout (deferred), property-based testing.

## Coverage

All 20 v0.3 requirements are mapped to one of the four phases (see `.planning/REQUIREMENTS.md` → Traceability table).

## After This Milestone

After v0.3 ships:
- Tag and publish `0.3.0` to PyPI.
- Reassess the v0.4+ backlog in `REQUIREMENTS.md` (async, snake_case attributes, retries, formatter rollout).
- Update `.planning/codebase/CONCERNS.md` to remove resolved items.

---
*Roadmap created: 2026-05-12*
