# Testing

**Analysis Date:** 2026-05-12

## Framework

- **pytest >= 7.0** — installed via the `test` extra (`pyproject.toml` `[project.optional-dependencies]`).
- **responses >= 0.23** — HTTP request mocking, monkey-patches `requests` at the transport boundary.
- **`unittest.mock`** (stdlib) — used for CLI dispatch tests to patch `ApiClient` methods.
- No `pytest.ini` / no `[tool.pytest.ini_options]` block — defaults are used.
- No coverage tooling configured (no `coverage`, `pytest-cov`, or coverage threshold).

## Layout

```
tests/
├── __init__.py            # empty; allows tests/ to be a package
├── conftest.py            # all shared fixtures + sample JSON payloads (457 lines)
├── test_apiclient.py      # ApiClient HTTP behavior + decoding (966 lines)
├── test_resources.py      # Resource model parsing (698 lines)
└── test_cli.py            # CLI argparse + dispatch (731 lines)
```

- Tests live in a sibling `tests/` directory — **not** co-located with source.
- One test file per source module, plus the CLI.

## Patterns

### Fixtures

- Defined in `tests/conftest.py` as `@pytest.fixture` functions returning dicts shaped like the OpenProject API JSON (`project_json`, `child_project_json`, `workpackage_json`, etc.).
- Module-level helpers `make_collection(...)` and `make_wp_collection(...)` build paged-collection envelopes from a list of element dicts — used by tests that exercise pagination.
- Fixtures cover: projects, work packages, relations, users, memberships, statuses, grids, queries, types, priorities, time entries, activities, attachments, notifications, categories.

### HTTP Mocking

```python
import responses

@responses.activate
def test_get_projects(api_client, project_json):
    responses.add(
        responses.GET,
        "https://op.example.com/api/v3/projects",
        json=make_collection([project_json]),
        status=200,
    )
    projects = api_client.get_projects()
    assert projects[0].name == "My Project"
```

- `@responses.activate` decorator wraps every test that hits HTTP.
- `responses.add(...)` enumerates expected URL + method + JSON body + status.
- Pagination tests register multiple URLs with different `offset` query strings.

### Test Class Grouping

Tests are organized into classes by feature, e.g.:

- `class TestApiClientInit:` — constructor validation
- `class TestGetWorkpackages:` — `get_workpackages` happy / error paths
- `class TestCreateWorkpackage:` — write semantics
- `class TestDecodeResponse:` — decoder behavior

Class grouping is **optional** — bare `def test_*()` functions also appear, especially in `test_resources.py`.

### CLI Tests

`tests/test_cli.py` uses `unittest.mock.patch` to replace `ApiClient` methods on the patched-in module, then runs `cli.main()` with crafted `sys.argv` lists and asserts on `capsys.readouterr()` stdout. This avoids any HTTP traffic for CLI tests.

### Resource Model Tests

`tests/test_resources.py` instantiates resource classes directly from fixture dicts and asserts attribute values, datetime parsing, `_links` expansion, and `_embedded` recursion. No HTTP layer involved.

## Mocking Boundary

- HTTP is mocked at `responses` (closest to the network).
- Custom doubles / fakes are **not** used — the real `ApiClient` is exercised end-to-end against mocked HTTP responses.
- No database, no filesystem, no time mocking required.

## Coverage

- No coverage measurement configured.
- Empirically: ~2.4k lines of test for ~2.2k lines of source — roughly 1:1 ratio.
- All public `ApiClient` methods have at least a happy-path test; many also have error-path tests.

## Running Tests

```bash
pip install -e ".[test]"
pytest -v
```

CI (`.github/workflows/ci.yml`) runs `pytest -v` against the Python 3.9–3.13 matrix on every push and PR to `main`.

## Notable Gaps

- No integration tests against a live OpenProject instance (intentional — adds infra cost).
- No property-based testing (e.g. Hypothesis).
- No tests for `Collection` with missing `_embedded` (see `.planning/codebase/CONCERNS.md`).
- No tests for unrecognized API `_type` strings hitting `decode`.
- No timeout / retry / network-failure tests (the code has none of those behaviors).

---

*Testing analysis: 2026-05-12*
