# Codex watchface feasibility record

> Historical feasibility record for the gate that preceded implementation. The current
> OpenGT package, build, and synchronization instructions live in [`README.md`](../README.md).

## Executive answer

1. **YES — Can GT1 install our custom watchface?** **PHYSICALLY CONFIRMED:** Gadgetbridge 0.92.2 installed and activated the reviewed `Shiyong_2.1.1.hwt` on this FTN-B19 as a watchface. The installer reported no warning or compatibility error.

2. **YES — Can that watchface display a value controlled by us?** **PHYSICALLY CONFIRMED:** the active Shiyong face displayed synthetic current temperature `42` beside its sun icon after Gadgetbridge received `currentTemp = 315` through `ACTION_GENERIC_WEATHER`. This is semantic reuse of weather, not a custom variable.

3. **YES — Can that value change without reinstalling the watchface?** **PHYSICALLY CONFIRMED:** a second stock weather update with `currentTemp = 346` changed the same active face from `42` to `73`. The HWT installer was not reopened and no watchface reinstall, upload, replacement, or re-selection occurred between values.

4. **YES — Can exact Codex remaining quota and reset time be obtained programmatically?** **CONFIRMED:** OpenAI officially documents Codex app-server RPC `account/rateLimits/read`; each quota window returns integer `usedPercent` and Unix-seconds `resetsAt`. The displayed remaining percentage is `clamp(100 - usedPercent, 0, 100)`, not a token/billing estimate. The app-server command is still marked **experimental**, so a later integration must pin and validate a CLI version rather than call the underlying private backend endpoint directly.

There is **no evidenced clean GT1 custom-data binding, script engine, expression language, or arbitrary variable**. The only supported path found for user-controlled face data is pragmatic reuse of a predefined phone-fed field.

## Watchface architecture

### GT1 package and rendering model

**CONFIRMED GT1 (artifact; not a physical install):** [`ninlith/shiyong` at `621fa6a`](https://github.com/ninlith/shiyong/tree/621fa6adf6cb850d62f9414dfb11af0839c10c21) identifies itself as an FTN-B19 face. Its [`description.xml`](https://github.com/ninlith/shiyong/blob/621fa6adf6cb850d62f9414dfb11af0839c10c21/project/Shiyong/description.xml#L1-L10) selects `HWHD02`; its exported HWT is a ZIP containing:

- `description.xml`;
- optional `preview/cover.jpg` and `preview/icon_small.jpg`;
- `com.huawei.watchface`, the compiled face payload.

The editable project contains PNG resources, `watch_face_info.xml`, and declarative [`watch_face_config.xml`](https://github.com/ninlith/shiyong/blob/621fa6adf6cb850d62f9414dfb11af0839c10c21/project/Shiyong/watchface/watch_face_config.xml). **STRONG EVIDENCE:** the Huawei-authored guide bundled with that project says GT at 454×454 is the original `GT` target, limits a GT face to 25 controls, and describes export as image data (`gui01.bin`) plus nanopb-encoded control metadata and a header. The guide's hosting provenance is not independently authenticated, so it corroborates rather than proves the full format. The public FTN-B19 project itself directly demonstrates fixed resources and fixed `DATA_*` bindings, not native code.

**STRONG EVIDENCE (model-specific guide), corroborated by the FTN-B19 project:** supported control families are:

- single/static image;
- rotating hand;
- circular and linear progress bars;
- dynamic text;
- selected/enumerated image;
- connected text with a fixed separator.

“Dynamic” here means that the stock renderer substitutes a predefined watch-system value. It does **not** mean JavaScript, Lua, expressions, arbitrary variables, or downloadable executable logic.

The GT guide's predefined bindings include:

- time/date: 12/24-hour, minute, second, date, weekday, month and their ratios/digits;
- watch state: battery value/ratio/enumeration and unread-message boolean;
- fitness/sensors: steps, calorie, heart rate and min/max/ratio, intensity time, standing count, VO2 max, pressure, altitude;
- phone-fed weather: current temperature, weather type, PM2.5, and temperature unit; the exact public FTN-B19 example also uses current/min/max temperature and weather type at [lines 92–102](https://github.com/ninlith/shiyong/blob/621fa6adf6cb850d62f9414dfb11af0839c10c21/project/Shiyong/watchface/watch_face_config.xml#L92-L104).

A face's layout and resources change only by replacing/reinstalling a package. Bound stock values can change without reinstalling when the watch or phone updates the corresponding stock data.

### Creation and installation tools

- **STRONG EVIDENCE — compatible authoring:** Huawei WatchFace Designer `10.12.31` for Windows. The copy bundled in the FTN-B19 project has SHA-256 `bf265238da282eda8ad06504b00730b0b5e8ac201590f6eadaaabaae733bb562`; its guide explicitly covers original GT at 454×454. Its executable provenance is not independently authenticated, and it was **not executed** in this research. Verify provenance or isolate it before use.
- **INFERENCE FROM OTHER HUAWEI MODELS — not a GT1 recommendation:** current official Theme Studio documentation creates 466×466 or 408×480 works. Those later resolutions and features, including video/AOD examples, must not be transferred to FTN-B19.
- **STRONG EVIDENCE — transport:** Gadgetbridge snapshot [`0827b056`](https://codeberg.org/Freeyourgadget/Gadgetbridge/src/commit/0827b056b36142184d8c7ff2ce7f20c191d0cbf2) has a [GT1 name-prefix coordinator](https://codeberg.org/Freeyourgadget/Gadgetbridge/src/commit/0827b056b36142184d8c7ff2ce7f20c191d0cbf2/app/src/main/java/nodomain/freeyourgadget/gadgetbridge/devices/huawei/huaweiwatchgt/HuaweiWatchGTCoordinator.java#L28-L42), parses HWT `description.xml` and `com.huawei.watchface` (including older direct binaries), validates `HWHD02` as 454×454, uploads file type `watchface`, confirms it, and activates it. Source support is clear; successful FTN-B19 installation remains unperformed.

## Dynamic data options

### A. Clean solution

**NO / UNKNOWN:** no GT1 evidence exposes a custom key/value slot that a phone can update and a face can bind by user-defined name. A clean `{quotaRemaining, resetsAt}` binding is therefore unavailable on evidenced stock firmware.

### B. Pragmatic solution

**Best-supported proof carrier — current temperature.** Gadgetbridge capability-checks weather service `0x0f`, command `0x01`, negotiates supported fields, and serializes current temperature as a signed byte after subtracting 273 from Kelvin-form `WeatherSpec`. The public FTN-B19 face binds it as `DATA_TEMPERATURE`. Weather sync is separate from watchface upload, so source evidence says a new value does not require reinstalling the face.

**Potentially cleaner numeric carrier — PM2.5.** The model-specific GT guide exposes PM2.5 dynamic text over `0–500`, and Gadgetbridge can send PM2.5 when the watch advertises that weather capability. It avoids pretending a percentage is a temperature, but no public FTN-B19 artifact found here demonstrates that binding and the physical watch's PM2.5 capability is unknown. It is an option to test, not a conclusion.

A phone can precompute `remainingPercent` and `resetsInDays` and place them into two negotiated numeric weather bindings; the face itself does not need to subtract timestamps. Current/min/max temperature provide a plausible second small integer, but this remains semantic abuse and would replace genuine weather values.

### C. Impossible without firmware modification

Arbitrary named variables, phone-supplied arbitrary face text, a Unix timestamp interpreted by the face, a locally evaluated `resetsAt - now` expression, arbitrary pixels, or custom executable face logic are not represented in the known GT1 format. A phone can still periodically send a precomputed number through a stock binding. Notifications can carry arbitrary text but remain in the stock notification UI, not the watchface. The user-mentioned notification runbook was searched for but is absent from this checkout; the completed notification milestone is accepted from the user's physical observation and is not repeated here.

| Option | Clean? | Dynamic? | Reinstall required? | Evidence | Recommendation |
| --- | --- | --- | --- | --- | --- |
| Custom face variable `{quotaRemaining, resetsAt}` | Yes in design; unavailable in stock evidence | Would be | No | **UNKNOWN:** no GT1 binding/service found | Do not plan around it |
| Current weather temperature relabeled as quota | No | Yes, after stock weather sync | No, if GT1 refreshes the active face as expected | **CONFIRMED GT1** field; **STRONG EVIDENCE** Gadgetbridge sender; physical refresh **UNKNOWN** | Use for the first gate experiment |
| PM2.5 relabeled as quota | No, but semantically less awkward than temperature | Yes if negotiated | No | **STRONG EVIDENCE:** GT guide + Gadgetbridge packet; physical GT1 support **UNKNOWN** | Test only after the temperature gate |
| Weather min/max as a second small integer | No | Yes, capability-dependent | No | **CONFIRMED GT1** bindings; exact phone/watch behavior **UNKNOWN** | Possible reset-days carrier; defer until the first gate passes |
| Battery/steps/heart-rate bindings | No for phone quota | Yes, from stock watch state | No | **CONFIRMED GT1** | Not writable quota channels |
| Notification text | No; wrong UI surface | Yes | No | User-confirmed physical milestone | Not a watchface solution |
| Rebuild/reinstall HWT for each value | No | Snapshot only | Yes | Package upload path exists | Reject |
| Script/expression/native renderer | No stock path | Potentially | N/A | **UNKNOWN** undocumented; absent from evidenced GT1 format | Requires a separate firmware/runtime path |

## Codex quota source

### Authoritative interface

**CONFIRMED:** OpenAI's [Codex App Server documentation](https://developers.openai.com/codex/app-server#rate-limits-chatgpt) specifies:

```json
{ "method": "account/rateLimits/read", "id": 2 }
```

Relevant response shape, using the official documentation's illustrative values and reduced to the required fields:

```json
{
  "result": {
    "rateLimits": {
      "primary": {
        "usedPercent": 25,
        "windowDurationMins": 15,
        "resetsAt": 1730947200
      },
      "secondary": null
    }
  }
}
```

The generated first-party schema at Codex commit [`8cabf5a6`](https://github.com/openai/codex/tree/8cabf5a6cf103cebe338d46346e43e3201e64f41) defines [`RateLimitWindow`](https://github.com/openai/codex/blob/8cabf5a6cf103cebe338d46346e43e3201e64f41/codex-rs/app-server-protocol/schema/typescript/v2/RateLimitWindow.ts) as `usedPercent`, optional `windowDurationMins`, and optional `resetsAt`; [`GetAccountRateLimitsResponse`](https://github.com/openai/codex/blob/8cabf5a6cf103cebe338d46346e43e3201e64f41/codex-rs/app-server-protocol/schema/typescript/v2/GetAccountRateLimitsResponse.ts) also supports multiple metered buckets. The CLI computes displayed remaining as `clamp(100 - usedPercent, 0, 100)` in [`status_controls.rs`](https://github.com/openai/codex/blob/8cabf5a6cf103cebe338d46346e43e3201e64f41/codex-rs/tui/src/chatwidget/status_controls.rs#L395-L400). `resetsAt` is Unix seconds; time-to-reset is `max(0, resetsAt - currentUnixSeconds)`.

Codex can expose primary and secondary windows and more than one `limitId`; there is not always one universal percentage. An eventual consumer must select and label the intended backend-reported window rather than combine windows into an estimate.

Local validation with installed `codex-cli 0.147.0` confirmed that the shipped app-server schema contains `account/rateLimits/read`, `usedPercent`, `windowDurationMins`, `resetsAt`, and sparse `account/rateLimits/updated` notifications. Transient personal quota values are deliberately not recorded in this report.

### Authentication, support, and refresh

- **CONFIRMED:** rate-limit reads require ChatGPT/Codex-backend authentication; API-key billing is a different surface and must not be substituted. Official auth docs say credentials are managed by Codex in an OS credential store or `CODEX_HOME/auth.json` (default `~/.codex/auth.json`). Treat that file as a secret; OpenGT should invoke the local authenticated app-server, never parse or copy tokens.
- **CONFIRMED:** the app-server RPC is officially documented. **Qualification:** `codex app-server --help` labels the command experimental, so pin a tested CLI version and tolerate nullable/multiple windows. The direct backend endpoint visible in source is not the integration contract.
- Prefer one long-lived app-server connection: make one read at startup, merge `account/rateLimits/updated` notifications, and re-read after reconnect. If periodic fallback is needed, five minutes is reasonable; compute countdown locally between reads and stop at zero. The first-party TUI treats snapshots older than 15 minutes as stale, so do not present older data as exact.

## Minimal proof-of-concept

**Status: passed on the live watch.** Pairing and arbitrary notification display were already user-confirmed milestones and were not repeated. The validation used only Gadgetbridge's reviewed stock watchface and weather paths—never direct BLE writes, OTA, or firmware operations.

A literal **OpenGT**-labeled package is not prepared here: the only GT1-specific compiler located is an unauthenticated Windows binary bundle, which was inspected but not executed. That does not need to block the capability gate. The reviewed public [`Shiyong_2.1.1.hwt`](https://github.com/ninlith/shiyong/blob/621fa6adf6cb850d62f9414dfb11af0839c10c21/export/Shiyong/Shiyong_2.1.1.hwt) already targets FTN-B19/`HWHD02` and visibly binds `DATA_TEMPERATURE`; its SHA-256 is `35c249020be3977eed8c5b63c77c0eeb0c2a0435db3ce8a174f88b7778840003`. It can prove install plus same-face dynamic refresh before any custom tooling work.

### Prerequisites

1. On the already-paired Gadgetbridge phone, record the Gadgetbridge version/commit, watch firmware, battery level, selected face, and available custom-face slot.
2. Confirm Gadgetbridge initializes the watch, reports 454×454 watchface parameters, and negotiates weather service `0x0f/0x01`. Stop if either capability is absent.
3. Transfer the hash-checked HWT to the Android phone. Set Gadgetbridge temperature units to Celsius and temporarily disable normal weather-provider updates so they cannot overwrite the fixture.
4. Connect the paired Android phone to this host with ADB, or run the equivalent broadcast from a trusted Android test shell. The current CachyOS session has no ADB executable/device connection, so this prerequisite is not presently met.

### Procedure and stop conditions

1. Open the HWT through Android's **Open with → Gadgetbridge FW/App installer**. Verify that Gadgetbridge identifies it as watchface `Shiyong`, version `2.1.1`, 454×454—not firmware/OTA—then install it once. Do not enable unsupported-file installation. Stop on a resolution mismatch, parse error, disconnect, or low-space response.
2. Select the installed face and record its identifier/name. Do not delete stock faces.
3. Send `42 °C` through Gadgetbridge's exported `GenericWeatherReceiver` while its communication service is connected:

   ```sh
   NOW=$(date +%s)
   WEATHER_JSON=$(printf '{"timestamp":%s,"location":"OpenGT test","currentTemp":315,"todayMinTemp":315,"todayMaxTemp":315,"currentCondition":"clear","currentConditionCode":800,"currentHumidity":50,"windSpeed":0,"windDirection":0}' "$NOW")
   adb shell "am broadcast -a nodomain.freeyourgadget.gadgetbridge.ACTION_GENERIC_WEATHER --es WeatherJson '$WEATHER_JSON' nodomain.freeyourgadget.gadgetbridge"
   ```

   `315 - 273 = 42`, matching Gadgetbridge's Huawei serializer. `WeatherJson` is deprecated for new production integrations but remains the documented one-shot test input; this experiment does not make it an OpenGT architecture. Wait for normal weather sync and record whether the active face's temperature field shows `42`.
4. Without opening the installer, changing face, or reinstalling, repeat with a fresh timestamp and all three temperature values set to `346` (`346 - 273 = 73`). Record whether the same installed face now shows `73`.
5. Restore genuine weather (or disable weather), return to the prior face, and retain Gadgetbridge logs/screenshots plus the HWT hash. Delete only the custom face through supported UI if desired.

If the installed Gadgetbridge uses a different application ID, substitute that ID for `nodomain.freeyourgadget.gadgetbridge`. **Pass:** the same installed face changes its bound numeric value `42 → 73`, and Gadgetbridge performs no file upload after step 1. The static `CODEX` / `% LEFT` artwork can then be added with a provenance-verified GT1 authoring tool. **Fail/UNKNOWN:** installation fails, weather capability is absent, only the stock weather screen changes, the face needs re-selection, values are reformatted, or any reinstall is required.

## Physical validation

- **Gadgetbridge:** 0.92.2, versionCode 251; application ID `nodomain.freeyourgadget.gadgetbridge`.
- **Artifact:** `Shiyong_2.1.1.hwt`, SHA-256 `35c249020be3977eed8c5b63c77c0eeb0c2a0435db3ce8a174f88b7778840003`.
- **Install:** installed exactly once as watchface Shiyong 2.1.1 and visibly activated; no installer warning or compatibility error. No separate face identifier was shown.
- **42:** `currentTemp`, `todayMinTemp`, and `todayMaxTemp` were set to `315` through `ACTION_GENERIC_WEATHER`; the active face visibly showed `42` beside its sun icon.
- **73:** the same fields were then set to `346` with a fresh timestamp; the same active face visibly changed to `73`.
- **Reinstall:** none between values; the installer was not reopened and the face was not replaced, uploaded again, changed, or reselected.
- **Result:** **PASS** — the same stock GT1 custom watchface can update a phone-controlled value from `42` to `73` without reinstalling.
- **Evidence:** `captures/physical-validation-20260810T084426Z/install-record.txt`, `weather-42-broadcast.txt`, `weather-42-logcat.txt`, `weather-73-broadcast.txt`, and `weather-73-logcat.txt`.

## Blockers

- **Physical gate closed:** HWT installation, negotiated weather service `0x0f` responses, and weather-to-active-face refresh are physically confirmed on this watch.
- **Android control path established for this test:** CachyOS `android-tools` 37.0.0-1.1 supplied ADB 1.0.41; the phone was visible as an authorized USB device. Direct Linux BLE writes were not used.
- **Tool provenance:** the located GT1-compatible designer is a third-party-hosted Windows bundle with no independently verified distribution hash. Current official Theme Studio has no Linux build and its GT1 export compatibility is unproven.
- **No clean channel:** predefined phone-fed weather fields can carry integers, but no arbitrary GT1 variable, text binding, or expression exists in the evidenced format. Using weather would displace genuine weather data.
- **Model-specific uncertainty:** current Gadgetbridge's Huawei upload path is shared across models; source presence does not prove every GT1 firmware branch accepts it. The passive baseline also did not independently resolve the user-reported FTN-B19 / firmware identity discrepancy.

The requested notification runbook is absent from this checkout, remote branch history, stashes, and nearby project files. That missing document does not block this gate because the notification milestone is accepted as a completed physical observation.

### Concise source register

- **Huawei/GT1:** [official FTN-B19 quick-start page](https://consumer.huawei.com/cn/support/content/zh-cn00732834/); [official current Theme Studio codelab](https://developer.huawei.com/consumer/en/codelab/theme-Watchface/index.html) (later-model comparison only); Huawei WatchFace Designer guide bundled, not executed, in [`ninlith/shiyong@621fa6a`](https://github.com/ninlith/shiyong/blob/621fa6adf6cb850d62f9414dfb11af0839c10c21/tools/hw-wfdesigner-10.12.31.zip).
- **Exact GT1 artifact:** [`description.xml`](https://github.com/ninlith/shiyong/blob/621fa6adf6cb850d62f9414dfb11af0839c10c21/project/Shiyong/description.xml) and [`watch_face_config.xml`](https://github.com/ninlith/shiyong/blob/621fa6adf6cb850d62f9414dfb11af0839c10c21/project/Shiyong/watchface/watch_face_config.xml).
- **Gadgetbridge `0827b056`:** [GT1 coordinator](https://codeberg.org/Freeyourgadget/Gadgetbridge/src/commit/0827b056b36142184d8c7ff2ce7f20c191d0cbf2/app/src/main/java/nodomain/freeyourgadget/gadgetbridge/devices/huawei/huaweiwatchgt/HuaweiWatchGTCoordinator.java), [HWT parser](https://codeberg.org/Freeyourgadget/Gadgetbridge/src/commit/0827b056b36142184d8c7ff2ce7f20c191d0cbf2/app/src/main/java/nodomain/freeyourgadget/gadgetbridge/service/devices/huawei/HuaweiFwHelper.java#L321-L378), [installer validation](https://codeberg.org/Freeyourgadget/Gadgetbridge/src/commit/0827b056b36142184d8c7ff2ce7f20c191d0cbf2/app/src/main/java/nodomain/freeyourgadget/gadgetbridge/devices/huawei/HuaweiInstallHandler.java#L196-L245), [weather packet](https://codeberg.org/Freeyourgadget/Gadgetbridge/src/commit/0827b056b36142184d8c7ff2ce7f20c191d0cbf2/app/src/main/java/nodomain/freeyourgadget/gadgetbridge/devices/huawei/packets/Weather.java#L277-L344), [current-weather request](https://codeberg.org/Freeyourgadget/Gadgetbridge/src/commit/0827b056b36142184d8c7ff2ce7f20c191d0cbf2/app/src/main/java/nodomain/freeyourgadget/gadgetbridge/service/devices/huawei/requests/SendWeatherCurrentRequest.java#L42-L75), [official installer instructions](https://gadgetbridge.org/internals/features/installer/), and [official generic weather integration](https://gadgetbridge.org/internals/development/weather-support/).
- **OpenAI/Codex:** [official app-server rate-limit docs](https://developers.openai.com/codex/app-server#rate-limits-chatgpt), [official authentication docs](https://developers.openai.com/codex/auth), and open-source Codex [`8cabf5a6`](https://github.com/openai/codex/tree/8cabf5a6cf103cebe338d46346e43e3201e64f41) protocol/schema/UI sources cited above. Local validation used release `codex-cli 0.147.0` (tag commit [`3ed6f04f`](https://github.com/openai/codex/tree/3ed6f04f6bf8b7c46299d1cb1ff99c74ce21a51d)).

## Recommendation

**The physical feasibility gate passed:** the reviewed, hash-pinned FTN-B19 Shiyong face
changed `42 → 73` through Gadgetbridge weather updates without reinstalling. That gate now
feeds the implemented OpenGT watchface and synchronizer documented in the repository
README; this report remains the evidence and source record for the original decision.
