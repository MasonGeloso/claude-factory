# Conditional failure checks

Apply only to changed behavior. Reuse evidence in existing gates; add no review rounds.

- **Mark work complete only after its result is saved.** After partial failure, retries must recover unfinished work without duplicating effects.
- **Check queue delays under realistic load.** Slow jobs must not push other work past its required delivery window.
- **Check meaning, not just rendering.** Format, translation and series changes must preserve units, frequency, dates and machine identifiers through their consumers.
- **Validate external responses before caching them.** HTTP 200 does not prove the body is valid; check at the shared client boundary.
- **Verify monitoring catches missing work.** Test upstream failure and stalled output; distinguish failure from legitimate inactivity.
