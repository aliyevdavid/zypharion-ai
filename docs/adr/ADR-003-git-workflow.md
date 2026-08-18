# ADR-003: Use Develop as a Temporary Integration Branch

- Status: Superseded
- Date: 2026-07-20
- Updated: 2026-08-13

This record documents the former transitional workflow. The current workflow
uses short-lived feature branches and reviewed pull requests directly into
`main`, as defined in the engineering standards.

## Context

Zypharion needs controlled integration, pull-request review, readable history,
and a release-ready `main` branch. The repository currently integrates work
through `develop` while documentation, CI, and branch protections are prepared
for promotion to a main-based workflow.

## Decision

Use the following current workflow:

```text
short-lived feature branch -> develop -> main promotion
```

Feature branches are created from the current integration baseline and merged
through reviewed pull requests. `develop` is a temporary integration branch;
`main` remains the release boundary until the readiness work is complete.

After `main` is promoted and protected, the intended workflow is GitHub Flow:

```text
short-lived feature branch -> reviewed pull request -> main
```

That transition is planned, not yet adopted. It requires passing pull-request
CI, configured branch protection, and an explicit workflow decision update.

## Consequences

### Positive

- Preserves the repository's current integration path during main readiness
- Keeps the release boundary separate from active integration work
- Establishes clear prerequisites for a simpler future workflow
- Supports small changes, review, and automated quality gates

### Negative

- Two long-lived branches add integration ceremony
- `develop` and `main` can diverge if promotions are delayed
- Contributors must confirm the correct pull-request base during transition

## Transition criteria

Before adopting the main-based workflow:

- promote an approved, verified `develop` state to `main`;
- require CI checks on pull requests;
- protect `main` from direct pushes and history rewrites;
- require reviewed pull requests for changes; and
- update this ADR or supersede it with a dedicated workflow ADR.

## Alternatives considered

- Direct commits to `main`
- Immediate GitHub Flow without readiness controls
- Permanent `develop` integration
- Full Git Flow with permanent release and hotfix branches
