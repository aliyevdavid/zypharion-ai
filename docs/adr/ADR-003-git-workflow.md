# ADR-003: Use Main, Develop, and Short-Lived Feature Branches

- Status: Accepted
- Date: 2026-07-20

## Context

The portfolio should demonstrate controlled integration, pull-request review,
readable history, and release separation.

## Decision

Use:

```text

feature branch -> develop -> main

Feature branches are created from the latest develop and merged through pull
requests. main remains release-ready.
```
## Consequences

## Positive

Demonstrates pull-request workflow

Keeps release code separate from active development

Provides a clear integration point

Supports future CI branch policies

## Negative

More ceremony than trunk-based development for a solo developer

develop and main can diverge if release merges are neglected

## Alternatives Considered
Direct commits to main

GitHub Flow with only main

Full Git Flow including permanent release and hotfix branches