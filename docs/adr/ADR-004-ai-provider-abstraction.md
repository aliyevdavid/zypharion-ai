
# ADR-004: Use a Provider-Independent AI Engine Contract

- Status: Accepted
- Date: 2026-07-20

## Context

The platform may use different language-model providers over time. Business logic
should not be coupled directly to one vendor SDK.

## Decision

Define a provider-independent `AIEngine` contract with structured request and
response models. Add provider adapters behind that contract.

## Consequences

### Positive

- Providers can be replaced with limited impact
- Deterministic mocks can be used in tests
- Core application logic avoids vendor-specific dependencies
- Provider comparison and fallback become possible

### Negative

- The abstraction adds initial code
- Provider-specific capabilities may not fit one universal interface
- The contract may need to evolve as use cases become clearer

## Alternatives Considered

- Import the OpenAI SDK directly throughout the application
- Use an orchestration framework immediately
- Support only one hardcoded provider
