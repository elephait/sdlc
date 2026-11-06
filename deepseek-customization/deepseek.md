# DeepSeek setup and commands

Open the SDLC checkout as the session workspace, then start a new chat. A session opened on its parent does not load this repository's instructions until it works with files inside it. The checkout can live anywhere: the snippet below finds it from `SDLC_HOME` when you set it, otherwise from the locator that onboarding writes.

```powershell
# Inside a project onboarded by this toolkit; otherwise set SDLC_HOME first.
$sdlc = if ($env:SDLC_HOME) { $env:SDLC_HOME } else { (Get-Content .sdlc\sdlc-source.txt) }
```

`AGENTS.md` is generated from `policy/universal.md` and `policy/harness-notes.md`; it is the same file Codex reads. Skills are generated into `.agents/skills/`; edit only `skills/`. This adapter installs no hooks, no user-level settings, no model selection and no approval overrides.

## Runnable commands

From any directory. `--workspace` regenerates the adapters and onboards that project; it does **not** run validation, and it prints the project it chose:

```powershell
& "$sdlc\aicode.cmd" --workspace "$sdlc"
```

Validate when you need to, either through the launcher or directly:

```powershell
& "$sdlc\aicode.cmd" --verify
python "$sdlc\scripts\verify.py"
```

Two cautions about the picker: without `--workspace` it defaults to the most recently used project, and validation only passes for a project whose `.sdlc/project.yaml` declares `validation.<name>.command` entries.

`--all` scans the **current folder** and its immediate children, not a fixed root, so run it from the folder that contains the projects:

```powershell
Set-Location <folder containing the projects>
& "$sdlc\aicode.cmd" --all
```

A project already tracking a story is resumed, not skipped: its instructions and skill folders are reinstalled and its ledger may be repaired. `--dry-run` previews without writing. Python 3.11+ is required.

From the checkout itself:

```powershell
Set-Location $sdlc
python scripts/sync-customizations.py
python scripts/verify.py
python scripts/sdlc.py --help
python scripts/reports.py --limit 5
```

The CLI works from any directory by absolute path. Optional install: `python -m pip install --no-deps -e "$sdlc\core"`.

## Gate-backed delivery

`commit-ready` requires an active story, a tracked and clean `README.md`, a ledger `story.md`, and every gate the commit needs. Gates other than `analysis` bind to the current HEAD and, for `implementation` and `customization`, to the exact staged tree, so stage first and re-record after any further staging or commit. `--artifact` is optional; when given it must exist and is hashed into the gate.

For a workspace without tracking:

```powershell
python "$sdlc\scripts\sdlc.py" project-onboard --workspace $PWD --repository elephait/sdlc --story SDLC-002 --intent "Unify agent customization" --tracking-hooks none
```

That fails if the workspace already has a different active story: onboarding never rebinds. Continue the existing story instead:

```powershell
$story = (Get-Content .sdlc/active-story.json -Raw | ConvertFrom-Json).storyId
$session = python "$sdlc\scripts\sdlc.py" session-start --story $story --role implementation --host deepseek

# 1. Analysis and acceptance
python "$sdlc\scripts\sdlc.py" gate --workspace $PWD --story $story --gate analysis --artifact .sdlc/analysis.md --evidence "Criteria accepted in chat" --approved-by "<user>" --recorded-by deepseek

# 2. Stage, then implementation evidence from a real suite run
git add <reviewed files>
python "$sdlc\scripts\sdlc.py" gate --workspace $PWD --story $story --gate implementation --run-verify --approved-by "<user>" --recorded-by deepseek
# Add this before the commit when staged paths touch policy, skills, core, scripts, a launcher or an adapter:
#   --gate customization --evidence "sync and verify passed"
python "$sdlc\scripts\sdlc.py" commit-ready --workspace $PWD --message "unify agent customization" --ai-name deepseek --prepared-by DeepSeek --summary "Describe the reviewed change" --validation-summary "Describe checks actually run" --co-author "DeepSeek <noreply@deepseek.com>"

# 3. Review, then the closing commit (its title needs review + docs)
python "$sdlc\scripts\sdlc.py" gate --workspace $PWD --story $story --gate review --artifact <review file> --approved-by "<user>" --recorded-by deepseek
python "$sdlc\scripts\sdlc.py" gate --workspace $PWD --story $story --gate docs --artifact README.md --approved-by "<user>" --recorded-by deepseek
python "$sdlc\scripts\sdlc.py" commit-ready --workspace $PWD --message "ai code review by deepseek: <verdict>" --ai-name deepseek --prepared-by DeepSeek --summary "Describe the review outcome"

python "$sdlc\scripts\sdlc.py" session-stop --session $session --outcome DONE
```

`--run-verify` runs `scripts/verify.py` and stores its exit code, test count, tree hash and any untracked files it could see. It refuses when the working tree has unstaged changes, and it will not record a pass when the result is a failure. Verification evidence cannot be supplied through `--details-json`; only `--run-verify` produces it. `--recorded-by` records provenance, separate from the approver.

`--gate customization` is required for `policy/`, `skills/`, `core/`, `scripts/`, `AGENTS.md`, `CLAUDE.md`, `aicode.cmd`, `onboard.cmd`, `onboard-all.cmd`, `reports.cmd`, any `*-customization/` folder and `.agents/skills/`. `--gate docs` and `--gate review` are required together for a commit titled `ai code review by …`. An explicit waiver records the approver and the reason: `gate --status waived --approved-by <user> --evidence <reason>`.

Tracking is optional for small tasks, but this host records nothing automatically: with no session and no events, `commit-ready` adds a "no telemetry" finding because duration, retries and cost cannot be measured. `session-stop` needs the real outcome, and `DONE` needs acceptance evidence. `tracking-report` exits 2 when capture is stale or absent.

## Boundaries

The host sandbox and approvals remain authoritative. `SDLC_WORKSPACE_ROOT` widens the path guard for managed projects; when it is unset the toolkit performs no additional confinement. These instructions grant no filesystem or network access.

## Skills in this host

Generated skills live in `.agents/skills/`: `tracked-story` and `distributed-service-design-review`. If the session does not list a skill, read its `SKILL.md` by path and follow it; the file is the same one the plugin hosts load.

## Use in another repository

Run `aicode.cmd` and select the project, or pass `--workspace`. Onboarding refreshes a managed block in that project's `AGENTS.md`, the Claude and Copilot managed files, and the shared skill folders under `.github/skills`, `.claude/skills` and `.agents/skills`, while preserving unrelated instructions and skills. The checkout location is written to `.sdlc/sdlc-source.txt` and excluded from Git there, so no machine path is committed.

## Verify activation

In a new chat rooted here, ask DeepSeek to name the five handoff gates and list `tracked-story`. Then run a real command, for example `python scripts\sdlc.py tracking-report --workspace $sdlc`, and confirm it reflects recorded evidence rather than an assumption. Local checks verify generated content and Python behavior; they cannot prove discovery inside an already-running session.
