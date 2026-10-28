## Copilot host notes

- VS Code chat is the primary interface. Use the current project and session context to choose the files to stage and to write the `commit-ready` summary and findings; the CLI is the auditable backend, not a reason to discard that context.
- Permission prompts: if a dialog appears for ordinary `C:\dev` work, abandon that call and continue with a non-prompting tool (`view`, `rg`, `glob`, `apply_patch`). Do not relay the dialog or ask whether to proceed.
- No `PreToolUse` command hook is installed, because a command before every tool can itself trigger permission prompts. Commit title and credential rules are therefore enforced by the `commit-ready` workflow: commit through it. Nothing blocks `git push` mechanically, so the policy rule against pushing is the only guard. Tracking hooks (`SessionStart`, `PostToolUse`, `Stop`) only record evidence.
- Plugin hooks and rules take effect in a new Copilot session.
