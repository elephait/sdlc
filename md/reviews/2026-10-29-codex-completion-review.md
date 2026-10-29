# Codex completion review after the shared-host updates

Reviewed 2026-10-29 on local HEAD `f5a6216`. The working tree was clean at the start. The newer local commits were `7e94d59` (2026-10-28 20:23 EDT, four-host customization and gates) and `f5a6216` (2026-10-29 02:35 EDT, named-AI titles and project picker). These are the latest locally available commits; this review did not fetch remote history or assume an additional afternoon commit exists.

## Earlier Codex work is retained

`7e94d59` includes generated root `AGENTS.md`, `.agents/skills/` with Codex metadata, `codex-customization/`, the CLI and verification wrappers, the Windows onboarding launcher, signing preservation, optional workspace hooks and the earlier scope/tracking regression tests. The former Codex host notes were consolidated into `policy/harness-notes.md`, now shared with DeepSeek. That consolidation is intentional and retained. `f5a6216` updates the shared title contract and project selection; both remain intact.

## Findings fixed in this working tree

| Priority | Finding | Resolution |
|---|---|---|
| P2 | `scripts/onboard-all.py --dry-run` runs adapter generation and validation before inspecting the dry-run flag. The existing test supplied `--skip-refresh`, masking the write side effect. | Dry-run bypasses refresh, validation and optional report execution; regression test invokes dry-run without skip-refresh and checks that only a read-only Git identity lookup occurs. |
| P2 | Codex guide claims the bare launcher selects SDLC, but Claude's restored picker can choose another recent project, including automatically in noninteractive execution. | SDLC examples specify `--workspace C:\dev\common\sdlc`. The interactive picker and recent-project default remain unchanged. |
| P2 | Codex validation example uses `--type validation --progress`, which `record_event` rejects because progress is only valid for `Iteration`. | Removed the invalid flag and exercised the documented validation-event CLI in an isolated database. |
| P2 | Codex commit instructions omit the new required gates; fixed sample session IDs can refer to an already closed session. | Added gate-status, required-gate explanation and evidence/actual-approver example. Session-start now generates a fresh ID and reads the existing active story. No approvals or gates were fabricated. |
| P3 | The single-project launcher has no tracking-only mode, so an agent must refresh potentially in-use adapter files to refresh registration. | Added `--skip-refresh` to single-project onboarding, matching bulk mode. Its output explicitly says adapters were neither refreshed nor validated. |

## Does onboarding interrupt ongoing tracking?

For an existing, unmoved workspace, the tracking refresh preserves the active story, sessions, events, gates and installed workspace hooks. It does not call session-stop, clear history, rebind to another story, or terminate agents. `--tracking-hooks none` means no hook installation, not disabling existing hooks. Missing schema initialization and project-recency updates still occur, so this is not a read-only operation. SQLite may briefly serialize writes; this is not a zero-latency guarantee.

Use the single-project launcher with an explicit workspace and `--skip-refresh` while work is in progress. A full refresh additionally rewrites changed generated files; it is not an atomic hot upgrade across running hosts. Perform full refreshes when agents using those files are idle, and use a new chat when ready to load updated instructions. Bulk onboarding skips projects that already have active bindings.

## Validation

`python scripts/verify.py`: 50 tests passed, both skills passed validation, generated payloads were in sync. Added tests cover the tracking-only launch path, dry-run without a hidden skip-refresh prerequisite, the documented Codex event, and a real open session across registration refresh. The continuity test compares logical database records and binding/story/gate/hook bytes, then appends another hook event and database event without closing the session. This establishes persistence and continuation, not an exhaustive concurrent-load or host hot-reload test.

Closed SQLite connections in the touched test fixtures after Python 3.14 reported resource warnings on the first run. Live Codex skill-selector activation in a newly opened app chat was not exercised; the documented activation check remains necessary. The current parent-directory chat cannot establish child-repository discovery.

## Scope and remaining limits

Only Codex documentation, shared onboarding scripts, focused tests, the root README and this review changed. No Claude or DeepSeek-specific customization files changed, and no generated payload refresh was needed. Existing shared gate semantics and named-AI commit titles were preserved. Gate records remain user-supplied evidence; passing a recorded gate does not independently prove current code correctness or grant commit authorization.

Before commit preparation, no production tracking refresh, session stop, commit, push or host restart was performed during this follow-up. Tests use isolated databases and ledgers. The user subsequently authorized a local commit with "ready to commit" on 2026-10-29. Fresh review, customization and documentation gates record this change; the shared commit workflow produces the commit-matched handoff report. Publication is not authorized.
