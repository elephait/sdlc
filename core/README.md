# SDLC core

Host-neutral Python 3.11+ tooling behind both the Copilot and Claude adapters: stories, sessions, evidence, reviews, local commits, scorecards and retention. No third-party runtime dependency. Rules live in [the policy](../policy/universal.md); this file covers operation only.

## Run

Install once so any workspace can call the CLI (`copilot-sdlc`; the name is historical, the tool is host-neutral):

```powershell
pip install --no-deps -e C:\dev\common\sdlc\core
```

From this folder, `python -m copilot_customization.cli` works without installing.

| Command | Purpose |
|---|---|
| `project-onboard` | Create or refresh `.sdlc/` tracking metadata and Copilot workspace tracking hooks for a workspace. |
| `tracking-report` | Capture health first; exit code `2` when evidence is missing or older than 15 minutes (`--allow-stale` to override). |
| `commit-ready` | Validate commit policy, make one local commit, write a hash-named handoff report. Takes `--co-author` (default `$SDLC_CO_AUTHOR`, then Copilot). |
| `event`, `decision`, `resolve-event`, `session-*`, `scorecard`, `compact`, `bottlenecks` | Record and analyze evidence; run `--help` for flags. |

Normal delivery commits use `ai commit: `; fresh-review fixes use `ai code review: `. Credential-like files are excluded from commits unless approved (recorded with approver, time, reason, paths and staged blob hashes). Push is never done by this tool.

## Layout

| Path | Responsibility |
|---|---|
| `src/copilot_customization/` | CLI, onboarding, coordination, reports, commit workflow |
| `scripts/` | Hook scripts: `tracking_hook.py` (evidence), `scope_hook.py` (commit, credential, push and path guard). Copied into each host plugin by `scripts/sync-customizations.py`. |
| `sql/schema.sql` | SQLite coordination schema |
| `tests/` | Unit tests, including a check that host plugins match these sources |

Markdown and JSON under the story ledger are the reviewable source of intent; SQLite is the local coordination index. A workspace's `.sdlc/project.yaml` holds its identity and validation commands, and `.sdlc/active-story.json` binds it to a story and ledger.

## Hooks

Tracking hooks capture `SessionStart`, tool outcomes (`PostToolUse`, plus `PostToolUseFailure` on Claude) and `Stop`. `scope_hook.py` runs before tools only where the host wires it (Claude, with `--no-allow`); it is always invoked by `commit-ready`. It judges git operations on the shell command only.

## Limitations

- Tracking does not expose authoritative token usage.
- SQLite coordinates processes on one shared filesystem, not across machines.
- Paths assume `C:\dev`; hook locking works on Windows and POSIX, path policy is Windows-only.
- Session analysis quality depends on recorded events and review summaries.
