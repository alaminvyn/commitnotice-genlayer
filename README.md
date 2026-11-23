# CommitNotice

A repository can include a license and still leave it unclear whether a vendored file carries the required notice. CommitNotice verifies the supplied Git snapshots and records one scoped license-evidence decision per file pair. Maintainers and reviewers can inspect the same inputs and see which rule the record covers.

| Rule | What a PASS establishes |
| --- | --- |
| `mit-notice` | Byte-identical source files and a designated standalone MIT notice containing the recognized complete grant and the upstream copyright line. |
| `apache-license-copy` | Byte-identical source files and a designated standalone copy of the complete recognized Apache-2.0 text under §4(a). |
| `apache-modified-notice` | A verified source-body difference and a prominent leading Python comment that independently evaluating validators interpreted as a clear acknowledgment of a downstream change under §4(b). |

Every result applies to the selected rule and files proven to belong to the supplied commits. Repository names, license applicability, reuse direction, and redistribution are caller declarations. Reviewers must independently associate each commit with the intended repository. The result carries no legal certification or claim about what recipients received.

## How it works

The caller submits a bounded JSON proof containing base64-encoded raw Git commits, root trees, and selected blobs. The contract recomputes each Git object ID and verifies the full path from each declared commit to each required file. This replaces runtime HTTP evidence fetching. MIT and §4(a) checks run deterministically. For §4(b), the leader and validators independently classify the verified header and compare the result against the same evidence. A normal hash comparison can establish that a file changed. GenLayer consensus is useful when the reviewer must also decide what the notice means. The contract records evidence digests and a fixed reason code.

- **PASS** means the selected check is supported.
- **FAIL** means the verified evidence affirmatively contradicts the selected check.
- **REVIEW** means the verified evidence leaves the rule unclear or outside the supported policy. Invalid proof, failed execution, timeout, and lack of agreement can leave no record.

## Verified Studionet deployment

Chain ID `61999` · Contract `0x34c35Df6DC950EF9EdEFB17EF3F694A797525048`. The deployment and all three Apache §4(b) assessments finalized with successful execution. Each assessment recorded three agreeing votes and two idle validators. Read-only Studionet RPC checks confirmed the stored outcomes. [Contract](https://explorer-studio.genlayer.com/address/0x34c35Df6DC950EF9EdEFB17EF3F694A797525048) · [Deployment](https://explorer-studio.genlayer.com/tx/0x46dab6300bb93213e9471e093702237af3402cadc02a495d79fa46c5d17624a2)

| Stored verdict | Reason | Receipt |
| --- | --- | --- |
| PASS | `change_acknowledged` | [PASS transaction](https://explorer-studio.genlayer.com/tx/0x1c67b1743491a435c751191eff77f88b3d384e2332759ea51af1250c0450edd7) |
| FAIL | `unchanged_claim_contradicted` | [FAIL transaction](https://explorer-studio.genlayer.com/tx/0x4dd2b49fd1d82948bb9bdf3fbce44701625c0ae88c95a82eb320abad010ddd04) |
| REVIEW | `notice_unclear` | [REVIEW transaction](https://explorer-studio.genlayer.com/tx/0x52feeaa0064edd5316c242774127382494c312848d58d305c0f9dc444bcf83a4) |

The MIT and Apache §4(a) paths and the hostile-header fixture were tested locally. Studionet is a temporary development environment, so the deployed state and receipts may become unavailable after a reset. [Reviewer walkthrough](REVIEWER_GUIDE.md) · [GenLayer networks](https://docs.genlayer.com/developers/networks)

## Local verification

Use Python 3.9+ and Git with support for SHA-1 object databases. No additional Python packages are required for local tests or proof generation.

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
```

All 21 local tests passed. They use real locally generated Git objects and cross-check object IDs with Git. The local suite mocks the model and the GenLayer boundary. See the reviewer guide for proof export, Studio usage, and read-only record lookup.

- [Contract](contracts/commit_notice.py)
- [Local Git proof generator](tools/git_proof.py)
- [Tests](tests/test_commit_notice.py) and [sample Studio proof](tests/fixtures/sample_proof.json)
- [Reviewer guide](REVIEWER_GUIDE.md), [security model](SECURITY.md), and [submission draft](SUBMISSION_DRAFT.md)

The first-line runner pin follows the [official GenLayer snippets](https://docs.genlayer.com/developers/intelligent-contracts/examples/snippets). Policy fingerprints use the [official Apache license text](https://www.apache.org/licenses/LICENSE-2.0.txt) and the [SPDX MIT license text](https://github.com/spdx/license-list-data/blob/main/text/MIT.txt).

## License

CommitNotice is licensed under the MIT License. Copyright (c) 2026 Al Amin. The Apache-2.0 and MIT texts in the fixture directory are evidence inputs. [Project license](LICENSE)
