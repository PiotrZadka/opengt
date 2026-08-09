# OpenGT

Software-only reverse engineering and experimentation with the first-generation HUAWEI
WATCH GT (FTN-B19, platform codename **Fortuna**).

This is a hobby research project exploring how much of an old watch can be understood,
customized, and used with an open companion instead of Huawei Health. Custom watchfaces
and documented stock features are the near-term focus; richer displays or native custom
applications are unproven stretch goals. Opening the watch and hardware debug probing are
intentionally out of scope.

## Current state

- Read-only BLE scan and GATT observation are implemented.
- The LPv2 frame/TLV/slicing codec is implemented and tested offline.
- Public Huawei/Gadgetbridge protocol, OTA, firmware-source, hardware, and boot-chain
  evidence is documented.
- No verified public FTN-B19 firmware image or native-code execution path is known.
- No active pairing, notification, weather, or watchface experiment has been run by this
  repository yet.

## Direction

```text
optional local/external data
             |
     open phone companion
             |
         BLE / LPv2
             |
      HUAWEI WATCH GT
```

The staged plan is:

1. validate first-generation Watch GT pairing with an open companion;
2. confirm documented stock operations such as notifications and weather;
3. install a reversible stock-format custom watchface;
4. experiment with user-defined data through supported stock surfaces;
5. assess whether anything richer is technically possible.

See [the software-only roadmap](research/software-only-roadmap.md) for feasibility,
architecture, evidence levels, and safety gates.

## Safety and scope

The watch is a throwaway software research unit, but operations are still staged. Ordinary,
well-understood pairing, capability, notification, weather, and stock watchface operations
are in scope. OTA, flashing, fuzzing, malformed payloads, exploit testing, and native-code
execution require a separate explicit decision. Hardware opening/probing is out of scope.

Read [AGENTS.md](AGENTS.md) before working on the live device.

## Read-only observer

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

PYTHONPATH=src .venv/bin/python scripts/ble_observe.py --scan-seconds 20
PYTHONPATH=src .venv/bin/python scripts/ble_observe.py --scan-seconds 30 --connect
```

The current observer writes no Huawei application packets. Public captures are sanitized;
raw neighborhood scans remain local.

## Tests

```sh
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
```

## Research index

- [Custom firmware gap analysis](research/ftn-b19-custom-firmware-gap-analysis.md)
- [Firmware sources and OTA server](research/ftn-b19-firmware-sources-and-ota-server.md)
- [Huawei UUID and LPv2 protocol research](research/huawei-uuid-protocol.md)
- [Hardware and BLE baseline](docs/hardware-and-ble-baseline.md)
- [LPv2 codec notes](docs/lpv2-codec.md)

## Project status

Research project; expect incomplete model-specific behavior and explicit UNKNOWN findings.
There is no claim that arbitrary live graphics, native applications, or custom firmware are
currently possible. No license has been selected yet.
