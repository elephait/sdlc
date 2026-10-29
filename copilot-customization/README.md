# Copilot customization

VS Code Copilot adapter for the shared SDLC workflow. It contains only what is specific to Copilot; policy, skills, hook scripts and the CLI are shared (see the [repository README](../README.md)).

| Path | What it is |
|---|---|
| `host-notes.md` | The only Copilot-specific instruction text; appended to the generated universal rule. |
| `plugin/plugin.json`, `plugin/com.github.copilot/hooks/hooks.json` | Agent Plugins 1.0 manifest and tracking-only hook wiring. |
| `plugin/skills/`, `plugin/scripts/`, `plugin/com.github.copilot/rules/` | **Generated** by `python scripts/sync-customizations.py`. Do not edit. |

## Use

- Install the plugin in VS Code Copilot from `plugin/`, then start a new session.
- Workspace tracking hooks live at `.github/hooks/copilot-sdlc.json` in the tracked workspace; `copilot-sdlc project-onboard --tracking-hooks copilot-workspace` writes them.
- Operation, CLI and architecture: [core/README.md](../core/README.md).

## Limits

- No `PreToolUse` hook is installed (it can trigger repeated permission prompts), so commit policy is enforced through `commit-ready`.
- Standard Copilot surfaces do not expose authoritative token usage.
- Enterprise plugin distribution needs administrator approval.

Use plugin tracking OR workspace tracking, never both. Default onboarding installs no hooks. This repository keeps an empty workspace hook registration to avoid duplicate plugin events. For an existing workspace, remove only the old SDLC hook entries when switching to plugin tracking.
