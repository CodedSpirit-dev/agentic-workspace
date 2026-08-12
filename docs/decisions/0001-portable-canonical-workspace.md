# ADR-0001: Keep one canonical installed workspace

- **Status:** accepted
- **Date:** 2026-08-12

## Context

The source repositories accumulated useful but divergent copies of skills,
agents, hooks, workspaces, and project templates. Copying every provider
surface into a new repository would preserve drift and domain assumptions.

## Decision

Install one canonical `agentic-workspace/` into each destination repository.
Expose it through provider-specific adapters. Keep project knowledge in an
indexed documentation tree and project execution state in one registry.

Support `traditional`, `sprint`, and `flexible` project modes over the same
artifact identity and relation model.

## Consequences

- Provider adapters remain small and replaceable.
- A skill or agent is edited once.
- Existing repository instructions must be preserved before the root entry
  point is replaced.
- Updates require a managed-file conflict policy.
- Domain-specific procedures are opt-in extensions, not universal defaults.
