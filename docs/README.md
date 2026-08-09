# Huawei Watch GT reverse engineering

Phase 1 is observation-only. `scripts/ble_observe.py` scans with macOS CoreBluetooth, optionally connects to a uniquely identified Huawei Watch candidate, enumerates GATT, reads only `read` characteristics, and records JSON under `captures/`.

```sh
PYTHONPATH=src .venv/bin/python scripts/ble_observe.py --scan-seconds 20
PYTHONPATH=src .venv/bin/python scripts/ble_observe.py --scan-seconds 20 --connect
PYTHONPATH=src .venv/bin/python scripts/ble_observe.py --scan-seconds 30 --connect --subscribe-notifications --notification-seconds 20
```

The notification mode subscribes only to FE02, decodes LPv2 frames, and does not send FE01 application packets or touch FE03/FE04/3802/4A02.

On macOS, the BLE identifier printed by Bleak is normally a CoreBluetooth UUID rather than a hardware MAC address.
