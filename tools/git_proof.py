"""Export a CommitNotice proof from local SHA-1 Git object databases."""

import argparse
import base64
import json
import os
import re
import subprocess
import sys
import unicodedata


def git(repo, *args, data=None):
    env = dict(
        os.environ,
        GIT_NO_REPLACE_OBJECTS="1",
        GIT_NO_LAZY_FETCH="1",
        GIT_ALLOW_PROTOCOL="",
        GIT_TERMINAL_PROMPT="0",
    )
    return subprocess.run(
        ["git", "-C", str(repo), *args], input=data, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, env=env, check=True, timeout=10,
    ).stdout


def read_object(repo, kind, oid, limit):
    if git(repo, "cat-file", "-t", oid).strip() != kind.encode("ascii"):
        raise ValueError(f"{oid} is not a {kind}")
    size = int(git(repo, "cat-file", "-s", oid))
    if not 0 < size <= limit:
        raise ValueError(f"{kind} is empty or exceeds {limit} bytes")
    raw = git(repo, "cat-file", kind, oid)
    computed = git(repo, "hash-object", "-t", kind, "--stdin", data=raw).strip().decode("ascii")
    if len(raw) != size or computed != oid:
        raise ValueError(f"Raw {kind} does not match {oid}")
    return raw


def snapshot(repo, commit, paths):
    if not re.fullmatch(r"[0-9a-f]{40}", commit) or git(repo, "rev-parse", "--show-object-format") != b"sha1\n":
        raise ValueError("A local SHA-1 repository and a full lowercase commit SHA are required")
    if len(set(paths.values())) != len(paths) or any(
        not re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_.-]{0,95}", path) for path in paths.values()
    ):
        raise ValueError("Evidence paths must be distinct, simple root-level file names")
    raw_commit = read_object(repo, "commit", commit, 4096)
    tree = git(repo, "rev-parse", "--verify", f"{commit}^{{tree}}").strip().decode("ascii")
    if raw_commit.split(b"\n", 1)[0] != b"tree " + tree.encode("ascii"):
        raise ValueError("Commit tree pointer mismatch")
    raw_tree = read_object(repo, "tree", tree, 8192)
    objects = {"commit": raw_commit, "tree": raw_tree}
    members = {}
    previous = b""
    listing = git(repo, "ls-tree", "-z", tree)
    entries = listing[:-1].split(b"\0") if listing else []
    if len(entries) > 256:
        raise ValueError("Tree exceeds 256 entries")
    for entry in entries:
        metadata, name = entry.split(b"\t", 1)
        mode, kind, oid = metadata.split(b" ")
        key = name + (b"/" if mode == b"040000" else b"")
        if not name or name in (b".", b"..") or b"/" in name or name in members or key <= previous:
            raise ValueError("Invalid, duplicate, or unsorted tree path")
        if mode not in (b"100644", b"100755", b"040000", b"120000", b"160000"):
            raise ValueError("Unsupported tree mode")
        members[name] = (mode, kind, oid)
        previous = key
    for field, path in paths.items():
        mode, kind, oid = members.get(path.encode("ascii"), (b"", b"", b""))
        if mode not in (b"100644", b"100755") or kind != b"blob":
            raise ValueError(f"{path} is missing or is not a regular file")
        raw = read_object(repo, "blob", oid.decode("ascii"), 16384)
        text = raw.decode("utf-8")
        if text.lstrip().startswith("version https://git-lfs.github.com/spec/v1") or any(
            unicodedata.category(char) in ("Cc", "Cf", "Zl", "Zp") and char not in "\t\r\n"
            for char in text
        ):
            raise ValueError(f"{path} is a Git LFS pointer or contains binary or hidden characters")
        objects[field] = raw
    return objects


def make_proof(up_repo, up_commit, up_source, up_license, down_repo, down_commit, down_source, down_evidence=""):
    down_paths = {"source": down_source}
    if down_evidence:
        down_paths["evidence"] = down_evidence
    snapshots = {
        "upstream": snapshot(up_repo, up_commit, {"source": up_source, "license": up_license}),
        "downstream": snapshot(down_repo, down_commit, down_paths),
    }
    decoded = sum(len(raw) for objects in snapshots.values() for raw in objects.values())
    if decoded > 32768:
        raise ValueError("Proof exceeds 32768 decoded bytes")
    packet = {"version": "git-sha1/1"}
    for side, objects in snapshots.items():
        packet[side] = {field: base64.b64encode(raw).decode("ascii") for field, raw in objects.items()}
    proof = json.dumps(packet, separators=(",", ":"))
    if len(proof) > 49152:
        raise ValueError("Proof exceeds 49152 JSON bytes")
    return proof, decoded


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("up_repo")
    parser.add_argument("up_commit")
    parser.add_argument("up_source")
    parser.add_argument("up_license")
    parser.add_argument("down_repo")
    parser.add_argument("down_commit")
    parser.add_argument("down_source")
    parser.add_argument("--down-evidence", default="")
    args = parser.parse_args()
    try:
        proof, decoded = make_proof(**vars(args))
    except subprocess.CalledProcessError as error:
        parser.exit(1, f"Git could not read or verify the local objects: {error.stderr.decode(errors='replace').strip()}\n")
    except (OSError, ValueError, subprocess.TimeoutExpired) as error:
        parser.exit(1, f"{error}\n")
    print(f"Proof size: {decoded} decoded bytes, {len(proof)} JSON bytes", file=sys.stderr)
    print(proof)


if __name__ == "__main__":
    main()
