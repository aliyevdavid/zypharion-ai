# Zypharion Engineering Standards

## Branching

- `main` contains release-ready code.
- `develop` contains integrated development work.
- Each work item uses a branch created from the latest `develop`.
- Feature branches are merged through pull requests.
- Remote feature branches are deleted after merge.
- Local historical branches may be retained but must not receive new work.

## Branch Naming

```text
feature/day-XX-short-description

Example: feature/day-04-engineering-roadmap
```

## Commit Format

```text
Zypharion uses Conventional Commit-style messages:
type(scope): concise description


Examples:

feat(ai): add provider-independent AI engine
test(core): validate cached application settings
docs(architecture): document target system design
fix(automation): ensure browser closes after navigation failure
```

## Pull Requests

```text
Every pull request must include:

summary;
key changes;
validation performed;
test results;
known limitations;
correct base branch: develop.

```

## Definition of Done

```text

A feature is complete when:

1. Acceptance behavior is implemented.
2. Appropriate automated tests pass.
3. Existing tests remain green.
4. No secrets are committed.
5. Documentation is updated when architecture or behavior changes.
6. The staged diff has been reviewed.
7. A pull request has been reviewed and merged.
8. Local develop has been synchronized after merge.

```

## Python Standards

```text

Use type annotations for public functions.
Prefer explicit and descriptive naming.
Keep API routes thin.
Avoid hidden global mutable state.
Validate external input.
Use structured models for data crossing boundaries.
Close browser, network, file, and database resources reliably.
Do not call real external AI services from unit tests.

```

## Testing Principles

```text

Unit tests must be deterministic and fast.
Integration tests may use local services or controlled external targets.
External-network tests will be marked and separated in CI.
LLM behavior must be evaluated, not assumed.
Every defect fix should include a regression test when practical.

```