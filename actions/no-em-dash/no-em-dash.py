#!/usr/bin/env python3
"""Fail if any tracked file contains an em-dash (U+2014) or en-dash (U+2013).

These read as an authoring "tell" and complicate diffs and greps; use ASCII
'-' (or '--') instead. Paths whose prefix is listed in $SKIP_PREFIXES
(whitespace separated) are exempt -- for verbatim files like licenses or
fixtures. The chars are referenced by codepoint so this script stays
ASCII-clean and does not trip its own gate.
"""
import os
import subprocess
import sys

em, en = chr(0x2014), chr(0x2013)
skip = tuple(os.environ.get("SKIP_PREFIXES", "").split())
files = subprocess.check_output(["git", "ls-files"]).decode().splitlines()

bad = []
for f in files:
    if skip and f.startswith(skip):
        continue
    try:
        text = open(f, encoding="utf-8").read()
    except (UnicodeDecodeError, IsADirectoryError):
        continue
    for n, line in enumerate(text.splitlines(), 1):
        if em in line or en in line:
            bad.append(f"{f}:{n}: {line.strip()[:100]}")

if bad:
    print("Em-dash or en-dash found; use ASCII '-' instead:\n")
    print("\n".join(bad))
    sys.exit(1)
print("clean: no em-dashes or en-dashes")
