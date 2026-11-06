# Guarantee boundaries

Verify actual product/client versions and effective configuration. These notes describe boundaries, not permanent defaults.

## Delivery and consistency

- State the guarantee per link, not per system: at-most-once delivery, at-least-once delivery, or a deduplicated effect. Exactly-once is an effect built from a stable identity, an atomic record of the effect, and duplicate rejection. No broker setting makes an external side effect exactly once.
- Acknowledgement is not completion. Distinguish transport ack, broker acceptance, local commit and completed business work. A crash after the effect but before the ack yields a duplicate; before the effect it yields a loss or a retry, depending on who owns the retry.
- In-sequence holds inside a scope and only for the stated producer concurrency: partition, key, message group, or a single producer session. Rebalances, retries from a second producer and replays can break a claim made without that scope. Say what the consumer does with a gap.
- Eventual consistency needs a convergence window and an owner: whether a reader sees its own write, how stale a read may be, and which job or reconciliation closes the window.
- Durability: an acknowledged write, a replicated copy and a backup are three different things. Replication propagates corruption and deletion; only a tested restore bounds RPO/RTO.

## Idempotency and uncertain effects

Use a stable identity for the same caller's business intent across retries. Bind it to tenant/operation and define incompatible payload reuse, concurrent in-progress requests and retention relative to replay.

Where the identity is only known after the fact, a monotonic sequence or version number per scope can stand in for it, provided the durable high-water mark survives retries and restarts.

For local effects, atomically persist the operation identity/outcome and business changes, backed by constraints where appropriate. Deduplication outside that transaction leaves a crash window: a Redis SETNX or TTL before an independent database or external effect does not prove the effect happened once, and key expiry is not a guarantee.

For external effects, inspect provider idempotency and lookup capabilities and their retention. After an ambiguous timeout, preserve uncertainty; query or reconcile by durable identity. If neither exists, state the unresolved limit and recovery policy. Compensation can also fail or become uncertain.

## Kafka

- Producer idempotence covers supported producer-retry duplicates within the producer session and its retained batches; arbitrary application resends, a new producer identity and consumer effects need separate reasoning.
- Do not disable retries to obtain exactly-once behavior. The cited Kafka 4.1 Java producer documentation requires `retries` greater than zero, `acks=all`, and `max.in.flight.requests.per.connection` at most 5 for idempotence. Check the actual client and version.
- Transactions can commit output records and consumed offsets together for the read/process/write loop. Kafka Streams is one implementation, not the only API.
- `isolation.level=read_committed` is a consumer setting. It hides aborted transactional records, also returns nontransactional records, and does not make consumer effects transactional. The cited default is `read_uncommitted`.
- External database writes, charges and emails lie outside Kafka transactions. Coordinate durable input progress with the output, or use suitable idempotency and reconciliation.
- Define partition/key ordering, concurrency, rebalance behavior, transactional identity/fencing, offset commit placement, retention and replay.
- Kafka suits ordered, replayable streams. Using it as a work queue imports partition-ordering and rebalance behavior; a queue with per-message visibility, delay or priority may fit differently. Name the need before choosing the product.

## SQS FIFO

- Documented send deduplication lasts five minutes; business retries can occur later.
- Ordering is per message group. Inspect visibility timeout, deletion, redelivery and concurrency before claiming ordered business completion.
- Queue guarantees do not atomically commit a consumer's database or external effect. Distinguish acceptance, delivery, processing and completion.

## Outbox, CDC, sagas and 2PC

- Outbox commits business state and publication intent in one local transaction, not necessarily one table. Relays/CDC may publish duplicates; define consumer protection and ordering.
- CDC transports committed changes; it does not alone specify business semantics, downstream deduplication or rebuild behavior.
- Sagas coordinate local transactions through orchestration or choreography and business compensation. Step Functions is one option. Compensation is not an isolated ACID rollback; concurrent readers may observe intermediate state and some effects are irreversible.
- Two-phase commit is a coordinator/participant prepare-and-commit protocol. Storing related data in one table, or committing them in one local transaction, is not 2PC. Evaluate participants, recovery, blocking and operational cost.
- Reconciliation compares durable intent/progress against authoritative effects and repairs discrepancies. Define ownership, cadence, safe repair and escalation. Retrying alone is not reconciliation, and compensation does not prove the original effect failed.

See [primary sources and version anchors](sources.md).
