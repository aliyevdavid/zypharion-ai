# Zypharion Architecture

## Architectural intent

Zypharion separates deterministic application intelligence from optional AI
enhancement. Browser observations are normalized into typed models before any
analysis. Deterministic conclusions remain usable and explainable without an
AI provider, while AI integrations consume the same structured contracts
through provider-neutral boundaries.

## Current request paths

The FastAPI application is created by `create_app()` in `app/api/main.py`.
Application settings are attached to app state, and a shared router exposes:

- service metadata and health routes;
- a basic Playwright smoke route;
- browser extraction and deterministic intelligence routes; and
- the preferred versioned page-analysis workflow.

The principal workflow is:

```text
POST /api/v1/analyze
  -> FastAPI dependency composition
  -> PageAnalysisService
  -> Playwright browser extractor
  -> BrowserIntelligenceResult
  -> deterministic analyzer
  -> deterministic PageAnalysisResult
  -> optional AIIntelligenceEngine
  -> application PageAnalysisResult
```

`PageAnalysisService` owns orchestration and controlled error behavior. It
returns structured `success`, `partial_success`, or `failed` outcomes and keeps
the HTTP route thin. Browser or extraction failure prevents downstream
analysis; an optional AI failure preserves deterministic results and produces
a partial-success response.

## API routes

| Method | Path | Current behavior |
| --- | --- | --- |
| `GET` | `/` | Service status and environment metadata |
| `GET` | `/health` | Health, version, and environment metadata |
| `GET` | `/automation/smoke` | Playwright navigation, response-status, and title validation |
| `POST` | `/intelligence/analyze` | Browser intelligence extraction |
| `POST` | `/ai/analyze` | Browser extraction followed by deterministic analysis |
| `POST` | `/api/v1/analyze` | Complete workflow with optional AI enhancement |

The `/ai/analyze` name is retained for API compatibility; its current
implementation is deterministic. `/api/v1/analyze` is the preferred workflow
contract.

## Browser intelligence extraction

`app/intelligence/extractor.py` opens a public URL with Playwright and collects
page metadata, headings, links, images, forms, buttons, inputs, console errors,
response status, and timing. Repeated elements are collected through
browser-side snapshots instead of live `count()` and `nth()` iteration.

Each extraction category is isolated. A localized failure returns a safe
fallback and an `ExtractionWarning`, allowing other useful observations to
survive. Browser resources are closed in a `finally` block. The resulting
`BrowserIntelligenceResult` is the normalized boundary between unreliable web
content and downstream intelligence.

## Deterministic analysis and explainability

`app/intelligence/analyzer.py` interprets browser observations with explicit,
testable heuristics. It currently produces:

- page classification and confidence;
- detected features;
- accessibility, reliability, and form findings;
- recommendations;
- typed `EvidenceItem` records; and
- an `IntelligenceExplanation` linking a conclusion to evidence and, where
  appropriate, uncertainty.

This layer does not invoke an AI model. A conclusion remains traceable to page
content, structure, metadata, or observed behavior.

## Application behavior contracts

`app/intelligence/behavior_models.py` defines provider-neutral descriptions of
observable, testable application behavior, including navigation, form
submission, authentication, search, data entry, and user actions. A behavior
contains its source, evidence, and optional confidence. It deliberately does
not claim to be an executable test scenario: steps, assertions, expected
results, and negative cases belong to later test-design and execution layers.

## Optional AI enhancement

The AI layer has two boundaries:

1. `AIEngine` is the low-level provider contract for a structured `AIRequest`
   and `AIResponse`.
2. `AIIntelligenceEngine` is the page-intelligence contract that accepts a
   deterministic analysis and returns typed classification, summary, and
   recommendations.

Composition selects a provider from settings. The current adapters are a
deterministic mock and Azure OpenAI. Application services depend on contracts,
not vendor SDKs, so additional providers can be introduced without changing
the workflow or response models.

### Prompt contract

`PageIntelligencePromptBuilder` creates a provider-neutral request from the
deterministic result. The prompt contract is versioned, includes the expected
JSON schema, supplies structured evidence, requires evidence-grounded output,
and treats webpage content as untrusted data rather than instructions.

### Response parsing and normalization

`PageIntelligenceResponseParser` accepts one JSON object, including a narrowly
supported JSON Markdown fence, and rejects malformed, ambiguous, or extra
structured values. Pydantic then validates the normalized object against
`AIIntelligenceResult`. Provider content that fails decoding or validation is
converted to a controlled `AIResponseValidationError` and handled as partial
workflow success.

## Package responsibilities

- `app/api`: app factory, HTTP routes, and dependency entry points
- `app/analysis`: application-level workflow models, orchestration, and
  composition
- `app/automation`: basic deterministic smoke automation
- `app/intelligence`: browser extraction, normalized observations,
  deterministic analysis, evidence, and behavior contracts
- `app/ai`: provider-neutral contracts, prompt construction, response parsing,
  composition, and provider adapters
- `app/services`: compatibility service for extraction and deterministic
  analysis endpoints
- `app/core`: typed application settings
- `app/storage`: reserved boundary for future persistence
- `app/utils`: reserved boundary for cross-cutting helpers

## Architectural rules

- Keep routes thin and orchestration in application services.
- Keep deterministic analysis independent of AI providers.
- Normalize external browser and provider data into explicit models.
- Treat external pages and model responses as untrusted input.
- Preserve partial results when an optional or localized stage fails.
- Keep provider-specific SDK usage inside provider adapters.
- Use deterministic substitutes for AI providers in automated tests.
- Require explicit human approval for future high-impact autonomous actions.

## Future architecture boundaries

Persistence, tenant isolation, dashboards, repository and CI integrations,
multi-page application mapping, test generation, broad execution orchestration,
historical retrieval, and Quality Autopilot are future capabilities. They must
extend the current typed boundaries rather than bypass deterministic evidence
or couple product workflows to one provider.
