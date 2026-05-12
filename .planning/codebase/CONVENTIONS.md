# Conventions

**Analysis Date:** 2026-05-12

## Language Conventions

- **Python 3.9+** — confirmed by `pyproject.toml` `requires-python = ">=3.9"` and CI matrix 3.9 – 3.13.
- `from __future__ import annotations` at the top of every source module — enables PEP 563 deferred annotation evaluation.
- Type hints used on **public** `ApiClient` methods (parameters and return types). Not consistently used on private helpers or resource model fields.
- Module docstrings present on every source file; class docstrings on `ApiClient` and most resource classes; sparse method docstrings.
- `__all__` declared explicitly in every module (`apiclient.py:20`, `resources.py:13`, `__init__.py`) — defines public API.

## Style & Formatting

- **No linter / formatter configured** — no `ruff`, `black`, `flake8`, `pre-commit`, or `isort` settings in `pyproject.toml`. Style is hand-maintained.
- 4-space indentation, ~120-char effective line length, double-quoted strings dominant (some single quotes in older blocks).
- Blank line groupings: 2 blanks between top-level defs (PEP 8), 1 between methods.
- f-strings used everywhere for interpolation (`f"{self.base_url}{self._rootpath}/{resource}"`).

## Naming

- Classes: `PascalCase` (`ApiClient`, `WorkPackage`, `WorkPackageCollection`, `PlaceholderUser`).
- Functions / methods / variables: `snake_case`.
- Module-private: leading `_` (`_endpoint`, `_headers`, `_obj_to_dict`).
- Class-private: double underscore for true name-mangling (`__parse_datetime`, `__type` in `GenericType`).
- Constants: not many; the few used (`_rootpath`) are instance attrs rather than `UPPER_SNAKE_CASE` constants.
- JSON → attribute mapping: API camelCase keys are forced to `.lower()` (`resources.py:47-52`). So `createdAt` becomes `obj.createdat`, not `obj.created_at`.

## Resource Class Pattern

Every resource model in `openproject_api_client/resources.py` follows this 3-step init:

```python
class Project(GenericType):
    def __init__(self, json_object=None):
        # 1. Declare attribute defaults
        self.id = 0
        self.identifier = ''
        self.name = ''
        ...

        # 2. Call super().__init__ with datetime/date field lists
        super().__init__(json_object, datetime_fields=['createdat', 'updatedat'])

        # 3. If json_object provided, parse `_links` / `_embedded`
        if json_object:
            links = json_object.get('_links', {})
            ...
```

When adding a new resource, follow this exact shape.

## Function Signatures — Write Methods

Write methods use **keyword-only arguments** after a small set of positional required args:

```python
def create_workpackage(self, project_id: int, subject: str, *,
                       type_id: int = None,
                       assignee_id: int = None,
                       priority_id: int = None,
                       ...): ...
```

The `*` separator is intentional — forces call sites to be self-documenting.

## Error Handling

- Two custom exception types: `ApiError` (HTTP / API-side failure) and `RequestError` (transport failure) — both in `apiclient.py`.
- `decode_response` (`apiclient.py:198`) raises `ApiError(status_code, body)` on non-2xx.
- Constructor validates `base_url` and `apikey` are non-empty and raises `ApiError` if missing (`apiclient.py:37-41`).
- No retries, no backoff, no timeout — failures bubble up immediately.
- Tests assert exception types with `pytest.raises(ApiError)`.

## Logging

- Stdlib `logging` module, one logger per module: `logger = logging.getLogger(__name__)` (`apiclient.py:22`).
- Positional `%s`-style format strings — `logger.debug("GET %s -> %s", endpoint, resp.status_code)` — not f-strings. This is correct: defers formatting until the level is enabled.
- Levels used: `DEBUG` for request/response details. No `INFO`/`WARNING`/`ERROR` in library code (errors raise instead).

## Sentinels & Defaults

- `None` is the universal "absent" sentinel for optional kwargs and for unset attributes.
- Empty list `[]` / dict `{}` used inside methods, never as default arg values (avoids the mutable-default trap).

## Imports

- Stdlib first, then third-party (`requests`), then intra-package — separated by blank lines.
- Explicit `from openproject_api_client import apiclient` inside `resources.py:11` despite the circular shape; works because the import is at module load time and only `apiclient` (module object) is referenced.

## CLI Style

- Argparse hierarchy: top-level parser with `--baseurl`, `--apikey`, `--json` flags, then `add_subparsers(dest='command')` with one subcommand per `ApiClient` method category.
- Dispatch is a single big `if/elif` in `dispatch()` mapping subcommand → method call.
- Two output formatters: `text_out()` (human-readable) and `json_out()` (machine-readable) — selected by top-level `--json`.
- `_obj_to_dict()` does manual serialization of resource model objects, walking `vars(obj)`.

---

*Conventions analysis: 2026-05-12*
