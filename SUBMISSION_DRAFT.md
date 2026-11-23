# CommitNotice

**Category** · Intelligent Contracts

**One-liner** · CommitNotice verifies Git snapshot evidence and records validator-backed decisions about Apache modified-file notices.

## Problem and utility

When maintainers vendor source code, a license file does not tell them whether the changed file itself acknowledges a downstream modification. CommitNotice gives maintainers and reviewers a shared record of that specific check, tied to the exact evidence they can inspect.

## How it works

A caller supplies raw Git objects for the upstream and downstream snapshots. CommitNotice recomputes the commit, root tree, and file blob IDs without fetching repository content at runtime. It records SHA-256 evidence digests and checks the file body difference deterministically.

Under Apache-2.0 §4(b), GenLayer evaluators independently interpret the verified leading comment. The validator compares the bounded classification and its evidence with the leader’s result. The contract stores PASS for a clear downstream acknowledgment, FAIL for an unchanged claim contradicted by the file, and REVIEW when attribution is unclear. MIT notice preservation and Apache §4(a) license-copy checks are deterministic and covered by local tests.

**Technical stack** · Python Intelligent Contract, raw Git object proofs, GenLayer LLM calls, and custom equivalence validation.

## Evidence

Studionet chain `61999`, contract `0x34c35Df6DC950EF9EdEFB17EF3F694A797525048`. Read-only RPC checks confirmed the deployment and all three §4(b) assessments finalized with successful execution. Each assessment recorded three agree and two idle. [Contract](https://explorer-studio.genlayer.com/address/0x34c35Df6DC950EF9EdEFB17EF3F694A797525048) · [Deployment](https://explorer-studio.genlayer.com/tx/0x46dab6300bb93213e9471e093702237af3402cadc02a495d79fa46c5d17624a2) · [PASS](https://explorer-studio.genlayer.com/tx/0x1c67b1743491a435c751191eff77f88b3d384e2332759ea51af1250c0450edd7) · [FAIL](https://explorer-studio.genlayer.com/tx/0x4dd2b49fd1d82948bb9bdf3fbce44701625c0ae88c95a82eb320abad010ddd04) · [REVIEW](https://explorer-studio.genlayer.com/tx/0x52feeaa0064edd5316c242774127382494c312848d58d305c0f9dc444bcf83a4)

Reviewers can inspect the votes and query finalized records with `get_record` using the IDs in the [reviewer guide](REVIEWER_GUIDE.md). The local suite passed 21 tests with real Git objects and mocked GenLayer and model behavior.

## Security and scope

The proof establishes file membership relative to supplied Git SHA-1 commit IDs. Repository attribution and distribution are caller declarations. SHA-256 digests support byte comparison and do not authenticate those declarations. The semantic prompt receives only a bounded verified header and checks citations. The demonstrated outcomes cover three synthetic fixtures. MIT, Apache §4(a), and hostile-header behavior have no live receipts, and Studionet state is temporary.

## Submission fields to complete

- **Repository name:** `commitnotice-genlayer`
- **Repository URL:** Add after approved publication.
- **Portal fields:** Confirm the current form and field limits before submitting. The public Portal overview describes steward review and GitHub verification. [GenLayer Portal](https://portal.genlayer.foundation/how-it-works/)
