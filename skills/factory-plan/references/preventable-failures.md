# Conditional failure checks

Use only the checks whose trigger intersects the changed behavior. During planning, name the
invariant and a way to falsify it; during code review, trace the implementation; during QA, run the
applicable failure scenario in an isolated environment. Reuse that evidence across gates. These
checks belong in existing correctness/risk/scenario rows, not new gates or mandatory report rows.
An unrelated change requires no new experiment. A blocker needs a concrete violated requirement or
reachable wrong outcome; a hypothetical improvement is not enough.

- **Commit progress only after the outcome it represents is durable.** For cursors, daily stamps,
  acknowledgements or completion flags, distinguish queued, attempted and completed work. Walk a
  partial failure followed by retry: no lost items or duplicate external effects. A scan cursor may
  advance past failure only if durable retry ownership preserves that work.
- **Check shared-worker delay with realistic competing work.** For scheduling or queue changes,
  trace the actual ordering, concurrency and longest relevant job against the required delivery
  window. Exercise a busy worker, not only an empty queue. No separate priority lane is required
  when bounded waiting meets the requirement; do not invent a delivery deadline.
- **Preserve meaning across representation changes.** When combining series, translating stored
  values or changing formats, trace consumers of units, frequency, dates and machine identifiers.
  Check a known input through the actual calculation/parser, including mismatched representations.
  A rendered chart or translated label alone is not proof; display-only copy needs no numeric test.
- **Validate external payloads before persisting success.** For transport/cache changes, check the
  promised body format and relevant error/redirect behavior, including an error body under HTTP 200.
  Reject invalid content before it becomes durable cached data. Reuse validation at the shared client
  boundary; do not duplicate it in each caller when that boundary already guarantees the contract.
- **Make health checks detect missing work.** For pipeline monitoring or progress changes, walk
  zero new output, upstream failure and stalled progress. Check the denominator and source of each
  success/freshness signal; a metric derived solely from successful rows or its own completion stamp
  cannot prove input coverage. Use an independent expectation/error signal where coverage matters,
  and distinguish a legitimate idle source from failure rather than alerting on every empty result.
