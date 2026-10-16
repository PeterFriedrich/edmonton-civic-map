"""Refresh guard: a passing refresh may change dates, and addresses, nothing else.

Runs in .github/workflows/refresh.yml after the rebuild is copied into
site/public/data and before anything is committed. It checks the working tree
against HEAD, independently of src/diff_check.py:

  - officeholders.json: only `last_verified` may differ;
  - layers.json: only `last_verified`, `source_sha256` and `addresses_checked`;
  - addresses/: street files, streets.json and manifest.txt may change (new
    addresses pass, docs/SPEC_data_schema.md §9.6 point 2);
  - any other change, anywhere in the repo, fails.

So a boundary file that moved by less than the diff check's geometry threshold
still holds the run for a person.

Exit codes: 0 ok; 6 something else changed.

    python scripts/check_refresh_diff.py [--root /path/to/checkout]
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

DATA = "site/public/data"
MAY_CHANGE = {
    f"{DATA}/officeholders.json": ("seat_id", {"last_verified"}),
    f"{DATA}/layers.json": ("id", {"last_verified", "source_sha256", "addresses_checked"}),
}


def _git(root, *args):
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=True).stdout


def changed_paths(root):
    """Modified, deleted and untracked paths relative to HEAD."""
    tracked = _git(root, "diff", "--name-only", "HEAD", "--").splitlines()
    untracked = _git(root, "ls-files", "--others", "--exclude-standard").splitlines()
    return sorted(set(tracked) | set(untracked))


def _records_problems(path, old, new, key, allowed):
    old, new = {r[key]: r for r in old}, {r[key]: r for r in new}
    if old.keys() != new.keys():
        return [f"{path}: records added or removed: {sorted(old.keys() ^ new.keys())}"]
    out = []
    for k in old:
        for f in sorted((old[k].keys() | new[k].keys()) - allowed):
            if old[k].get(f) != new[k].get(f):
                out.append(f"{path}: {k}: {f} changed")
    return out


def problems(root):
    out = []
    for path in changed_paths(root):
        if path in MAY_CHANGE:
            key, allowed = MAY_CHANGE[path]
            try:
                old = json.loads(_git(root, "show", f"HEAD:{path}"))
                new = json.loads((root / path).read_text(encoding="utf-8"))
            except (subprocess.CalledProcessError, FileNotFoundError, json.JSONDecodeError) as e:
                out.append(f"{path}: cannot compare: {e}")
                continue
            out += _records_problems(path, old, new, key, allowed)
        elif path.startswith(f"{DATA}/addresses/") and path.count("/") == 4 and path.endswith((".json", ".txt")):
            continue
        else:
            out.append(f"{path}: may not change in a passing refresh")
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = ap.parse_args(argv)
    found = problems(args.root)
    if found:
        print("FAIL  the refresh changed more than dates and addresses:")
        for p in found:
            print("  " + p)
        return 6
    print("OK  the refresh changed only dates and addresses")
    return 0


if __name__ == "__main__":
    sys.exit(main())
