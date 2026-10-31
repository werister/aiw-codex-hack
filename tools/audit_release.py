"""Scan tracked files and optionally reachable Git objects without printing values."""

import argparse
import json
import re
import subprocess
from pathlib import Path

PATTERNS = {
    "credential_shape": rb"(?:sk-[A-Za-z0-9_-]{20,}|AKIA[A-Z0-9]{16}|gh[pousr]_[A-Za-z0-9]{30,}|-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----)",
    "email": rb"[A-Za-z0-9_.+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
    "phone": rb"\+[1-9][0-9]{0,2}[ -](?:\(?[0-9]{2,4}\)?[ -]){2,4}[0-9]{3,}",
    "home_path": rb"(?:[A-Za-z]:[\\/]Users[\\/]|/Users/|/home/|/private/tmp/)",
    "private_host": rb"(?:[a-z0-9-]+\.ts\.net|https?://[a-z0-9.-]+\.(?:internal|lan|local)\b)",
    "private_link": rb"https?://[^\s\"<>]+\.chatgpt\.site",
}
COMPILED = {name: re.compile(pattern, re.I) for name, pattern in PATTERNS.items()}


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args])


def explanation(path, category, match):
    value = match.group().decode("ascii", errors="replace").lower()
    if path == "tools/audit_release.py":
        return "Scanner definitions intentionally include the patterns being checked."
    if category == "email" and value.endswith("@users.noreply.github.com"):
        return "Explicitly requested public commit identity."
    if category == "email" and path.endswith("verify_assets.py") and value.endswith("@v.co"):
        return "Matrix multiplication syntax in geometric verification, not an address."
    return None


def inspect(path, raw):
    found = []
    for category, pattern in COMPILED.items():
        matches = list(pattern.finditer(raw))
        if not matches:
            continue
        reasons = {explanation(path, category, match) for match in matches}
        found.append({"path": path, "category": category, "count": len(matches),
                      "explained": None not in reasons,
                      "reasons": sorted(reason for reason in reasons if reason)})
    return found


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", type=Path, default=Path.cwd())
    parser.add_argument("--git-history", action="store_true")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    paths = git(root, "ls-files", "-z").decode("utf-8").split("\0")
    findings = []
    count = 0
    for path in filter(None, paths):
        target = root / path
        if target.exists():
            findings.extend(inspect(path, target.read_bytes()))
            count += 1
    objects = 0
    if args.git_history:
        # Every reachable object is inspected through Git's decompression API.
        rows = git(root, "rev-list", "--objects", "--all").decode("utf-8").splitlines()
        for row in rows:
            oid, _, path = row.partition(" ")
            kind = git(root, "cat-file", "-t", oid).strip()
            if kind not in {b"blob", b"commit", b"tag"}:
                continue
            raw = git(root, "cat-file", "-p", oid)
            findings.extend(inspect(path or ".git/commit", raw))
            objects += 1
        for path in (root / ".git").rglob("*"):
            if path.is_file() and "objects" not in path.relative_to(root / ".git").parts and path.name != "index":
                findings.extend(inspect(path.relative_to(root).as_posix(), path.read_bytes()))
    result = {"tracked_files": count, "git_objects": objects,
              "findings": findings,
              "unexplained": sum(not item["explained"] for item in findings)}
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in result.items() if key != "findings"}))
    if result["unexplained"]:
        print(json.dumps([item for item in findings if not item["explained"]], indent=2))
    return int(result["unexplained"] > 0)


if __name__ == "__main__":
    raise SystemExit(main())
