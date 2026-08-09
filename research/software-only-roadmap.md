# FTN-B19 software-only roadmap

Status: planning and source-backed feasibility assessment. No active BLE experiment from
this roadmap has been run yet.

## Goal

Explore how far a first-generation HUAWEI WATCH GT can be customized while it continues to
work with a phone, without Huawei Health and without opening the watch.

Desired capabilities, in order:

1. install custom stock-format watchfaces;
2. pair and synchronize through an open phone companion;
3. send user-defined information through supported stock display surfaces;
4. determine whether useful information can update frequently enough to feel live;
5. explore a native custom application as a stretch goal.

## Proposed architecture

```text
local or external data
          |
 optional data adapters -> Android companion -> BLE/LPv2 -> FTN-B19
```

The watch is not known to provide a general network client. The phone is therefore the
default gateway: it can gather optional local, LAN, or API data, normalize it, and send only
display state over the authenticated Huawei BLE protocol.

## Optional external data

Specific data providers are deliberately not part of the project promise. They may be local
machine metrics, home services, personal APIs, or anything else a user-controlled adapter
can normalize. The watch-facing protocol should consume a small generic display model such
as a title, short lines, numeric values, status, and timestamp rather than provider-specific
credentials or response formats.

Do not put provider session tokens or service credentials on the watch. Collection and
authentication stay on the phone or a trusted gateway.

## Display paths on stock firmware

### A. Notifications

Gadgetbridge's Huawei support can send a title, sender, and body through the documented
notification request. This is the fastest end-to-end proof and supports arbitrary text,
but the result lives in the stock notification UI rather than on the watchface.

### B. Custom watchface plus weather fields

The public FTN-B19 watchface example uses predefined fields including current/min/max
temperature, weather type, battery, heart rate, steps, and unread-message state. A custom
face can label selected weather fields as telemetry and the phone can update well-formed
weather data. This could provide an always-visible low-rate dashboard, subject to numeric
ranges, formatting, refresh behavior, and battery impact that still need testing.

### C. Other stock screens

Music metadata, calendar entries, or other capability-gated Huawei services may provide
additional text surfaces. Their availability and behavior on this exact FTN-B19 build are
UNKNOWN until the open companion completes normal authentication and capability queries.

### D. Arbitrary live pixels

No documented stock LPv2 command or watchface field is known to stream a framebuffer or
arbitrary drawing operations. Frequent notification/weather updates are not equivalent to
a live custom canvas. A genuinely live renderer probably requires a native application,
firmware modification, or a software vulnerability.

## Phone without Huawei Health

Current Gadgetbridge source contains a dedicated first-generation Huawei Watch GT
coordinator and generic Huawei handlers for authentication, notifications, weather, and
watchface/file management. Actual support is capability-dependent. The first live milestone
is therefore compatibility validation, not a rewrite from scratch:

1. pair/authenticate with Gadgetbridge using its normal UI;
2. record the negotiated supported services, commands, and constraints;
3. verify an ordinary notification;
4. verify ordinary weather synchronization;
5. list and install a known-valid stock-format watchface.

These are allowed reviewed stock operations under `AGENTS.md`. Keep active code separate
from the frozen read-only observer.

## Milestones

| Milestone | Outcome | Gate |
| --- | --- | --- |
| M0 | Public, sanitized research baseline | Documentation only |
| M1 | FTN-B19 pairs with Gadgetbridge and reports capabilities | Documented pairing/auth only |
| M2 | A test notification and ordinary weather update appear | Documented stock commands only |
| M3 | A known-valid custom watchface installs and can be restored/removed | Stock-format watchface operations only |
| M4 | A generic adapter exposes normalized user-defined data | Host/phone implementation; no watch risk |
| M5 | User-defined data reaches at least one supported stock display surface | Reviewed stock operations |
| M6 | Determine whether music/calendar/file/app capabilities add richer surfaces | Capability-led research; no guessed commands |
| M7 | Native application or software-only code execution | Separate explicit decision required |

## Native application stretch goal

There is no confirmed third-party application runtime for the first-generation Watch GT.
Generic "app management" code in a modern Huawei companion is not evidence that FTN-B19
accepts native applications. This goal needs one of:

- a previously undocumented, capability-confirmed FTN-B19 app package/runtime;
- an accepted but richer declarative package format;
- a reproducible software-only native-code entry point in a parser, transport, or OTA
  component; or
- a modifiable, verifiably recoverable stock firmware image.

Do not test guessed packages, malformed files, fuzzing payloads, OTA images, or exploit
proofs under the current milestone. Each requires the separate decision defined in
`AGENTS.md`.

## Immediate next step

Stop treating a downloadable firmware image as the sole prerequisite. Validate the open
phone path first: Gadgetbridge pairing, negotiated capabilities, notification, weather,
and a reversible stock-format watchface. Firmware acquisition continues in parallel for
offline static analysis and the native-app stretch goal.
