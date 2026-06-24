---
name: test-writing
description: Write tests for a just-finished feature before opening a PR. Use at the end of every feature in the and-you repo — covers pytest (backend) and Vitest/Playwright (frontend) conventions, the behavior-coverage bar, and how to mock the LLM. Triggers when the user says "write tests", "add tests", finishes a feature, or is about to open a PR.
---

# test-writing

In `and-you`, **no feature is done without tests, and no PR is opened without them.** This skill is the
checklist for writing those tests. Invoke it at the end of every feature.

## The bar: behavior, not a percentage

There is **no coverage % gate.** Instead, for the feature's core logic test:

1. **Happy path** — the main intended behavior, with a realistic input.
2. **Key edge cases** — empty/zero/boundary inputs, the largest realistic case.
3. **Failure modes** — invalid input, the dependency erroring, the "rejection"/wrong-answer paths
   (this product is *about* detecting wrong AI output — test those branches explicitly).

If a behavior matters for the demo or scoring, it gets a test. If it's a trivial passthrough, it doesn't.

## Mock the LLM in unit tests

LLM calls are non-deterministic, slow, and cost money — **mock them in unit tests** so tests are fast,
free, and repeatable.

- Inject the LLM client / make the call point patchable; in tests, return canned responses
  (including malformed / wrong ones to exercise rejection and Precision/Recall scoring logic).
- Backend: patch the call with `pytest`'s `monkeypatch` or `unittest.mock.patch`, or pass a fake client.
- Assert on **your logic** (parsing, scoring, ret(ry/judge aggregation), not on the model's wording.
- Add a **small** number of real **integration tests** (1–2 per LLM feature) that hit the model for real,
  marked so they can be skipped in CI / when no API key is set (e.g. `@pytest.mark.integration` +
  skip-if-no-key). CI runs the mocked unit tests; integration tests are opt-in.

## Backend (pytest)

- Location: `backend/tests/`, files `test_*.py`, functions `test_*`.
- Run: `pytest` — single test: `pytest tests/test_x.py::test_name`.
- For FastAPI endpoints, use `fastapi.testclient.TestClient`.
- Keep fixtures small; mock the DB or use a transactional test DB rather than the real one.

## Frontend (Vitest / Playwright)

- Unit/component tests: Vitest, colocated as `*.test.ts(x)`. Run: `npm test` — single file:
  `npm test -- src/foo.test.ts`.
- E2E (full user flow, e.g. login → solve problem → see result): Playwright.
- Don't call the real backend in unit tests — mock `fetch` / the API client.

## Before you open the PR

- [ ] Tests written for happy path + key edge/failure cases of the feature.
- [ ] LLM calls mocked in unit tests (+ integration test added if it's an LLM feature).
- [ ] `pytest` green (backend) / `npm test` green (frontend).
- [ ] `ruff check .` / `npm run lint` + `npm run typecheck` clean.

Then hand off to the `ship-feature` skill (or its commit → PR steps) to open the PR.
