### BE Unit Test Overview

This document provides a clear, complete overview of backend (BE) unit tests: scope, counts, locations, and how they run in CI.

## What we execute as "unit tests"

- We run the entire `backend/tests/` tree with a selector that excludes integration/e2e/performance/security suites.
- CI command (collection and run use the same filter):

```bash
pytest -v -rA -s -p pytest_asyncio -n auto \
  tests \
  -k "not integration and not e2e and not performance and not security" \
  --maxfail=0 --disable-warnings
```

## Test counts

- Unit tests executed in CI (runtime collection): **227 tests**
  - Note: runtime count > static count due to parametrization/fixtures.
- Static function counts (lower bound):
  - Unit suite (`tests/unit/*` only): **107** tests across **8** files

## Unit test locations (executed by the filter above)

- Primary unit directory:
  - `tests/unit/test_auth.py`
  - `tests/unit/test_auth_security.py`
  - `tests/unit/test_database.py`
  - `tests/unit/test_embed_widget.py`
  - `tests/unit/test_example_with_timeouts.py`
  - `tests/unit/test_middleware.py`
  - `tests/unit/test_production_rag_advanced.py`
  - `tests/unit/test_websocket.py`
- Additional unit-focused files at repo root (included by the filter):
  - `tests/test_services_unit.py`
  - `tests/test_api_endpoints_unit.py`

## Suites deliberately excluded from "unit" runs

- Integration: `tests/integration/*`
- E2E: `tests/e2e/*`
- Performance: `tests/performance/*`
- Security directory (if added later)
- Other mixed top-level suites (whitebox/blackbox/system) are excluded by the `-k` expression unless they are clearly unit-focused.

## Environment and reliability measures in CI

- Env flags for speed/reliability:
  - `TESTING=1`, `ENVIRONMENT=test`, SQLite DB
  - `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` and explicit `-p pytest_asyncio`
  - Parallel: `pytest-xdist` via `-n auto`
  - Disable heavy/optional middlewares in tests: `ENABLE_RATE_LIMITING=false`, `ENABLE_SECURITY_HEADERS=false`, `ENABLE_REQUEST_LOGGING=false`, `ENABLE_INPUT_VALIDATION=false`
- Heavy dependency guards:
  - Fake embeddings model under TESTING (prevents network downloads)
  - Skip NLTK/model init for RAG in tests
  - Centralized Redis usage to a mocked/fallback client during tests

## Result

- Latest CI unit run: **227 unit tests collected and executed** — passed.


