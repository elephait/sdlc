# AI Native Software Development

Shared instructions, reusable skills and a lightweight Python control plane for AI-assisted delivery in VS Code Copilot, Claude Code, Codex app and DeepSeek app's. Native agents do the work; recorded evidence supports acceptance. This is a local Windows pilot, not production certification.

| Layer | Source of truth |
|---|---|
| Operating rules | [policy/universal.md](policy/universal.md); [research guidance](policy/research.md) only when needed |
| Direction and pilot plan | [policy/decisions.md](policy/decisions.md) |
| Tracking, review and local commit backend | [core/README.md](core/README.md) |
| On-demand workflows | [skills/README.md](skills/README.md) |
| VS Code loading and hooks | [copilot-customization/README.md](copilot-customization/README.md) |
| Claude loading and hooks | [claude-customization/README.md](claude-customization/README.md) |
| Codex app setup and runnable commands | [codex-customization/codex.md](codex-customization/codex.md) |
| DeepSeek session setup and runnable commands | [deepseek-customization/deepseek.md](deepseek-customization/deepseek.md) |

## One source, four hosts

For this SDLC project, run one command from any PowerShell directory:

```powershell
sdlc\aicode.cmd
```

The menu onboards the latest project with `1`, onboards all Git projects under the current folder with `2`, maps `3` through `10` to older recent projects, verifies the current Git project with `V`, and exits with `E`. `R` shows the latest five reports and `R10` shows ten, so report counts never conflict with numeric project choices. Actions can be chained without punctuation: `1R10V` onboards the latest project, lists ten reports and verifies; `1VR` is also valid. A project number, when present, must come first. After each successful chain, the same menu is shown again until `E` is selected.

This refreshes all four adapters, installs the latest managed Copilot, Claude, Codex and DeepSeek instructions and skills in the selected project, and refreshes shared tracking while preserving the active story. It does not run the project test suite during routine onboarding. Use menu option `V` or `aicode.cmd --verify` to run the current Git project's commands from `.sdlc/project.yaml`; validation evidence belongs at implementation, ready-to-commit, and review gates. Python 3.11+ must be on PATH. For a first-time story (or an active interactive session), supply `--story <ID> --intent "<intent>"` ; an existing different active story is never replaced.

Adapter refresh and validation always run against the SDLC checkout containing the launcher, regardless of your current directory. It uses the latest local sources and does not pull Git changes, install global settings, or launch four agents.


Run `aicode.cmd --reports` for the five newest analysis, scorecard, review and handoff artifacts, or pass another count such as `aicode.cmd --reports 12`. To look at them through the underlying script:

```powershell
python scripts/reports.py --limit 5
```

Reports are read newest first from `core/reports/generated/`, the active story's `reviews/` folder and `md/reviews/`.

For an already-running story, `aicode.cmd --workspace <project> --skip-refresh` refreshes tracking without regenerating shared adapters or running validation. It does not stop sessions, clear events or replace the active story; database initialization and project-recency updates can still occur. A normal full refresh can change shared files that a running host uses, so do that when those agents are idle. `aicode.cmd --all --dry-run` previews the bulk scan under the current folder without sync, verification or tracking writes.

Use this same command for updates, then start a new chat in your chosen host. Workspace instructions and skills are refreshed automatically without replacing unrelated `AGENTS.md` content or unrelated skills. Host-level plugin activation may still be required where the host does not support project-local activation.

Edit `policy/`, `skills/` and `core/`; host-specific instruction text lives only where a host needs something the others must not receive (currently Copilot and Claude). Generate and verify from this repository with Python 3.11+:

```powershell
python scripts/sync-customizations.py
python scripts/verify.py
python scripts/sdlc.py --help
```

The verifier checks generated-file drift, skill structure and regression tests with the correct Python import path. It does not stage, commit or publish. No third-party runtime dependency or global installation is needed.

Generated files are the Copilot/Claude plugin `skills/` and `scripts/`, Copilot rules, root `AGENTS.md` and `.agents/skills/`. Do not edit generated files. Host manifests and hook wiring remain host-specific. No extra agent personas or model overrides are required.

## Handoff gates

A story moves through five handoffs: analysis and acceptance, implementation, review, customization (when policy, skills, core, scripts, a root launcher or an adapter changes) and the final README reconcile. Each records its evidence and a named approver with `python scripts/sdlc.py gate`. `commit-ready` refuses while a gate it needs is missing or stale: an `ai commit by <ai>: ` needs `analysis` and `implementation`, an `ai code review by <ai>: ` needs `review` and `docs`, and either needs `customization` when the staged paths touch the customization layers. `implementation` and `customization` bind to the staged tree, so stage the reviewed files before recording them; `review` and `docs` must postdate the last commit; `analysis` is story-level and is not re-recorded per commit. `gate --run-verify` runs `scripts/verify.py` and stores its exit code, test count and result, refusing when the working tree has unstaged changes; `--recorded-by` records the host that wrote the gate as provenance, separate from the approver. When a story has no sessions or events, the handoff report states that duration, retries and cost cannot be measured. The full sequence is in [skills/tracked-story/SKILL.md](skills/tracked-story/SKILL.md).

A story can start on one host and finish on another. The payload is shared and the gate records are in the shared database, so the next host continues from the commit report rather than from a transcript. The first customization commit in this repository was made in Copilot; later ones in Claude and Codex; nothing in the workflow is tied to the host that opened the story.

## Activate a host

- **Copilot:** install `copilot-customization/plugin` in VS Code, then start a new session. Plugin hooks record active tracked stories. Do not also enable workspace copies of the same hooks.
- **Claude:** launch `claude --plugin-dir C:\dev\common\sdlc\claude-customization\plugin`. Root `CLAUDE.md` imports policy. For other repositories see the adapter README.
- **Codex:** open `C:\dev\common\sdlc` as the project and start a new chat. Root `AGENTS.md` and `.agents/skills/` provide discovery. See [codex.md](codex-customization/codex.md) for runnable tracking and commit commands. This adapter uses explicit tracking commands, not automatic lifecycle hooks.
- **DeepSeek:** open `C:\dev\common\sdlc` as the session workspace and start a new chat. It reads the same `AGENTS.md` and `.agents/skills/` as Codex. See [deepseek.md](deepseek-customization/deepseek.md) for runnable commands, gates and activation checks. No hooks are installed.

## Optional story tracking

```powershell
python scripts/sdlc.py project-onboard --workspace C:\dev\common\sdlc --repository elephait/sdlc --story SDLC-002 --intent "Unify agent customization" --ledger-root C:\dev\common\sdlc\.sdlc\ledger --tracking-hooks none
```

Choose a fresh story ID and preserve existing bindings. `none` is the default: it installs no hooks, and does not remove existing hooks. Use `copilot-workspace` only when not using the Copilot plugin's tracking. Claude uses its own plugin wiring. For another workspace supply its identity and paths.

An existing story belongs to one project/repository. To switch stories, finish or hand off the current story and explicitly deactivate its local `.sdlc/active-story.json`; onboarding never silently rebinds it. Tracking reports exit 2 for stale or absent evidence.

Record each handoff as it closes, with the evidence the approver saw:

```powershell
python scripts/sdlc.py gate --story SDLC-002 --gate analysis --artifact .sdlc/analysis.md --evidence "Criteria accepted in chat" --approved-by "<user>" --recorded-by <ai>
python scripts/sdlc.py gate-status --story SDLC-002
```

`--status waived --approved-by <user> --evidence <reason>` records an explicit waiver. A gate report is written under the story ledger, and the commit handoff report names the gates that authorised it.

Optional editable install: `python -m pip install --no-deps -e core`. Both `sdlc` and the historical `copilot-sdlc` entry points call the same backend. Non-editable wheels are not supported yet because runtime resources live in the checkout.

## Review and validation limits

[Review of commits 3627ca2 and 5247c8c](md/reviews/2026-10-28-three-host-review.md) records the original defects and fixes. [Review of the four-host and gate work](md/reviews/2026-10-28-four-host-gates-review.md) covers this change and its residual risks. [Codex usage analysis](md/reviews/2026-10-28-codex-usage-analysis.md) explains why the credit question had no evidence and what was added to answer it. Local tests exercise Python and generated artifacts. A new session in each host is still needed to verify plugin/skill activation; successful local tests do not establish live host behavior. Scope hooks are best-effort guards, not a shell sandbox. The host's native permissions remain authoritative.

[Codex completion review (2026-10-29)](md/reviews/2026-10-29-codex-completion-review.md) verifies that prior Codex work survived the newer commits and documents tracking continuity, launcher fixes and validation.
