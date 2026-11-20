# Technical details — HR M03 EQ2 (`A5G_BY_G23_M03_EQ2_012_20250715`)

## Source package

| Field | Value |
|---|---|
| Official files | `A5G_BY_G23_M03_EQ2_012_20250715_{L,R}_FotaPackage_20250717*.bin` (L and R are byte-identical) |
| Original size | 1,055,011 bytes |
| Original SHA-256 | `488f6fdbd1866998db073007aa5ef2dd981b53dd8ec37e4e47c1784ce42d5821` |
| Source | BullSuper OTA endpoint: `GET http://43.138.251.38/upgrade?deviceType=A5G_BY_G23_M03_EQ2&gray=` |
| Container | Airoha FOTA (LZMA payload + SHA-256 package/section integrity hashes, no signature) |
| Section layout | 4 sections identical to M03 ST: `0x14000` (4096 B), `0x15000` (1,400,832 B), `0x19b000` (45,056 B), `0x1a6000` (638,976 B) |
| Uncompressed payload size | 2,088,960 bytes |
| Uncompressed original payload SHA-256 | `d7bf7992ce352ed83e6e003d02287ec860f128b613061ebe8eb0662683cc5c98` |

## Firmware analysis and patch

The negotiation validation function from HR+ V007 (`0x6b01c`) and HR M03 ST V012 (`0x6b00c`) is present in `A5G_BY_G23_M03_EQ2_012_20250715` at uncompressed payload offset **`0x69144`**, with the 37-byte validation block at **`0x691f8`** (7,696 bytes earlier than M03 ST).

Instruction-by-instruction comparison across the entire `0x115`-byte function (`entry` through `retw.n`):

- **Zero unexpected instruction differences.**
- All differences outside the 5 unreachable bytes after an unconditional `j` (`0xf7..0xfb`) are standard PC-relative relocations due to the shifted code offset:
  - 9 `l32r` literal-pool immediates (`0x12`, `0x15`, `0x18`, `0x74`, `0x8f`, `0xae`, `0xd3`, `0x103`, `0x10b`); the log-function loads at `0x74`, `0x8f`, `0xae`, `0xd3`, and `0x103` all resolve to the same log pointer `0x280ffa30`.
  - 2 `call8` targets (`0x0d`, `0xe2`), shifted uniformly.
- Inside the **37-byte check block** at `0x691f8..0x6921d`, all 37 bytes are **byte-for-byte identical to M03 ST** (and 35/37 bytes identical to HR+ V007, differing only at byte `0x20` = the `l32r` immediate for the debug-log call replaced by `j` + `nop.n`).
- Every instruction in the replacement block (`562c00b0b064c79b2b3841c600003df03df0`) is strictly position-independent:
  - `bne` at block `+0x19` branches to `+0x48` (`fn+0xfc` = `0x69240`), matching the original `bne` target.
  - `j` at block `+0x1e` branches to `+0x25` (`0x6921d`, exact end of the 37-byte block).

```text
offset 0x691f8 (uncompressed payload)
original  a86182040192040437983ca79939c851b20405c79b310c0ab1ccff38410c0c818a5de00800
patched   a86182040192040437983ca79939c851b20405562c00b0b064c79b2b3841c600003df03df0
```

After patching and rebuilding the Airoha FOTA container:
- Exactly **18 bytes** differ in the uncompressed payload (`0x6920b..0x6921c`).
- Sections 0, 2, and 3 remain byte-identical with unchanged hashes; only section 1's SHA-256 and the package SHA-256 update.
- Round-trip decompression matches the patched payload byte-for-byte.

| Field | Value |
|---|---|
| Patched package size | 1,054,442 bytes (`0x1016ea`) |
| Patched package SHA-256 | `324dd70fa0db8717363c2be138fe019f4ecb0786addbb44aa20d2991c4ebf43e` |

## APK changes vs Issue #2 (`HR-M03-iOS27-patch.apk`)

Rebuilt with `apktool 3.0.3` (`-r`, keeping raw resources untouched) and signed/zipaligned with `uber-apk-signer 1.3.0` (debug key, v1/v2/v3 verified):

- Only `smali_classes20/local/hrpatch/Guard.smali` and `assets/hrpatch/{left,right}.bin` were modified:
  - Accepted profile locked strictly to `A5G_BY_G23_M03_EQ2_012_20250715_L`.
  - Expected file length set to `1054442` (`0x1016ea`) and SHA-256 set to `324dd70fa0db8717363c2be138fe019f4ecb0786addbb44aa20d2991c4ebf43e`.
  - Local extraction folder set to `hr-ios27-eq2-v1`.
  - Bundled `left.bin` and `right.bin` replaced with `HR_M03_EQ2_V012_iOS27_{left,right}.bin`.
- Final APK SHA-256: `7e8dc82c0fa77a9ff769ab597b5dfb0252c5cfcb6a77be7a7024849f041736f2` (`14,603,048` bytes).
- Note: because `-r` preserves `resources.arsc`, the top toolbar title still reads `HR M03 iOS27 patch`, while all `Guard` status/confirmation/mismatch messages explicitly identify `HR M03 EQ2 V012`.
