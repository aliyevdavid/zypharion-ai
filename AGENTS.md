# Zypharion AI Repository Instructions

## 1. Project Mission

Zypharion AI is an Application Intelligence and AI Quality-Control Platform. Its purpose is to observe, understand, map, test, diagnose, and eventually help heal software applications.

Work in this repository should advance that mission while preserving a clear boundary between deterministic application intelligence and future LLM-driven intelligence.

## 2. Current Architecture

The current intelligence flow is:

```text
FastAPI
→ IntelligenceService
→ Playwright extraction
→ BrowserIntelligenceResult
→ deterministic analyzer
→ PageAnalysisResult
```

The current HTTP endpoints are:

- `GET /`
- `GET /health`
- `GET /automation/smoke`
- `POST /intelligence/analyze`
- `POST /ai/analyze`

The `app/ai` abstraction exists, but it is not currently part of the intelligence request flow. Keep deterministic intelligence separate from future LLM intelligence unless an architectural change is explicitly approved.

## 3. Current Implementation Status

- Day 6 is complete and merged.
- The current test count is 31.
- The service supports Playwright-based browser extraction and deterministic page analysis.
- The known extractor weakness is live `locator.count()`/`locator.nth()` iteration: extraction can fail when a page mutates the DOM during iteration.
- Treat these statements as the current repository baseline. Verify implementation details and test counts when a task depends on them.

## 4. Engineering Principles

- Prefer small, targeted changes over broad rewrites.
- Preserve existing behavior and API contracts unless a change is explicitly approved.
- Keep deterministic intelligence separate from future LLM intelligence.
- Favor clear boundaries, explicit data flow, and maintainable abstractions.
- Explain the reason for architectural changes and identify their effects on existing behavior.
- Avoid site-specific workarounds unless they are clearly justified.
- Clearly distinguish verified facts, assumptions, and recommendations.

## 5. Python and FastAPI Standards

- Prefer typed Python throughout production code and tests.
- Use explicit Pydantic models for request, response, extraction, and analysis data.
- Keep FastAPI endpoint contracts stable unless an API change is explicitly approved.
- Keep route handlers thin; orchestration belongs in services and domain behavior belongs in the relevant intelligence components.
- Preserve the separation among API, service, extraction, deterministic analysis, and future AI layers.
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

- Do not modify `main` or `develop` directly.
- Feature branches follow `feature/day-XX-description`.
- Changes merge in this order: feature branch → `develop` → `main`.
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
- Do not commit, push, merge, delete branches, modify Git history, or work directly on `main` or `develop` without explicit approval.
- Never read `.env` values or expose credentials unless explicitly requested.
- At handoff, report changed files, tests run and their results, and any remaining risks.

## 11. Current Milestone: Day 7

Day 7 focuses on extractor resilience for dynamic real-world websites.

The primary known issue is that live Playwright locator iteration using `count()` and `nth()` can become invalid while a page mutates its DOM. Day 7 work should prefer browser-side stable snapshots, preserve partial extraction results, emit structured warnings, and prevent a single unreadable element from failing the entire page analysis.

Success for this milestone means extractor behavior is more resilient without unnecessary API changes, broad rewrites, or site-specific fixes, and the behavior is covered by focused tests plus the full test suite.
