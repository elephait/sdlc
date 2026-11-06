# Design matrix

Apply relevant questions, not mandatory implementations. Vendor names are examples. Prefer established project conventions and the simplest design satisfying the invariant. Consult [sources](sources.md) for the underlying frameworks.

## Ownership, identity and correctness

- Who owns each authoritative fact? Which stores are projections, caches or workflow journals? Can a middleman recover truth after losing a response, and does it stay out of the way of the owner?
- Separate request/trace ID, event ID and business transaction ID (a UUID minted once per intent). Define tenant scope, intent/payload mismatch, concurrent duplicate behavior and retention relative to replay windows.
- Which changes commit atomically? Inspect constraints and transaction boundaries rather than application-level existence checks alone.
- Define pending, successful, rejected, compensated and unresolved states where useful; transition authority, late arrivals and terminal-state rules.
- What does success mean to the caller: a stored request, a committed transaction, or completed business work? State the failure model and possible data loss.
- For money movement, state the double-entry invariant (postings balance, no negative balance without an authorised facility), the value date and cut-off rules, and which ledger or scheme report is authoritative. Reconcile against the scheme's own file, not only against internal state.

Evidence: schema, constraints, state machine, transaction code, status API and durability settings. Check concurrent requests and a crash after effect but before response.

## Delivery, ordering and consistency

- What delivery guarantee is claimed, and by which link: at-most-once, at-least-once, or a deduplicated effect? Name the link, not the product.
- Acknowledgement: what the ack commits, who waits for it, and what a crash between the effect and the ack duplicates or loses.
- In-sequence: the ordering scope (entity, key, partition, message group), producer concurrency, and the rule for gaps, retries and replays. Delivery order and processing completion order are different claims.
- Eventual consistency: the convergence window, whether a caller sees its own write, the stale-read policy, and which job or reconciliation closes the window.
- Durability: an acknowledged write, replication and a backup are three different things. Replication propagates corruption and deletion; only a tested restore bounds RPO/RTO.

Evidence: broker and client settings, offsets, deduplication store and TTL, sequence or version columns, reconciliation jobs, restore reports. Check loss, duplicate, reorder and replay against the claim itself.

## HTTP and API contract

- Resource identity; safe/idempotent method semantics; validation; bounded pagination/filtering; status/error contracts; concurrency preconditions such as ETag/If-Match where appropriate.
- For asynchronous work, distinguish acceptance from completion; specify status lookup, correlation, cancellation and expiration. HTTP 202 does not mean business success.
- Retry contract for transient errors, definitive rejection and ambiguous timeout; deadlines and mutation idempotency where needed.
- Compatibility of fields, enums, error formats and event schemas; consumer-driven versioning/deprecation. Do not impose one company's URL conventions universally.

Evidence: OpenAPI, consumers, contract tests and response handling. Check stale updates and incompatible consumers. Idempotent HTTP semantics do not require byte-identical responses on each attempt.

## Messaging and workflows

- Replay horizon, poison messages, dead-letter owner and safe redrive, backlog and retention bounds.
- Database/event dual writes: atomic local state plus outbox, relay/CDC failure, duplicate publication and consumer effects. CDC means change data capture, not a complete business protocol.
- Cross-service transactions: durable progress, local commits, compensation, irreversible steps, intermediate visibility and reconciliation. Compare orchestration/choreography only when applicable.
- Priority queues: starvation, fairness, ordering conflicts and per-class capacity.

Read [messaging caveats](messaging.md). Check crashes at relevant writes/acknowledgments, then verify both final business state and workflow progress after replay.

## Dependency resilience

- End-to-end deadline; connect/read/request timeouts; cancellation and bounded resource usage.
- Retryable conditions, retry owner, capped attempts/time budget, jitter, Retry-After and retry multiplication across SDKs/layers. Ambiguous effects require a protocol before retrying.
- Bulkheads, circuit breakers, pools, rate limits and throttling tied to actual bottlenecks. Resilience4j offers mechanisms; effective configuration and fallback behavior establish safety.
- Decide fail-open/closed per consequence. Specify stale/degraded responses; a fallback must not fabricate mutation success or silently bypass authorization.

Evidence: SDK settings, timeout paths, queue/pool limits and external contracts. Check slow dependency, lost response, rate limiting and partial outage without retry amplification.

## Scale, concurrency, performance and cost

- Stateless compute still relies on stateful systems. Locate sessions, hot keys/partitions, shared limits and single failure points.
- Size against traffic shape, bursts, p95/p99 latency, saturation, queue age and recovery time. A 50-70% utilization target is a hypothesis, not a universal rule; include startup delay, quotas and failover headroom.
- Cache authority, staleness, invalidation, stampedes, tenant isolation and failure behavior. Buffering handles bounded bursts, not indefinite overload.
- Concurrency checks, locks, leases and fencing: what rejects a stale worker's write? Lease expiration does not terminate a process. Uniqueness, deduplication, mutual exclusion and fencing serve different purposes.
- Compare cost per successful operation, idle capacity, retention, transfer, managed infrastructure and operational effort. Do not claim savings without workload evidence.

Check representative bursts/soaks, capacity loss, cache outage and stale workers against both latency/backlog bounds and business invariants.

## Security

- Authentication and object-, function-, property-level authorization; tenant boundaries and least-privilege service identities.
- MFA for relevant human access does not replace service authorization. Secrets lifecycle, transport protection, sensitive-data minimization, redaction and retention.
- Resource limits, business-flow abuse, outbound/SSRF boundaries, untrusted inputs and provider responses, API inventory and retirement.

Use OWASP API Security as a risk checklist, not certification. Check negative cross-tenant/privilege cases and resource abuse; live invasive tests require appropriate authorization.

## Reliability, observability and recovery

- User-visible availability, latency, correctness and freshness indicators/SLOs; define counted requests and success. Use error budgets to inform changes.
- Correlate requests, business operations, events and progress. Separate logs, metrics, traces and audit records. CloudWatch logging alone is not observability.
- Alert on impact, unresolved/stuck operations, oldest queue age, retries/dead letters, lag and capacity where relevant. Bound cardinality and sensitive fields.
- Backups with a tested restore, RPO/RTO, failure domains, reconciliation owner, audited repair and runbooks.

Check restore drills and unresolved-effect reconciliation, including whether operators can detect and resolve the problem within the target.

## Deployment and change

- Rolling/canary/blue-green strategy, readiness, draining, in-flight jobs and mixed versions; measurable rollback triggers.
- Expand/contract data and event migrations; compatibility and rollback feasibility after state changes.
- Feature flags: owner, safe default, outage behavior, kill switch and retirement where appropriate. Togglz is one implementation.
- CI checks appropriate to the change: contracts, migrations, authorization, important concurrency and recovery paths. Avoid tests that merely repeat implementation details.

Check old/new instance overlap, restart during work and rollback after partial rollout. Relate sustainability concerns to applicable capacity, retention and resource-efficiency choices rather than adding an unrelated audit.
