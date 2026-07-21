# ADR-002: Use Playwright for Browser Automation

- Status: Accepted
- Date: 2026-07-20

## Context

Zypharion requires reliable browser interaction, modern web support, network
inspection, screenshots, isolated contexts, and future autonomous exploration.

## Decision

Use Playwright as the browser automation engine.

## Consequences

### Positive

- Modern cross-browser automation
- Built-in waiting behavior
- Browser contexts and isolation
- Network and tracing capabilities
- Strong fit for browser-intelligence collection

### Negative

- Browser binaries increase environment size
- External websites can make tests nondeterministic
- Long-running browser tasks should eventually move outside request threads

## Alternatives Considered

- Selenium
- Cypress
- Puppeteer