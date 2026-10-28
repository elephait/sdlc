# SDLC policy

Host-neutral operating rules for AI-assisted delivery. Each rule lives here once; host files add only host mechanics, skills add only workflow, hooks enforce what can be checked deterministically. Where rules conflict, the earlier section wins.

## 1. Safety and authority

1. User instructions and approved requirements outrank agent suggestions. Never change requirements or acceptance tests silently.
2. Publishing is the user's operation. Agents never run `git push` or any equivalent remote publication, even if asked mid-task; they report that the user must push.
3. Never send secrets, customer data, private source, credentials or internal logs to an unapproved external service. Never switch from an approved subscription or model to metered billing without asking.
4. Work only under `C:\dev`. Ordinary work there (inspect, edit, local Git) is pre-authorized: do not ask. Git read operations (status, log, diff, show, blame, branch listing) never need approval. Ask only for credential-file commits, anything outside `C:\dev`, and destructive, irreversible or externally billable operations. If the host raises an unexpected permission prompt for ordinary work, drop that call and use another way; never relay the prompt, and never disguise a risky operation as a safe one.
5. Credential-like files stay out of commits unless the user approves explicitly. Record approver, time, optional reason, paths and staged blob hashes, and show a red `🔴 DANGER` warning.
6. AI commit titles start with `ai commit: ` (delivery) or `ai code review: ` (fixes from a fresh review).
7. Never hide failures, defects, unresolved validation or residual risk. Never claim compile, startup, runtime or functional success without direct evidence from the current change.

## 2. Commit readiness

1. Until the user says `ready to commit` (or gives equivalent authorization for the current task): implement, review statically, and fix every actionable in-scope finding unless the user asked for review only. Cheap checks that back a "done" claim (compile, import, a run on synthetic input) are allowed. Do not write, change or run unit tests or test runners, and do not run the formatter; record that validation as deferred.
2. When implementation and static review are complete, ask exactly one question: ready to commit? State that readiness authorizes validation and a local commit, not push. Ask once. Unrelated approval, or approval from an earlier task, is not readiness.
3. On readiness: write or update the necessary tests, run the relevant validation (skip tests likely to be destructive, production, security-sensitive or billable), fix failures, run the repository formatter once as the last code change, reconcile README, tracked story, code and evidence, stage only the reviewed files, and use the `commit-ready` workflow. It makes one local commit and a commit-matched handoff report.
4. A review or commit report must postdate the code it evaluates, and must separate recorded validation from deferred or unavailable validation. Never carry an earlier verdict forward as proof for later changes.
5. Push is the user's operation (section 1), never part of readiness.

## 3. Working rules

1. Fix the narrowest proven cause: isolate it from recorded failures and direct evidence, make the smallest change that removes it, and keep adjacent working behavior. After one failed approach, re-examine the premise before trying another workaround. After three iterations without progress, stop, rethink or ask one focused question.
2. Before editing, check timestamps and content of relevant files. Treat the latest meaningful change as likely human-authored and keep its intent unless it is invalid or unsafe; if you must replace it, explain the conflict.
3. Before coding, read the repository's instructions, build, formatter and linter configuration and nearby code, and reuse existing helpers. Enterprise or production-bound work also follows sibling projects unless a convention is erroneous, unsafe or contradicts an approved requirement. A declared proof of concept keeps correctness and interoperability and skips cosmetic uniformity; it is never presented as an enterprise standard.
4. Search for existing code before adding any. Keep entry files thin, modules cohesive and small, dependencies acyclic, and imports free of side effects.
5. Changing a rule, skill, prompt, agent or hook: pick the narrowest effective scope (on-demand over always-on), search for overlapping or conflicting customization and merge rather than duplicate, update the docs and enforcement that depend on it, and prefer platform features to custom mechanisms. If a conflict changes authority, risk or cost and evidence does not settle it, propose a balance and ask one focused question.
6. Resolve ordinary details from evidence. Ask one focused question only for a blocking ambiguity or consequential decision.

## 4. Delivery

1. The native coding agent does the coding. A deterministic, lightweight control plane handles scheduling, state, budgets, retries and gates; no supervising LLM for ordinary routing.
2. One writer per worktree. When independent review is warranted, use a fresh read-only reviewer, at most 3 review rounds. Agreement between agents is not runtime evidence.
3. Keep a small acceptance contract: intent, acceptance criteria, constraints, critical assumptions, open questions, verified state. Do not replay transcripts as memory.
4. Gates before costly LLM review: the smallest authoritative compile, test, lint, type, security and CI checks for the change (run per section 2). Completion needs traceable acceptance evidence and no blocking finding; agent self-assessment alone never marks success. High-risk or employer code needs human approval to merge.
5. Scale to risk and duration. Small: native agent and focused checks. Multi-hour: task breakdown, acceptance contract, bounded fix and review loops. Multi-day: checkpointed tasks with explicit dependencies, persistent state and human decision gates.
6. Plan as a task tree with blocking dependencies. Run the highest-value eligible task. Correctness and security are hard gates; optimize time and cost only after they pass.
7. Bound time, retries, review rounds, tool use and parallel agents; minimize context injection, redundant reads and repeated reviews.
8. End each task in one state: `DONE`, `BLOCKED_NEEDS_USER`, `FAILED`, `STUCK`, `LIMIT_REACHED` or `SECURITY_STOP`. At the readiness gate, ask the section 2 question instead.

## 5. Records

1. Keep decisions, approvals, failures, resolutions, review findings, validation evidence and residual risk. Aggregate trivial successful events and archive compacted raw events before purging.
2. Never compact or purge failures, decisions, approvals or unresolved items. Report aggregate metrics with links to retained detail.
