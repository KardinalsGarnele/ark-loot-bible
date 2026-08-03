# Verification Policy

## Status values

- `VERIFIED`
- `COMMUNITY_VERIFIED`
- `NEEDS_VERIFICATION`
- `DISPUTED`
- `DEPRECATED`

## Evidence priority

1. Official game data or official development assets
2. Official patch notes or official documentation
3. Reproducible in-game verification
4. Independently repeated community verification
5. Unverified community report

## Canonical publication rules

- Every canonical fact must reference at least one source.
- Conflicting claims are preserved as evidence records and marked `DISPUTED` until resolved.
- Unknown values remain null; they are never filled with guesses.
- Derived values must record their formula, inputs, and calculation version.
- Every verification change creates a new verification event.
