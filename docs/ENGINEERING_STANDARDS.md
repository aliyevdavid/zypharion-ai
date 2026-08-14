# Zypharion Engineering Standards

## Branching and integration

- Use small, short-lived branches for each coherent change.
- The current integration path is feature branch to `develop`, followed by a
  deliberate promotion from `develop` to `main`.
- Keep `main` release-ready. After it becomes the active integration branch,
  changes must reach it through reviewed pull requests; direct pushes are not
  permitted.
- Require passing continuous integration before adopting a main-based workflow.
- Name branches by intent, for example `feature/behavior-discovery`,
  `fix/extraction-warning`, or `docs/main-readiness`.
- Do not mix unrelated cleanup into a product change.

## Commits and pull requests

Use concise Conventional Commit-style messages, for example:

```text
feat(intelligence): add behavior evidence
fix(extractor): preserve partial results
test(analysis): cover provider validation failure
docs(architecture): document workflow boundaries
```

Every pull request should identify:

- the problem and intended outcome;
- key changes and architectural effects;
- validation performed and exact test results;
- known limitations or follow-up work; and
- the correct integration branch for the current workflow.

Tests must pass before merge. Review the complete diff and keep commits free of
credentials, generated local artifacts, and unrelated changes.

## Definition of done

A change is complete when:

1. Its acceptance behavior is implemented without unnecessary scope expansion.
2. Focused automated tests cover changed behavior and relevant failure paths.
3. The full test suite passes.
4. Public contracts and documentation match the implementation.
5. No secrets, local configuration, or unintended files are included.
6. Formatting and diff checks pass.
7. The pull request is reviewed and all required CI checks pass.

## Python and API standards

- Use type annotations for production interfaces and tests.
- Prefer explicit Pydantic models for data crossing boundaries.
- Keep FastAPI routes thin; orchestration belongs in application services.
- Validate external input and return deliberate, structured errors.
- Avoid hidden global mutable state.
- Close browser, network, file, and database resources reliably.
- Preserve API compatibility unless a contract change is explicitly approved.
- Keep dependency composition separate from request execution.

## Intelligence and AI standards

- Keep deterministic extraction and analysis independent of AI.
- Build deterministic conclusions from explicit evidence and expose uncertainty.
- Treat web content and provider responses as untrusted input.
- Preserve partial results when a localized or optional stage fails.
- Use provider-neutral request, response, and intelligence contracts.
- Keep vendor SDKs and provider-specific configuration inside adapters.
- Version prompt contracts and validate normalized model output against typed
  schemas.
- Do not call external AI services from unit tests; use deterministic
  substitutes.
- Evaluate AI behavior with repeatable datasets and regression criteria before
  relying on it in consequential workflows.

## Testing and continuous integration

- Unit tests must be deterministic and fast.
- Add regression coverage for defects when practical.
- Test success, failure, and partial-success behavior at service boundaries.
- Separate controlled integration tests from external-network checks.
- Run focused tests during implementation and the full suite before merge.
- CI should install pinned dependencies and the required Playwright browser,
  run the full suite, and block merge on failure.
- Do not install or upgrade dependencies solely to bypass a failing check.

## Security and operations

- Load secrets from environment variables or an approved secret manager.
- Never commit real credentials or local `.env` files.
- Apply explicit network, tenant, and artifact-retention boundaries as the SaaS
  platform evolves.
- Require human approval and an audit trail for future high-impact automated
  actions.
