# Huawei Watch GT FTN-B19 custom-firmware gap analysis

**Status:** research-only baseline; no firmware implementation or watch modification
**Research date:** 2026-08-08
**Target:** user-reported first-generation HUAWEI WATCH GT, model FTN-B19

## Safety boundary

This report uses the repository's existing passive observations and public documentation/source code. No BLE application command, firmware update, flash operation, reset, pairing, authentication exchange, or watch opening was performed for this report. The existing implementation files are preserved, but LPv2 work is intentionally stopped here.

## 0. Current repository state and completed work

### Repository contents

- `.venv/` with Python 3.9.6 and `bleak==1.1.1`.
- `scripts/ble_observe.py`: read-only macOS/CoreBluetooth scanner and GATT observer. Its current notification mode restricts subscriptions to FE02, decodes captured FE02 frames with the offline codec, reads only standard Device Information characteristics, and does not send FE01 application packets or touch FE03/FE04/3802/4A02.
- `captures/`:
  - `scan-20260808T192122Z.json`
  - `scan-20260808T192145Z.json`
  - `scan-20260808T192617Z.json`
  - `gatt-20260808T192145Z.json`
- `docs/hardware-and-ble-baseline.md`: environment, advertisement, GATT map, readable values, and limitations.
- `research/huawei-uuid-protocol.md`: UUID inventory, LPv2 source comparison, authentication boundary, and reasons to leave undocumented channels untouched.
- `src/huawei_lpv2/codec.py` and `src/huawei_lpv2/__init__.py`: the small offline LPv2 framing/TLV/slicing compatibility layer that was already in progress. It is not an attempt to replace the mature public protocol implementations.
- `tests/test_lpv2_codec.py`: seven offline tests, including the public zyv test frame, CRC checking, VarInts, TLVs, stream chunks, and slicing/reassembly. The tests passed before this direction change with `PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v`.
- `docs/lpv2-codec.md`: field meanings, slicing notes, and source citations.
- `pyproject.toml`, `pyrightconfig.json`, `requirements.txt`, `.gitignore`, and project README material.

The files are currently uncommitted/untracked in the working tree; no completed work was deleted. The codec and observer changes should now be treated as frozen compatibility/research tooling rather than an invitation to extend LPv2.

### What was completed in the previous task

1. Recorded the macOS 14.8.7 / x86_64 / Python 3.9.6 / BCM_4350 environment.
2. Found and connected to an advertisement named `HUAWEI WATCH GT-E3A`; the public copy redacts its macOS CoreBluetooth identifier. This identifier class is a CoreBluetooth UUID, not a Bluetooth MAC address.
3. Saved the advertisement and GATT observations. The live map contained:
   - standard Device Information service `180A`;
   - Huawei service `FE86` with FE01 write, FE02 notify, FE03 write, and FE04 notify;
   - vendor service `3802` with `4A02`.
4. Read the explicitly readable standard characteristics. A historical read attempt on `4A02` returned `CBATTErrorDomain Code=2` (“Reading is not permitted”); no write or notification subscription was made to that channel.
5. Correlated FE86/FE01/FE02 with current Gadgetbridge and the public `zyv/huawei-lpv2` and `psolyca/huawei-lpv2` implementations. FE03, FE04, 3802, and 4A02 remain unassigned.
6. Confirmed that the observed advertisement/name and generic GATT revision values do not independently prove the user-supplied FTN-B19 / `1.0.12.26` identity: the watch advertised as `HUAWEI WATCH GT-E3A`, while standard revision characteristics returned `1.0.0.1`.
7. Stopped live work when the watch ceased advertising intermittently. No authenticated Huawei traffic was initiated.

## Executive result

- The best public hardware identification is **STMicroelectronics STM32L4R9-family ARM Cortex-M4 MCU**, not Kirin A1 and not Apollo3 Blue. A 2019 teardown labels the main IC `STM32L4R9`; the exact package suffix and the user unit's board revision remain unverified.
- The same teardown identifies a **Toshiba/Kioxia TC58CYG0S3H 1-Gbit (128 MB) serial NAND** storage device, plus Broadcom GNSS, NXP NFC, ST motion sensing, and AKM compass parts.
- The exact Bluetooth controller IC, display controller, touch controller, barometer, and heart-rate AFE are not established by authoritative public FTN-B19 documentation.
- Public work documents the Huawei BLE/LPv2 application transport and, in current Gadgetbridge, a Huawei OTA service and package parser. That is not a public bootloader unlock or custom-firmware path.
- No verified public FTN-B19 raw dump, bootloader image, partition map, debug-pad pinout, working bootloader exploit, or custom-firmware project was found.
- A production STM32L4R9 can enforce readout/debug protections, but the actual RDP/WRP/PCROP option state and Huawei signature-verification chain cannot be determined without a dump or board-level inspection.
- **Current answer:** there is no known, model-specific public path to arbitrary code execution on FTN-B19. The least risky eventual route is a volatile SRAM-only experiment through a verified, unlocked debug path on a sacrificial donor, after first obtaining a complete read-only dump and a recovery plan. OTA or flash replacement is not the first experiment.

## Evidence labels

- **CONFIRMED:** directly shown by the local capture, an official document, or a source implementation itself.
- **STRONG EVIDENCE:** corroborated teardown/source evidence, but not independently verified on this physical watch or not sufficient to prove the security state.
- **HYPOTHESIS:** technically plausible inference that must not be used as a flashing assumption.
- **UNKNOWN:** no reliable public result or no way to distinguish alternatives without new evidence.

# Findings by status

## CONFIRMED

### Identity, regulatory material, and product behavior

- Huawei's official documentation identifies **FTN-B19 as HUAWEI WATCH GT**, the first-generation/fashion variant. The FCC filing is **QISFTN-B19**. [S1][S2]
- The FCC filing contains an official internal-photo exhibit. It is useful for overall board/mechanical layout, but it does not expose a complete schematic, readable full BOM, bootloader, or debug-pad map. [S2]
- Official product material describes a circular AMOLED display at approximately **1.39 inches and 454 x 454 pixels**, plus Bluetooth, GNSS, optical heart-rate, motion, compass, barometer, and ambient-light functions. It does not publish the controller part numbers or pinouts. [S17]
- Official Huawei support directs normal wearable firmware updates through **Huawei Health -> Devices -> the watch -> Firmware update**, rather than a user-facing PC flashing tool. [S8]
- Huawei's update-failure guidance recommends charging, restarting, retrying Huawei Health, resetting only as a last resort, and using service support if recovery fails. It does not document a public FTN-B19 bootloader console or manual recovery image. [S9]
- The local observation confirms a real device exposing `180A`, `FE86/FE01/FE02/FE03/FE04`, and `3802/4A02`; it does not confirm that the device is the user's FTN-B19 because the advertisement/model/version values disagree. [L1]

### MCU vendor capabilities (conditional on the teardown identification)

- ST documents the STM32L4R9 family as Cortex-M4F MCUs with embedded Flash, SRAM, SWD debug, system-memory bootloader support, and readout/write/code protection mechanisms such as RDP, WRP, and PCROP. These are capabilities of the silicon family, not proof of how Huawei configured this watch. [S5][S6]
- ST documents that RDP Level 1 restricts debug/main-Flash access and that returning to Level 0 is destructive; RDP Level 2 disables debug/system-memory boot access irreversibly. [S6]
- ST documents factory system-memory bootloader interfaces and their model-dependent entry conditions in AN2606. This establishes a possible MCU-level recovery mechanism in an unprotected, physically accessible design, not a user-accessible FTN-B19 mode. [S6]

### Public source-code facts

- Current Gadgetbridge has a generic Huawei OTA implementation. It recognizes Huawei service `0x09`, negotiates OTA capabilities, validates an extracted payload's size/MD5/SHA-256 against `filelist.xml`, and transfers chunks through Huawei packet requests. This is a fact about the checked source snapshot, not evidence that an update was performed here. [S10][S11]
- Current Gadgetbridge's Huawei support still identifies the original GT family by the `huawei watch gt-` advertised-name prefix and uses the FE86/FE01/FE02 family. [S12]
- AsteroidOS's supported `sturgeon` device is the older Android-based Huawei Watch, not the proprietary-LiteOS Watch GT family. No AsteroidOS support entry establishes FTN-B19 support. [S15]
- Huawei PSIRT advisory `HUAWEI-SA-20181031-01` documents an improper-authorization issue in Huawei watches. The advisory does not describe arbitrary native code execution or a bootloader unlock. [S13]

## STRONG EVIDENCE

### 1. Exact SoC / MCU

**Best answer: STM32L4R9 family; exact suffix/package still unconfirmed.**

The 2019 Jiwei/Sohu teardown labels the main IC **STMicroelectronics STM32L4R9, ultra-low-power ARM Cortex-M4**. It separately labels the Broadcom GNSS and Toshiba storage devices. TechInsights has a paid FTN-B19 teardown entry consistent with this model. [S3][S4]

An earlier search result incorrectly associated Apollo3 Blue with the first-generation GT. The cited Ambiq datasheet describes the Apollo3 Blue family, but it is not evidence about FTN-B19. The direct FTN-B19 teardown evidence supports STM32L4R9 instead; **Apollo3 Blue must not be used as the target architecture unless a board photo or dump proves it.** [S3][S5]

The exact ordering suffix (`STM32L4R9ZI`, `...VI`, etc.), package, die revision, and whether every FTN-B19 board revision uses the same part are still unverified. ST's memory sizes and pin/peripheral data should therefore be treated as family reference information, not as the watch's confirmed flash layout. [S5][S6]

### 2. PCB and component identification

The teardown reports a three-board arrangement: main PCB, heart-rate PCB/FPC, and button FPC. It reports extensive adhesive, shielding, foam, conductive tape, and water-sealing construction. The FCC photos independently confirm the availability of internal board/mechanical views. [S2][S3]

The same teardown labels these parts:

| Function | Reported part | Confidence and limitation |
| --- | --- | --- |
| Main MCU | ST STM32L4R9 | Strong; source-reported, not read from our board |
| GNSS | Broadcom BCM47752, GPS/GLONASS | Strong; source-reported |
| NFC | NXP PN80T | Strong; source-reported |
| Accelerometer/gyro | ST LSM6DSL | Strong; source-reported; ST identifies it as a 6-axis IMU |
| Magnetometer/compass | AKM AK09918 | Strong; source-reported |
| External nonvolatile storage | Toshiba/Kioxia TC58CYG0S3H | Strong; part datasheet identifies a 1-Gbit serial NAND |
| Power | TI TPS61256 and TPS62743 | Strong; source-reported |
| Display module | WB014ZNM-T00, 1.39-inch AMOLED | Strong; controller remains unidentified |
| Battery | HB512627ECW+, roughly 420 mAh / 3.82 V | Strong; source-reported |

The Sohu teardown's “16 MB RAM + 128 MB ROM” is a system-level capacity statement. The TC58CYG0S3H datasheet identifies that Toshiba/Kioxia part as 128-MB-class serial NAND, **not RAM**; the RAM device/package and exact wiring are not identified here. [S3][S7]

### 3. FCC/internal/teardown photos

- **Free primary regulatory photos:** FCC internal photos for QISFTN-B19. They show the opened watch and board views but are too limited to establish every IC marking or test pad. [S2]
- **Free repair/opening references:** iFixit's opening guide documents the mechanical opening procedure and the risk to sealing/cables. This is not an electrical schematic or debug guide. [S19]
- **Commercial high-resolution source:** TechInsights DDT-1905-806 is specifically titled for the Huawei Watch GT FTN-B19, but detailed access is paid. [S4]
- **Component teardown:** Jiwei/Sohu's 2019 article provides the strongest freely readable component list found in this search. [S3]

### 4. Firmware packages and update mechanism

**Delivery is well supported; an exact FTN-B19 package is not.**

Huawei documents the Huawei Health delivery path. Public news/community references report FTN-B19-era versions including `1.0.12.26`, and third-party archives list some Watch GT files, but no downloaded file with a verifiable FTN-B19 region/build/hash was found in this repository or verified as an official standalone package. [S8][S18]

Current Gadgetbridge provides a valuable package-format clue:

- outer container is parsed as a ZIP;
- root `filelist.xml` describes a component and files;
- each file has `spath`, `dpath`, `operation`, `md5`, `sha256`, `size`, package/version fields, and optional OS version;
- the firmware payload selected by the parser has a path ending in `.bin.apk`;
- the host checks the extracted payload size and MD5/SHA-256 before upload;
- the OTA manager reads a little-endian field at payload offset 4 and combines it with a default or capability-reported signature length to form a file identifier.

This is confirmed source behavior for the checked Gadgetbridge implementation, and strong evidence of a Huawei wearable OTA family format. It does **not** prove that the exact FTN-B19 `1.0.12.26` download uses the same outer file or that `bin.apk` is directly executable firmware. [S10][S11]

### 5. OTA protocol boundary

Gadgetbridge's OTA packet definitions use Huawei service `0x09`, with commands for start/query, data parameters, chunk requests, chunk send, result, errors, status, auto-update, new-version notification, and device requests. The actual image transfer is capability- and version-dependent. The source has comments such as “not sure” around encryption on some OTA-control packets; therefore these classes should not be treated as a complete security specification. [S10][S11]

The normal Huawei FE01/FE02 protocol is authenticated/encrypted in the broader Huawei path. No OTA or authentication packet was sent from this project. Existing LPv2 implementation work is sufficient for offline parsing and should not become the main reverse-engineering effort. [L2][S10]

### 6. Storage and candidate flash layout

Strong hardware evidence exists for at least two storage domains:

- STM32L4R9 internal Flash/SRAM, with exact part suffix and option bytes unknown.
- A 1-Gbit serial NAND device identified as TC58CYG0S3H, with NAND page/spare/ECC/bad-block behavior documented by Kioxia/Toshiba. [S3][S7]

This makes a layout containing boot/application data in internal Flash and assets/filesystem/update staging in external NAND plausible, but no partition boundary, filesystem, slot count, image base address, or boot record has been observed. See HYPOTHESIS below.

### 7. Debug and code-execution prerequisites

ST's STM32L4R9 documentation establishes SWD signals and system bootloader behavior for the MCU family. No reliable FTN-B19 board photo or public source identifies SWD, UART, BOOT0, NRST, or test-pad locations, voltage, or option-byte state. A potential SWD route is therefore a **hardware possibility**, not a known path on this watch. [S6][S19]

## HYPOTHESIS

These statements are engineering models only; none is a basis for touching the watch.

### 1. Likely boot chain

A plausible chain is:

```text
STM32 reset / factory system memory
        -> Huawei user-flash boot or update agent
        -> Huawei application / LiteOS image
        -> external NAND assets, services, and data
```

The first element is a documented STM32 family capability. The middle and final elements are inferred from the proprietary product architecture and the existence of a Huawei OTA transfer agent; their addresses, image names, and exact control flow are unknown. A Huawei bootloader could also be integrated with the application or store more code in external NAND.

### 2. Secure boot and signing

It is reasonable to expect some combination of image authentication, version checks, encrypted transport, anti-rollback, or protected debug because:

- the OTA manifest carries cryptographic hashes;
- Gadgetbridge has capability-dependent signature-length logic;
- the MCU family provides RDP/WRP/PCROP/firewall controls;
- Huawei Health is the controlled update distributor.

That is not proof that the stock FTN-B19 boot chain verifies a public-key signature. The manifest hashes may only provide transport/integrity checking, and the actual signature may be in the `.bin.apk` payload or an omitted layer. The algorithm, key location, certificate chain, anti-rollback counter, and acceptance behavior remain unknown.

### 3. Bluetooth architecture

Because the teardown identifies an STM32L4R9 rather than an MCU with the relevant integrated radio, a separate Bluetooth controller/SoC or module is likely. A Dialog Semiconductor / DA14681 identification appears in low-confidence community/secondary search results, while other search results incorrectly transfer later GT2/HiSilicon parts to the first-generation GT. The safe hypothesis is only “separate BLE radio/controller exists”; the exact part and host interface are unresolved.

The exposed FE86/FE01/FE02 path is the Huawei application protocol over BLE, not proof that the FE86 service is implemented by a particular radio IC.

### 4. Display and touch path

The display is an AMOLED/touch module with NFC antenna material on or behind the display flex according to the teardown. The STM32L4R9 family has display-related peripherals, including variants with LTDC/DSI capability, but no source ties those signals or a particular controller to FTN-B19. The panel may use a DSI, SPI, proprietary serial, or module-integrated controller path. The touch controller may be on the flex/module or hidden under a package; no pinout should be guessed.

### 5. Firmware locations

The likely internal/external split is:

```text
internal MCU Flash: reset vectors, boot/update code, or critical application code
external serial NAND: resources, filesystem/data, staged update payloads, or additional code
```

This is a capacity-and-device-architecture hypothesis. NAND is not transparent NOR/XIP storage: page reads, ECC, bad-block management, and a Huawei translation layer would matter. No partition table or raw dump exists.

### 6. Recovery behavior

The Huawei Health update agent may be able to resume or reinstall a valid vendor package while the normal boot/update path remains alive. That does not imply a freely accessible recovery mode. The physical charging contacts are documented for charging, not as a public USB data/bootloader interface. A hidden service path may exist, but no public FTN-B19 procedure was found.

### 7. Production protection state

Commercial hardware commonly enables at least some readout/debug restrictions, but there is no direct measurement of this unit. It is unsafe to assume either RDP Level 0 (“easy dump”) or RDP Level 2 (“permanently locked”). Treat the state as unknown until a non-destructive debugger probe on a sacrificial donor establishes it.

## UNKNOWN

The following are unresolved gaps, explicitly mapped to the requested research questions.

| # | Question | Current status | What would close the gap without starting firmware implementation |
| ---: | --- | --- | --- |
| 1 | Exact SoC/MCU used in FTN-B19 | STM32L4R9 family is strong evidence; exact suffix/package, revision, and any companion MCU unknown | High-resolution board photo, TechInsights BOM, or a read-only device identification/dump |
| 2 | PCB/component identification | Main/heart-rate/button board structure and several IC labels are strong; complete BOM/schematic and board revision unknown | FCC image enhancement, paid teardown/BOM, or later owner-supplied macro photos |
| 3 | FCC/internal/teardown photos | FCC internal photos and public teardown exist; readable coverage is incomplete | Preserve/download cited source exhibits and obtain board-side macro photos only after explicit decision to open a sacrificial unit |
| 4 | Firmware packages publicly available | Version reports and unverified third-party listings exist; no verified FTN-B19 package/hash in this project | Acquire an official package through an explicitly approved Huawei Health observation and preserve its original hash; do not install it |
| 5 | Huawei firmware update mechanism | Huawei Health delivery and Gadgetbridge OTA service are documented; exact FTN-B19 negotiation, auth branch, and update state machine unknown | Passive trace from an authorized official update, without replay or modification |
| 6 | Firmware container/package format | Gadgetbridge shows ZIP + `filelist.xml` + `.bin.apk` for its supported Huawei OTA path; exact FTN-B19 payload header/codec unknown | Obtain one real FTN-B19 package and analyze it offline |
| 7 | Bootloader architecture | STM32 ROM bootloader is documented; Huawei second-stage/application boot chain is unknown | Static analysis of an externally acquired image or a read-only dump |
| 8 | Secure boot/signature verification | MCU protection features and OTA signature-related code exist; actual FTN-B19 key/verification chain unknown | Package/bootloader analysis; never test by sending modified firmware |
| 9 | Flash layout/partitions | Internal MCU Flash and external serial NAND are strongly supported; addresses, partitions, slots, filesystems, and boot flags unknown | Read-only dump with known memory boundaries and ECC-aware NAND reconstruction |
| 10 | Recovery/update modes | Official Health/service recovery guidance exists; physical entry pins and a user-accessible bootloader menu unknown | Public service documentation or passive observation of a failed update on a sacrificial unit; no induced failure |
| 11 | UART/SWD/JTAG/test pads | STM32 family pin capabilities are documented; FTN-B19 pad locations, voltage, mux, and protection state unknown | Board photos and non-invasive continuity/voltage work on a sacrificial unit; no drive/program action |
| 12 | Existing firmware dumps | No verified FTN-B19 raw dump was found in the checked public sources or this repository | Search model/codename/version combinations and validate provenance/hashes; avoid random archives |
| 13 | Bootloader exploits/RCE research | No credible FTN-B19-specific bootloader exploit or public working RCE was found; CVE-2018-7926 is authorization, not RCE | Exact-firmware static/vulnerability research and responsible disclosure; do not test exploit payloads against the watch |
| 14 | Display controller/interface | Panel model/resolution are strong; driver IC, bus, GPIO map, initialization, and framebuffer ownership unknown | Panel-flex macro photos, FCC/TechInsights BOM, or a dump; do not probe the sealed primary unit |
| 15 | Touch controller | Capacitive touch is confirmed; controller IC, bus, firmware, and interrupt/reset lines unknown | Display-module identification or board photos |
| 16 | Bluetooth controller/stack | BLE operation and Huawei FE86 application transport are confirmed; exact radio IC, firmware, host transport, and stack split unknown | Readable board marking or authoritative teardown; no guessed BLE writes |
| 17 | Sensor chips/interfaces | LSM6DSL and AK09918 are strong; GNSS/NFC parts are strong; barometer, PPG/HR AFE, ambient sensor, buses, and GPIOs incomplete | Complete BOM or later passive board inspection |
| 18 | Prior custom code/custom firmware on FTN-B19 | No completed public custom-firmware project, exploit, or FTN-B19 native-code execution report was found; absence is not proof | Search archives/model codenames and require a reproducible FTN-B19-specific artifact |

# Direct answers

## A. Is there a known path to arbitrary code execution on FTN-B19?

**No known public, model-specific path was found.**

- No verified FTN-B19 bootloader unlock, custom image loader, public RCE proof of concept, or working custom-firmware project surfaced.
- The Huawei watch advisory located during research concerns improper authorization, not arbitrary native code execution. [S13]
- HiSilicon phone/TEE/bootloader exploit research is not evidence for this STM32L4R9-based watch; it targets different silicon and boot chains.
- A possible **non-exploit hardware path** would exist only if a sacrificial board exposes an unlocked SWD/debug path or an unprotected STM32 system bootloader. That is conditional on physical access and option bytes, and remains unverified.

## B. Is the boot chain signed / secure?

**Not confirmed for this exact watch; secure enforcement is the leading hypothesis, not a proven fact.**

Confirmed facts are that STM32L4R9 supports RDP/WRP/PCROP-style protection and that Gadgetbridge's Huawei OTA path has manifest hashes plus capability-dependent signature-length handling. Neither proves the FTN-B19 bootloader's signature algorithm, key, or option-byte configuration. [S6][S10][S11]

Operationally, treat the stock chain as signed/protected until a vendor package and bootloader analysis prove otherwise. Do not test that assumption by sending an altered image.

## C. Can firmware be dumped or obtained externally?

**Obtaining a vendor package is more plausible than obtaining a raw dump today; neither is completed here.**

- An official Huawei Health update may leave a package in phone/app storage before transfer; preserving that package would require a separately approved, authorized observation and careful hashing.
- Gadgetbridge demonstrates that Huawei firmware packages with ZIP/manifest/payload structure exist in its supported OTA path, but no FTN-B19 package was captured here. [S10][S11]
- A raw MCU dump may be possible through SWD only at a permissive protection state. At STM32 RDP1, recovery to RDP0 is destructive; at RDP2, debug/system boot access is disabled. [S6]
- The external serial NAND is a possible separate storage acquisition target, but an in-circuit read would require power/ECC/bad-block care and the NAND's partition contents are unknown. No board opening or flash read is authorized in this phase.

## D. Can we recover the watch if a custom image fails?

**There is no guaranteed recovery path currently.**

- A volatile SRAM-only test that is never written to Flash should be recoverable by reset/power loss if the board remains electrically healthy.
- A Flash/OTA modification could be recoverable through Huawei Health or service only if the vendor update path and boot/update agent still run.
- An unlocked SWD path plus a verified original dump would provide a stronger recovery option.
- RDP1-to-RDP0 recovery destroys user Flash, and RDP2 is intended to be irreversible; a raw external-NAND copy may not restore internal MCU Flash or protected option bytes. [S6]
- Without a complete original dump, verified package, and confirmed recovery interface, assume a failed custom image can turn the watch into a service/motherboard-replacement case.

## E. Least risky path toward one tiny custom ARM program

The least risky path is **not OTA and not replacement firmware**:

1. Freeze the primary watch in its current state and resolve the FTN-B19 identity/version discrepancy from passive evidence.
2. Build and test a tiny Cortex-M4 program on an STM32L4R9 evaluation board first; do not use the watch as a development board.
3. Obtain a sacrificial FTN-B19 donor before any opening or electrical work.
4. On that donor, identify the MCU/package and debug/test pads non-destructively. First attempt only device identification/read-only access; do not change option bytes or send program/erase commands.
5. If and only if debug access is confirmed and protection permits it, make and independently verify complete internal-Flash and relevant external-NAND backups before executing anything.
6. Prefer a **RAM-loaded, reset-discarded** test with no Flash/NAND writes, no BLE application commands, no persistent state changes, and a known hardware reset/charger recovery path.
7. Stop if the device reports RDP1/RDP2, readout is blocked, pad identity is uncertain, or no verified recovery image/dump exists. Do not downgrade protection merely to make an experiment possible.

This path still requires a separate explicit decision before pairing/authentication, opening the watch, probing pads, or using a debugger. It is a research gate, not an implementation plan.

# Source register

### Hardware and product

- **[S1] Huawei official FTN-B19 quick-start/manual identification:** [WATCH GT fashion edition quick start, FTN-B19](https://consumer.huawei.com/cn/support/content/zh-cn00732834/)
- **[S2] FCC QISFTN-B19 filing and internal photos:** [FCC filing](https://fccid.io/QISFTN-B19), [Internal Photos of E1762](https://fccid.io/QISFTN-B19/Internal-Photos/Internal-Photos-4020860)
- **[S3] Jiwei/Sohu teardown, published 2019-08-02:** [Huawei WATCH GT teardown and component labels](https://www.sohu.com/a/331084070_166680)
- **[S4] Commercial model-specific teardown:** [TechInsights DDT-1905-806, Huawei Watch GT FTN-B19](https://www.techinsights.com/products/ddt-1905-806)
- **[S5] ST MCU documentation:** [STM32L4R9ZI product page](https://www.st.com/en/microcontrollers-microprocessors/stm32l4r9zi.html), [STM32L4R9 datasheet](https://www.st.com/resource/en/datasheet/stm32l4r9vg.pdf)
- **[S6] ST boot/security documentation:** [RM0432 / STM32L4+ reference manual](https://www.st.com/resource/en/reference_manual/dm00310109-stm32l4-series-advanced-armbased-32bit-mcus-stmicroelectronics.pdf), [AN2606 system-memory boot mode](https://www.st.com/resource/en/application_note/an2606-stm32microcontroller-system-memory-boot-mode-stmicroelectronics.pdf), [AN3155 USART bootloader protocol](https://www.st.com/resource/en/application_note/an3155-usart-protocol-used-in-the-stm32-bootloader-stmicroelectronics.pdf), [AN5056 SBSFU guide](https://www.st.com/resource/en/application_note/dm00414677-integration-guide-for-the-x-cube-sbsfu-stm32cube-expansion-package-stmicroelectronics.pdf)
- **[S7] Toshiba/Kioxia storage datasheet:** [TC58CYG0S3H serial NAND](https://media.digikey.com/pdf/Data%20Sheets/Toshiba%20PDFs/TC58CYG0S3HxAIx_Rev1.1_2016-11-08.pdf)
- **[S17] Huawei official Watch GT specifications:** [Watch GT specifications](https://consumer.huawei.com/kw-en/wearables/watch-gt/specs/)
- **[S19] iFixit mechanical reference:** [How to open the Huawei Watch GT](https://www.ifixit.com/Guide/How%2Bto%2Bopen%2Bthe%2BHuawei%2BWatch%2BGT/134984)

### Firmware/update/security

- **[S8] Huawei official update procedure:** [Updating your HUAWEI watch/band](https://consumer.huawei.com/en/support/content/en-us16066728/)
- **[S9] Huawei official failed-update guidance:** [My HUAWEI wearable device fails to update](https://consumer.huawei.com/en/support/content/en-us15868264/)
- **[S10] Gadgetbridge source snapshot:** repository [Freeyourgadget/Gadgetbridge](https://codeberg.org/Freeyourgadget/Gadgetbridge), snapshot `3f0bb26cc331aba34c8bbcea85b48b68d5b3e909`; relevant files are [`HuaweiFwHelper.java`](https://codeberg.org/Freeyourgadget/Gadgetbridge/src/commit/3f0bb26cc331aba34c8bbcea85b48b68d5b3e909/app/src/main/java/nodomain/freeyourgadget/gadgetbridge/service/devices/huawei/HuaweiFwHelper.java), [`HuaweiOTAFileList.java`](https://codeberg.org/Freeyourgadget/Gadgetbridge/src/commit/3f0bb26cc331aba34c8bbcea85b48b68d5b3e909/app/src/main/java/nodomain/freeyourgadget/gadgetbridge/devices/huawei/ota/HuaweiOTAFileList.java), [`HuaweiOTAManager.java`](https://codeberg.org/Freeyourgadget/Gadgetbridge/src/commit/3f0bb26cc331aba34c8bbcea85b48b68d5b3e909/app/src/main/java/nodomain/freeyourgadget/gadgetbridge/service/devices/huawei/HuaweiOTAManager.java), [`OTA.java`](https://codeberg.org/Freeyourgadget/Gadgetbridge/src/commit/3f0bb26cc331aba34c8bbcea85b48b68d5b3e909/app/src/main/java/nodomain/freeyourgadget/gadgetbridge/devices/huawei/packets/OTA.java), and [`HuaweiPacket.java`](https://codeberg.org/Freeyourgadget/Gadgetbridge/src/commit/3f0bb26cc331aba34c8bbcea85b48b68d5b3e909/app/src/main/java/nodomain/freeyourgadget/gadgetbridge/devices/huawei/HuaweiPacket.java).
- **[S11] Gadgetbridge OTA capability state:** [`HuaweiState.java`](https://codeberg.org/Freeyourgadget/Gadgetbridge/src/commit/3f0bb26cc331aba34c8bbcea85b48b68d5b3e909/app/src/main/java/nodomain/freeyourgadget/gadgetbridge/devices/huawei/HuaweiState.java), including service `0x09` capability checks and signature capability.
- **[S12] Gadgetbridge original GT coordinator:** [`HuaweiWatchGTCoordinator.java`](https://codeberg.org/Freeyourgadget/Gadgetbridge/src/commit/3f0bb26cc331aba34c8bbcea85b48b68d5b3e909/app/src/main/java/nodomain/freeyourgadget/gadgetbridge/devices/huawei/huaweiwatchgt/HuaweiWatchGTCoordinator.java)
- **[S13] Huawei watch security advisory:** [HUAWEI-SA-20181031-01](https://www.huawei.com/en/psirt/security-advisories/2018/huawei-sa-20181031-01-watch-en)
- **[S15] AsteroidOS status:** [Porting status](https://wiki.asteroidos.org/index.php/Porting_Status), [sturgeon device page](https://wiki.asteroidos.org/index.php/Sturgeon)
- **[S18] Public version report, not a package provenance source:** [Huawei Watch GT v1.0.90.26 / v1.0.12.26 report](https://www.huaweiupdate.com/huawei-watch-gt-getting-v1-0-90-26-and-v1-0-12-26-update/)

### Existing local evidence

- **[L1]** `captures/scan-20260808T192122Z.json`, `captures/scan-20260808T192145Z.json`, `captures/scan-20260808T192617Z.json`, and `captures/gatt-20260808T192145Z.json`.
- **[L2]** `research/huawei-uuid-protocol.md`, which cites `zyv/huawei-lpv2`, `psolyca/huawei-lpv2`, the public GT-DEE transcript, and Gadgetbridge's FE86/FE01/FE02/authentication source paths.

## Recommended next research gate

Do not write to or open the primary watch. The next useful deliverable is a **passive evidence package**, not firmware code: independently verify the physical model, obtain a hashable official FTN-B19 update artifact only if separately authorized, and compare its metadata/container against the Gadgetbridge parser offline. Hardware/debug work should wait for a sacrificial donor and a documented recovery plan.
