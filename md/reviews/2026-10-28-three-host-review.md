# Review: Copilot 3627ca2 and Claude 5247c8c, with Codex integration

Reviewed 2026-10-28 against the two requested commits and the resulting working tree. Changes remain uncommitted. This review covers shared instructions, host loading, generated payloads, hooks, onboarding, CLI invocation and the commit path. It is not an exhaustive audit of the 2,200-line reporting service.

## Intended architecture

The Markdown describes native coding harnesses backed by a small deterministic control plane: shared policy, on-demand skills, story/session evidence and a local commit handoff. It aims to reduce supervision and context overhead while preserving acceptance evidence. The Claude commit establishes the right shared-source split; adding another hand-maintained policy or a supervising LLM would work against that intent.

## Findings and disposition

| Priority | Defect in reviewed commits | Fix / current status |
|---|---|---|
| P1 | `core/src/copilot_customization/service.py`, `commit_ready`: unconditionally sets `commit.gpgsign=false`, silently bypassing a repository signing requirement. Introduced in the Copilot commit and retained in Claude. | Removed the override. An isolated Git integration test requires signing with an unavailable signer and verifies the operation fails without creating HEAD. |
| P2 | `README.md` advertises Codex, but no root `AGENTS.md` or `.agents/skills/` provides native discovery; `skills/` alone is not a Codex repository discovery directory. | Added `codex-customization/`; generator produces root instructions and discoverable skills including UI metadata. New-chat activation still needs host verification. |
| P2 | `service.py`, `onboard_project`: installs Copilot workspace hooks for every host; the repository workspace hook and Copilot plugin register the same events, yielding duplicate evidence. | Default installs no hooks; standalone workspace tracking is explicit opt-in. Repository registration is empty; the plugin is the default owner. Existing external workspace registrations are not silently removed. |
| P2 | Copilot hook wiring omits `PostToolUseFailure`, so failed calls are absent from tool-outcome evidence even though the Claude commit adds failure normalization. | Added failure hooks to the plugin and optional workspace wiring. Synthetic hook execution writes a failed event to an isolated ledger. |
| P2 | `core/scripts/scope_hook.py` scans file content for external paths, denying an ordinary documentation edit containing a path such as `D:\outside`; relative write paths can escape `C:\dev` unchecked. | Inspect destination fields rather than file content; normalize relative destinations against cwd. Regression tests cover both. Shell interpretation remains best-effort, not a security boundary. |
| P2 | Root README and project metadata run unittest without putting `core/src` on the import path; imports fail in a clean, uninstalled checkout. | Added `scripts/verify.py` with explicit import path and `scripts/sdlc.py` for CLI use from any cwd. Updated documented commands. |
| P2 | Shared policy delays tests until commit approval, conflicts with evidence-first delivery, and instructs agents to abandon permission prompts for another tool. | Validation is part of implementation; commit authorization is separate. Host permissions remain authoritative. Removed duplicate prompt-avoidance instructions. |
| P3 | `.sdlc/project.yaml` says local commits need no approval while policy requires it; policy and skill repeatedly mandate a readiness question even when no commit is requested. | Aligned configuration, policy and tracked-story workflow. Leave changes uncommitted when no commit was authorized. |
| P3 | Research policy imposes two sources and claim labels on routine facts; Claude loads it for every task. Tracked-story depends on an unbundled `/better` command. | Research is concise and on demand; cross-check contested/high-impact claims. Removed the unbundled command dependency. |

## Shared versus host-specific

- Shared: `policy/`, `skills/`, Python core, CLI wrapper and verification script.
- Copilot: plugin manifest, rule frontmatter and tracking hook registration.
- Claude: `CLAUDE.md` imports, plugin manifest and nested hook registration.
- Codex: generated `AGENTS.md`, generated `.agents/skills/` with `agents/openai.yaml`, and short host notes. No copied Claude/Copilot hook configuration or user-level permission/model overrides.
- Generated duplication is intentional packaging, not multiple editable sources. Sync checks detect drift; canonical skills remain in `skills/`.

## Verification performed

On Windows in this checkout, `python scripts/verify.py` passed 21 tests plus skill validation and generated-content drift checking. Tests include real isolated onboarding/SQLite, CLI invocation from a foreign cwd, a failed-tool ledger append, and required Git signing rejection. `git diff --check` passed. CLI onboarding help exposes the documented tracking option. No real project story was created, no real index was staged and no commit or push was made.

The original README test command's import-path issue is fixed by the runner; the supported runner is the command to use from the root. This review does not reuse the earlier Linux-only report as evidence for these changes.

## Remaining limits

- Live plugin loading and hook firing in VS Code and Claude, and skill discovery in a fresh Codex chat, have not been observed in this review. The documented per-host activation checks remain necessary. Current chat was opened at `C:\dev\common`; open the child SDLC project for automatic Codex discovery.
- Codex tracking is explicit CLI evidence, not automatic tool telemetry. No host supplies authoritative token accounting here.
- Regex scope checks cannot securely parse arbitrary shell commands, aliases, nested interpreters or every Git invocation. Claude's hook can fail open; Copilot has no pre-tool hook. Native sandbox/permission enforcement is required. Never describe these checks as comprehensive protection.
- The Python package still supports editable checkout installation only: schema and hook resources are loaded outside the package. Windows `C:\dev` remains a deliberate toolkit constraint. No Linux/macOS runtime support claim is made.
- `commit-ready` checks policy and records supplied evidence; it does not independently execute validation or verify human authorization. These remain the host workflow's responsibility.
- The large service module and historical package/plugin branding remain follow-up maintenance work; neither is required to add a third adapter. No broad service rewrite was mixed into this change.

## Official compatibility references

Checked 2026-10-28:

- [Codex instructions discovery](https://learn.chatgpt.com/docs/agent-configuration/agents-md) and [skill discovery](https://learn.chatgpt.com/docs/build-skills): repository instructions and `.agents/skills/`, including optional UI metadata.
- [VS Code plugin hooks](https://code.visualstudio.com/docs/agents/reference/agent-plugin-reference): plugin hooks add to workspace hooks rather than replacing them.
- [GitHub Copilot hook reference](https://docs.github.com/en/copilot/reference/hooks-reference): PascalCase compatibility events and `PostToolUseFailure`. Existing casing is supported and was preserved.
- [Claude hook reference](https://code.claude.com/docs/en/hooks): host-specific nesting and decision handling. Local JSON tests validate structure, not successful live activation.
