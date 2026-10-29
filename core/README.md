# SDLC core

Host-neutral Python 3.11+ tooling behind the Copilot, Claude, Codex and DeepSeek adapters: stories, sessions, evidence, gates, reviews, local commits, scorecards and retention. No third-party runtime dependency. Rules live in [the policy](../policy/universal.md); this file covers operation only.

## Run

Install once so any workspace can call the CLI (`copilot-sdlc`; the name is historical, the tool is host-neutral):

```powershell
pip install --no-deps -e C:\dev\common\sdlc\core
```

From this folder, `python -m copilot_customization.cli` works without installing. From any folder, use the absolute path to `scripts/sdlc.py`. Run `python scripts/verify.py` from the repository root for all local checks. Only editable installation is supported; the runtime currently reads schema and hook resources from the source checkout.

| Command | Purpose |
|---|---|
| `project-onboard` | Create or refresh `.sdlc/` metadata; use `--tracking-hooks copilot-workspace` only without plugin tracking. Default `none` installs no hooks. |
| `tracking-report` | Capture health first; exit code `2` when evidence is missing or older than 15 minutes (`--allow-stale` to override). |
| `gate` | Record a handoff gate (`analysis`, `implementation`, `review`, `customization`, `docs`) with its artifact, evidence, named approver and optional recording host (`--recorded-by`, default `$SDLC_AI_NAME`). `--run-verify` runs `scripts/verify.py` first and stores the exit code, test count, result and the staged-tree hash it ran against (refuses unstaged changes, or a tree that changes during or after the run); `gate-status` shows the latest state. `implementation` and `customization` bind to the staged tree; `analysis` is story-level. |
| `commit-ready` | Validate commit policy and the required gates (all must postdate HEAD; `implementation` and `customization` must also match the staged tree), make one local commit, write a hash-named handoff report. Takes `--co-author` (default `$SDLC_CO_AUTHOR`, otherwise no trailer) and `--ai-name` (default `$SDLC_AI_NAME`, then the co-author name, then `--prepared-by`) for the title. |
| `event`, `decision`, `resolve-event`, `session-*`, `scorecard`, `compact`, `bottlenecks` | Record and analyze evidence; run `--help` for flags. `session-start --host` attributes a session to a harness. |

Normal delivery commits use `ai commit by <ai>: ` (for example `ai commit by claude: add gates`); fresh-review fixes use `ai code review by <ai>: `. `commit-ready` adds the AI name to a bare or legacy `ai commit: ` message, and the scope hook rejects a direct `git commit` whose title lacks it. An `ai commit by <ai>: ` requires the `analysis` and `implementation` gates, an `ai code review by <ai>: ` requires `review` and `docs`, and either requires `customization` when staged paths touch policy, skills, core, scripts, a root launcher or an adapter. A missing or stale gate stops the commit before Git runs. Credential-like files are excluded from commits unless approved (recorded with approver, time, reason, paths and staged blob hashes). Push is never done by this tool.

## Layout

| Path | Responsibility |
|---|---|
| `src/copilot_customization/` | CLI, onboarding, coordination, reports, commit workflow |
| `scripts/` | Hook scripts: `tracking_hook.py` (evidence), `scope_hook.py` (commit, credential, push and path guard). Copied into each host plugin by `scripts/sync-customizations.py`. |
| `sql/schema.sql` | SQLite coordination schema |
| `tests/` | Unit tests, including a check that host plugins match these sources |

Markdown and JSON under the story ledger are the reviewable source of intent; SQLite is the local coordination index. A workspace's `.sdlc/project.yaml` holds its identity and validation commands, and `.sdlc/active-story.json` binds it to a story and ledger.

## Hooks

Tracking hooks capture `SessionStart`, tool outcomes (`PostToolUse`, plus `PostToolUseFailure` on both plugin hosts) and `Stop`. `scope_hook.py` runs before tools only where the host wires it (Claude, with `--no-allow`); it is always invoked by `commit-ready`. It judges git operations on the shell command only.

## Limitations

- Tracking does not expose authoritative token usage. Sessions carry a `--host` label for attribution; billing units are not recorded because no host supplies them.
- SQLite coordinates processes on one shared filesystem, not across machines.
- Paths are resolved per selected workspace. Set `SDLC_WORKSPACE_ROOT` only when a host needs an explicit broader boundary; hook locking works on Windows and POSIX.
- Session analysis quality depends on recorded events and review summaries.

Codex uses explicit CLI evidence rather than these hooks. Hook path/command checks are best-effort: shell aliases, wrappers and arbitrary interpreters require native host sandbox enforcement. A scope-hook crash is not an authorization grant.
