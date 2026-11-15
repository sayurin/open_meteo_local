"""Validate Conventional Commit subjects in a pull request."""

import argparse
import re
import subprocess
import sys

SUBJECT = re.compile(r"^[a-z][a-z0-9-]*(?:\([^()\r\n]+\))?!?: \S.*$")


def valid_subject(subject: str) -> bool:
    """Return whether a subject has a Conventional Commit header."""
    return SUBJECT.fullmatch(subject) is not None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("base")
    parser.add_argument("head")
    parser.add_argument("--title")
    args = parser.parse_args()
    subjects = subprocess.run(
        ["git", "log", "--format=%s", "--no-merges", f"{args.base}..{args.head}"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    if args.title is not None:
        subjects.append(args.title)
    invalid = [subject for subject in subjects if not valid_subject(subject)]
    for subject in invalid:
        print(f"Invalid Conventional Commit subject: {subject}", file=sys.stderr)
    return int(bool(invalid))


if __name__ == "__main__":
    raise SystemExit(main())
