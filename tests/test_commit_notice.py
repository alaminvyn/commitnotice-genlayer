"""Host Python tests with an explicit SDK boundary double; no network or GenVM."""

import base64
import hashlib
import importlib.util
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.git_proof import git, make_proof

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"
UP = "fixture/upstream"
DOWN = "fixture/downstream"



class UserError(Exception):
    pass


class Return:
    def __init__(self, calldata):
        self.calldata = calldata


class Disagreement(Exception):
    pass


def load_contract():
    sdk = types.ModuleType("genlayer")
    sdk.TreeMap = dict

    def public(method):
        return method

    sdk.gl = types.SimpleNamespace(
        Contract=object,
        public=types.SimpleNamespace(write=public, view=public),
        message=types.SimpleNamespace(sender_address="test-sender"),
        nondet=types.SimpleNamespace(exec_prompt=None),
        vm=types.SimpleNamespace(Return=Return, UserError=UserError, run_nondet_unsafe=None),
    )
    source = importlib.util.spec_from_file_location("commit_notice", ROOT / "contracts" / "commit_notice.py")
    module = importlib.util.module_from_spec(source)
    with patch.dict(sys.modules, {"genlayer": sdk}):
        source.loader.exec_module(module)
    return module


contract = load_contract()


def write_object(repo, kind, raw):
    return git(repo, "hash-object", "-w", "--literally", "-t", kind, "--stdin", data=raw).strip().decode("ascii")


def write_snapshot(repo, files, message):
    lines = []
    for path, (mode, raw) in sorted(files.items()):
        oid = write_object(repo, "blob", raw)
        lines.append(f"{mode} blob {oid}\t{path}\n".encode("ascii"))
    tree = git(repo, "mktree", data=b"".join(lines)).strip().decode("ascii")
    return write_commit(repo, tree, message)


def write_commit(repo, tree, message):
    identity = "CommitNotice Fixture <fixture@example.invalid> 1795478400 +0000"
    raw = f"tree {tree}\nauthor {identity}\ncommitter {identity}\n\n{message}\n".encode("ascii")
    return write_object(repo, "commit", raw)


def init_fixture_repo(repo):
    git(repo, "init", "--quiet", "--object-format=sha1", "--template=", ".")


def fixture(name):
    return (FIXTURES / name).read_bytes()


def mit_notice(holder):
    _, grant = fixture("MIT-template.txt").split(b"Permission is hereby granted", 1)
    return b"MIT License\n\nCopyright (c) 2026 " + holder + b"\n\nPermission is hereby granted" + grant


class CommitNoticeTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.repo_path = Path(temporary.name)
        init_fixture_repo(self.repo_path)
        self.instance = contract.CommitNotice()
        self.instance.records = {}
        self.prompts = []
        self.answers = []
        self.proposal_edit = None
        self.up_commit = self.down_commit = "1" * 40
        self.proof = ""
        contract.gl.message.sender_address = "test-sender"
        contract.gl.nondet.exec_prompt = self.prompt
        contract.gl.vm.run_nondet_unsafe = self.consensus

    def prompt(self, prompt, *, response_format):
        self.assertEqual(response_format, "json")
        self.prompts.append(prompt)
        return self.answers.pop(0)

    def consensus(self, leader, validator):
        proposed = leader()
        if self.proposal_edit is not None:
            proposed = self.proposal_edit(proposed)
        if not validator(Return(proposed)):
            raise Disagreement()
        return proposed

    def setup_evidence(self, upstream, downstream, license_text, downstream_license=None):
        self.up_commit = write_snapshot(self.repo_path, {
            "LICENSE": ("100644", license_text), "component.py": ("100644", upstream),
        }, "upstream")
        files = {"component.py": ("100644", downstream)}
        if downstream_license is not None:
            files["EVIDENCE"] = ("100644", downstream_license)
        self.down_commit = write_snapshot(self.repo_path, files, "downstream")
        self.proof, self.raw_size = make_proof(
            self.repo_path, self.up_commit, "component.py", "LICENSE",
            self.repo_path, self.down_commit, "component.py",
            "EVIDENCE" if downstream_license is not None else "",
        )

    def replace_object(self, side, field, raw):
        packet = json.loads(self.proof)
        packet[side][field] = base64.b64encode(raw).decode("ascii")
        self.proof = json.dumps(packet, separators=(",", ":"))

    def assert_proof_rejected(self, message, **kwargs):
        with self.assertRaisesRegex(UserError, message):
            self.assess(**kwargs)
        self.assertEqual(self.instance.records, {})
        self.assertEqual(self.prompts, [])

    def replace_tree_and_commit(self, raw_tree):
        oid = write_object(self.repo_path, "tree", raw_tree)
        self.down_commit = write_commit(self.repo_path, oid, "negative fixture")
        raw_commit = git(self.repo_path, "cat-file", "commit", self.down_commit)
        self.replace_object("downstream", "tree", raw_tree)
        self.replace_object("downstream", "commit", raw_commit)

    def assess(self, rule=contract.APACHE_CHANGE, attempt="first", **override):
        args = dict(
            upstream_repo=UP, upstream_commit=self.up_commit, upstream_path="component.py",
            upstream_license_path="LICENSE", downstream_repo=DOWN, downstream_commit=self.down_commit,
            downstream_path="component.py",
            downstream_evidence_path="" if rule == contract.APACHE_CHANGE else "EVIDENCE",
            rule=rule, declared_reuse=True, declared_redistribution=True, attempt=attempt, proof=self.proof,
        )
        return self.instance.assess(**dict(args, **override))

    def record(self, *args, **kwargs):
        return json.loads(self.instance.get_record(self.assess(*args, **kwargs)))

    def semantic_fixture(self, name, label):
        self.setup_evidence(fixture("upstream.py"), fixture(name), fixture("APACHE-2.0.txt"))
        ids = [] if label == "unclear" else [1]
        self.answers = [{"label": label, "line_ids": ids}] * 2

    def test_semantic_cases_and_independent_evaluation(self):
        cases = [
            ("pass.py", "acknowledges", "PASS", "change_acknowledged"),
            ("fail.py", "unchanged", "FAIL", "unchanged_claim_contradicted"),
            ("review.py", "unclear", "REVIEW", "notice_unclear"),
        ]
        for name, label, outcome, reason in cases:
            with self.subTest(fixture=name):
                self.semantic_fixture(name, label)
                self.prompts.clear()
                record = self.record(attempt=name.split(".")[0])
                self.assertEqual((record["outcome"], record["reason"]), (outcome, reason))
                self.assertEqual(record["header_range"], [1, 1])
                self.assertEqual(record["repository_attribution"], "unverified_caller_declaration")
                self.assertEqual(record["upstream"]["declared_repository"], UP)
                self.assertEqual(len(self.prompts), 2)
                self.assertEqual(self.prompts[0], self.prompts[1])
                self.assertNotIn("return int", self.prompts[0])
                self.assertEqual(record["evidence"]["downstream_source"]["sha256"],
                                 hashlib.sha256(fixture(name)).hexdigest())

    def test_hostile_header_stops_before_model(self):
        self.semantic_fixture("hostile.py", "acknowledges")
        self.assertEqual(self.record()["reason"], "header_directive")
        self.assertEqual(self.prompts, [])
        self.assertEqual(len(self.answers), 2)

    def test_checked_in_studio_sample_matches_real_git_objects(self):
        self.semantic_fixture("pass.py", "acknowledges")
        self.assertEqual(self.up_commit, "ab07629c95a4f81130b1aa13145b37091787c63f")
        self.assertEqual(self.down_commit, "c9fcf45fbb2b89dab8938cd7023579e4a7b3babc")
        sample = fixture("sample_proof.json").decode("ascii").rstrip("\n")
        self.assertEqual(sample, self.proof)
        self.assertEqual(self.record(proof=sample)["outcome"], "PASS")

    def test_mit_preservation_mismatch_and_partial(self):
        source = fixture("upstream.py")
        original = mit_notice(b"Upstream Author")
        for index, (evidence, outcome) in enumerate([
            (original, "PASS"), (mit_notice(b"Other Author"), "FAIL"),
            (original[:100], "REVIEW"),
        ]):
            self.setup_evidence(source, source, original, evidence)
            self.assertEqual(self.record(contract.MIT, str(index))["outcome"], outcome)
        self.assertEqual(self.prompts, [])

    def test_apache_complete_copy_and_replacement(self):
        source = fixture("upstream.py")
        license_text = fixture("APACHE-2.0.txt")
        for index, (evidence, outcome) in enumerate([
            (license_text, "PASS"), (mit_notice(b"Other Author"), "FAIL"),
            (license_text[:-100], "REVIEW"),
        ]):
            self.setup_evidence(source, source, license_text, evidence)
            self.assertEqual(self.record(contract.APACHE_COPY, str(index))["outcome"], outcome)
            if outcome == "PASS":
                self.assertGreater(self.raw_size, 2 * len(license_text))
                self.assertLessEqual(self.raw_size, contract.MAX_PROOF)
                self.assertLessEqual(len(self.proof), contract.MAX_PROOF_JSON)
        self.assertEqual(self.prompts, [])

    def test_header_only_or_line_ending_changes_do_not_call_model(self):
        source = fixture("upstream.py")
        downstream = b"# We changed this file.\r\n\r\n" + source.replace(b"\n", b"\r\n")
        self.setup_evidence(source, downstream, fixture("APACHE-2.0.txt"))
        self.assertEqual(self.record()["reason"], "source_body_unchanged")
        self.assertEqual(self.prompts, [])

    def test_labels_can_disagree_without_storing_review(self):
        self.semantic_fixture("pass.py", "acknowledges")
        self.answers[1] = {"label": "unclear", "line_ids": []}
        with self.assertRaises(Disagreement):
            self.assess()
        self.assertEqual(self.instance.records, {})

    def test_forged_leader_evidence_is_rejected(self):
        self.semantic_fixture("pass.py", "acknowledges")

        def edit(proposed):
            result = json.loads(proposed)
            result["evidence"]["downstream_source"]["sha256"] = "0" * 64
            return contract._canonical(result)

        self.proposal_edit = edit
        with self.assertRaises(Disagreement):
            self.assess()
        self.assertEqual(self.instance.records, {})

    def test_bad_model_schema_cannot_write(self):
        self.semantic_fixture("pass.py", "acknowledges")
        self.answers[0] = {"label": "acknowledges", "line_ids": [True]}
        with self.assertRaises(UserError):
            self.assess()
        self.assertFalse(self.instance.records)

    def test_different_supporting_lines_can_agree(self):
        upstream = fixture("upstream.py")
        downstream = b"# We revised this file.\n" + fixture("pass.py")
        self.setup_evidence(upstream, downstream, fixture("APACHE-2.0.txt"))
        self.answers = [
            {"label": "acknowledges", "line_ids": [1]},
            {"label": "acknowledges", "line_ids": [2]},
        ]
        record = self.record()
        self.assertEqual(record["outcome"], "PASS")
        self.assertEqual(record["header_range"], [1, 2])

    def test_inherited_citation_cannot_establish_a_downstream_change(self):
        notice = b"# We adapted this file for offline use.\n"
        self.setup_evidence(
            notice + fixture("upstream.py"),
            notice + b"# Parser module.\n" + b"def parse_timestamp(value):\n    return int(value.strip())\n",
            fixture("APACHE-2.0.txt"),
        )
        self.answers = [{"label": "acknowledges", "line_ids": [1]}] * 2
        self.assertEqual(self.record()["outcome"], "REVIEW")

    def test_duplicate_record_rejected_and_retry_distinct(self):
        self.semantic_fixture("pass.py", "acknowledges")
        first = self.assess()
        with self.assertRaises(UserError):
            self.assess()
        self.semantic_fixture("pass.py", "acknowledges")
        second = self.assess(attempt="retry")
        self.assertNotEqual(first, second)
        self.assertEqual(len(self.instance.records), 2)

    def test_invalid_input_cannot_write(self):
        for args in (
            {"upstream_repo": "https://attacker.invalid/owner/repo"}, {"upstream_commit": "main"},
            {"upstream_repo": "owner/.."}, {"downstream_path": "../component.py"},
            {"declared_redistribution": False},
        ):
            with self.subTest(args=args), self.assertRaises(UserError):
                self.assess(**args)
        self.assertEqual(self.instance.records, {})
        self.assertEqual(self.prompts, [])

    def test_wrong_declared_sha_is_rejected(self):
        self.semantic_fixture("pass.py", "acknowledges")
        self.assert_proof_rejected("Git commit ID", upstream_commit=self.down_commit)

    def test_substituted_tree_is_rejected(self):
        self.semantic_fixture("pass.py", "acknowledges")
        raw = git(self.repo_path, "cat-file", "tree", f"{self.up_commit}^{{tree}}")
        self.replace_object("downstream", "tree", raw)
        self.assert_proof_rejected("Git tree ID")

    def test_substituted_blob_is_rejected(self):
        self.semantic_fixture("pass.py", "acknowledges")
        raw = git(self.repo_path, "cat-file", "blob", f"{self.up_commit}:component.py")
        self.replace_object("downstream", "source", raw)
        self.assert_proof_rejected("Git blob ID")

    def test_hash_matching_duplicate_truncated_and_unsupported_tree_entries(self):
        self.semantic_fixture("pass.py", "acknowledges")
        raw = git(self.repo_path, "cat-file", "tree", f"{self.down_commit}^{{tree}}")
        for modified, message in (
            (raw + raw, "duplicate Git tree"),
            (raw[:-1], "Truncated"),
            (raw.replace(b"100644", b"120000", 1), "unsupported Git file mode"),
            (raw.replace(b"100644", b"100664", 1), "Invalid or duplicate"),
        ):
            with self.subTest(message=message):
                self.replace_tree_and_commit(modified)
                self.assert_proof_rejected(message)

    def test_hash_matching_malformed_commit_is_rejected(self):
        self.semantic_fixture("pass.py", "acknowledges")
        raw = git(self.repo_path, "cat-file", "commit", self.down_commit)
        tree = raw.split(b"\n", 1)[0]
        malformed = tree + b"\n" + raw
        self.down_commit = write_object(self.repo_path, "commit", malformed)
        self.replace_object("downstream", "commit", malformed)
        self.assert_proof_rejected("Malformed Git commit header")

    def test_oversized_or_malformed_proof_is_rejected(self):
        self.semantic_fixture("pass.py", "acknowledges")
        for proof, error in (
            (" " * (contract.MAX_PROOF_JSON + 1), "Proof JSON exceeds"),
            ('{"version":"git-sha1/1","version":"git-sha1/1"}', "Malformed proof JSON"),
            (self.proof.replace('"git-sha1/1"', '"git-sha256/1"'), "Unsupported proof envelope"),
        ):
            with self.subTest(error=error):
                self.assert_proof_rejected(error, proof=proof)
        packet = json.loads(self.proof)
        packet["upstream"]["commit"] = "not base64"
        self.assert_proof_rejected("Invalid base64", proof=json.dumps(packet))
        self.replace_object("upstream", "commit", b"x" * (contract.MAX_COMMIT + 1))
        self.assert_proof_rejected("oversized")

    def test_total_decoded_cap_is_checked_before_hashing(self):
        self.semantic_fixture("pass.py", "acknowledges")
        for side in ("upstream", "downstream"):
            self.replace_object(side, "source", b"x" * (11 * 1024))
        self.assertLess(len(self.proof), contract.MAX_PROOF_JSON)
        self.assert_proof_rejected("Decoded proof exceeds")

    def test_lfs_non_utf8_and_binary_evidence_do_not_reach_model(self):
        self.semantic_fixture("pass.py", "acknowledges")
        for data, error in (
            (b"version https://git-lfs.github.com/spec/v1\noid sha256:abc\n", "Git LFS"),
            (b"\xff" * 12, "not UTF-8"),
            (b"# comment\n\x00", "Binary or hidden"),
        ):
            self.down_commit = write_snapshot(self.repo_path, {"component.py": ("100644", data)}, "bad text")
            tree = git(self.repo_path, "cat-file", "tree", f"{self.down_commit}^{{tree}}")
            self.replace_object("downstream", "commit", git(self.repo_path, "cat-file", "commit", self.down_commit))
            self.replace_object("downstream", "tree", tree)
            self.replace_object("downstream", "source", data)
            self.assert_proof_rejected(error)


if __name__ == "__main__":
    unittest.main()
