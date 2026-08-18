# ADR-003: Use Develop as a Temporary Integration Branch

- Status: Superseded
- Date: 2026-07-20
- Updated: 2026-08-13

This record documents the former transitional workflow. The current workflow
uses short-lived feature branches and reviewed pull requests directly into
`main`, as defined in the engineering standards.

## Context

Zypharion needed controlled integration, pull-request review, readable history,
and a release-ready `main` branch. At the time of this decision, the repository
integrated work through `develop` while documentation, CI, and branch
protections were prepared for a main-based workflow.

## Decision

The transitional workflow was:

```text
short-lived feature branch -> develop -> main promotion
```

Feature branches were created from the integration baseline and merged through
reviewed pull requests. `develop` served as a temporary integration branch;
`main` remained the release boundary during readiness work.

The intended replacement was a main-based workflow:

```text
short-lived feature branch -> reviewed pull request -> main
```

That transition has since been adopted. Current guidance is defined in the
engineering standards linked above.

## Consequences

### Positive

- Preserved the repository's integration path during transition preparation
- Kept the release boundary separate from active integration work
- Established clear prerequisites for a simpler workflow
- Supported small changes, review, and automated quality gates

### Negative

- Two long-lived branches added integration ceremony
- `develop` and `main` could diverge when promotions were delayed
- Contributors had to confirm the correct pull-request base during transition

## Transition criteria

The transition criteria were:

- promotion of an approved, verified `develop` state to `main`;
- required CI checks on pull requests;
- protection of `main` from direct pushes and history rewrites;
- required reviewed pull requests for changes; and
- an update to this ADR or a superseding workflow ADR.

## Alternatives considered

- Direct commits to `main`
- Immediate GitHub Flow without readiness controls
- Permanent `develop` integration
- Full Git Flow with permanent release and hotfix branches
