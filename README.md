# zypharion-ai
Zypharion is an AI Software Intelligence Platform that understands, tests, monitors, and predicts software behavior using LLMs and automation.

## Local API validation

Start the API:

```powershell
.\venv\Scripts\python.exe -m uvicorn app.api.main:app --reload
```

Validate health:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

Open Swagger at http://127.0.0.1:8000/docs.

Run a deterministic analysis request:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/api/v1/analyze `
  -ContentType "application/json" `
  -Body '{"url":"https://example.com","use_ai":false}'
```

Run an AI-enabled analysis request:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/api/v1/analyze `
  -ContentType "application/json" `
  -Body '{"url":"https://example.com","use_ai":true}'
```

Analysis requests require the configured runtime providers. Playwright browser
binaries may need to be installed before browser-backed analysis works:

```powershell
.\venv\Scripts\python.exe -m playwright install chromium
```
