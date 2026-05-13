# Phase 04 — TEST-01..08 Coverage Audit

**Audit date:** 2026-05-13
**Auditor:** Claude executor (gsd-execute-phase, plan 04-01)
**Source of truth for gaps:** .planning/codebase/CONCERNS.md → "Test Coverage Gaps"
**Source of truth for requirements:** .planning/REQUIREMENTS.md → TEST section

## Method

For each TEST-XX requirement, grep for test functions whose name or class
matches the documented behavior, then read the test body to confirm it
exercises the requirement's actual contract (not just a related path).
A row is marked COVERED only if at least one existing test exercises the
exact behavior described in the requirement. Otherwise: GAP.

## Traceability Table

| Req | Behavior | Test function(s) | File:line | Disposition |
|-----|----------|------------------|-----------|-------------|
| TEST-01 | Collection missing `_embedded` / `_embedded.elements` iterates safely | `TestCollection.test_collection_missing_embedded`, `TestCollection.test_collection_embedded_without_elements`, `TestCollection.test_collection_empty_elements_regression`, `TestCollection.test_collection_items_default_is_list` | tests/test_resources.py:630, tests/test_resources.py:636, tests/test_resources.py:641, tests/test_resources.py:646 | COVERED |
| TEST-02 | href parsing: None / empty / URN → None (not ValueError) | `TestParseHrefId.test_parse_href_id_happy_paths`, `TestParseHrefId.test_parse_href_id_returns_none_for_invalid`, plus 8× `TestHrefParsingRobustness.test_*` | tests/test_resources.py:38, tests/test_resources.py:45, tests/test_resources.py:787 | COVERED |
| TEST-03 | unknown `_type` in `decode()` returns GenericType (no raise) | `TestDecode.test_decode_unknown_type_returns_generic` | tests/test_apiclient.py:203 | COVERED |
| TEST-04 | `pageSize: null` in paged response — loop terminates | `TestGetWorkpackagesByQueryId.test_get_workpackages_by_query_id_pagesize_none`, `TestGetWorkpackagesByQueryId.test_get_workpackages_by_query_id_empty_collection` | tests/test_apiclient.py:713, tests/test_apiclient.py:697 | COVERED |
| TEST-05 | unknown `status=` → silent no-op + DEBUG log | `TestGetWorkpackagesUnknownStatus.test_get_workpackages_unknown_status_no_filter`, `TestGetWorkpackagesUnknownStatus.test_get_workpackages_unknown_status_logs_debug`, `TestGetWorkpackagesUnknownStatus.test_get_workpackages_open_status_regression`, `TestGetWorkpackagesUnknownStatus.test_get_workpackages_uppercase_status_regression` | tests/test_apiclient.py:600, tests/test_apiclient.py:615, tests/test_apiclient.py:632, tests/test_apiclient.py:647 | COVERED |
| TEST-06 | API key substring absent from DEBUG log records for GET/POST/PATCH/DELETE | `TestApiKeyNotInDebugLogs.test_no_key_in_get_debug`, `TestApiKeyNotInDebugLogs.test_no_key_in_post_debug`, `TestApiKeyNotInDebugLogs.test_no_key_in_patch_debug`, `TestApiKeyNotInDebugLogs.test_no_key_in_delete_debug` | tests/test_apiclient.py:1469, tests/test_apiclient.py:1487, tests/test_apiclient.py:1505, tests/test_apiclient.py:1523 | COVERED |
| TEST-07 | Session reused across two sequential http_get calls | `TestSessionReuse.test_session_is_reused_across_calls` | tests/test_apiclient.py:168 | COVERED |
| TEST-08 | `timeout` and `verify` propagated to all four http_* methods | `TestSecurityKwargsPropagation.test_http_get_default_propagates_none_and_true`, `TestSecurityKwargsPropagation.test_http_get_custom_propagates`, `TestSecurityKwargsPropagation.test_http_post_propagates`, `TestSecurityKwargsPropagation.test_http_patch_propagates`, `TestSecurityKwargsPropagation.test_http_delete_propagates`, `TestSecurityKwargsPropagation.test_ca_bundle_path_propagates` | tests/test_apiclient.py:116, tests/test_apiclient.py:124, tests/test_apiclient.py:132, tests/test_apiclient.py:140, tests/test_apiclient.py:148, tests/test_apiclient.py:156 | COVERED |

## Gap Summary

- **Total requirements audited:** 8
- **COVERED:** 8
- **GAP:** 0
- **Action:** No gap-fill work required. All TEST-XX requirements are covered by tests added incidentally during Phases 1–3. Task 2 (gap fill) is a no-op.

## Cross-check against CONCERNS.md "Test Coverage Gaps"

| CONCERNS.md gap | Maps to TEST-XX | Now COVERED? |
|-----------------|-----------------|--------------|
| `urn:openproject-org:api:v3:undisclosed` href in WorkPackage | TEST-02 | yes (TestHrefParsingRobustness.test_workpackage_parent_undisclosed_urn) |
| `Collection` with missing `_embedded` / `_embedded.elements` | TEST-01 | yes (TestCollection.test_collection_missing_embedded, test_collection_embedded_without_elements) |
| `get_workpackages_by_query_id` pagination (incl. pageSize null) | TEST-04 | yes (TestGetWorkpackagesByQueryId.test_get_workpackages_by_query_id_pagesize_none + …_multipage) |
| Network errors / timeouts | (out of scope — not a TEST-XX requirement; remains an open Medium concern) | n/a |
| CLI missing-mode path | (out of scope — not a TEST-XX requirement; remains an open Low concern) | n/a |
