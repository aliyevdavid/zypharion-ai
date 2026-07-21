# Zypharion Architecture

## Current System

```text
Client
  |
  v
FastAPI
  |
  +-- Health API
  |
  +-- Automation API
          |
          v
      Playwright
          |
          v
     Target Website
```     

## Target Architecture

```text
User or CI/CD
      |
      v
API and Dashboard Layer
      |
      v
Application Services
      |
      +-------------------+
      |                   |
      v                   v
Browser Intelligence    AI Orchestrator
      |                   |
      v                   v
Playwright Engine      LLM Providers
      |                   |
      +---------+---------+
                |
                v
       Structured Intelligence
                |
        +-------+--------+
        |                |
        v                v
   PostgreSQL        Vector Store
        |                |
        +-------+--------+
                |
                v
        Risk and Insight Engine
                |
                v
      Reports, Actions, and PRs
```

## Package Responsibilities

### `app/api`

Defines HTTP endpoints and request/response contracts. It should remain thin
and delegate business behavior to services.

### `app/automation`

Contains deterministic browser and API automation capabilities.

### `app/ai`

Contains provider-independent AI contracts, model adapters, prompts, and
evaluation-aware AI behavior.

### `app/intelligence`

Transforms collected software signals into structured findings, risks, and
recommendations.

### `app/services`

Coordinates use cases across automation, AI, storage, and intelligence layers.

### `app/storage`

Contains persistence abstractions for relational data, artifacts, and vector
memory.

### `app/core`

Contains application-wide settings, exceptions, logging, and foundational
infrastructure.

### `app/utils`

Contains small reusable helpers that do not belong to a business domain.

## Architectural Boundaries

- API endpoints should not contain complex business logic.
- AI providers should not be imported directly outside `app/ai`.
- Automation should produce structured data before LLM analysis.
- Secrets must come from environment variables or secret-management systems.
- Tests must use deterministic substitutes for external AI providers.
- High-impact autonomous actions require a human-approval boundary.
