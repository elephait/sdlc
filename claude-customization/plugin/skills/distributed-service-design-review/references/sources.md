# Foundations and provenance

Reviewed 2026-10-25. This is an original synthesis of the maintainer's design matrix and established guidance, not a copied framework or a professionally certified review. No claim is made that this new agent skill is popular or production-proven. Recheck version-sensitive claims for each deployment.

The matrix comes from banking delivery work. It is generalised here, and its vocabulary (transaction UUID, deduplication key and sequence, lease duration, outbox, saga, Resilience4j, Togglz, CloudWatch, blue/green) is kept as a set of triggers rather than a set of mandates.

| Source | Contribution | Limits |
|---|---|---|
| [SEI ATAM, Kazman et al.](https://www.sei.cmu.edu/library/the-architecture-tradeoff-analysis-method-2/) | Quality scenarios and architectural tradeoffs | This skill does not perform a formal ATAM workshop |
| [AWS Well-Architected](https://docs.aws.amazon.com/wellarchitected/latest/framework/the-pillars-of-the-framework.html) | Operational, security, reliability, performance, cost and sustainability coverage | Does not mandate AWS products |
| [Google SRE: Implementing SLOs](https://sre.google/workbook/implementing-slos/) | User-visible objectives and reliability evidence | Targets depend on the business |
| [Zalando RESTful API and Event Guidelines](https://opensource.zalando.com/restful-api-guidelines/) | Concrete contract and compatibility review | Company conventions are not universal standards |
| [OWASP API Security Top 10, 2023](https://api-security.owasp.org/editions/2023/en/0x11-t10/) | API authorization, abuse and trust-boundary risks | Risk awareness, not complete security assurance |
| [AWS: Making retries safe with idempotent APIs, Malcolm Featonby](https://builder.aws.com/content/3Ev0BENTyBr0XxzRk5FDZzgNYos/making-retries-safe-with-idempotent-apis) | Intent identity and atomic operation recording | External effects require their own protocol |
| [AWS: Timeouts, retries, and backoff with jitter, Marc Brooker](https://builder.aws.com/content/3EumjoZascWd1oZiEgL8ORlv3qE/timeouts-retries-and-backoff-with-jitter) | Deadlines and retry amplification | Inspect effective client settings |
| [Chris Richardson: Outbox](https://microservices.io/patterns/data/transactional-outbox.html) and [Saga](https://microservices.io/patterns/data/saga.html) | Established solutions to dual writes and distributed transactions | Apply only when justified |
| [RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html) and [RFC 9457](https://www.rfc-editor.org/rfc/rfc9457.html) | HTTP semantics and problem details | Respect compatible existing contracts |

## Product anchors

Pinned to the versions reviewed. Check the client and broker actually in use before repeating a setting.

- [Kafka 4.1 producer settings](https://kafka.apache.org/41/configuration/producer-configs/) and [transaction/delivery design](https://kafka.apache.org/41/design/design/).
- [SQS FIFO send deduplication](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/FIFO-queues-exactly-once-processing.html).
- [AWS transactional outbox guidance](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html).

## Where this guidance corrects a common heuristic

Each of these appears in the source matrix as a shorthand. The shorthand is useful as a prompt and wrong as a rule, so the correction is recorded here rather than silently dropped.

- **"Disable retry" for exactly-once.** Kafka idempotence requires `retries` greater than zero. Disabling producer retries removes duplicate risk by introducing loss; it does not buy exactly-once.
- **"2PC means storing on the same table."** A single local transaction is atomicity, which is usually the better answer, but it is not two-phase commit. 2PC is a coordinator protocol with prepare, commit and blocking behavior.
- **"`read_committed` gives exactly-once."** It is a consumer isolation setting. It hides aborted transactional records and leaves the consumer's database, charges and emails outside the transaction.
- **"The deduplication key proves once."** A key with a TTL, written outside the business transaction, leaves a crash window and expires inside long retry or replay horizons.

## Prompt method

The maintainer's [/better gist by joshp123](https://gist.github.com/joshp123/a1443d30fa1b7c577e74882895cea61b), revision `5d2b31e50c31ab5cc7dda8aa313ab7e3c50329c3`, informed the emphasis on professional methods, raw evidence and externally checkable acceptance criteria. The original text and attribution remain in the separate local checkout; this skill does not copy or require it.

Existing professional methods already cover this discipline. The added value is portable agent instructions and the maintainer's priorities of authoritative ownership and uncertain outcomes. A fork of an entire framework would add maintenance without improving this focused workflow.
