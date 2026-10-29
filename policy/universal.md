# SDLC policy

Shared operating rules for Copilot, Claude, Codex and DeepSeek. Host notes describe loading and tool mechanics; skills describe on-demand workflows. Historical reviews and pilot plans are evidence, not additional instructions.

## Authority and boundaries

- Follow the user's intent, accepted requirements and repository conventions within host/system permissions. Preserve unrelated edits. Do not silently change acceptance criteria.
- Ordinary local work in the authorized workspace is expected. C:\dev is the default workspace boundary for this Windows toolkit, not a permission grant. Respect host sandbox and approval decisions; request required access rather than bypassing a denial.
- Do not send secrets, private source or internal logs to unapproved services, or incur external charges without authorization.
- Publication is a human operation: leave pushes and releases to the user. Local commits require explicit authorization for the current task. Use `ai commit by <ai>: ` or `ai code review by <ai>: ` titles, naming the AI that made the commit (`ai commit by claude: ...`; claude, deepseek, codex or copilot) and preserve repository signing settings.
- Exclude credential-like files from commits unless explicitly approved for the exact staged content. Record approver, time, paths and blob hashes through the shared credential-approval command.

## Handoff gates

Five handoffs structure a story. Each closes with recorded evidence and a named approver before the next opens; the commands are in the tracked-story skill.

1. **Analysis and acceptance.** Intent, acceptance criteria, assumptions, out-of-scope and risks are written down and accepted.
2. **Implementation.** The change is complete, validation has run, and a commit is authorized. It ends in a local commit and handoff report.
3. **Review.** Findings, dispositions and residual risk are recorded; at most three rounds.
4. **Customization.** Any change to policy, skills, core, scripts, the root launchers or a host adapter names its layer and passes the drift check.
5. **Documentation.** The end-user README matches current operation, architecture and limits.

`copilot-sdlc gate` records a gate with its artifact, evidence, approver and (when supplied) the host that recorded it. `commit-ready` refuses while a required gate is missing or stale, and every gate names who approved it. `implementation` and `customization` bind to the staged tree and must be recorded after staging; `analysis` is story-level and stays valid across commits. A waiver is evidence too: name the approver and the reason.

## Delivery and evidence

- Inspect relevant instructions, recent edits, build configuration and nearby code before changing anything. Reuse existing implementations. Fix the narrowest proven cause; avoid unrelated refactoring.
- Resolve routine choices from evidence. Ask only for a blocking ambiguity or a consequential decision outside existing authorization. Continue independent work while waiting.
- Validate during implementation: run focused, safe tests and checks appropriate to the change, then inspect the final diff. Validation does not authorize a commit. Defer destructive, production or externally billable checks until authorized. Format changed code when needed and recheck affected behavior afterwards.
- Report only checks actually run and their results. Separate static inspection, synthetic checks and live host verification. Do not present agreement between agents, a pilot or an untested configuration as runtime proof.
- Before an authorized commit, reconcile code, documentation and evidence; stage only reviewed files and use `commit-ready` for tracked stories. It creates a local commit and handoff report; it does not run tests or prove acceptance. If no commit was requested, leave reviewed changes uncommitted and report them.

## Scale and focus

- Keep small tasks lightweight. For long or risky work, maintain a compact acceptance contract: intent, criteria, constraints, assumptions, dependencies and verified state. Use durable checkpoints instead of transcript replay.
- Native agents do coding; deterministic tools handle state, scheduling and measurable gates. One writer per worktree. Use independent review when warranted and available, with bounded time, retries and at most three review rounds. Agent agreement is not a substitute for validation.
- After a failed approach, revisit the evidence. After three iterations without progress, stop that approach and reassess or ask a focused question. Record unresolved risk honestly.
- Keep customization at the narrowest useful layer. Edit shared policy, core or skills once, regenerate adapters and check drift. Avoid repeating host defaults, adding ceremonial agents, or loading irrelevant workflows.
- For external research affecting a software decision, read `policy/research.md` from the SDLC source repository. Load workflow skills only when relevant.

## Records and handoff

- For tracked stories, retain decisions, approvals, failures, resolutions and validation evidence. Aggregate trivial successes; preserve unresolved items and archive details before compaction.
- End with the outcome, changes, evidence and material limits. For automated tracking use `DONE`, `BLOCKED_NEEDS_USER`, `FAILED`, `STUCK`, `LIMIT_REACHED` or `SECURITY_STOP` accurately. Never mark success solely on self-assessment.
