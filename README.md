# AirReps HR M03 EQ2 (`A5G_BY_G23_M03_EQ2`) — unofficial iOS 27 patch

Port of [Niaktou/hrplus-ios27-patch](https://github.com/Niaktou/hrplus-ios27-patch) (HR+ V007) and [Issue #2](https://github.com/Niaktou/hrplus-ios27-patch/issues/2) (HR M03 ST V012) to the **HR M03 EQ2** firmware profile `A5G_BY_G23_M03_EQ2_012_20250715_L` (commonly sold as AirPods Pro 2 3.0 Guangmang Yuedong / 公牛 HR M03 EQ2, Airoha AB1562AE).

> **Experimental. Tested on one pair.** Flashing firmware can brick your earbuds and recovery is not guaranteed. Use at your own risk.

## Tested

| | |
|---|---|
| Earbuds | HR M03 EQ2 (sold domestically as AirPods Pro 2 3.0 Guangmang Yuedong / 公牛 HR M03 EQ2, Airoha AB1562AE) |
| Profile before & after update | `A5G_BY_G23_M03_EQ2_012_20250715_L` (displays `V12`) |
| Base firmware | Official `A5G_BY_G23_M03_EQ2_012_20250715` + 18-byte iOS 27 negotiation patch |
| Phone & OS | **iPhone 17 / iOS 27.1** — pairing, dual-earbud playback, ANC/transparency, and calls confirmed working |
| Flashed from | Android, using `apk/HR-M03-EQ2-iOS27-patch.apk` |

## Downloads

Choose **one** option from the [v0.1.0 Release](https://github.com/DDDIABLE/hr-m03-eq2-ios27-patch/releases/tag/v0.1.0):

- **Android installer (recommended):** `HR-M03-EQ2-iOS27-patch.apk` (already bundles both patched `.bin` files + strict identity/hash guard)
- **Standalone firmware only:** `firmware/HR_M03_EQ2_V012_iOS27_left.bin` and `firmware/HR_M03_EQ2_V012_iOS27_right.bin`
- **Complete bundle:** `HR-M03-EQ2-iOS27-patch-release.zip`

## Compatibility

The bundled APK **only** accepts this exact device profile:
- `A5G_BY_G23_M03_EQ2_012_20250715_L`

It refuses every other profile and displays the profile string reported by the connected earbuds. Do not bypass the identity check or flash this package onto `M05` (HR+) or `M03_ST` units.

## Contents

```text
apk/HR-M03-EQ2-iOS27-patch.apk          Modified BullSuper-based installer locked to M03 EQ2 V012
firmware/HR_M03_EQ2_V012_iOS27_left.bin
firmware/HR_M03_EQ2_V012_iOS27_right.bin
docs/PATCH.md                           Technical details and relocation verification
tools/hr_ios27_port_eq2.py              Offline script reproducing the exact patched .bin files
tools/airoha/                           Airoha FOTA container tooling (PairBridge, MIT)
SHA256SUMS.txt
```

## Install (Android)

1. Uninstall any previous `com.hzm.contro.gearphone.hrpatch` test app (such as `HR+ iOS27 Test` or `HR M03 iOS27 patch`), since they share the same package name. Official BullSuper can stay installed, but force-stop it before flashing.
2. Disconnect/forget the earbuds on other multipoint devices (e.g. Mac/iPhone) so the Airoha SPP/FOTA channel is not occupied (otherwise FOTA may stall at 0% with `RESPONSE TIMEOUT`).
3. Install `apk/HR-M03-EQ2-iOS27-patch.apk` (debug-signed).
4. Take **both** earbuds out of the charging case (charged above 50% recommended), pair them in Android Bluetooth settings, connect them inside the app, and tap **Update → Earbud firmware → Verify patch** (read-only check; does not flash).
5. When it confirms *"HR M03 EQ2 (V012) confirmed"*, tap **Install patch**, confirm, and keep the screen awake and app open until both earbuds finish restarting and report success.
6. Disconnect from Android, forget any old Bluetooth entry on the iPhone, and pair fresh.

The firmware version still displays **V12**. Do not reflash a second time, and avoid running official BullSuper updates afterwards (which would overwrite the 18-byte patch).

## Reproduce it yourself

```sh
# Official vendor packages from BullSuper OTA server:
# GET http://43.138.251.38/upgrade?deviceType=A5G_BY_G23_M03_EQ2&gray=
python3 tools/hr_ios27_port_eq2.py <official_L.bin> <official_R.bin> --out out
# out/HR_M03_EQ2_V012_iOS27_{left,right}.bin must match SHA256SUMS.txt
```

## Credits

- Original HR+ V007 iOS 27 patch and guarded BullSuper installer: [Niaktou/hrplus-ios27-patch](https://github.com/Niaktou/hrplus-ios27-patch)
- HR M03 ST port and `hr_ios27_port.py` methodology: `NoRiCKaB3` ([Issue #2](https://github.com/Niaktou/hrplus-ios27-patch/issues/2))
- Airoha FOTA container tooling: [MattiaIppoliti/pairbridge](https://github.com/MattiaIppoliti/pairbridge) (MIT)
