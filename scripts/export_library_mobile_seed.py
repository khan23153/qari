#!/usr/bin/env python3
"""Write the offline library snapshot bundled in the APK.

    python scripts/export_library_mobile_seed.py

Regenerate after changing backend/core_api/app/library/data/*. The core API
test suite fails if mobile/assets/library/library_seed.json is stale.
"""

import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "backend" / "core_api"), str(ROOT / "backend")]

from app.library.mobile_export import build_mobile_seed  # noqa: E402
from app.library.service import LibraryService  # noqa: E402

OUT = ROOT / "mobile" / "assets" / "library" / "library_seed.json"


def main() -> None:
    seed = asyncio.run(build_mobile_seed(LibraryService.from_bundled_data()))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(seed, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size // 1024} KiB): "
          f"{len(seed['collections'])} collections, {len(seed['hadiths'])} hadith, "
          f"{len(seed['narrators'])} narrators, {len(seed['gharib'])} gharib")


if __name__ == "__main__":
    main()
