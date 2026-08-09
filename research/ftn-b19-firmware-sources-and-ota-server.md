# FTN-B19 firmware package sources and Huawei OTA server flow

**Status:** passive research only; no watch interaction, no BLE traffic, no download completed (mirror login/limits). APK analysis was static (unzip + bytecode disassembly of a public APK).
**Research date:** 2026-08-09
**Target:** HUAWEI WATCH GT first generation, model FTN-B19 (platform codename `Fortuna`, retail name `Fortuna-B19S`)

Companion to `ftn-b19-custom-firmware-gap-analysis.md`; closes/advances gaps **#4 (packages)**, **#5 (update mechanism)**, **#6 (container format)**, **#16 (BT controller)**.

---

## 1. Public firmware package inventory (mirror, hashes NOT yet verified)

All four files are hosted on `kurdishfirmware.com` (GSM-service mirror, engine "Real Easy Store", sister domain `easy-firmware.com` is now parked/GoDaddy). Downloads require a free account (endpoint `c=download` returns 302 → `a=login`); account-level download limits apply ("package limits"). No Wayback captures exist for any of these pages or files.

| File | Size | Upload | URL (page / download) |
| --- | --- | --- | --- |
| `[ Board Software ] Fortuna-B19S-BD 1.0.95.99_Board Software_general_NA_NA_05022MEU.rar` | 148.46 MB | 2019-07-29 | `index.php?a=downloads&b=file&id=14586` / `...&c=download&id=14586` |
| `Fortuna-B19S 1.0.12.8(C06)_Firmware_general_NA_05016TCQ.zip` | 167.40 MB | 2021-03-04 | `...&b=file&id=25062` / `...&c=download&id=25062` |
| `Fortuna-B19S 1.0.11.8(C03)_Firmware_general_NA_05015NXN.zip` | 144.76 MB | 2021-03-04 | `...&b=file&id=25063` / `...&c=download&id=25063` |
| `Fortuna-B19S 1.0.11.10(C02)_Firmware_general_NA_05015NKQ.zip` | 151.33 MB | 2021-03-04 | `...&b=file&id=25064` / `...&c=download&id=25064` |

- Base host: `https://kurdishfirmware.com/`; folder tree: Downloads → Firmwares → HUAWEI → HUAWEI FIRMWARE → F-SERIES → `FTN-B19` (id=7532) and `FORTUNA-B19` (id=11067).
- Site-internal search (`?a=downloads&b=search&keyword=Fortuna`) returns exactly these 4 files — the inventory is complete on this mirror.
- Naming matches the Huawei hicloud full-package scheme (`Board_Software_<product>_<version>Board_Software_general_NA_NA_<build>.rar`); the OTA zips match the hicloud OTA-package scheme (`<product> <version>(C<xx>)_Firmware_general_NA_<build>.zip`).
- **Version lineage cross-check:** huaweiupdate.com (2020-08-16): Watch GT **Sport = 1.0.12.26**, basic version 1.0.12.18; Elegant variant on separate track 1.0.90.26. stiwe.com (2020-07-19): 1.0.12.18 OTA ≈ 1.29 MB. The full package 1.0.95.99 (2019) predates the OTA track 1.0.11.x → 1.0.12.x.

**Remaining action:** download (account), then verify: RAR/ZIP listing, `filelist.xml` (expect `com.huawei.FTN-B19.firmware` component + `Fortuna_mcu_bt_dsp_app_<ver>.bin.apk` entry), SHA-256 of every artifact, header analysis of `.bin.apk` against section 4.

---

## 2. Huawei Health OTA server flow (static APK analysis)

Artifact: `com.huawei.health` **16.1.5.320**, Uptodown, 203,913,390 bytes, **SHA-256 `fe5a89bc9137b13e4b4e1135c8c97ed0868c67bfb4e8eb0c29768fafb0c518bb`**. Decompiled bytecode from `classes6.dex` (androguard 4.1.4).

### 2.1 Endpoint and URL selection

- Production fallback URL: `https://query.hicloud.com/accessory/v2/checkEx.action` (string in `classes6.dex`; referenced from `Lcom/huawei/hwversionmgr/selfupdate/appupdate/UpdateBase;->e(...)`).
- Test-mode URL: `/ring2/v2/CheckEx.action?ruleAttr=true` (relative).
- **Real URL comes from GRS remote config**: `Lnja;->e(Z,Z)` logs `"getUpdateUrl isHonor: ..."` and resolves via `GRSManager` (`Lhealth/compact/a/GRSManager;`). The hardcoded `checkEx.action` is only the fallback. This is the most likely reason raw probes to the fallback URL return a canned response (see 2.4).
- Companion config endpoint: `https://configserver.hicloud.com/servicesupport/updateserver/getLatestVersion` (returned 590 "Unexpected producer error" without proper params).

### 2.2 Request JSON (from `Lnju;->b(Context, String, String, String, String)`)

```json
{
  "rules": {
    "DeviceName": "<map lookup by product UUID, may be null>",
    "deviceId": "<product UUID>",
    "Language": "en-us",
    "OS": "Android <release>",
    "PackageType": "full"
  },
  "components": [
    {
      "componentID": "1",
      "PackageName": "com.huawei.health",
      "PackageVersionCode": "<versionCode>",
      "PackageVersionName": "<versionName>",
      "FirmWare": "FW_SCALE"
    }
  ]
}
```

- `DeviceName` is looked up in a UUID→name map (`Lnju$5.<init>`): `34fa0346-...`→`HuaweiCH18`, `33123f39-...`→`HuaweiCH100`, `ccd1f0f8-...`→`HuaweiAH100`, `25c6df38-ca23-11e9-...`→`LUP-B19`, `8358eb90-b40d-11e9-...`→`HAG-B19`, `b29df4e3-...`→`HAG-B19`, `e835d102-...`→`HEM-B19`. **Fortuna is not in the map** → `DeviceName` is null in the app's own request.
- `FirmWare`: `"FW_OS"` if product UUID == `ccd1f0f8-8c57-4bd7-a884-0ef38482f15f`, else `"FW_SCALE"`.
- `deviceId` vs `IMEI` key chosen by `Lhealth/compact/a/CommonUtil;->r(String)` (deviceId for the watch UUID path).
- HTTP layer (`Lnjr;->d`, `Llig;->b`, `Llih;->a`): plain `HttpURLConnection` POST, raw JSON body, **no encryption, no signature, no custom headers**.

### 2.3 Response JSON (from `Lnjq;->a/b/e` parsers)

```json
{
  "status": "0",
  "versionPackageCheckResults": [
    {
      "status": "0",
      "components": [
        {
          "name": "...", "version": "...", "versionID": "...",
          "description": "...", "url": "<file name>",
          "createTime": "...", "size": "...", "componentID": "...",
          "ruleAttr": "..."
        }
      ]
    }
  ]
}
```

- Status semantics: `1` = no new version; `0` = update available (from `Lnjq;->e(String, boolean)`: non-zero status short-circuits to "no update").
- Download construction (`Lnjw;->cdB_`): app fetches `<base>full/filelist.xml` (method log: "getFileListXMLFromServer"), then `<base>full/<components[0].url>`; `base` is `Lnim;->x()` from the response.

### 2.4 Probe results (2026-08-09, passive HTTP only)

- Endpoint is alive; JSON payloads are accepted (malformed → `{"status":"-1"}`, valid JSON → `{"status":"1"}`).
- `{"status":"1"}` returned for **all** payload variants (deviceId = Fortuna UUID / "003N" / "80", versions 1.0.0.0/1.0.12.8, DeviceName Fortuna/Fortuna-B19S/null) **and also for active products** (JPT-B19 GT3, LTN-B19 GT2, UUIDs from `product_map.json`).
- Conclusion: the fallback URL returns a canned/legacy response; the production URL is resolved via GRS remote config and is **not reachable without that config** (or an additional session layer). Not usable as-is; see Leads.

### 2.5 `assets/product_map.json` (from the same APK)

Full device→UUID map for wearables. Relevant entries:

| modelName | productId (UUID) | deviceId | smartProductId | marketingName |
| --- | --- | --- | --- | --- |
| **Fortuna** | `a8ab58b1-0893-42ce-8b2d-2de08aed4ab4` | 80 | 003N | (Watch GT 1) |
| LTN-B19 | `ce2ceada-adf8-40f2-b8b7-d595a6628a67` | 88 | 005W/005X | HUAWEI WATCH GT 2 |
| DAN-B19 / HCT-B19 / Vidar-B19 | `ce2ceada-...` (same) | 88/112/113 | — | GT 2 family |
| JPT-B19 / ODN-B19 / MIL-B19 / RUN-B19 / FRG-B19 / PNX-B19 / ARA-B19 | `8df8e0d8-e4bf-42f0-b0f3-0e11bf16caff` | 395+ | M0A2... | GT 3 / GT 4 family |
| MNS-B19 / HBE-B19 | `568d8802-6506-4f74-991b-76b5c50b915b` | 89 | 005Y/005Z | (Honor) |
| Hes-B19 | `87b9e25c-9b4e-473e-a1dc-c94b9f827f69` | 122 | N002/N003 | (Honor) |

The UUID is what a paired watch reports over BLE and what the app passes into the check flow. Useful for any future OTA-client work in this repo.

---

## 3. `.bin.apk` container format (sibling GT2 evidence, same family)

Source: GitHub `cnoim/ltn_b19_1_0_13_20` release "full" — filelist.xml (809 B), changelog.xml (55,642 B), `Latona_mcu_bt_dsp_app_1.0.13.20.bin.apk` (180,205,441 B).

- `filelist.xml` (GT2 era): `<component name="com.huawei.LTN-B19.firmware">` + `<file>` entries with `spath/dpath/operation/md5/size/packageName/versionName/versionCode`. Referenced md5s: `D0C22B1578385461F563F0770995F21B` (changelog.xml), `34391AFDC64FB19DD1043C7B2C34A3B1` (bin.apk). **Newer format** (GT3 `cnoim/jpt_b29_package_3_0_0_97`) adds `sha256` and `osVersion` fields per file.
- **`.bin.apk` is NOT a ZIP/APK.** First 256 KB header analysis (SHA-256 of the 256-KB prefix: `6e7d1f18ebe263d9089df9be86df93f758b9d19a643ee205660ed99e3a16b994`):

```text
0100 8800 5606 0000 0100 0000   header (u16 magic 0x0001, u16 0x0088, u32 0x00000656, u16 1, u16 0)
"Latona\0"                      16-byte codename field
"1.0.13.20\0"                   16-byte version field
0200 2000                       
"2021.08.14\0" "13:08:07\0"     build date/time fields
<component table>               entries: u16 id (0x05..0x22), offset/size, 16-byte name
                                (e.g. "B500"), 16B + 16B hashes, per-component version
                                strings ("2.0.0.29", "2.0.0.18", "2.6.194", "1.1.20",
                                "1.0.0.6", ...)
<compressed payload>             rest of file; trailer is payload, no signature block
```

- Consistent with Gadgetbridge's note ("little-endian field at payload offset 4" used with a signature length) — GB parses the **outer ZIP + filelist.xml**; the `.bin.apk` payload carries this binary header on top.
- Expected FTN-B19 analogue: component `com.huawei.FTN-B19.firmware`, payload `Fortuna_mcu_bt_dsp_app_<version>.bin.apk` (HYPOTHESIS, high confidence from naming pattern: Latona=GT2, Jupiter=GT3, Molly=Watch D, Fortuna=GT1).

---

## 4. New hardware / identity evidence

| Finding | Evidence | Confidence |
| --- | --- | --- |
| BT controller = **Dialog Semiconductor** | XDA thread "Huawei Watch GT firmware dump, mods and flashing" (t/4350685), post by `grayhades649299` 2024-10-14: "the MCU is just a stm32l4r9… the Bluetooth chip looks like its from dialog" + 2 PCB photos (XDA attachments 6154830, 6154820 — **not archived**, must be fetched from live XDA) | STRONG EVIDENCE (community observation, unverified photo) |
| No public dump/mod path exists | same thread: 2022-01-31 "we have no information about dumping and modding system files for Huawei GT watches. You could be the first one!"; thread active to 2025 | CONFIRMED (negative) |
| 128 MB flash / 16 MB RAM retail spec | Fortuna-B19S retail listings (istoric-preturi.info, flipkart, etc.) | CONFIRMED — matches TC58CYG0S3H 1 Gbit SPI-NAND (u-boot `drivers/mtd/nand/spi/toshiba.c`: TC58CYG0S3HRAIG/RAIJ, 1.8 V 1 Gbit, READID 0xB2/0xD2, page 2048, OOB 128, ECC 8/512; also in NeoProgrammer CH341A device list) and phonedb (Cortex-M4, 16 MiB RAM) |
| Display panel codename `HWHD02` | `ninlith/shiyong` (GitHub, 2025-12-17) — watchface project for FTN-B19; `project/Shiyong/description.xml` has `<screen>HWHD02</screen>`; exports: `.hwt` 297,394 B and compiled `.bin` 467,406 B (the GT1 watchface binary format — only public "custom code" deployment path for FTN-B19) | STRONG EVIDENCE |
| GT-E3A | The user's watch advertises as `HUAWEI WATCH GT-E3A` (existing L1 capture). No public model database entry ties GT-E3A to a distinct model; treat as the family advertisement name, not a separate board | UNKNOWN |

---

## 5. Negative results (checked 2026-08-09)

- Wayback CDX: **zero** captures containing "Fortuna" or "FTN-B19" on `update.hicloud.com`; zero captures of kurdishfirmware Fortuna pages; zero of easy-firmware.com (parked domain, no archives).
- GitHub/GitLab/Gitee/Sourcegraph/grep.app: no public code references to `FTN-B19`, `Fortuna-B19S`, `mcu_bt_dsp_app`, `filelist.xml`+`bin.apk` (only repo: `ninlith/shiyong` watchface). `cnoim` mirrors full packages for GT2/GT3/GT Cyber/Watch D — **not** Watch GT 1.
- General search engines (Brave/Yahoo/DDG/Bing RSS/searx instances/Yandex): query `"05022MEU"` yields only kurdishfirmware, dead easy-firmware, and unreachable CN mirrors (iteye ×2, CSDN ×1 — all Cloudflare 521 from this network).
- FCC databases (fccid.io, fcc.report) bot-blocked from this network; the FCC filing **QISFTN-B19** (with internal photos) remains the primary regulatory source (already cited in gap analysis).
- No public FTN-B19 teardown beyond Jiwei/Sohu 2019-08-02 (already cited) and paid TechInsights DDT-1905-806. eWisetech.com unreachable from this network (potential high-res PCB/BOM source for Chinese-market teardowns).

---

## 6. Leads — where and what to search next

Priority order:

1. **4PDA thread (RU forum)** — highest-value lead. Watch GT firmware threads historically post **direct hicloud URLs** (`http://update.hicloud.com/TDS/data/files/p3/s15/G####/g####/v#####/f1/full/Board_Software_Fortuna-...rar` and the OTA XML). Search in a browser: `site:4pda.to "Huawei Watch GT"` or `4pda.to Watch GT прошивка`. Any hicloud URL found can be fetched without an account; use the changelog trick (replace file name with `changelog.xml`) to check if the package is still live.
2. **XDA t/4309313** ("Firmware for Huawei Watch GT 75A model FTN-B19 attempting to update to 1.0.5.22") — needs an XDA account; may contain a real filelist.xml / hicloud URL from an actual update attempt.
3. **XDA t/4350685 attachments 6154830 / 6154820** — the only known public FTN-B19 PCB photos (Dialog BT + STM32 markings). Fetch from live XDA (Wayback has none).
4. **kurdishfirmware.com** — contact via site Contact form or WhatsApp `+9647502160403` to lift the download limit for one file; or create a second free account (limits appear account-bound); or wait for a quota reset. After download: hash + structure check per section 1.
5. **CN mirrors** — `iteye.com/resource/qq_37320554-10624295`, `iteye.com/resource/y358965134-10957964`, `download.csdn.net/download/qq513584158/7389113` (all matched the `05022MEU` build suffix; Cloudflare 521 from this network — try from a CN/mobile network).
6. **Authorized Huawei Health observation** (per gap-analysis recommendation): on a paired phone, an official update leaves `filelist.xml` + `*.bin.apk` in app storage before BLE transfer; preserve and hash it. This yields the only *verified-origin* FTN-B19 package.
7. **GRS remote config** — production checkEx URL is resolved via GRS; an old Health APK (2019–2020 era, e.g. 10.x from Uptodown/APKMirror version history) may hardcode the era-correct endpoint without GRS indirection. Check its strings for `hicloud` + `check`/`update`.
8. **FCC internal photos (QISFTN-B19)** — high-zoom on the RF section may identify the Dialog BLE part number and test pads; exhibit "Internal Photos of E1762".
9. **Dialog BLE part hunt** — search `DA14681`/`DA14585` + huawei watch / `HUAWEI WATCH GT-E3A` FCC; the GT-era Dialog parts are DA14585/DA1468x family.
10. **huaweiupdate.com** — runs a user-sourced firmware collection (email `firmware@huaweiupdate.com`); they published the 1.0.12.26/1.0.90.26 changelogs and may hold the package or a working hicloud link.

---

## 7. Source register

- `kurdishfirmware.com` file pages: ids 14586, 25062, 25063, 25064 (URLs in section 1).
- `huaweiupdate.com` — "Huawei Watch GT getting v1.0.90.26 and v1.0.12.26 update" (2020-08-16).
- `stiwe.com` — "Huawei Watch GT Firmware Update 1.0.12.18 available" (2020-07-19; Wayback 2020-09-17).
- GitHub `cnoim/ltn_b19_1_0_13_20` and `cnoim/jpt_b29_package_3_0_0_97` (release assets: filelist.xml, changelog.xml, bin.apk).
- Huawei Health APK 16.1.5.320 (Uptodown; SHA-256 `fe5a89bc…518bb`); `assets/product_map.json`; classes6.dex strings/bytecode (UpdateBase, Lnjw, Lnju, Lnjr, Lnja, Lnjq, Lnjq$5, Llig, Llih).
- XDA `t/4350685` (Wayback capture 2025-05-26) and `t/4309313` (live only).
- GitHub `ninlith/shiyong` (watchface project, `description.xml` HWHD02).
- Mainline u-boot `drivers/mtd/nand/spi/toshiba.c` (TC58CYG0S3HRAIG/RAIJ); `YTEC-info/CH341A-Softwares` NeoProgrammer devicelist.
- Retail spec cross-check: `istoric-preturi.info/pd/6960857/55023259/...` (16 MB RAM / 128 MB flash).

## 8. Open items

- Download + hash the four kurdishfirmware artifacts; verify filelist.xml component name (`com.huawei.FTN-B19.firmware`) and `.bin.apk` header against section 3.
- Resolve the production checkEx URL (GRS or old-APK) and retry the passive check for Fortuna UUID `a8ab58b1-0893-42ce-8b2d-2de08aed4ab4`.
- Fetch XDA PCB attachments 6154830/6154820; identify Dialog part marking.
- Confirm whether `1.0.95.99` is the last full package served for Fortuna (vs. 1.0.12.26 OTA track).
