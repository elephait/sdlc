# DeepSeek setup and commands

Open `C:\dev\common\sdlc` as the session workspace, then start a new chat. A session opened on the parent `C:\dev\common` does not load this repository's instructions until it works with files inside it.

`AGENTS.md` is generated from `policy/universal.md` and `policy/harness-notes.md`; it is the same file Codex reads. Skills are generated into `.agents/skills/`; edit only `skills/`. This adapter installs no hooks, no user-level settings, no model selection and no approval overrides.

## Runnable commands

One command refreshes every adapter, validates, and refreshes tracking without changing the active story. It works from any directory:

```powershell
C:\dev\common\sdlc\onboard.cmd
```

To refresh and track every untracked project under `C:\dev\common` as well, add `--all`; tracked projects are reported and left untouched:

```powershell
C:\dev\common\sdlc\onboard.cmd --all
```

Python 3.11+ is required. From the repository:

```powershell
Set-Location C:\dev\common\sdlc
python scripts/sync-customizations.py
python scripts/verify.py
python scripts/sdlc.py --help
python scripts/reports.py --limit 5
```

`reports.py` lists the newest scorecards, failure reports, commit analysis and review write-ups; `onboard.cmd --all --reports 5` does the same at the end of a full refresh.

The CLI works from any directory by absolute path. Optional install: `python -m pip install --no-deps -e C:\dev\common\sdlc\core`.

## Gate-backed delivery

Each handoff is a gate with an artifact and an approver; `commit-ready` refuses while a required gate is missing. For a new story:

```powershell
python scripts/sdlc.py project-onboard --workspace C:\dev\common\sdlc --repository elephait/sdlc --story SDLC-002 --intent "Unify agent customization" --ledger-root C:\dev\common\sdlc\.sdlc\ledger --tracking-hooks none
python scripts/sdlc.py session-start --story SDLC-002 --role implementation --session-id deepseek-sdlc-002 --host deepseek
python scripts/sdlc.py gate --story SDLC-002 --gate analysis --artifact .sdlc/analysis.md --evidence "Criteria accepted in chat" --approved-by "<user>"
python scripts/sdlc.py gate --story SDLC-002 --gate implementation --evidence "python scripts/verify.py passed" --approved-by "<user>"
python scripts/sdlc.py commit-ready --workspace C:\dev\common\sdlc --message "ai commit: unify agent customization" --prepared-by DeepSeek --summary "Describe the reviewed change" --validation-summary "Describe checks actually run" --co-author "DeepSeek <noreply@deepseek.com>"
```

Use `--gate review` with the review file before an `ai code review:` commit, `--gate customization` when the change touches policy, skills, core or an adapter, and `--gate docs` after the README reconcile. `gate --status waived --approved-by <user> --evidence <reason>` records an explicit waiver instead of a pass.

Tracking is optional for small tasks. `session-stop` needs the real outcome, and `DONE` needs acceptance evidence. `tracking-report` exits 2 when capture is stale or absent; this host records nothing automatically, so the report reflects only what you record.

## Skills in this host

Generated skills live in `.agents/skills/`: `tracked-story` and `distributed-service-design-review`. If the session does not list a skill, read its `SKILL.md` by path and follow it; the file is the same one the plugin hosts load.

## Use in another repository

Add one line to that project's `AGENTS.md`: read `C:/dev/common/sdlc/policy/universal.md`, `C:/dev/common/sdlc/policy/harness-notes.md`, and `policy/research.md` only when researching external claims. Keep the project's own instructions. Copy the skill folders you need into its `.agents/skills/`, and use the absolute CLI path with that project's workspace, repository and story identity.

## Verify activation

In a new chat rooted here, ask DeepSeek to name the five handoff gates and list `tracked-story`. Then run a real command, for example `python scripts/sdlc.py tracking-report --workspace C:\dev\common\sdlc`, and confirm it reflects recorded evidence rather than an assumption. Local checks verify generated content and Python behavior; they cannot prove discovery inside an already-running session.

Host behavior, sandbox and approvals remain authoritative. These instructions grant no filesystem or network access.
