# Review: seven commits, 2026-10-29 to 2026-10-30

Reviewed commits `12b9642`, `9afba64`, `fbcaace`, `bb5404b`, `ecedea3`, `ef73225`, `816e652` against HEAD `816e652`. `origin/main` sits at `ecedea3`, so the last two are local. The working tree was clean at review start; the fixes below are uncommitted.

## Verdict

The direction is right and the tree-binding work is real. Three regressions mattered: the verification suite could not run in this environment, a gate could claim measured validation without running it, and the DeepSeek guide had drifted from the CLI it documents. All three are fixed; the remaining findings are recorded, not silently dropped.

## Findings and disposition

| Severity | Commit | Finding | Disposition |
|---|---|---|---|
| High | 12b9642 | A gate could pass on caller-supplied `--details-json`: the tree hash was compared but `verification.result` and `exitCode` were never checked, so a commit could claim "passed" with no suite run, even carrying `result: failed`. | Fixed twice: the CLI refuses `verification` in `--details-json` unless `--run-verify` produced it, and `record_gate` refuses a passed gate whose verification failed or exited non-zero. Test added. |
| High | all | `python scripts/verify.py` failed in this environment: 13 errors because new sync tests used `tempfile` and the shared helper defaulted to the user profile, whose directories the sandbox cannot traverse. | Fixed: `support.py` defaults beside the repository (`SDLC_TEST_ROOT` overrides) and exposes a `workspace()` context manager; `test_sync.py` uses it. 111 tests pass. |
| Medium | 9afba64 | `onboard.cmd` and `onboard-all.cmd` no longer triggered the customization gate, although policy names "the root launchers". | Fixed: both added to `_CUSTOMIZATION_FILES`; the launcher test covers them. |
| Medium | 12b9642 | The tracked-story skill committed at step 2 but recorded `customization` at step 4, so following it in order could not satisfy a customization commit. | Fixed: step 2 now says to record `customization` at the same point when the staged paths require it. |
| Medium | ef73225 | `run_verify` refused tracked working-tree changes but ignored untracked files that the suite can execute, so its evidence described a superset of the staged tree. | Changed rather than blocked: the result now carries `untracked` and `untrackedCount`. A blanket refusal would break every project that keeps untracked `.sdlc` or ledger files, so the evidence names them and the reviewer sees the gap. |
| Medium | ef73225 | `test_onboard_launcher` asserted that `--story` was absent, which depended on the gitignored `.sdlc/active-story.json`; a fresh clone adds `--story` and both tests fail. | Fixed: `onboard.py` has `has_active_story()`, and the tests patch it instead of depending on local state. |
| Low | ef73225 | `aicode.py` let `EOFError` escape when stdin was closed, unlike `onboard.py`. | Fixed: clean error and exit 1. |
| Low | 9afba64 | `onboard-all.py` reported success for an empty scan with no explanation. | Fixed: prints "no Git projects found; nothing to onboard". |
| Low | 816e652 | Installed `AGENTS.md` lost the absolute path, but the embedded harness notes still carried `[codex.md](codex-customization/codex.md)` links that dangle outside the checkout. | Fixed: harness notes name the files as paths inside the checkout, no links. |
| Low | 816e652 | The DeepSeek guide still embedded `C:\dev\common` paths and described validation that the launcher no longer performs. | Fixed: guide rewritten around `$sdlc` via `SDLC_HOME` or `.sdlc/sdlc-source.txt`. The Codex guide's absolute paths were removed in the same pass. |
| Low | ef73225 | README's launcher example was relative (`sdlc\aicode.cmd`) while claiming any directory. | Fixed twice: the first change used an absolute path, which reintroduced the machine-path problem; it is now `<sdlc-checkout>\aicode.cmd` with the placeholder explained. |
| Low | ecedea3 | A relocated copy whose old ledger path still exists is never rehomed; evidence lands in the source checkout. | Recorded. Rehoming on existence is deliberate; automatic relocation needs an identity the project file no longer carries. |
| Low | 12b9642 | Gate selection trusts the title: `ai code review by …` needs only review and docs, even when it changes ordinary code. | Recorded. The title states intent; a reviewer who mislabels a delivery commit wears that. |
| Low | 816e652 | Legacy skill adoption scans up to 100 commits, one `git show` per file, per skill and host, twice per install. | Recorded. Bounded and only on first adoption, but it is the slowest path in onboarding. |
| Low | 9afba64 | `SDLC_WORKSPACE_ROOT` is described as a boundary, but the guard only confines when it is set. | Recorded. The host sandbox is the real boundary and policy says neither is a permission grant, but the wording invites the stronger reading. |

## What is solid

- Tree binding is genuine: `git write-tree` at the repository root, HEAD and tree compared for `implementation` and `customization`, `analysis` kept story-level, and a HEAD/tree re-check immediately before `git commit`.
- `run_verify` re-checks the tree after the run, refuses an untracked verifier, and rejects HEAD movement or working-tree mutation during verification.
- `sync --check` detects missing, differing and extra generated files; workspace install refuses unmanaged Copilot instructions, Claude rules and skills while preserving user files inside managed skill folders.
- `.sdlc/project.yaml` carries no machine path, and `onboarding_identity` preserves configured repository and story across renames.
- Launchers propagate exit codes; `--dry-run` is side-effect free; the project picker defaults without blocking on a non-TTY.

## DeepSeek side

`deepseek.md` was the weakest document in the set. It claimed the refresh validates, described `--all` as scanning `C:\dev\common` and leaving tracked projects untouched, and carried eleven machine-specific paths. It also omitted that a review commit needs `docs` as well as `review`, that every gate except `analysis` is HEAD-bound, and that `--artifact` is optional.

The rewritten guide uses a `$sdlc` locator, separates refresh from validation (`--verify`), states that `--all` scans the current folder and its immediate children, and that an already-tracked project is resumed while its adapters are reinstalled. It adds the full two-commit gate sequence, the customization path list, the `SDLC_WORKSPACE_ROOT` behaviour, and the preconditions `commit-ready` enforces (active story, tracked and clean README, ledger `story.md`).

No other DeepSeek-specific change was needed: `AGENTS.md` is generated from shared policy, `.agents/skills/tracked-story` matches its source after normalisation, and nothing in the adapter installs hooks or host settings.

## Verification performed

- `python scripts/verify.py`: 111 tests pass, generated payloads in sync, skill validation clean.
- New tests: forged failed verification refused, launcher paths require customization, untracked verification inputs recorded.
- Not run: no live DeepSeek, Codex, Claude or Copilot session; no commit was made, so this review's fixes are uncommitted.

## Residual risks

1. Gates are enforced at `commit-ready`; a direct `git commit` still bypasses them.
2. Approval is recorded, not authenticated; `--approved-by` is a claim.
3. `--details-json` can no longer forge verification through the CLI, but a caller using the Python API directly can still pass a fabricated `verification` object. `record_gate` validates a supplied result against the status; it cannot authenticate who produced it.
4. Credential detection remains name-based.
5. Test-workspace cleanup can leave empty directories under `.sdlc-test-work` when Git releases handles late; they are ignored and harmless.
