# ADR-0002: Platform-First Architecture

- Status: Accepted
- Date: 2026-07-30

## Context
The project will serve a website, API, bot, app, spreadsheets, and downloadable databases.

## Decision
Canonical data and domain logic belong to the platform layer. User interfaces are clients of that layer.

## Consequences
No canonical fact or core calculation may exist exclusively inside one interface.
