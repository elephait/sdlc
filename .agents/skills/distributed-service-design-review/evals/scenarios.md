# Skill regression fixtures

Run a fixture by handing the skill the fixture text as the system description, with the instruction "review this". Judge the reply against its expected line. After a material skill change, re-run the fixtures that touch the changed reference. The acceptance rubric below is for the skill, not a maturity score for a user's system. Tabletop reasoning does not prove runtime safety.

## External charge and lost response

Fixture: Redis SETNX on tenant/operation with a 60-second TTL; call provider.charge without provider idempotency; record success afterward in PostgreSQL. On timeout return failed. Client retries after 90 seconds. Provider status/idempotency support unspecified.

Expected: identify effect/record crash window, false definitive failure and expired protection; preserve uncertainty, seek provider capabilities and offer conditional reconciliation. Must not claim a local outbox makes the external charge atomic or that a duplicate has already occurred.

## Simple local transaction

Fixture: one PostgreSQL transaction records tenant-scoped operation identity, checks intent hash, conditionally decrements stock and stores the reservation result. Unique constraint on tenant/operation; authorized status API; no external effects or events. Ten requests/second; retention and recovery objectives unspecified.

Expected: recognize local atomicity; label retention/concurrent in-progress behavior/restore evidence as unknown where needed. Do not prescribe Kafka, Redis, saga, 2PC or multi-region without a requirement. Do not claim tests passed from a prose fixture.

## Kafka to database

Fixture: read_committed consumer inserts an invoice with a random ID, then commits its Kafka offset. No unique source-operation constraint. It can crash between insert and offset commit.

Expected: trace replay producing another invoice; explain consumer isolation limits; consider durable operation identity and atomic effect/deduplication or coordinated input progress. Do not assert Kafka transactions alone cover the external database or disable retries.

## Stale lease holder

Fixture: A holds a 30-second lease, pauses 45 seconds; B acquires lease and writes version 12; A resumes and unconditionally writes version 11. Rolling deployment overlaps workers.

Expected: identify stale-owner write; distinguish lease from storage-enforced fencing or conditional version writes. Specify a reproducible stale-worker check. Increasing TTL is not proof of exclusivity.

## Compensated transfer, rail settles later

Fixture: a transfer saga debits wallet A, calls a payment rail, and on a 10-second timeout compensates A and returns failed. The rail later succeeds and credits B at the network. Nothing reads the rail's settlement file; support resolves disputes by hand from logs.

Expected: identify stranded or duplicated funds and the false definitive failure; require durable operation identity, reconciliation against the scheme's settlement file with an owner, cadence, safe repair and escalation; reject the idea that compensation proves the rail did nothing. Do not accept a retry-only remedy.

## Durability claim from replication

Fixture: the operator states "durable, we replicate to three nodes in one region; RPO is zero." No backup history, no restore drill, deletion propagated by replication. Synchronous acknowledgment on the primary, asynchronous to replicas.

Expected: separate acknowledged write, replication and backup; identify that replication propagates deletion and corruption, that asynchronous replica acknowledgment bounds RPO above zero, and that restore is untested. Ask for restore evidence rather than accepting the topology as proof.

## Prompt method scope

Request to /better: Improve this prompt: "Review our service architecture."

Expected: professional method, raw evidence, concrete tools/techniques and external acceptance criteria, then a rewritten prompt. Do not implement a system or fabricate evidence. For an already-authorized ongoing review, deepen it without changing its objective.
