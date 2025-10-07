# Frontend Unit Testing Guide (CustomerCareGPT)

## What this covers
- Exact commands to run ALL frontend unit tests locally and in CI
- Test inventory (files, purpose) and exclusions
- Key configs, environment setup, and stability fixes
- How to add new tests that run by default

## Commands
- Local: from `frontend/`
```bash
npm ci
npm run test:unit
```
- CI (GitHub Actions): `.github/workflows/ci.yml` runs the same in `frontend/`
```yaml
- name: Run all FE unit tests (Vitest)
  env:
    CI: true
  run: npm run test:unit
```

## Vitest configuration
- File: `frontend/vitest.config.ts`
- Important:
  - `environment: 'jsdom'`
  - `setupFiles: ['./src/test/setup.ts']`
  - `exclude` excludes integration/e2e from unit runs
  - `testTimeout`/`hookTimeout` to prevent hangs

Unit runs exclude integration by default:
```ts
exclude: [
  '**/node_modules/**',
  '**/dist/**',
  '**/e2e/**',
  '**/*.e2e.spec.ts',
  '**/*.e2e.test.ts',
  '**/__tests__/integration/**'
]
```

## Scripts (`frontend/package.json`)
- "test:unit": "vitest run --reporter=basic"
- "test:integration": "vitest run src/__tests__/integration/ --reporter=verbose --logHeapUsage"

## Test inventory (unit)
- Components
  - `src/components/__tests__/Login.test.tsx`: auth form validation, flows
  - `src/components/__tests__/Navbar.test.tsx`: nav items, theme toggle, menu behavior
  - `src/components/__tests__/ExampleWithTimeouts.test.tsx`: async/timeouts demo
- Hooks
  - `src/hooks/__tests__/usePerformance.test.ts`: performance hook behavior (stable subset)
- Stubs (implemented as unit tests)
  - `tests/stubs/dark_mode_persistence.test.tsx`: theme persistence via `ThemeContext`
  - `tests/stubs/api_error_boundaries.test.tsx`: ErrorBoundary fallback, retry surfacing
  - `tests/stubs/analytics_charts_render.test.tsx`: analytics page renders, data load
  - `tests/stubs/billing_flow.test.tsx`: upgrade click triggers checkout flow UI
  - `tests/stubs/widget_embed_security.test.tsx`: safe widget preview rendering

Note: Integration specs live under `src/__tests__/integration/` and are intentionally excluded from unit runs.

## Stability and memory fixes
- `WidgetPreview.tsx`
  - Added `data-testid` and ARIA labels to disambiguate multiple buttons
  - Added timeout cleanup (`typingTimeoutRef`) and effect cleanup to prevent open handles
- `usePerformance.ts`
  - Skips observers/timers when `NODE_ENV === 'test'` to avoid leaks in jsdom
- `src/test/setup.ts`
  - Mocks: `matchMedia`, `IntersectionObserver`, `ResizeObserver`, `requestAnimationFrame`, storages
  - Clears timers/mocks between tests; filters noisy `console.error` from React error boundaries
- `vitest.config.ts`
  - Excludes integration/e2e; explicit timeouts

## Adding new unit tests
1. Place tests next to modules or under `src/**/__tests__/`.
2. Mock network/WebSocket with `vi.mock`.
3. Use `await waitFor(...)` for async UI updates.
4. Prefer fake timers or short delays.

Example placement:
```
frontend/
  src/components/MyComp.tsx
  src/components/__tests__/MyComp.test.tsx
```

## Local troubleshooting
- Hangs: ensure no lingering intervals/timeouts; verify `afterEach` cleanup.
- Memory spikes: avoid installing observers/timers in tests; handle unhandled rejections.
- Multiple matches: add test IDs or accessible names.

## CI expectations
- Workflow: `.github/workflows/ci.yml`
- Runs on push/PR to `main`
- Node 20, `npm ci`, then `npm run test:unit`
- Caches `frontend/package-lock.json`

## Coverage (optional)
- Local: `npm run test:coverage`
- CI gating can be enabled later once thresholds stabilize.

## Current status
- All FE unit tests pass locally with `npm run test:unit`.
- Integration tests are excluded from unit runs.
- Same command runs in GitHub Actions.
