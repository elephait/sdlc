## Copilot host notes

- VS Code chat is the primary interface. Use the current project and session context to choose the files to stage and to write the `commit-ready` summary and findings; the CLI is the auditable backend, not a reason to discard that context.
- Respect VS Code permission settings. Use the host approval flow when access is required; repository policy does not grant access.
- No `PreToolUse` command hook is installed, because a command before every tool can itself trigger permission prompts. Commit title and credential rules are therefore enforced by the `commit-ready` workflow: commit through it. Nothing blocks `git push` mechanically, so the policy rule against pushing is the only guard. Tracking hooks (`SessionStart`, `PostToolUse`, `PostToolUseFailure`, `Stop`) only record evidence.
- Plugin hooks and rules take effect in a new Copilot session.
