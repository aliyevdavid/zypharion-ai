# Zypharion Repository Instructions

## 1. Project Mission

Zypharion is an AI-powered Quality Engineering intelligence platform.
This repository provides the backend foundation for collecting browser evidence,
discovering observable application behavior, and producing structured,
explainable quality intelligence. Broader test design, coverage, diagnosis,
optimization, and release-quality outcomes remain product direction unless
identified as implemented in `docs/ROADMAP.md`.

Work in this repository should advance that mission while preserving a clear
boundary between deterministic application intelligence and optional,
provider-neutral AI enhancement.

## 2. Current Architecture

The current intelligence flow is:

```text
FastAPI backend
→ PageAnalysisService
→ Playwright browser extraction
→ BrowserIntelligenceResult
→ deterministic page analysis, structured evidence, and behavior discovery
→ optional provider-neutral AI enhancement
→ PageAnalysisResult
```

The current HTTP endpoints are:

- `GET /`
- `GET /health`
- `GET /automation/smoke`
- `POST /intelligence/analyze`
- `POST /ai/analyze`
- `POST /api/v1/analyze` (preferred versioned analysis endpoint)

The preferred workflow keeps browser extraction and deterministic intelligence
independent of AI. Optional AI enhancement consumes structured deterministic
results through provider-neutral contracts and must not replace their evidence
or failure behavior.

## 3. Current Implementation Status

- The backend supports Playwright extraction, deterministic page analysis,
  structured evidence, behavior discovery, and optional AI enhancement.
- Repeated browser elements are collected through stable browser-side snapshots,
  with category-level warnings and partial results for localized failures.
- Treat `docs/ROADMAP.md` as the capability-status reference and verify
  implementation details and test counts when a task depends on them.

## 4. Engineering Principles

- Prefer small, targeted changes over broad rewrites.
- Preserve existing behavior and API contracts unless a change is explicitly approved.
- Keep deterministic intelligence separate from optional AI enhancement.
- Favor clear boundaries, explicit data flow, and maintainable abstractions.
- Explain the reason for architectural changes and identify their effects on existing behavior.
- Avoid site-specific workarounds unless they are clearly justified.
- Clearly distinguish verified facts, assumptions, and recommendations.

## 5. Python and FastAPI Standards

- Prefer typed Python throughout production code and tests.
- Use explicit Pydantic models for request, response, extraction, and analysis data.
- Keep FastAPI endpoint contracts stable unless an API change is explicitly approved.
- Keep route handlers thin; orchestration belongs in services and domain behavior belongs in the relevant intelligence components.
- Preserve the separation among API, service, extraction, deterministic analysis, and optional AI enhancement layers.
- Make error behavior deliberate, structured, and testable.

## 6. Playwright Extraction Standards

- Treat every external web page as dynamic and unreliable.
- Prefer browser-side stable snapshots over live locator `count()`/`nth()` iteration when collecting repeated elements.
- Design extraction for partial success.
- Return structured warnings when content cannot be read or extraction is incomplete.
- One unreadable or detached element must not fail the entire page analysis.
- Do not turn a localized extraction error into a page-wide failure when useful data can still be returned.
- Normalize browser-derived data into explicit models before deterministic analysis.
- Avoid timing assumptions and site-specific selectors unless they are clearly justified and documented.

## 7. Testing Standards

- Inspect the relevant implementation and tests before editing.
- Add or update focused tests for changed behavior, including failure and partial-success paths.
- Run relevant targeted tests while implementing.
- Run the full `pytest` suite after every implementation change.
- Never claim success without running the relevant tests.
- Report the exact test command and result. If tests cannot run, state that clearly and do not describe the change as verified.
- Do not install or upgrade dependencies to make tests pass without explicit approval.

## 8. Git Workflow

- Use a small, short-lived feature, fix, chore, or documentation branch.
- Merge changes through a reviewed pull request directly into `main`.
- Keep `main` release-ready; direct pushes to `main` are not permitted.
- Require continuous integration to pass before merge.
- Do not commit, push, merge, delete branches, or modify Git history without explicit approval.
- Preserve unrelated working-tree changes and do not overwrite user work.

## 9. Change Safety Rules

- Modify only files required by the approved task.
- Do not modify files outside this repository.
- Do not install or upgrade dependencies without explicit approval.
- Never expose secrets or read `.env` values unless explicitly requested.
- Preserve existing behavior, data models, and API contracts unless explicitly approved.
- Avoid destructive operations and broad automated rewrites.
- Before editing, inspect the relevant implementation and tests.
- After editing, show the changed files, test results, and remaining risks.

## 10. Codex Operating Instructions

- Begin by inspecting repository state, the relevant implementation, and relevant tests.
- Make reasonable, clearly stated assumptions only when they do not materially change scope or architecture.
- Prefer the smallest coherent change that fulfills the request.
- Keep deterministic analysis independent of the `app/ai` abstraction.
- Explain architectural decisions and noteworthy tradeoffs.
- Clearly label verified facts, assumptions, and recommendations in reports.
- Validate implementation changes with targeted tests and the full `pytest` suite.
- Never claim that work succeeded when it was not tested.
- Do not install or upgrade dependencies without explicit approval.
- Do not commit, push, merge, delete branches, modify Git history, or work directly on `main` without explicit approval.
- Never read `.env` values or expose credentials unless explicitly requested.
- At handoff, report changed files, tests run and their results, and any remaining risks.

## 11. Current Product Direction

Use `docs/ROADMAP.md` to distinguish the implemented foundation from near-term,
mid-term, and later work. Do not infer that a roadmap outcome is implemented.
Keep current behavior aligned with `docs/PROJECT_ARCHITECTURE.md` and preserve
the capability boundaries documented in the README and project vision.
