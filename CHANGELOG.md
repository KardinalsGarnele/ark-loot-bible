# Changelog

## 0.26.0

- Added Dockerfile and Docker Compose.
- Added one-click Windows launcher and Linux/macOS launcher.
- Added local-preview quick-start documentation.
- Verified all primary browser routes against a live Uvicorn server.


## 0.25.0

- Added Verification Coverage Dashboard.
- Added global, domain and map coverage APIs.
- Added prioritized data-gap reporting.
- Added five automated tests.


## 0.24.0

- Added Blueprint Finder browser view.
- Added reverse Blueprint -> Loot Source traversal.
- Added map, group, color, ring and level filters.
- Added location and respawn data to blueprint profiles.
- Added five automated finder tests.


## 0.23.0

- Added map regions and geometry placeholders.
- Added fixed, regional, route and moving loot locations.
- Added nullable respawn profiles and pool metadata.
- Added REST endpoints and five validation tests.


## 0.22.0

- Added map-level Loot Source Groups.
- Separated Supply, Cave, Deep Sea and Boss/Tek contexts.
- Added empty-group coverage indicators.
- Added source-group filtering to browser, CSV and JSON matrix exports.
- Added five automated tests.


## 0.21.0

- Added player-facing Loot Matrix browser view.
- Added stable map/color/ring/level sorting.
- Added map, color, ring, level and verification filters.
- Added CSV and JSON exports from the same query service.
- Added five automated consistency tests.


## 0.20.0

- Connected quality profiles to loot sources.
- Added color, ring and required-level metadata.
- Added item quality multipliers and automatic effective-range calculation.
- Added matrix API, CLI and five automated tests.


## 0.19.0

- Added Quality Profile & Blueprint Range Engine.
- Added transparent formula versioning and audit runs.
- Added REST API, CLI and five tests.


## 0.18.0

- Added manifest-based Loot Content Pipeline.
- Added Loot Source, Set and Entry content imports.
- Added nullable quality, chance and quantity proof-of-concept.
- Added CLI, API and four automated tests.


## 0.17.0

- Added item and blueprint content manifests.
- Added item component collections.
- Added idempotent import CLI and API.
- Added Rex Saddle structural reference package.
- Added four pipeline tests.


## 0.16.0

- Added creature content manifests and importer.
- Added Rex structural reference package.
- Added creature component graph and content API.
- Added idempotency and no-gameplay-claim tests.


## 0.15.0

### Added
- Official Content Manifest pipeline.
- Dry-run validation and atomic commit mode.
- Content manifest and record audit tables.
- Map component collections and graph relationships.
- First reproducible The Island package.
- Content import CLI and API.

### Quality
- 47 tests passing.
- Repository validation passing.
- Unsupported child content remains explicitly empty.


## 0.14.0

### Added
- Source & Evidence Workbench.
- Immutable content-addressed source snapshots.
- Source health-check history.
- Source-version comparison and unified textual diffs.
- Field-level claim evidence links.
- Stale-source detection.
- Source REST API and browser console.
- ADR-0015: Content-addressed source evidence.

### Quality
- 43 tests passing.
- Repository and HTTP validation passing.
- Canonical promotion remains human-reviewed and atomic.


## 0.13.0

- Added the browser-based Data Steward Console.
- Added operational summary, ingestion-run, and review-workspace APIs.
- Added progressive claim review, conflict resolution, promotion preview, atomic commit, and revision-history UI.
- Added steward-console API and static-page tests.

## 0.11.0 — Review & Promotion Workflow

- Added review cases for staged import records.
- Added field-level claim decisions and normalized reviewed values.
- Added automatic conflict detection and explicit conflict resolution.
- Added auditable reviewer decisions and optimistic row versions.
- Added API and CLI review operations.
- Approval is blocked until every claim is accepted and every conflict is resolved.
- Canonical writes remain isolated in entity-specific promotion tools.
- Added ADR-0012 and workflow documentation.
- 33 automated tests pass.

## 0.10.0

- Added adapter-based data ingestion with CSV and JSONL support.

## 0.12.0 - 2026-07-31

### Added
- Entity-specific canonical promotion for MAP, ITEM and CREATURE review cases.
- Field-level promotion previews.
- Immutable canonical revision snapshots.
- Optimistic row-version guard against stale review promotion.
- Atomic evidence linking and full rollback on failed validation.
- Promotion CLI and API endpoints.
