# OpenGT

Open companion and stock-watchface experimentation for the first-generation HUAWEI
WATCH GT (FTN-B19, platform codename **Fortuna**).

OpenGT currently turns a stock-format GT1 watchface into a Codex quota desk companion:

- exact weekly Codex quota remaining;
- a 10%-step quota bezel;
- reset countdown in days;
- a native, thin battery ring;
- current time;
- automatic updates through Gadgetbridge without reinstalling the face.

![OpenGT watchface preview](watchfaces/OpenGT/preview/cover.jpg)

## Current status

The complete path has been physically validated on the project watch:

```text
Codex app-server
      |
scripts/opengt-sync
      |
ADB -> Gadgetbridge generic weather integration
      |
Huawei LPv2 / stock weather service
      |
OpenGT.hwt on FTN-B19
```

Gadgetbridge 0.92.2 pairs with the watch, installs and activates the custom HWT, and
updates its bound fields without another watchface upload. The current build is **0.7.2**.

The GT1 renderer has no custom variable API. OpenGT deliberately reuses three stock
weather values:

| Weather value | OpenGT meaning |
| --- | --- |
| current temperature | quota decile `0..10`, selecting one of 11 bezel images |
| maximum temperature | exact quota percentage shown as text |
| minimum temperature | days until quota reset |

The quota ring is therefore quantized to the nearest 10%, while the numeric percentage is
exact. The battery ring uses the watch's native battery ratio and does not depend on the
phone. This prototype replaces genuine weather values while active.

## Install

Requirements:

- Python 3.9+;
- an authenticated `codex` CLI using ChatGPT/Codex credentials;
- Android Debug Bridge (`adb`);
- Gadgetbridge paired and connected to the watch.

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Build the watchface:

```sh
PYTHONPATH=src .venv/bin/python scripts/build_opengt_watchface.py
```

The stable outputs are:

```text
watchfaces/OpenGT/export/OpenGT.bin
watchfaces/OpenGT/export/OpenGT.hwt
```

Copy `OpenGT.hwt` to the phone, open it with Gadgetbridge's FW/App installer, verify that
it is identified as an `HWHD02` 454×454 watchface, and install it.

The builder starts from `watchfaces/OpenGT/base/OpenGT_0.1.0.bin`, a minimal GT1 payload
previously exported by Huawei WatchFace Designer. Subsequent layout, resources, bindings,
and packaging are generated locally by `src/opengt_watchface/builder.py`.

## Synchronize Codex quota

For a USB-connected phone, set `ANDROID_SERIAL` when more than one ADB device is present:

```sh
ANDROID_SERIAL=<adb-serial> ./scripts/opengt-sync
```

For wireless ADB, store the selected endpoint once:

```sh
mkdir -p ~/.config/opengt
printf '%s\n' '<phone-ip>:5555' > ~/.config/opengt/adb-serial
adb connect "$(cat ~/.config/opengt/adb-serial)"
./scripts/opengt-sync
```

Continuous foreground synchronization is also available:

```sh
./scripts/opengt-sync --watch --interval 300
```

The synchronizer reads the authenticated Codex app-server RPC
`account/rateLimits/read`, selects the exact seven-day Codex window, and sends only the
three documented weather values through Gadgetbridge. It does not read or copy Codex
authentication tokens and does not expose arbitrary BLE writes.

## Passive BLE tooling

The original observer remains read-only:

```sh
PYTHONPATH=src .venv/bin/python scripts/ble_observe.py --scan-seconds 20
PYTHONPATH=src .venv/bin/python scripts/ble_observe.py --scan-seconds 30 --connect
PYTHONPATH=src .venv/bin/python scripts/ble_observe.py \
  --scan-seconds 30 --connect \
  --subscribe-notifications --notification-seconds 20
```

It scans with Bleak/CoreBluetooth, reads GATT characteristics, and can subscribe to FE02.
It never writes Huawei application packets.

## Tests

```sh
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
```

The suite covers the LPv2 codec, watchface geometry, GT1 data bindings, generated payload,
and HWT structure.

## Repository map

- `watchfaces/OpenGT/` — source assets, GT1 payload seed, previews, and current build.
- `src/opengt_watchface/` — reproducible OpenGT watchface builder.
- `scripts/opengt-sync` — Codex-to-Gadgetbridge synchronization.
- `src/huawei_lpv2/` — offline LPv2 framing/TLV/slicing codec.
- `scripts/ble_observe.py` — passive BLE/GATT observer.
- `captures/` — reviewed physical-validation and GATT evidence.
- `research/` — source-backed protocol, firmware, OTA, and security findings.

## Research

- [Codex watchface feasibility and physical gate](research/codex-watchface-feasibility.md)
- [Custom firmware gap analysis](research/ftn-b19-custom-firmware-gap-analysis.md)
- [Firmware sources and OTA server](research/ftn-b19-firmware-sources-and-ota-server.md)
- [Huawei UUID and LPv2 protocol research](research/huawei-uuid-protocol.md)
- [Hardware and BLE baseline](docs/hardware-and-ble-baseline.md)
- [LPv2 codec notes](docs/lpv2-codec.md)

## Safety and scope

Ordinary pairing, notification/weather synchronization, passive observation, and
stock-format watchface operations are in scope. OTA, flashing, malformed payloads,
fuzzing, exploit work, and persistent modification require a separate explicit decision.
Opening or electrically probing the watch is out of scope.

See [AGENTS.md](AGENTS.md) before live-device or firmware work.

No license has been selected yet.
