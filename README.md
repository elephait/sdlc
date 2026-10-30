# Governed Multi-Agent Software Delivery

This utility provides a shared operating framework for reliable AI-assisted software delivery. It allows engineering teams to apply multiple or one particular AI coding tools across different programming languages and stages of the development lifecycle without tying the workflow to one model, vendor or technology stack.

## Strategic Goals

1. **Support software delivery across programming languages.** Provide a consistent workflow and control model that can be applied to diverse codebases while allowing each language and repository to retain its own engineering standards and toolchain.
2. **Enable effective cooperation across AI models.** Allow different AI coding tools to take responsibility for different stages of delivery, with durable handoffs that preserve intent, decisions, evidence and remaining work.
3. **Make quality gates central to delivery.** Require explicit, evidence-backed checkpoints so that work advances because defined criteria have been met, not because one or more models agree that it is complete.
4. **Make engineering best practices the default through `aicode`.** Equip each supported coding tool with shared coding, software design and AI-native delivery practices: understand requirements and existing code, keep designs simple and maintainable, make bounded changes, validate behavior, and preserve decisions and evidence across agent handoffs. Adapt these practices to the project's language, architecture and toolchain.
5. **Enable project-specific self-improvement from measured results.** Use collected project metrics—validation failures, confirmed review defects, retries, elapsed time and human intervention, plus usage or cost when available—to identify recurring problems and improve instructions, skills, checks and workflows. Compare changes against a project baseline, retain improvements that measurably help, and revise or roll back regressions. Keep changes reviewable and governed by human intent; missing telemetry is a measurement gap, never evidence of improvement.

`aicode` currently installs and refreshes customizations, onboards tracking, and exposes reports and project verification. Metric-driven self-improvement is a strategic goal supported by the shared evidence records and commit analysis; it is not yet an autonomous tuning loop. Codex requires explicit evidence recording and provides no automatic tool or token telemetry through this integration.

## Operating Model

Native coding agents perform the engineering work within their established environments. A lightweight, model-neutral control plane carries context between stages, records evidence and coordinates handoffs. Deterministic checks and named approvals provide the basis for accepting results and improving the workflow over time.

The intended outcome is a dependable path from requirements through implementation, review and delivery, with the freedom to use the language and AI tool best suited to each step.

This is currently a local Windows pilot and does not represent production certification.

## Reference Map

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

## One Shared Source, Multiple AI Tools

For this SDLC project, run the launcher from any PowerShell directory (replace `<sdlc-checkout>` with the folder that contains this repository):

```powershell
& "<sdlc-checkout>\aicode.cmd"
```

Start a new chat in the selected host after onboarding or refreshing a project. Current host integrations include VS Code Copilot, Claude Code, Codex and DeepSeek.


## Evidence-Based Handoffs

A story advances through defined checkpoints for requirements, implementation, review and delivery readiness. Each checkpoint records its evidence and a named approver.

A story can start with one AI tool and continue with another. Shared artifacts and gate records allow the next tool to resume from verified state rather than reconstructing intent from a conversation transcript.
