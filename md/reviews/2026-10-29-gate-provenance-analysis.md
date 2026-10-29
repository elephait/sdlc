# Analysis: gate provenance and measured validation

Accepted 2026-10-29 after Claude's review of `01598ee`.

## Intent

Make gate evidence attributable and machine-measured where possible, surface missing telemetry instead of letting an empty report look clean, and correct the DeepSeek guide that still pointed at the wrong onboarding defaults.

## Acceptance criteria

1. `gates` records `recorded_by` separately from `approved_by`; `gate --recorded-by` stores it and the gate report shows both. Existing databases migrate additively.
2. `gate --run-verify` runs `scripts/verify.py`, stores exit code, test count, result and output tail in the gate details, and renders the verification line in the gate report. A passed gate is refused when the suite fails. The command refuses when `git diff` reports unstaged changes, because verify.py tests the worktree, not the staged tree.
3. `commit_ready` adds an automatic finding when the story has zero sessions and zero events: duration, retries and cost are unmeasured.
4. `deepseek.md` uses an explicit `--workspace`, starts a session with `--host deepseek`, stops it with a real outcome, and no longer offers an example that rebinds a story or reuses a fixed session ID.
5. `python scripts/verify.py` passes and generated payloads are in sync.

## Assumptions

- `verify.py` remains the repository's authoritative local check and is safe to run (it writes only test fixtures outside the checkout).
- A clean `git diff` is enough for the test result to describe the staged content; staged changes are expected and required.
- `recorded_by` is provenance, not authentication: the host name is still a claim, just a separate one.

## Out of scope

- Authenticating approvals or preventing an agent from typing an approver name.
- Binding `review`/`docs` gates to the staged tree (HEAD freshness only, as decided in the previous change).
- The `commit-ready --gates` shortcut: recording gates at commit time contradicts "a late gate is a claim without evidence", and one shared evidence string is weaker than per-gate evidence.
- Hard-failing the launcher when no terminal is attached: it already prints the chosen project; the doc now passes `--workspace` explicitly.

## Risks

- `--run-verify` makes a gate take as long as the suite (~25s). It is opt-in.
- The worktree/index guard is a precondition, not a sandbox: a process could edit files between the check and the suite run.
- A failed `--run-verify` refuses the gate, so a failing suite cannot be silently recorded as passed; recording `--status failed` remains possible with evidence.
- Older gate rows have no `recorded_by`; they display as unattributed rather than guessed.
