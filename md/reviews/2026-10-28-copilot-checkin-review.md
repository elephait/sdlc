# Review: Copilot check-in 3627ca2 and the Claude port

Reviewed 2026-10-28. Static review plus the 15 unit tests on Linux; nothing was run on Windows, in VS Code or in Claude.

## Intent

An AI-native SDLC with minimal human supervision: native coding agents do the work, a deterministic layer tracks state and enforces gates, evidence (not agent agreement) decides success, and every story leaves a reviewable ledger and a commit-matched report. `policy/decisions.md` holds the decisions, `copilot-customization` was the first implementation, `skills/` holds reusable skills.

## Findings

| # | Sev | Finding | Status |
|---|---|---|---|
| 1 | High | The design-review skill existed twice (`skills/` and the Copilot plugin) and had already drifted (`prompts.md`, `agents/`). | Fixed: `skills/` is the only source; `scripts/sync-customizations.py` generates the plugin copies; a unit test fails on drift. |
| 2 | High | `universal.instructions.md` (14 KB) restated rules up to five times (tests deferred until readiness, readiness question, terminal states, one writer, no metered billing, formatter once, POC vs enterprise), claimed "each rule once", and conflicted with `md/CLAUDE.md` (compile/import before done) and `sdlc/README.md` decision 6 (gates before review). | Fixed: `policy/universal.md`, 6.6 KB, one home per rule, ordered by priority. |
| 3 | High | Rule 2 mixed host mechanics (`view`, `rg`, `apply_patch`, "automatic response" wording) into the universal policy. | Fixed: moved to `host-notes.md` per host. |
| 4 | Med | `scope_hook` scanned the whole payload for `git push`, so editing any file that mentions it (this README does) was flagged; `git log --grep commit` was treated as a commit; `git commit -am` was denied. | Fixed in `core/scripts/scope_hook.py`, with tests. |
| 5 | Med | `tracking_hook` imported `msvcrt` at module level (crashes off Windows); a Stop event without `reason` was recorded as a failure; the SessionStart context used a key Claude and VS Code do not read; tool failures were not recorded. | Fixed, with tests. |
| 6 | Low | `commit-ready` hardcoded `Co-authored-by: Copilot`. | Fixed: `--co-author` / `$SDLC_CO_AUTHOR`. |
| 7 | Low | Committed `project.yaml` held stale machine values (`elephait\sdlc\copilot-customization`, repository `hnb-ent/...`). | Fixed to the current repo. |
| 8 | Low | `md/CLAUDE.md` duplicated the coding and research rules and sat in a folder Claude would not load from the root. | Merged into the policy; file removed. |
| 9 | Med | `service.py` is about 2,200 lines, against the repo's own cohesion rule. | Open: split into onboarding, commit, reporting and events modules. |
| 10 | Med | `commit-ready` forces `commit.gpgsign=false`, silently overriding a signing requirement. | Open: confirm or make it opt-in. |
| 11 | Med | Copilot has no pre-tool enforcement by design, so a raw `git commit` bypasses prefix and credential rules; the scope hook fails open if it crashes. | Open, documented. Claude wires it with `--no-allow`; `commit-ready` re-checks. |
| 12 | Low | Path policy is Windows-only (`ntpath`, `C:\dev`); the shell-mutation regex treats any `>` (including `2>&1`) as a write. | Open. |
| 13 | Low | Employer identifiers (`Huntington`, `hnb-*` package names) sit in a personal repo, against the policy on employer code. | Open: confirm intent. |
| 14 | Low | Package and CLI are named `copilot-*` though host-neutral. | Open: rename later; docs explain it. |

## Decisions to confirm

1. Cheap checks (compile, import, run on synthetic input) are allowed before `ready to commit`; unit tests, test runners and the formatter still wait. This follows `md/CLAUDE.md` and rule "no success claims without evidence"; the old text banned all validation.
2. The `/better` section was dropped from the skill's `prompts.md` (the Copilot copy had already dropped it, and the skill says it is self-contained).
3. The shared core, `.sdlc/` and `.github/hooks/` moved to the repository root so both hosts use one tracked workspace.
4. In Claude the scope hook returns no decision for allowed calls, so your Claude permission settings keep control; `git push` is denied outright (the user pushes), and git read operations are never gated.
5. Layout flattened: `sdlc/policy` -> `policy/`, `sdlc/core` -> `core/`, `sdlc/README.md` -> `policy/decisions.md`.

## Not verified

Claude plugin loading and hook schema (written from the documented format; no Claude CLI here), VS Code plugin reload, any Windows run, and `service.py` beyond the changed lines. After pulling this: reinstall the CLI (`pip install --no-deps -e core`), run `copilot-sdlc project-onboard --workspace C:\dev\common\sdlc`, and start new Copilot and Claude sessions.
