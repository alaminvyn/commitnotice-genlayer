# Security and evidence boundaries

## Git object proof

The `git-sha1/1` proof contains raw object payloads encoded as canonical base64 in an ASCII JSON envelope. CommitNotice recomputes SHA-1 over the Git object type, ASCII byte length, NUL, and payload. The declared commit SHA must match the supplied commit. The root tree must match the commit pointer, and every selected blob must match the exact root-level path and regular-file entry. The verifier rejects duplicate JSON keys, unexpected fields, wrong versions, malformed commit headers, duplicate or unsorted tree paths, truncated entries, and invalid or unsupported selected blobs. Unsupported blob content includes Git LFS pointers, invalid UTF-8, hidden format characters, and binary control characters.

Limits are **48 KiB** for the ASCII JSON argument, **32 KiB** total decoded, **4 KiB** per commit, **8 KiB** per tree, **16 KiB** per selected blob, and **256 entries** per root tree. These are application limits. Proofs contain complete root trees, so their payloads include root filenames and object IDs beyond the selected paths. Treat all submitted proof bytes as public transaction data. There is no packfile, decompression, subdirectory traversal, or validator-side HTTP evidence retrieval.

Repository names are unverified caller declarations. A valid proof establishes Git object membership under its supplied commit IDs. It does not establish repository ownership, publication, commit signatures, or upstream ancestry. Obtain commit IDs independently from the intended repositories or a trusted release reference for those attribution claims. Git SHA-1 is collision-weakened and the contract uses ordinary SHA-1 without Git's collision detection. Stored SHA-256 digests support comparison of the exact commit, tree, and blob payloads. They are not independent authentication or a replacement for a trusted anchor. [Git hash transition](https://git-scm.com/docs/hash-function-transition.html)

## Policy and model

The deterministic checks require matching source bytes and standalone license files. The MIT policy supports one copyright line with a four-digit year or year range. It checks the full recognized grant and disclaimer and compares copyright lines after trimming their edges. The Apache fingerprint covers the complete reference text including its appendix. Fingerprinting collapses whitespace. Partial and unrecognized evidence yields REVIEW. A complete recognized MIT notice in the designated Apache evidence file is contradictory evidence under the standalone-file scope.

The semantic policy uses contiguous column-zero `#` lines at the start of a Python file as the prominent header. It discards blank separator lines after the block and normalizes CRLF and CR to LF for the body comparison. It retains remaining body characters and refuses leading encoding declarations. A missing or unchanged header yields REVIEW. The complete assessed header is limited to 24 lines and 2 KiB. The contract never runs the source.

The fixed rubric receives only the verified line-numbered header. It has no model tools or secrets. A narrow guard routes recognizable model-directed instructions to REVIEW before any model call. Obfuscated injections may bypass that guard. A decisive citation must include a line absent from the upstream header after trimming. Citation validation proves the lines exist. Semantic interpretation remains a judgment, and validators can share model failure modes.

## Execution and state

The deterministic execution verifies all required objects before the custom consensus block can call a model. The leader and validators independently classify the verified header and compare the canonical evidence-bound result. Invalid proof, invalid model output, and unresolved disagreement can prevent a write. An agreed policy uncertainty yields REVIEW. Inspect both the receipt's execution outcome and consensus status.

Anyone can submit an assessment. The recorded address identifies the submitting account. The ID hashes the policy, evidence scheme, sender, scoped inputs, and caller-supplied attempt. The contract rejects an existing ID before proof verification or model calls. Use a new attempt for retries, and retain an independent copy of the proof if re-verification is important. A verdict covers one rule and the declared snapshot pair. Actual redistribution, reuse direction, and license applicability are caller premises.

## Live verification coverage

The deployment and three Apache §4(b) fixtures returned successfully and finalized on Studionet. Finalized read calls matched the stored PASS, FAIL, and REVIEW records to the fixture commits and source digests. Each receipt shows three agree and two idle. The deterministic MIT and Apache §4(a) checks and the hostile-header fixture have local test coverage only. The evidence supports the tested scenarios. Shared model failure modes and broader security properties remain outside that evidence. Studionet state is temporary. [Live verification records](REVIEWER_GUIDE.md) · [GenLayer networks](https://docs.genlayer.com/developers/networks)
