# Source Registry

The source registry records where a claim came from before the claim can enter canonical data.

A source and a source version are separate concepts:

- `sources` identifies the publisher, title, and locator.
- `source_versions` identifies the exact captured content by SHA-256 hash.

This prevents a changing web page, DevKit export, patch note, or test result from silently changing the meaning of previously imported evidence.

## Minimum source metadata

- stable source ID
- source type
- title
- publisher where known
- locator or local snapshot path
- retrieval timestamp
- content hash

A source being official does not automatically make every parsed claim correct. Import and field-level validation still apply.
