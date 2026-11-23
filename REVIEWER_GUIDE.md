# Reviewer guide

## Verify the live results in three steps

CommitNotice answers one question for a supplied pair of snapshots. For Apache §4(b), the contract verifies that the file body changed and asks independent GenLayer evaluators whether the leading notice acknowledges a downstream change. Git hashing establishes what bytes were assessed. Consensus establishes the decision reached under the contract’s rubric.

1. Open the [deployed contract](https://explorer-studio.genlayer.com/address/0x34c35Df6DC950EF9EdEFB17EF3F694A797525048) or [deployment receipt](https://explorer-studio.genlayer.com/tx/0x46dab6300bb93213e9471e093702237af3402cadc02a495d79fa46c5d17624a2) on **Studionet, chain ID 61999**. The contract address is `0x34c35Df6DC950EF9EdEFB17EF3F694A797525048`.
2. Open a receipt below. Read-only Studionet RPC checks confirmed `FINALIZED` and `FINISHED_WITH_RETURN` for the deployment and all three assessments. Each assessment shows **3 agree, 2 idle**. An idle validator did not contribute an agreeing vote. A stored FAIL is a policy finding from successful execution. REVIEW means the notice left downstream attribution unclear.
3. In Studio, import the contract by address and use **Read Methods → get_record** in the finalized state. Enter the assessment ID from the table. This is a view call. Compare the verdict, reason code, `git-sha1/1` scheme, and commit and digest references. The same fields were checked through read-only requests against finalized RPC state. [Studio read methods](https://docs.genlayer.com/developers/intelligent-contracts/tools/genlayer-studio/development-tips)

| Verdict | Explorer transaction | Assessment ID | Stored reason |
| --- | --- | --- | --- |
| PASS | [Receipt](https://explorer-studio.genlayer.com/tx/0x1c67b1743491a435c751191eff77f88b3d384e2332759ea51af1250c0450edd7) | `a09b475787a0d91083731af6b0a5c65bbac73a9dbca369a68461b4ce625914bb` | `change_acknowledged` |
| FAIL | [Receipt](https://explorer-studio.genlayer.com/tx/0x4dd2b49fd1d82948bb9bdf3fbce44701625c0ae88c95a82eb320abad010ddd04) | `a3503ec140e9c1436d13f0ce529d237003b1c9126f0a53d176b02fc6ba557f92` | `unchanged_claim_contradicted` |
| REVIEW | [Receipt](https://explorer-studio.genlayer.com/tx/0x52feeaa0064edd5316c242774127382494c312848d58d305c0f9dc444bcf83a4) | `2fddcf410ba6163712b05b0a801cb7931cd72479b9153b687864b2d2046495c6` | `notice_unclear` |

All three records use upstream commit `ab07629c95a4f81130b1aa13145b37091787c63f`. Their downstream references were confirmed independently.

| Verdict | Downstream commit | Downstream source SHA-256 |
| --- | --- | --- |
| PASS | `c9fcf45fbb2b89dab8938cd7023579e4a7b3babc` | `46167c2d9d5db264e8fbf7517b3cfa48718dc243020620dcf35a8b629052fcdd` |
| FAIL | `46312cef88f892002f036297ea4e6067e646aa47` | `c8d8becee010de02f20f93183490678f0188481178eee5f2ea49815f4f9a3faf` |
| REVIEW | `a3a481247285791015a628610c243038cac46cb8` | `caa72f0b35d3eda75452fddaa81208c3fb5270094caa168b67390d6066699b5e` |

The contract recomputes the raw commit, tree, and selected blob IDs before evaluation. The proof binds files to supplied commits. Repository labels remain caller declarations. These are synthetic fixtures, and three agreeing votes establish consensus on each fixture and rubric. They cannot establish repository ownership or predict other model judgments. MIT, Apache §4(a), and hostile-header cases have local coverage only. Studionet state is temporary. [Security boundaries](SECURITY.md) · [Network persistence](https://docs.genlayer.com/developers/networks)

## Local proof and cases

The downstream semantic fixtures share one source body and differ only in their header. The shared body differs from `tests/fixtures/upstream.py`.

| Fixture | Expected | Decoded proof bytes | JSON bytes |
| --- | --- | ---: | ---: |
| `pass.py` | PASS, clearly attributes a change to the downstream copy | 12,069 | 16,233 |
| `fail.py` | FAIL, claims it is unchanged despite a body difference | 12,044 | 16,197 |
| `review.py` | REVIEW, mentions an upstream edit but leaves downstream attribution unclear | 12,058 | 16,217 |
| `hostile.py` | REVIEW, explicit instruction blocked before the model | 12,109 | 16,285 |
| Apache §4(a) with two complete license copies | PASS, expected full text and identical source | 23,371 | 31,315 |
| MIT full notice | PASS, expected complete notice and identical source | 2,799 | 3,891 |

Sizes include the Git objects and their proof JSON. The JSON column excludes the terminal newline and GenLayer transaction encoding. The sample is generated from local synthetic fixture commits unaffiliated with external repositories. The test suite checks it byte-for-byte against a fresh Git export. Independent evaluator tests use mocked model outputs and do not execute live consensus.

## Export from local Git

Use explicit full commit IDs in local SHA-1 Git object databases. For a semantic proof, provide the upstream source and license paths and the downstream source path. All selected paths must be simple root-level regular-file names.

```sh
python3 tools/git_proof.py "$UPSTREAM_LOCAL_REPO" "$UPSTREAM_COMMIT" component.py LICENSE \
  "$DOWNSTREAM_LOCAL_REPO" "$DOWNSTREAM_COMMIT" component.py
```

For either deterministic policy, also pass `--down-evidence EVIDENCE` and choose appropriate stable commit and path inputs with byte-identical source. The exporter prints the proof to standard output and the measured sizes to standard error. It reads existing objects, disables replacement objects and Git network protocols, and recomputes their IDs using Git. To audit an export independently, extract each payload with `git cat-file <type> <oid>` and compare `git hash-object -t <type> --stdin` with the expected ID. Use `git ls-tree` to inspect selected path membership. [Git object extraction](https://git-scm.com/docs/git-cat-file) · [Git hashing](https://git-scm.com/docs/git-hash-object)

## Optional write inputs for an authorized reproduction

The following inputs describe the checked-in [PASS proof](tests/fixtures/sample_proof.json). Reading the existing evidence requires no new writes. For a separately authorized reproduction, import the existing contract in Studio, use the write method `assess`, and set a fresh attempt value.

| Argument | Value |
| --- | --- |
| `upstream_repo` | `fixture/upstream` |
| `upstream_commit` | `ab07629c95a4f81130b1aa13145b37091787c63f` |
| `upstream_path` | `component.py` |
| `upstream_license_path` | `LICENSE` |
| `downstream_repo` | `fixture/downstream` |
| `downstream_commit` | `c9fcf45fbb2b89dab8938cd7023579e4a7b3babc` |
| `downstream_path` | `component.py` |
| `downstream_evidence_path` | Empty string |
| `rule` | `apache-modified-notice` |
| `declared_reuse` | `true` |
| `declared_redistribution` | `true` |
| `attempt` | A fresh value. The published result used `first-pass`. |
| `proof` | The single JSON line from `sample_proof.json`, entered as the string value |

Before any separately authorized write, verify the target network, account, and transaction limits. The proof caps are application limits. Failed execution, disagreement, and timeouts can leave no stored verdict. A successful receipt and a matching finalized record are both required to reproduce a result. [Studio limitations](https://docs.genlayer.com/developers/intelligent-contracts/tools/genlayer-studio/limitations)
