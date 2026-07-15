"""Clear the executable-stack (RWE) bit on ctranslate2's shared library.

ctranslate2 (used by faster-whisper) ships a `libctranslate2*.so` whose
``GNU_STACK`` program header is marked executable (RWE). Some container kernels
refuse to enable an executable stack and abort loading the library with
``cannot enable executable stack as shared object requires: Invalid argument``.
This clears the execute bit so the live ASR engine loads on a CPU-only VPS.
"""

from __future__ import annotations

import glob
import struct


def main() -> None:
    pattern = (
        "/usr/local/lib/python3.12/site-packages/"
        "ctranslate2.libs/libctranslate2*.so*"
    )
    found = False
    for path in glob.glob(pattern):
        found = True
        with open(path, "rb") as f:
            data = bytearray(f.read())
        if data[:4] != b"\x7fELF":
            print("skip (not ELF):", path)
            continue
        e_phoff = struct.unpack_from("<Q", data, 0x20)[0]
        e_phentsize = struct.unpack_from("<H", data, 0x36)[0]
        e_phnum = struct.unpack_from("<H", data, 0x38)[0]
        patched = False
        for i in range(e_phnum):
            off = e_phoff + i * e_phentsize
            p_type = struct.unpack_from("<I", data, off)[0]
            if p_type == 0x6474E551:  # GNU_STACK
                p_flags = struct.unpack_from("<I", data, off + 4)[0]
                if p_flags & 1:
                    struct.pack_into("<I", data, off + 4, p_flags & ~1)
                    patched = True
        if patched:
            with open(path, "r+b") as f:
                f.write(data)
            print("cleared exec-stack on", path)
        else:
            print("already non-exec:", path)
    if not found:
        print("no ctranslate2 lib found at", pattern)


if __name__ == "__main__":
    main()
