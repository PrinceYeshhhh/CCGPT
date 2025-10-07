## CustomerCareGPT Test Coverage Map and Remediation Plan

This document inventories existing tests, maps them to core product functionality, highlights gaps, and defines a staged CI testing strategy. It also includes a local reproduction checklist.

### Scope
- Backend (`backend/`): FastAPI services: auth, documents/chunking/embeddings, RAG, chat sessions & WebSocket, embed widget, billing/Stripe, analytics, middleware/security.
- Frontend (`frontend/`): React app with Vitest unit/integration and Playwright E2E; UI flows including auth, dashboard (documents, analytics, billing), widget, and theme.

---

## Inventory of Existing Tests (High-level)

### Backend
- Unit tests: `backend/tests/unit/`
  - Auth, security, websocket, middleware, LLM services
  - Example: `test_auth.py`, `test_auth_security.py`, `test_websocket.py`, `test_middleware.py`, `test_llm_services.py`, `test_embed_widget.py`, `test_database.py`
- Integration tests: `backend/tests/integration/`
  - API integration (incl. comprehensive and error scenarios), BE-FE integration hooks
  - Example: `test_api_integration.py`, `test_api_integration_comprehensive.py`, `test_error_scenarios.py`, `test_be_fe_integration.py`
- E2E/system tests: `backend/tests/e2e/` and root-level smoke
  - Example: `test_user_journeys.py`, `test_production_rag_e2e.py`
- Performance: `backend/tests/performance/`
  - Example: `test_load_testing.py`, `test_stress_testing.py`, `test_production_rag_performance.py`
- Comprehensive suites: `test_whitebox_comprehensive.py`, `test_blackbox_comprehensive.py`, `test_system_comprehensive.py`
- Misc root-level: `backend/test_minimal.py`, `backend/test_simple.py`, `backend/test_rag_implementation.py`, `backend/test_embeddings_pipeline.py`, etc.

Notes:
- Pytest markers are defined in `backend/pytest.ini` (unit, integration, system, performance, auth, documents, chat, rag, billing, security).
- Coverage configured against `app/` with `--cov-fail-under=80`.

### Frontend
- Unit/integration (Vitest): `frontend/src/**/__tests__/*`
  - Example: `components/__tests__/Login.test.tsx`, `Navbar.test.tsx`, `hooks/__tests__/usePerformance.test.ts`, `__tests__/integration/api.test.tsx`, `__tests__/integration/websocket.test.tsx`
- E2E (Playwright): `frontend/e2e/*.spec.ts`
  - `auth.spec.ts`, `homepage.spec.ts`, `dashboard.spec.ts`, `documents.spec.ts`, `widget-greeting.spec.ts`
- Config: `vitest.config.ts` (jsdom, coverage v8), `playwright.config.ts` (serial on CI, retries, video/screenshot on failure)

---

## Test Inventory (Source of Truth)

Use this list when updating the CI. Each category is intended to run “once per kind,” executing all files in that group.

### Backend
- Unit
  - `backend/tests/unit/test_auth.py`
  - `backend/tests/unit/test_auth_security.py`
  - `backend/tests/unit/test_database.py`
  - `backend/tests/unit/test_embed_widget.py`
  - `backend/tests/unit/test_example_with_timeouts.py`
  - `backend/tests/unit/test_llm_services.py`
  - `backend/tests/unit/test_middleware.py`
  - `backend/tests/unit/test_production_rag_advanced.py`
  - `backend/tests/unit/test_websocket.py`
- Integration
  - `backend/tests/integration/test_api_integration.py`
  - `backend/tests/integration/test_api_integration_comprehensive.py`
  - `backend/tests/integration/test_be_fe_integration.py`
  - `backend/tests/integration/test_error_scenarios.py`
  - `backend/tests/test_integration.py`
  - `backend/tests/test_integration_comprehensive.py`
- E2E/System
  - `backend/tests/e2e/test_user_journeys.py`
  - `backend/tests/test_e2e_workflows.py`
  - `backend/tests/test_system_comprehensive.py`
  - `backend/tests/test_whitebox_comprehensive.py`
  - `backend/tests/test_blackbox_comprehensive.py`
- Performance (nightly)
  - `backend/tests/performance/test_load_testing.py`
  - `backend/tests/performance/test_production_rag_performance.py`
  - `backend/tests/performance/test_stress_testing.py`
- File processing / RAG pipeline
  - `backend/tests/test_file_processing.py`
  - `backend/test_embeddings_pipeline.py`
  - `backend/test_rag_implementation.py`
  - `backend/test_production_rag_system.py`
  - `backend/test_enhanced_rag_system.py`
- Web/Widget/Cloud
  - `backend/test_embeddable_widget.py`
  - `backend/test_chat_sessions_websocket.py`
  - `backend/tests/test_cloud_integration.py`
  - `backend/tests/test_cloud_performance.py`
  - `backend/tests/test_cloud_security.py`
- Smoke/Utilities
  - `backend/test_minimal.py`
  - `backend/tests/test_simple.py`
  - `backend/tests/test_utils.py`
  - `backend/test_performance_integration.py`
  - `backend/test_standalone.py`
  - `backend/tests/skip_problematic_tests.py`
  - `backend/tests/run_cloud_tests.py`

- Missing critical test stubs (to implement)
  - `backend/tests/stubs/test_billing_webhook_signature.py`
  - `backend/tests/stubs/test_websocket_security_limits.py`
  - `backend/tests/stubs/test_rag_rate_limits_and_budget.py`
  - `backend/tests/stubs/test_csrf_middleware_api.py`
  - `backend/tests/stubs/test_analytics_endpoints.py`

### Frontend
- Unit/Integration (Vitest)
  - `frontend/src/components/__tests__/Login.test.tsx`
  - `frontend/src/components/__tests__/Navbar.test.tsx`
  - `frontend/src/components/__tests__/ExampleWithTimeouts.test.tsx`
  - `frontend/src/hooks/__tests__/usePerformance.test.ts`
  - `frontend/src/__tests__/integration/api.test.tsx`
  - `frontend/src/__tests__/integration/websocket.test.tsx`
- E2E (Playwright)
  - `frontend/e2e/auth.spec.ts`
  - `frontend/e2e/homepage.spec.ts`
  - `frontend/e2e/dashboard.spec.ts`
  - `frontend/e2e/documents.spec.ts`
  - `frontend/e2e/widget-greeting.spec.ts`
- Missing critical test stubs (to implement)
  - `frontend/tests/stubs/dark_mode_persistence.test.tsx`
  - `frontend/tests/stubs/billing_flow.test.ts`
  - `frontend/tests/stubs/analytics_charts_render.test.tsx`
  - `frontend/tests/stubs/widget_embed_security.test.ts`
  - `frontend/tests/stubs/api_error_boundaries.test.tsx`

## Mapping: Product Areas → Current Tests

- Auth (login, tokens, dependencies)
  - BE: `tests/unit/test_auth.py`, `tests/unit/test_auth_security.py`, comprehensive suites
  - FE: `components/__tests__/Login.test.tsx`, E2E `auth.spec.ts`

- Documents, chunking, embeddings pipeline
  - BE: `test_embeddings_pipeline.py`, `tests/test_file_processing.py`, RAG comprehensive tests; vector service and production RAG covered by integration/e2e suites
  - FE: E2E `documents.spec.ts`

- RAG query and citations
  - BE: `test_rag_implementation.py`, `tests/e2e/test_production_rag_e2e.py`, `tests/integration/test_production_rag_integration.py`
  - FE: integration `api.test.tsx`; E2E covers dashboard/usage

- Chat sessions + WebSocket
  - BE: `tests/unit/test_websocket.py`, `tests/e2e/test_user_journeys.py`
  - FE: integration `websocket.test.tsx`

- Embed widget
  - BE: `tests/unit/test_embed_widget.py`
  - FE: E2E `widget-greeting.spec.ts`

- Billing and subscriptions (Stripe)
  - BE: Minimal to none in tests (endpoints present, `stripe_service.py` exists). Grep shows no direct billing/stripe tests.
  - FE: `pages/dashboard/Billing.tsx` present; no unit tests found for billing flow

- Analytics (dashboard metrics)
  - BE: Endpoints and service exist; limited explicit analytics tests found
  - FE: `pages/dashboard/Analytics.tsx`; no explicit tests for charts/data integrity

- UI flows (dashboard nav, auth redirects)
  - FE: Navbar/login tests; E2E covers homepage/dashboard smoke

- Dark/light mode
  - FE: `contexts/ThemeContext.tsx`, `components/ui/theme-toggle.tsx`; no tests found for persistence or class toggling

---

## Gaps and Missing Tests (Prioritized)

### Critical (blockers/business risk)
1. Backend billing/Stripe
   - Webhook signature verification paths; subscription lifecycle handling; checkout session creation happy-path and error-path.
2. Backend WebSocket security limits
   - Authentication of WS connections via token/API key, connection rate limits, forced close codes.
3. Backend rate limiting and token budget on RAG
   - `rag_query` endpoint: quota check, token budget enforcement, headers.
4. Backend CSRF middleware behavior for non-Bearer POST routes
   - `CSRFProtectionMiddleware` expected headers and exemptions.

### High
5. Backend storage adapters and document upload validation
   - Local/GCS/S3 save/read errors; file security validation rejects bad content types.
6. Backend analytics endpoints
   - `analytics.py` and `analytics_service.py` functional outputs and error handling.
7. Frontend billing UI
   - Plan change CTA wiring; checkout URL handling; disabled states.
8. Frontend analytics charts
   - Rendering with empty/large datasets; loading/error states.

### Medium
9. Frontend dark mode persistence
   - Theme toggle persists to localStorage, applies class to `html`/root.
10. Frontend error boundaries and API retry UX
   - Global error surfaces; retry/backoff behavior for key routes.
11. Embed widget security (frontend)
   - CSP nonce/script injection safety in preview; x-origin restrictions (at least unit-level guards).

---

## Remediation: Concrete Test Stubs Added

Created stub files (skipped by default) to accelerate implementation:

Backend (`backend/tests/stubs/`):
- `test_billing_webhook_signature.py`: Verify webhook signature and event parsing; create checkout session error handling.
- `test_websocket_security_limits.py`: WS auth, connection limits, and close codes.
- `test_rag_rate_limits_and_budget.py`: Quota and token budget enforcement in `rag_query`.
- `test_csrf_middleware_api.py`: CSRF header requirement and exemptions.
- `test_analytics_endpoints.py`: Overview, usage-stats, KPIs happy-path and error-path.

Frontend (`frontend/tests/stubs/`):
- `dark_mode_persistence.test.tsx`: Toggle persists theme; class toggling.
- `billing_flow.test.ts`: Plan change -> checkout URL flow; disabled states.
- `analytics_charts_render.test.tsx`: Charts render with empty/large datasets; loading/error.
- `widget_embed_security.test.ts`: Basic CSP/nonce presence in generated embed preview.
- `api_error_boundaries.test.tsx`: Network error surfaces and retry.

Implementation notes:
- Backend stubs use `pytest.mark.skip(reason="stub")` to avoid failing CI until implemented.
- Frontend stubs use `describe.skip()`/`test.todo()` to mark pending.

---

## Staged CI Testing Strategy

Phases run sequentially; later phases depend on earlier successes.

1) Fast Smoke
- Backend quick smoke: `backend/test_minimal.py`, `backend/test_simple.py`.

2) Backend Unit (no services)
- Paths: `backend/tests/unit/` and fast unit API tests.

3) Backend Integration (services up)
- Services: Postgres, Redis; run integration and selected e2e API tests.

4) Frontend Unit/Type-Check
- `npm run type-check` and `npm run test:unit` (Vitest, jsdom).

5) Frontend Integration (Vitest)
- `npm run test:integration`.

6) Frontend E2E (Playwright)
- Run all Playwright specs; retries enabled; record traces on failure.

Caching and optimizations:
- Use actions/setup-python and actions/setup-node caches; pip cache keyed by `backend/requirements.txt`; npm cache by `frontend/package-lock.json`.

---

## Local Reproduction Checklist

Backend
```bash
cd backend
python -m venv .venv && . .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
pytest -q test_minimal.py test_simple.py
pytest -q tests/unit
pytest -q tests/integration -m "not slow"
```

Frontend
```bash
cd frontend
npm ci
npm run type-check
npm run test:unit
npm run test:integration
npx playwright install --with-deps
npm run test:e2e
```

Services (optional for BE integration locally)
```bash
docker compose -f docker-compose.local.yml up -d db redis
```

---

## Open Questions / Ambiguities
- Which DB is authoritative for CI integration (SQLite vs Postgres)? Proposed: Postgres service with Alembic migrations; adjust if tests prefer SQLite.
- Which E2E specs are required for PRs vs nightly? Proposed: run a smoke subset on PR; full E2E nightly.
- Define strict thresholds for FE coverage. Proposed: set Vitest coverage gating when stabilized.

---

## Owner Handoffs
- Billing BE: implement Stripe tests in `backend/tests/stubs/test_billing_webhook_signature.py`.
- WebSocket security: complete `backend/tests/stubs/test_websocket_security_limits.py`.
- RAG quotas: complete `backend/tests/stubs/test_rag_rate_limits_and_budget.py`.
- FE billing/analytics/dark mode: complete corresponding FE stubs under `frontend/tests/stubs/`.


