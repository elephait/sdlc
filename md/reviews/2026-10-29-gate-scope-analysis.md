# Analysis: scope the customization gate and require current gates

Accepted 2026-10-29, based on the plan review recorded in chat (Claude review, second pass).

## Intent

Close two enforcement gaps found after `74c2b39`: changes under `scripts/` and the root launchers bypassed the `customization` gate, and a gate recorded before a commit kept authorising later commits whose content it never saw.

## Acceptance criteria

1. A staged path under `scripts/`, `onboard.cmd`, `onboard-all.cmd` or `reports.cmd` requires the `customization` gate; existing `policy/`, `skills/`, `core/`, `.agents/skills/` and `*-customization/` coverage is unchanged. Covered by `required_gates` tests.
2. `implementation` and `customization` gates record the current HEAD and the staged tree (`git write-tree`), and `commit-ready` refuses when either differs from the state being committed, naming the gate and the reason.
3. `analysis` is story-level: exempt from freshness and not re-recorded per commit. `review` and `docs` require current HEAD but are not tree-bound.
4. `commit-ready` re-reads HEAD and the staged tree immediately before `git commit` and aborts if another process changed either.
5. `python scripts/verify.py` passes, generated payloads are in sync, and the README, policy, skill and host guides describe the new behaviour.

## Assumptions

- The Git index is the unit a commit records, so the staged tree is the correct content hash.
- One commit per handoff remains the normal flow; multiple commits in one story require re-recording only the change-specific gates.
- `git write-tree` is available wherever `commit-ready` runs; recording is best-effort and `None` still compares equal for repositories without history.

## Out of scope

- A drift check for the local `.sdlc/hooks/` copy (separate proposal).
- Backfilling HEAD/tree hashes on existing gate rows: they go stale by design, forcing fresh evidence for the next commit.
- Eliminating the final check-to-commit window entirely; it is narrowed, not removed, because Git has no conditional commit.

## Risks

- More ceremony for back-to-back commits: `implementation` and `customization` must be re-recorded after each commit.
- Recording `implementation` before staging leaves the gate permanently stale until re-recorded; the docs now order staging first.
- Concurrent writers can still interleave between the last check and `git commit`; the window is milliseconds and the scope hook remains a second guard.

## Plan review disposition

Claude reviewed the first plan and identified: launchers missing from the customization set, HEAD-only freshness missing edits staged after the gate, analysis should not be re-recorded, and "fails closed" overstated the race. All four are adopted; analysis evidence here is a real gate, not a waiver.
