# Review: four-host customization and handoff gates

Reviewed 2026-10-28 against commits `3627ca2` (Copilot) and `5247c8c` (Claude), the uncommitted three-host work, and the new requirements: DeepSeek as a fourth host, gate-enforced handoffs, shared-layer minimisation, a batch onboarding command, and an evidence-based answer on Codex cost.

## What changed

| Area | Change |
|---|---|
| Handoff gates | New `gates` table, `gate` and `gate-status` commands, gate artifacts under the story ledger, and enforcement in `commit_ready`. An `ai commit: ` needs `analysis` and `implementation`; an `ai code review: ` needs `review` and `docs`; either needs `customization` when staged paths touch policy, skills, core or an adapter. |
| Shared instructions | `policy/universal.md` gains the five handoffs. New `policy/harness-notes.md` carries what repository-instruction hosts need, so Codex and DeepSeek read one generated `AGENTS.md` instead of two host-specific ones. `codex-customization/host-notes.md` is deleted; its content was either shared or belongs in `codex.md`. |
| DeepSeek | New `deepseek-customization/` with `README.md` and `deepseek.md`: setup, runnable commands, gate examples, skill access, activation check. No plugin, no hooks, no second copy of the payload. |
| Host attribution | `sessions.host` (additive migration), `session-start --host`, and `host` in the tracking report's session summary. |
| Commit path | A missing gate stops before Git runs. The Copilot co-author default is gone: with no `--co-author` and no `$SDLC_CO_AUTHOR`, no trailer is added rather than misattributing a Claude or Codex commit. Session outcomes are validated and cannot be rewritten; a policy-hook response that cannot be parsed is a clear error instead of a traceback. |
| Scope hook | `git.exe` is judged like `git`, and a `-C` inside a commit message no longer redirects the credential scan to another repository. Both have tests. |
| Test harness | Workspaces are created beside the repository in the sandbox root and removed with a read-only-bit pass. `tempfile.mkdtemp` mode `0700` produced directories the Windows sandbox could not traverse, so the previous suite could not run in this environment. |
| Onboarding | `scripts/onboard-all.py`, `onboard-all.cmd` and `onboard.cmd --all`: refresh all four payloads, validate, then track untracked projects while preserving every active binding. `--dry-run` previews. |
| Metadata | `.sdlc/project.yaml` claimed `COPILOT-CUSTOMIZATION-001` while `active-story.json` bound `SDLC-001`; aligned to the active story. |

## Findings from the audit

| Priority | Finding | Disposition |
|---|---|---|
| P1 | No workflow enforcement: `commit_ready` accepted any staged index with a message. | Fixed: required gates are checked before the commit and echoed in the result. Direct `git commit` still bypasses it; see residual risk 1. |
| P1 | Every commit without `--co-author` was attributed to Copilot. | Fixed: trailer only from the flag or `$SDLC_CO_AUTHOR`. |
| P1 | `git.exe push` and `git.exe commit` matched neither regex, a full bypass of the scope hook. | Fixed and tested. A wrapper script or nested interpreter still bypasses it. |
| P2 | `-C` anywhere in the command, including the message body, chose the repository to scan for staged credentials. | Fixed and tested: only global options before the subcommand count. |
| P2 | `stop_session` overwrote a closed session's outcome with any string. | Fixed: outcome validated, closed session refused, identical outcome idempotent. |
| P2 | Stall detection queried `session_id = NULL`, which never matches. | Fixed: a session is required for a stall signal. |
| P2 | An unparseable policy-hook response raised `KeyError` outside the CLI's error handling. | Fixed: `ValueError` with the hook's own message. |
| P2 | The test suite could not create usable temporary directories in this sandbox. | Fixed: sandbox-root workspaces with explicit cleanup. |
| P3 | Codex credit consumption could not be analysed: no host label, no tokens, story-level scorecards. | Partly fixed: `--host` attribution and per-session host reporting. Billing units remain unrecorded by design; see the [usage analysis](2026-10-28-codex-usage-analysis.md). |
| P3 | Story status and `story.md` stay `DRAFT`; nothing updates them. | Recorded, not fixed. Gate records are the stronger signal today. |
| P3 | Duplicated helpers: `require_under_dev`, `now()`, git invocation, prefix constants. | Recorded, not fixed. The copies already disagree on symlink and case semantics. |

## Shared versus host-specific

- Shared: `policy/`, `skills/`, `core/` (CLI, schema, hooks), `scripts/` (sync, verify, onboarding), and the gate model.
- Copilot: plugin manifest, rule frontmatter, hook wiring, `host-notes.md`.
- Claude: `CLAUDE.md` import, plugin manifest, hook wiring, `host-notes.md`.
- Codex and DeepSeek: documentation only. They share the generated `AGENTS.md` and `.agents/skills/`, and install no hooks.
- Generated duplication is packaging, not a second editable source: `sync-customizations.py --check` fails on drift.

## Verification performed

- `python scripts/verify.py`: PASS. 38 tests, generated-content drift check, and skill validation (2 skills, 0 errors).
- CLI end to end on a scratch repository: `commit-ready` refused with the two named missing gates, then succeeded after both were recorded, returning the gate map and a handoff report path.
- `onboard-all.py --skip-refresh --dry-run`: found `denistek` and `utils` as untracked, reported `sdlc` preserved, and listed all five host payloads as present.
- Codex analysis: read the SQLite database and every generated report; zero Codex sessions, zero token fields, two host-attributable commits.

Not run: no live Copilot, Claude, Codex or DeepSeek session; the real `onboard-all` was not executed against other repositories (only previewed); no runtime token or credit accounting exists to verify.

## Residual risks

1. **Gates are enforced at `commit-ready`, not in Git.** A direct `git commit` skips them, exactly as it skips the scope hook. A repository-level `pre-commit` hook would close this; it is not installed, because it would affect every commit in the workspace.
2. **Approval is recorded, not authenticated.** `--approved-by` is a claim. An agent can write a name it was not given. Only the host's approval prompt, or a human reading the handoff, establishes authorization.
3. **Credential detection is name-based.** A secret inside `config.json` passes; `commit-ready` also does not inspect staged content.
4. **Evidence is written after the commit.** If the handoff report fails, the commit exists without its report and a retry can duplicate it.
5. **Scorecards count only `PostToolUse` failures**, so `PostToolUseFailure` events do not block a `passed` outcome, and `runtimeVerified` is free input.
6. **No token, credit or cost accounting.** Host attribution is now possible; billing units are not.
7. **Ten empty scratch folders from an interrupted test run remain in `core/`.** They were created with permissions this user cannot change, so they cannot be deleted without widening access. They are empty, ignored by Git, and deletable by the user from an elevated shell with `Remove-Item core\sdlc-gate-*, core\probe-* -Recurse -Force`. New runs no longer create them: test workspaces are created beside the repository with normal permissions.

## Second self-review pass (2026-10-28)

Two defects found while reviewing the final diff, fixed before the commit:

| Priority | Finding | Disposition |
|---|---|---|
| P2 | `_is_customization_path` used `.lstrip("./")`, which strips the leading dot from `.agents/skills/...`; a commit touching only generated skills skipped the customization gate. | Fixed with `removeprefix("./")` and a regression test covering generated-skill and `./` paths. |
| P2 | The README says the handoff report names the gates that authorised the commit, but `_write_commit_analysis` never passed them through. | Fixed: `gates` now appears in the report and in its `handoff` section, asserted by test. |

Re-ran `python scripts/verify.py` after the fixes: 42 tests, generated drift check and skill validation pass.
