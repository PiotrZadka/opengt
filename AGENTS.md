# AGENTS.md — navigation index for this repository

## Purpose

Software-only reverse engineering and experimentation on the first-generation HUAWEI
WATCH GT (model FTN-B19, platform codename "Fortuna"). The project documents the BLE
transport (LPv2), GATT surface, OTA/server side, firmware formats, and known hardware.
Its practical goal is to explore a more open/custom companion and display experience and,
if a reproducible software-only entry point is found, eventual native-code or
custom-firmware research.

The single available watch is an explicitly designated **throwaway research unit**. There
is no separate primary/donor distinction. Loss of user data or a software brick is an
accepted project risk only for actions explicitly allowed below; this does not implicitly
authorize every destructive experiment.

## SAFETY BOUNDARY — read before any work, applies to every task

### Allowed without another project-scope decision

- Passive scanning, read-only GATT observation, notification subscription, capture
  analysis, APK/source research, and offline parsing.
- Pairing/authentication with Huawei Health or Gadgetbridge.
- Well-formed, documented BLE operations whose semantics are established from Huawei
  Health, Gadgetbridge, or an independently reviewed capture. Initially this is limited
  to capability/service queries, ordinary notification and weather synchronization, and
  stock-format watchface listing/install/delete operations.
- Development of companion software, protocol tooling, watchfaces, parsers, emulators,
  and firmware-analysis tooling. Active tooling must make the selected service, command,
  and user-visible purpose explicit; it must not expose a generic "send arbitrary bytes"
  path as a normal workflow.
- Downloads of public firmware/documents for **static analysis**. Preserve provenance and
  hashes, and never execute unknown host binaries.

### Requires a separate explicit decision before each new class of experiment

- OTA transfer, firmware flashing, bootloader/recovery operations, factory reset,
  persistent system modification, downgrade/rollback attempts, or erase operations.
- Unknown, malformed, guessed, or deliberately boundary-violating BLE payloads; blind
  replay; fuzzing; exploit payloads; parser-crash testing; or attempts at native code
  execution on the watch.
- Extending the current tooling from reviewed stock operations into generic raw transport,
  auth/crypto experimentation, OTA, or exploit delivery.

### Out of scope

- Opening the watch, removing the screen/back, probing pads, SWD/JTAG/UART/BOOT0 access,
  electrical measurements, chip-off work, or any other hardware/debug intervention.
- Executing downloaded firmware utilities or other untrusted binaries on the host.

The stock boot chain must be treated as signed/protected until proven otherwise. A
throwaway designation is not evidence of a recovery path: before any separately approved
persistent modification, preserve all obtainable stock artifacts and document the expected
failure and recovery behavior.

## How to use this index

Read **only** the file(s) matching your task, not the whole repo. Research files record
evidence; `captures/` hold raw observations; the OpenGT builder/synchronizer are active
prototype code; the LPv2 codec and BLE observer remain frozen research tooling.

## File map

| Path | Contents | Read when... |
| --- | --- | --- |
| `research/ftn-b19-custom-firmware-gap-analysis.md` | Master report: hardware, security, boot chain, all gaps (#1–#18), evidence labels, source register | Any firmware/security/hardware question — start here |
| `research/ftn-b19-firmware-sources-and-ota-server.md` | Firmware package inventory (mirrors, 4 known FTN-B19 files), Huawei Health OTA server flow (endpoint `query.hicloud.com/accessory/v2/checkEx.action`, request/response JSON, product UUID map), `.bin.apk` container format, new hardware evidence, open leads | Any task about firmware packages, OTA server, file formats, or "where to find X" |
| `research/codex-watchface-feasibility.md` | GT1 stock watchface install/data-binding gate, same-face dynamic-value proof, exact Codex quota source | Any task about showing Codex quota on GT1 or changing custom-watchface data without reinstalling |
| `src/opengt_watchface/builder.py` | Reproducible GT1 resource, protobuf payload, preview, BIN, and HWT builder | Changing the OpenGT layout, bindings, or package |
| `scripts/opengt-sync` | Codex app-server quota reader and reviewed Gadgetbridge weather broadcast | Changing or running quota synchronization |
| `watchfaces/OpenGT/` | Minimal seed payload, generated resources, preview, BIN, and HWT | Installing or inspecting the OpenGT watchface |
| `research/huawei-uuid-protocol.md` | UUID inventory: FE86/FE01/FE02/FE03/FE04/3802/4A02 vs Gadgetbridge and `zyv`/`psolyca` huawei-lpv2 sources | BLE protocol/GATT work, UUID questions |
| `docs/hardware-and-ble-baseline.md` | Environment (macOS/Bleak), observed advertisement, GATT map with handles, what was/wasn't read | BLE capture/observation tasks, device identity questions |
| `docs/lpv2-codec.md` | LPv2 framing/TLV/slicing field map, public test vector | Codec work, decoding captured frames |
| `src/huawei_lpv2/codec.py` | LPv2 framing/TLV/slicing codec (frozen research tooling; no auth/crypto by design) | Codec implementation questions |
| `scripts/ble_observe.py` | Read-only scanner + GATT observer (macOS CoreBluetooth via bleak) | Passive work touching the live watch |
| `tests/test_lpv2_codec.py` | Offline codec tests incl. public test frame | After any codec change |
| `tests/test_opengt_watchface.py` | Ring geometry, GT1 binding, payload, and HWT regression tests | After any OpenGT builder or binding change |
| `captures/gatt-*.json`, `captures/physical-validation-*/` | Reviewed GATT and live watchface/weather observations | Corroborating observations; treat as evidence, not truth |
| `pyproject.toml`, `requirements.txt`, `pyrightconfig.json` | Python 3.9 / bleak / Pillow / ruff configuration | Environment setup |

## Task → starting file

| Task | Start with | Then |
| --- | --- | --- |
| "Is there a custom firmware / RCE / bootloader path?" | `research/ftn-b19-custom-firmware-gap-analysis.md` (gaps #7–#13, Direct answers A–E) | Apply the software-only and no-opening boundary above |
| "Display Codex quota without firmware" | `research/codex-watchface-feasibility.md` | Then `src/opengt_watchface/builder.py` + `scripts/opengt-sync` |
| "Find firmware / OTA packages / filelist.xml" | `research/ftn-b19-firmware-sources-and-ota-server.md` §1, §3, §6 | kurdishfirmware links, XDA leads |
| "How does the OTA update work server-side?" | `research/ftn-b19-firmware-sources-and-ota-server.md` §2 | APK at `/tmp/health_16.1.5.320.apk` (SHA-256 `fe5a89bc…518bb`) |
| "Decode captured BLE frames / LPv2" | `docs/lpv2-codec.md` + `src/huawei_lpv2/codec.py` | `tests/test_lpv2_codec.py` |
| "What BLE services/chars does the watch expose?" | `docs/hardware-and-ble-baseline.md` + `research/huawei-uuid-protocol.md` | `captures/gatt-20260808T192145Z.json` |
| "Which MCU / sensors / display?" | gap analysis §STRONG EVIDENCE (tables) + firmware-sources §4 | FCC QISFTN-B19, Sohu teardown (S3) |
| "New research — where do I write it?" | Create `research/<topic>.md` following the gap-analysis style (evidence labels CONFIRMED/STRONG EVIDENCE/HYPOTHESIS/UNKNOWN + source register) | Then register it in this table |

## Commands

```sh
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
PYTHONPATH=src .venv/bin/python scripts/build_opengt_watchface.py
./scripts/opengt-sync
PYTHONPATH=src .venv/bin/python scripts/ble_observe.py --scan-seconds 20
PYTHONPATH=src .venv/bin/python scripts/ble_observe.py --scan-seconds 30 --connect
```

Observer baseline: macOS 14.8.7, Python 3.9.6, bleak 1.1.1. OpenGT synchronization
was validated from CachyOS through ADB and Gadgetbridge 0.92.2. The codec and observer
remain **frozen read-only research tooling**. Keep active stock operations in the separate
OpenGT modules; preserve the observer as read-only and the codec as transport-only.

## External references (pinned)

- Gadgetbridge snapshot `3f0bb26cc331aba34c8bbcea85b48b68d5b3e909` (Huawei OTA classes; see gap-analysis S10/S11)
- `zyv/huawei-lpv2`, `psolyca/huawei-lpv2` (LPv2 transport)
- FCC QISFTN-B19 (internal photos), TechInsights DDT-1905-806 (paid teardown)
- Huawei Health APK (Uptodown mirror) — source of the OTA server flow analysis
