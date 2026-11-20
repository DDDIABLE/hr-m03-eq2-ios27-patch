#!/usr/bin/env python3
"""
Port the HR+ V5.3 iOS 27 negotiation patch (Niaktou/hrplus-ios27-patch)
to Airoha AB1562AE HR M03 EQ2 (profile A5G_BY_G23_M03_EQ2_012_20250715).

Offline only: does not connect to any device and does not flash anything.
1. Validates the official Airoha FOTA container (package and section SHA-256).
2. Unpacks the LZMA payload.
3. Locates the exact 0x115-byte negotiation validation function, allowing only
   expected PC-relative L32R literal-pool immediates, CALL8 offsets, and the
   5 unreachable bytes after an unconditional jump (0xf7..0xfb).
4. Verifies the 37-byte check block matches byte-for-byte outside the debug-log
   L32R immediate (bytes 0x20..0x21), replaces it with the position-independent
   18-byte patch accepting {0x00, 0x80} when expected_byte5 == 0, rebuilds the
   container + SHA-256 integrity hashes, and verifies round-trip unpacking.

Usage:
  python3 hr_ios27_port_eq2.py left.bin right.bin --out out_dir
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from airoha.container import FirmwareError, Package, read_limited  # noqa: E402

ORIGINAL = bytes.fromhex(
    "a86182040192040437983ca79939c851b20405c79b310c0ab1ccff38410c0c81895de00800"
)
PATCHED = bytes.fromhex(
    "a86182040192040437983ca79939c851b20405562c00b0b064c79b2b3841c600003df03df0"
)
CTX_BEFORE = bytes.fromhex(
    "368100ad422aaaa2daffa20afba506eb0c1ec135a94136a9812fa9a9410ca30c0a7d0382"
    "0800d20402920404b20c00620c04520c02f20403c20c03420400808e93803b9380e5930c"
    "0b8074934d0b5d0480b693b951805f931c96806d93fd04dd0380499380fc93f961cd42b9"
    "01c971b1e0ff0c4c81a15de0080070d07460e07450f0740c0ab1dbff0c4c4090749901819"
    "a5de008004871b1d8ff0c4c2a44f20404e20403d20401a20405a9010c0a81925de00800"
)
CTX_AFTER = bytes.fromhex(
    "a203040c0b0c6cdd02a555eaad422aaaa20a00bd02a0a00425eaff46060000507605060c"
    "0ab1feff0c0c817d5de00800ad02817c5de008000c021df000000090"
)

_REF = CTX_BEFORE + ORIGINAL + CTX_AFTER
_L32R_AT = [0x12, 0x15, 0x18, 0x74, 0x8F, 0xAE, 0xD3, 0x103, 0x10B]
_CALL8_AT = [0x0D, 0xE2]
_CHECK_END = 0x115  # up to and including retw.n
_IGNORE = (
    {o + k for o in _L32R_AT for k in (1, 2)}
    | {o + k for o in _CALL8_AT for k in (0, 1, 2)}
    | set(range(0xF7, 0xFC))
)

assert len(ORIGINAL) == len(PATCHED) == 37
assert sum(a != b for a, b in zip(ORIGINAL, PATCHED)) == 18
assert all((_REF[o] & 0xF) == 1 for o in _L32R_AT)
assert all((_REF[o] & 0x3F) == 0x25 for o in _CALL8_AT)


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def find_all(hay: bytes, needle: bytes) -> list[int]:
    out, i = [], hay.find(needle)
    while i != -1:
        out.append(i)
        i = hay.find(needle, i + 1)
    return out


def find_relocated(payload: bytes) -> list[int]:
    hits = []
    # Match the first 12 bytes (before the first CALL8 at 0x0d)
    for start in find_all(payload, CTX_BEFORE[:12]):
        win = payload[start : start + _CHECK_END]
        if len(win) < _CHECK_END:
            continue
        if not all(win[i] == _REF[i] for i in range(_CHECK_END) if i not in _IGNORE):
            continue
        if not all((win[o] & 0xF) == 1 for o in _L32R_AT):
            continue
        if not all((win[o] & 0x3F) == 0x25 for o in _CALL8_AT):
            continue
        hits.append(start + len(CTX_BEFORE))
    return hits


def patch_one(path: Path) -> tuple[bytes, dict]:
    data = read_limited(path)
    pkg = Package(data, path.name)
    info = pkg.info()
    payload = pkg.unpack()

    hits = find_relocated(payload)
    if len(hits) != 1:
        raise FirmwareError(f"Expected 1 relocated function match, found {len(hits)}: {[hex(h) for h in hits]}")

    off = hits[0]
    blk = payload[off : off + 37]
    if not all(blk[i] == ORIGINAL[i] for i in range(37) if i not in (0x20, 0x21)):
        raise FirmwareError(f"37-byte check block at {hex(off)} did not match expected bytes")

    new_payload = bytearray(payload)
    new_payload[off : off + 37] = PATCHED
    new_payload_b = bytes(new_payload)

    diffs = [i for i in range(len(payload)) if payload[i] != new_payload_b[i]]
    assert len(diffs) == 18 and min(diffs) == off + 0x13 and max(diffs) == off + 0x24

    rebuilt = pkg.rebuild(new_payload_b)
    verify_pkg = Package(rebuilt, "verify")
    assert verify_pkg.unpack() == new_payload_b

    report = {
        "input_file": path.name,
        "input_size": len(data),
        "input_sha256": sha256(data),
        "input_payload_sha256": sha256(payload),
        "function_offset": hex(off - len(CTX_BEFORE)),
        "patch_block_offset": hex(off),
        "bytes_changed": len(diffs),
        "output_size": len(rebuilt),
        "output_sha256": sha256(rebuilt),
        "output_payload_sha256": sha256(new_payload_b),
        "sections": [(hex(s["payload_offset"]), hex(s["length"]), hex(s["destination"])) for s in info["sections"]],
    }
    return rebuilt, report


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("left", type=Path)
    ap.add_argument("right", type=Path)
    ap.add_argument("--out", type=Path, default=Path("out"))
    args = ap.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    reports = {}
    sums = []
    for side, src in (("left", args.left), ("right", args.right)):
        rebuilt, rep = patch_one(src)
        name = f"HR_M03_EQ2_V012_iOS27_{side}.bin"
        dst = args.out / name
        dst.write_bytes(rebuilt)
        reports[side] = rep
        sums.append(f"{rep['output_sha256']}  {name}")
        print(f"[{side}] OK @ {rep['patch_block_offset']} -> {dst} ({rep['output_size']} bytes, sha256={rep['output_sha256']})")

    (args.out / "SHA256SUMS.txt").write_text("\n".join(sums) + "\n")
    (args.out / "report.json").write_text(json.dumps(reports, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
