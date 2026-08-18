# Zypharion

Zypharion is an AI-powered Quality Engineering intelligence platform.
This repository provides the backend foundation for collecting browser evidence
and producing structured, explainable quality intelligence. Zypharion is being
built toward broader product outcomes including better test design, coverage
discovery, risk-based validation, failure diagnosis, automation optimization,
and release-quality decisions.

## Why Zypharion

Quality signals are commonly split across application structure, browser
behavior, test suites, CI systems, and incident reports. Teams spend valuable
time assembling that evidence by hand and still struggle to identify the most
important coverage and release risks. Zypharion is being built to turn those
signals into structured, explainable quality intelligence and actionable
validation workflows.

## Current capabilities

The current backend can:

- inspect a public web page with Playwright;
- capture metadata, headings, links, images, forms, buttons, inputs, console
  errors, response status, timing, and structured extraction warnings;
- preserve useful results when an extraction category cannot be read;
- deterministically classify page types and identify observable features;
- produce findings, recommendations, structured evidence, and explainable
  conclusions;
- identify application behavior contracts from browser evidence;
- run a complete analysis workflow with controlled success, partial-success,
  and failure responses; and
- optionally enrich deterministic results through a provider-neutral AI
  contract with a versioned prompt and validated response parsing.

## Architecture

```text
Client
  -> FastAPI application factory and routes
  -> PageAnalysisService
  -> Playwright browser extraction
  -> BrowserIntelligenceResult
  -> deterministic analysis and structured evidence
  -> optional provider-neutral AI enhancement
  -> PageAnalysisResult
```

Browser extraction and deterministic analysis are the foundation. They do not
depend on an LLM and remain available when AI enhancement is disabled or
fails. When requested, the AI layer receives structured deterministic results,
uses a provider-neutral request contract, and normalizes provider output into
validated response models. See
[Project Architecture](docs/PROJECT_ARCHITECTURE.md) for component details.

## Local setup (Windows PowerShell)

Python 3.11 is the current supported runtime assumption. Run these commands
from the repository root.

Create and activate a virtual environment:

```powershell
py -3.11 -m venv venv
.\venv\Scripts\Activate.ps1
```

Install the pinned dependencies and Chromium:

```powershell
python -m pip install -r requirements.txt
python -m playwright install chromium
```

Create the local configuration file from the tracked template:

```powershell
Copy-Item .env.example .env
```

The defaults use `AI_PROVIDER=mock`, which requires no external AI credentials.
To use Azure OpenAI, set `AI_PROVIDER=azure_openai` and provide the Azure
endpoint, API key, deployment, and API version listed in `.env.example`. Never
commit `.env` or real credentials.

Start the API:

```powershell
python -m uvicorn app.api.main:app --reload
```

The API is available at `http://127.0.0.1:8000`; interactive OpenAPI
documentation is at `http://127.0.0.1:8000/docs`.

Run the test suite:

```powershell
python -m pytest -q
```

Without an activated virtual environment, use
`.\venv\Scripts\python.exe` in place of `python`.

## API endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/` | Return service status and environment information. |
| `GET` | `/health` | Return health, version, and environment information. |
| `GET` | `/automation/smoke?url=...` | Run basic browser smoke validation against a public URL. |
| `POST` | `/intelligence/analyze` | Return structured Playwright browser observations. |
| `POST` | `/ai/analyze` | Run extraction plus deterministic, explainable analysis. Despite its legacy path, this endpoint does not invoke an AI provider. |
| `POST` | `/api/v1/analyze` | Run the complete workflow with optional AI enhancement. |

`POST /api/v1/analyze` is the preferred workflow endpoint because it composes
browser extraction, deterministic intelligence, and optional AI enhancement
behind one structured result contract.

Deterministic request:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/api/v1/analyze `
  -ContentType "application/json" `
  -Body '{"url":"https://example.com","use_ai":false}'
```

Set `use_ai` to `true` to request enhancement from the configured AI provider.

## Current boundaries

- Analysis currently targets one public URL per request; authenticated sessions,
  multi-page journeys, crawling, and persistent projects are not implemented.
- Browser-derived conclusions are heuristics based on observable page signals,
  not guarantees about complete application behavior or release safety.
- Current deterministic findings cover a focused set of page classification,
  accessibility, form, reliability, and behavior signals.
- The backend does not yet include a hosted dashboard, tenant isolation,
  persistence, CI/CD integrations, test generation, or test execution beyond
  the basic smoke endpoint.
- AI output is optional, provider-dependent, and validated, but it must not
  replace deterministic evidence or human review for release decisions.

## Roadmap

Near-term work focuses on deeper behavior discovery, test-design intelligence,
coverage-gap analysis, execution contracts, and CI quality gates. Mid-term work
adds persistent projects, failure diagnosis, release-quality views, and secure
team workflows. Quality Autopilot remains a later direction with explicit
guardrails and human approval. See [Roadmap](docs/ROADMAP.md).

Additional project guidance is available in
[Project Vision](docs/PROJECT_VISION.md),
[Engineering Standards](docs/ENGINEERING_STANDARDS.md), and the
[architecture decision records](docs/adr/README.md).
