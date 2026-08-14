# ADR-001: Use Python and FastAPI

- Status: Accepted
- Date: 2026-07-20

## Context

Zypharion requires strong integration with AI libraries, browser automation,
data processing, typed APIs, testing tools, and cloud services.

## Decision

Use Python as the primary language and FastAPI as the backend API framework.

## Consequences

### Positive

- Strong AI and machine-learning ecosystem
- Native integration with Playwright Python
- Type-driven API schemas
- Automatic OpenAPI documentation
- Straightforward testing with pytest

### Negative

- CPU-intensive workloads may require separate worker processes
- Async and synchronous code boundaries require careful design
- Python dependency management must be controlled

## Alternatives Considered

- TypeScript with Node.js
- Java with Spring Boot
- C# with ASP.NET Core