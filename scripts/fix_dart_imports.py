#!/usr/bin/env python3
"""
Fix broken relative imports in the Flutter (Dart) mobile app.

Many files were generated with relative import paths that are off by one or
more directory levels (e.g. ``../../../core/...`` where ``../../../../core/...``
is required). This script resolves every project-relative import against the
actual file tree and rewrites any that don't point at a real file, choosing the
correct relative path to the intended target (matched by basename).

Only ``package:``-free, project-relative imports/exports are touched. Imports
that already resolve correctly are left untouched. Ambiguous basenames (more
than one candidate file) are reported and skipped rather than guessed.

Usage:
    python3 scripts/fix_dart_imports.py [--lib-dir mobile/lib] [--apply]

Without ``--apply`` the script runs in dry-run mode and only reports.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

# Matches: import '...';  export '...';  (single or double quotes)
_IMPORT_RE = re.compile(
    r"""^(?P<indent>\s*)(?P<kw>import|export)\s+(?P<q>['"])(?P<path>[^'"]+)(?P=q)(?P<rest>[^;]*);"""
)


def build_basename_index(lib_dir: Path) -> dict[str, list[Path]]:
    """Map each .dart basename to the list of absolute paths that have it."""
    index: dict[str, list[Path]] = defaultdict(list)
    for path in lib_dir.rglob("*.dart"):
        index[path.name].append(path.resolve())
    return index


def relpath_import(from_file: Path, to_file: Path) -> str:
    """Compute a Dart relative import path from one file to another."""
    rel = os.path.relpath(to_file, from_file.parent)
    rel = rel.replace(os.sep, "/")
    # Dart requires an explicit ./ prefix for same-dir imports
    if not rel.startswith("."):
        rel = "./" + rel
    return rel


def fix_file(
    dart_file: Path,
    basename_index: dict[str, list[Path]],
    lib_dir: Path,
) -> tuple[list[str], list[str], str]:
    """
    Resolve and fix imports in a single Dart file.

    Returns (fixed_log, skipped_log, new_content).
    """
    original = dart_file.read_text(encoding="utf-8")
    lines = original.splitlines(keepends=True)
    fixed: list[str] = []
    skipped: list[str] = []
    out_lines: list[str] = []

    for line in lines:
        m = _IMPORT_RE.match(line)
        if not m:
            out_lines.append(line)
            continue

        import_path = m.group("path")

        # Leave package:, dart:, and http(s) imports alone
        if ":" in import_path.split("/")[0]:
            out_lines.append(line)
            continue

        # Resolve the current target relative to this file's directory
        target = (dart_file.parent / import_path).resolve()
        if target.exists():
            out_lines.append(line)  # already correct
            continue

        # Broken: try to locate the intended file by basename
        basename = Path(import_path).name
        candidates = basename_index.get(basename, [])

        if len(candidates) == 1:
            correct_rel = relpath_import(dart_file, candidates[0])
            new_line = (
                f"{m.group('indent')}{m.group('kw')} "
                f"{m.group('q')}{correct_rel}{m.group('q')}{m.group('rest')};\n"
            )
            # Preserve trailing content after the semicolon (e.g. comments)
            tail = line[m.end():]
            new_line = new_line.rstrip("\n") + tail
            if not new_line.endswith("\n"):
                new_line += "\n"
            out_lines.append(new_line)
            rel_from = dart_file.relative_to(lib_dir.parent)
            fixed.append(f"  {rel_from}: '{import_path}' -> '{correct_rel}'")
        elif len(candidates) == 0:
            out_lines.append(line)
            rel_from = dart_file.relative_to(lib_dir.parent)
            skipped.append(f"  {rel_from}: '{import_path}' — NO target file found")
        else:
            out_lines.append(line)
            rel_from = dart_file.relative_to(lib_dir.parent)
            names = ", ".join(str(c.relative_to(lib_dir.parent)) for c in candidates)
            skipped.append(
                f"  {rel_from}: '{import_path}' — AMBIGUOUS ({names})"
            )

    return fixed, skipped, "".join(out_lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Fix broken Dart relative imports")
    parser.add_argument("--lib-dir", default="mobile/lib", help="Path to Flutter lib/ dir")
    parser.add_argument("--apply", action="store_true", help="Write changes (default: dry run)")
    args = parser.parse_args()

    lib_dir = Path(args.lib_dir).resolve()
    if not lib_dir.exists():
        print(f"ERROR: lib dir not found: {lib_dir}", file=sys.stderr)
        return 2

    basename_index = build_basename_index(lib_dir)

    all_fixed: list[str] = []
    all_skipped: list[str] = []
    changed_files = 0

    for dart_file in sorted(lib_dir.rglob("*.dart")):
        fixed, skipped, new_content = fix_file(dart_file, basename_index, lib_dir)
        if fixed:
            all_fixed.extend(fixed)
            if args.apply:
                dart_file.write_text(new_content, encoding="utf-8")
            changed_files += 1
        all_skipped.extend(skipped)

    print(f"{'APPLIED' if args.apply else 'DRY RUN'} — {len(all_fixed)} imports fixed "
          f"across {changed_files} files")
    if all_fixed:
        print("\nFixed:")
        print("\n".join(all_fixed))
    if all_skipped:
        print(f"\nSkipped/unresolved ({len(all_skipped)}):")
        print("\n".join(all_skipped))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
