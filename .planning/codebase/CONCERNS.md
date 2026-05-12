# Codebase Concerns

**Analysis Date:** 2026-05-12

## Tech Debt

**Stale `docs/Status.md` Backlog:**
- Issue: `docs/Status.md` still lists "Write Support" and "CLI" items as open backlog (with unchecked boxes), but all of these features are already fully implemented in the current codebase. The document has not been updated to reflect the current state.
- Files: `docs/Status.md`
- Impact: Misleading for new contributors — they may think write/CLI features are unimplemented and duplicate work.
- Fix approach: Update `docs/Status.md` to reflect the current v0.2.0 feature set, or remove the stale backlog section.

**No Request Session / Connection Pooling:**
- Issue: Every HTTP call creates a fresh `requests.get/post/patch/delete` call instead of using a `requests.Session`. This means no connection pooling, no shared headers, and no shared auth object at the transport layer.
- Files: `openproject_api_client/apiclient.py` lines 70, 83, 96, 109
- Impact: Performance degradation when making many calls (e.g., paginated fetches over hundreds of pages); also makes it impossible to configure per-session settings like retries or mount adapters.
- Fix approach: Store a `requests.Session` on `__init__`, configure auth and default headers on it, and replace the four bare `requests.*` calls with `self._session.*` calls.

**Duplicated Filter-Building Logic:**
- Issue: The `status` filter construction (building a `filters` list with `status_id` operator values) is copy-pasted verbatim between `get_workpackages()` and `get_workpackages_by_project_id()`.
- Files: `openproject_api_client/apiclient.py` lines 277–292 and 309–325
- Impact: Any change to the filter format must be made in two places; bugs could diverge silently.
- Fix approach: Extract a private `_build_status_filter(status, status_ids)` helper method and call it from both public methods.

**API Key Stored as Plain Instance Attribute:**
- Issue: `self.apikey = apikey` stores the raw API key as a readable public attribute on the client instance. Any code holding a reference to the client can read the key via `client.apikey`.
- Files: `openproject_api_client/apiclient.py` line 45
- Impact: Key exposure via attribute access, accidental logging of the object repr, or serialization.
- Fix approach: Store as a private attribute (`self._apikey`) and remove it from public interface; the `requests` auth object (`self.auth`) already holds the credential and is the only place it is needed.

**`get_workpackages_by_query_id` Uses Hardcoded Page Size:**
- Issue: `get_workpackages_by_query_id()` hardcodes `page_size = 10` and does not expose a parameter, unlike every other paginated method which accepts `page_size`.
- Files: `openproject_api_client/apiclient.py` line 330
- Impact: Callers cannot tune page size for performance. Large query results take unnecessarily many round-trips.
- Fix approach: Add `page_size: int = 10` parameter to match the signature style of `get_workpackages()`.

**`Query` Class Always Uses `debug=True`:**
- Issue: `Query.__init__` calls `super().__init__(json_object, debug=True, ...)`. The `debug=True` flag attaches the full raw JSON as a `self.json` attribute and also keeps all underscore-prefixed API keys (like `_links`, `_embedded`) on the object.
- Files: `openproject_api_client/resources.py` line 582
- Impact: `Query` instances carry a full copy of the raw JSON payload in memory at all times, increasing memory usage especially for queries with large embedded results. This was likely left over from development debugging and never cleaned up.
- Fix approach: Change to `debug=False` or introduce an explicit `debug` parameter. If raw JSON access is needed for `Query` specifically, document and test it intentionally.

**`__pycache__` Committed with Multiple Python Version Bytecode:**
- Issue: The repository includes committed `__pycache__` directories containing `.pyc` files compiled for Python 3.6, 3.7, and 3.12.
- Files: `openproject_api_client/__pycache__/` (multiple `*.cpython-36.pyc`, `*.cpython-37.pyc`, `*.cpython-312.pyc`)
- Impact: Repository bloat; stale bytecode from old Python versions (3.6, 3.7) that are no longer in the CI matrix. These should not be version-controlled.
- Fix approach: Add `__pycache__/` and `*.pyc` to `.gitignore` and remove the committed files with `git rm -r --cached openproject_api_client/__pycache__/`.

**`openproject_api_client.egg-info/` Committed:**
- Issue: The `openproject_api_client.egg-info/` build artifact directory is committed to the repository.
- Files: `openproject_api_client.egg-info/` (entire directory)
- Impact: Generated build metadata should not be version-controlled; causes unnecessary diffs when package metadata changes.
- Fix approach: Add `*.egg-info/` to `.gitignore` and remove via `git rm -r --cached`.

---

## Known Bugs

**`get()` Uses Truthy Response Check Instead of Status Code:**
- Symptoms: `if response:` evaluates the `requests.Response` object's truthiness, which is `False` for any 4xx or 5xx HTTP status. This means a 404 returns `None` silently instead of raising `RequestError`.
- Files: `openproject_api_client/apiclient.py` line 121
- Trigger: Any `get()` call to a non-existent resource (e.g., `client.get_workpackage(99999)`) returns `None` rather than raising.
- Workaround: Callers that need to distinguish "not found" from "found but empty" cannot do so through the current API. Callers must check for `None` returns manually.
- Note: This is somewhat intentional (404 returns `None`) but is undocumented and inconsistent with `post()`, `patch()`, and `delete()` which all raise `RequestError` on 4xx/5xx.

**`WorkPackage.parent_id` Parsed Without `urn:openproject-org:api:v3:undisclosed` Guard:**
- Symptoms: If the API returns `"href": "urn:openproject-org:api:v3:undisclosed"` for the `parent` link of a `WorkPackage` (same special value that `Project` handles), `int("urn:openproject-org:api:v3:undisclosed".split("/")[-1])` will raise `ValueError` and crash instantiation.
- Files: `openproject_api_client/resources.py` line 191
- Trigger: Occurs when the API user does not have permission to view the parent work package. The `Project` class handles this case (line 114) but `WorkPackage` does not.
- Workaround: None — object instantiation will raise unhandled `ValueError`.
- Fix approach: Wrap in a `try/except (ValueError, TypeError)` block identical to the `Project` parent parsing at lines 115–119.

**Pagination Termination Off-by-One with Missing `pageSize`/`offset` from API:**
- Symptoms: Some OpenProject API endpoints omit `pageSize` and `offset` from collection responses. `get_paged_collection()` falls back to the requested `page_size` and the local `offset` variable, but the condition `collection.total < effective_offset * effective_pagesize` can over-terminate on the last page when `total` is an exact multiple of `page_size`.
- Files: `openproject_api_client/apiclient.py` lines 180–189
- Trigger: Fetching a collection where `total == N * page_size` (e.g., exactly 100 items with page size 100) stops after the first page because `100 < 1 * 100` is `False`, so it correctly continues — but when the API response omits `pageSize`, the fallback calculation may differ from what the server used.
- Workaround: Use larger `page_size` values to reduce the chance of hitting boundary conditions.

---

## Security Considerations

**No HTTP Request Timeout:**
- Risk: All four HTTP methods (`http_get`, `http_post`, `http_patch`, `http_delete`) call the `requests` library without a `timeout` parameter. A slow or hung server will block the calling thread indefinitely.
- Files: `openproject_api_client/apiclient.py` lines 70, 83, 96, 109
- Current mitigation: None.
- Recommendations: Add a configurable `timeout` parameter to `ApiClient.__init__` (defaulting to e.g. 30 seconds) and pass it to all requests calls.

**No SSL Certificate Verification Control:**
- Risk: The client always uses `requests` default SSL verification (enabled), but provides no way to override it for self-signed certificates in private OpenProject deployments. Users who need to disable verification must monkey-patch at the `requests` level.
- Files: `openproject_api_client/apiclient.py` lines 70, 83, 96, 109
- Current mitigation: SSL verification is on by default (correct behavior).
- Recommendations: Add an optional `verify` parameter to `ApiClient.__init__` that is passed through to all request calls.

**API Key Exposed as Public Attribute:**
- Risk: `self.apikey` stores the raw API key as a publicly readable attribute. If the client object is logged, inspected, or serialized, the key may be exposed.
- Files: `openproject_api_client/apiclient.py` line 45
- Current mitigation: None.
- Recommendations: Use a private name (`self._apikey`) or avoid storing the key at all since `self.auth` already encapsulates it.

---

## Performance Bottlenecks

**No Connection Pooling — Each Request Opens a New Connection:**
- Problem: Using bare `requests.get/post/patch/delete` instead of a persistent `requests.Session` means TCP connections are not reused between API calls.
- Files: `openproject_api_client/apiclient.py` lines 70, 83, 96, 109
- Cause: Architectural choice to use module-level `requests.*` functions.
- Improvement path: Switch to a `requests.Session` stored on the `ApiClient` instance. This enables connection keep-alive and reduces latency on workloads with many sequential requests.

**`get_workpackages_by_query_id` Hardcoded to page_size=10:**
- Problem: Fetching large query results (e.g., 500+ work packages) requires ~50+ API calls with the hardcoded `page_size=10`.
- Files: `openproject_api_client/apiclient.py` line 330
- Cause: Hardcoded default without a parameter.
- Improvement path: Expose `page_size` as a parameter; use a larger default (e.g., 100) consistent with other methods.

**`get_projects_dict()` Walks Parent Chain Per-Project (O(depth × n)):**
- Problem: The hierarchy-building loop in `get_projects_dict()` iterates over all projects, and for each project walks up its parent chain. For a deeply nested project tree with many projects, this is repeated work.
- Files: `openproject_api_client/apiclient.py` lines 247–257
- Cause: Simple iterative approach without memoization.
- Improvement path: Acceptable at current scale; only becomes an issue with hundreds of deeply nested projects. Consider a single-pass topological traversal if scale increases.

---

## Fragile Areas

**`resources.py` Link Parsing — Assumes Specific URL Structure:**
- Files: `openproject_api_client/resources.py` (throughout `__init__` methods of `WorkPackage`, `Relation`, `Membership`, `TimeEntry`, `Activity`, `Attachment`, `Notification`, `Category`, `Query`)
- Why fragile: All ID extraction uses `href.split("/")[-1]` and wraps it in `int()`. This silently breaks if OpenProject changes URL structure, or if the API returns a non-numeric ID (e.g., URNs, slugs). The `undisclosed` URN case is handled only for `Project.parent_id` — not for any other resource or link type.
- Safe modification: Always wrap `int(href.split("/")[-1])` in `try/except (ValueError, TypeError)` with a fallback of `None`. Test with fixture data that includes the `urn:openproject-org:api:v3:undisclosed` href.
- Test coverage: The `undisclosed` URN case is only tested for `Project`; no tests cover what happens in `WorkPackage` or other resource classes when link hrefs are URNs.

**`decode_response()` Fallback is Effectively Dead Code:**
- Files: `openproject_api_client/apiclient.py` lines 199–205
- Why fragile: The `except (ValueError, KeyError)` fallback calls `json.loads(response.text, object_hook=...)`. But `json.loads` will also raise `ValueError` if the response text is not valid JSON — meaning the fallback does not actually handle the case where the JSON is malformed. The test at line 108 of `test_apiclient.py` explicitly documents this: "this actually raises too." The fallback path is unreachable in practice because `decode()` raises `ApiError` (not `ValueError`/`KeyError`) for missing `_type`, and `ApiError` is not caught.
- Safe modification: Remove the dead fallback or explicitly handle the `ApiError` case. The current documented behavior (test at line 93) shows `ApiError` propagates, which is correct — but the fallback creates false confidence that non-typed responses are handled gracefully.
- Test coverage: The fallback path has a test that acknowledges it does not work as described.

**`Collection.__iter__` Returns `iter(None)` if `_items` is Never Set:**
- Files: `openproject_api_client/resources.py` lines 817–843
- Why fragile: `Collection._items` is initialized to `None`. If `_embedded.elements` is absent from the JSON, `_items` stays `None`. Calling `list(collection)` will then call `iter(None)` and raise `TypeError`.
- Safe modification: Initialize `self._items = []` instead of `None` in `Collection.__init__`.
- Test coverage: `TestCollection.test_empty_collection` only tests the case where `_embedded.elements` is `[]`, not the case where `_embedded` or `elements` is missing entirely.

**`examples/simple_client.py` Uses Bare `except:` Five Times:**
- Files: `examples/simple_client.py` lines 53, 77, 94, 110, 126
- Why fragile: Each `except:` silently swallows all exceptions including `KeyboardInterrupt`, `SystemExit`, and programming errors. This is a bad pattern that obscures bugs.
- Safe modification: While the example file is not part of the library, it is the primary usage reference for users. Replace bare `except:` with `except Exception:` at minimum, or handle the specific expected exceptions.
- Test coverage: Not tested (example script).

---

## Test Coverage Gaps

**`urn:openproject-org:api:v3:undisclosed` Href in WorkPackage:**
- What's not tested: Behavior of `WorkPackage.__init__` when `_links.parent.href` is the undisclosed URN string.
- Files: `openproject_api_client/resources.py` line 191
- Risk: `ValueError` crash during deserialization of work packages whose parent is not visible to the API key in use.
- Priority: High

**`Collection` with Missing `_embedded` or `_embedded.elements`:**
- What's not tested: Constructing a `Collection` from JSON that lacks `_embedded` entirely, or where `_embedded` exists but `elements` is missing.
- Files: `openproject_api_client/resources.py` lines 827–838
- Risk: `TypeError` when iterating the collection (calling `iter(None)`).
- Priority: High

**Network Errors and Timeouts:**
- What's not tested: Behavior when `requests` raises a connection error, timeout, or DNS failure (`requests.exceptions.RequestException` subclasses).
- Files: `openproject_api_client/apiclient.py` (all http_* methods)
- Risk: Unhandled exceptions propagate to callers with no guidance from the library.
- Priority: Medium

**CLI Error Path — Missing Mode After Credential Validation:**
- What's not tested: The CLI `main()` path where credentials are valid but `args.mode` is `None` (user runs `openproject-cli --baseurl X --apikey Y` with no subcommand). This silently returns without printing help.
- Files: `openproject_api_client/cli.py` lines 353–355
- Risk: Confusing user experience — no error message or help text shown.
- Priority: Low

**`get_workpackages_by_query_id` Pagination:**
- What's not tested: Multi-page query results or the case where `results` is not a `WorkPackageCollection`.
- Files: `openproject_api_client/apiclient.py` lines 327–348
- Risk: Pagination bugs would silently return partial results without error.
- Priority: Medium

---

*Concerns audit: 2026-05-12*
