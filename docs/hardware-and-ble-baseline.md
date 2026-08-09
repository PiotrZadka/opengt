# Hardware and BLE baseline

> Observation-only baseline. No firmware update, flash write, undocumented write, or factory reset was attempted.

## Target

- User-reported device: Huawei Watch GT first generation, model `FTN-B19`, firmware `1.0.12.26`.

## macOS environment

- macOS: `14.8.7` (build `23J520`)
- Architecture: `x86_64`
- Python: `3.9.6` (`.venv/bin/python`, virtual environment active)
- Homebrew: `Homebrew 6.0.12`
- Bleak: `1.1.1`

### Bluetooth controller

```text
Bluetooth:

      Bluetooth Controller:
          Address: REDACTED
          State: On
          Chipset: BCM_4350
          Discoverable: Off
          Firmware Version: v134 c5628
          Supported services: 0x392039 < HFP AVRCP A2DP HID Braille LEA AACP GATT SerialPort >
          Transport: UART
          Vendor ID: 0x004C (Apple)
      Other nearby devices: REDACTED
```

## Discovery

- Detected identifier: `REDACTED-COREBLUETOOTH-UUID`
- Identifier type: macOS CoreBluetooth identifiers are UUID-style and should not be treated as a Bluetooth MAC address.
- Advertised name: `HUAWEI WATCH GT-XXX` (public suffix redacted)
- RSSI: `-45` dBm
- TX power: `4`
- Service UUIDs: `none reported`
- Manufacturer data: `{"637": "01 03 00 ff ff"}`
- Service data: `{"00003802-0000-1000-8000-00805f9b34fb": "xx xx xx xx xx xx"}`

## GATT map

- Connected identifier: `REDACTED-COREBLUETOOTH-UUID`
- Notification subscriptions: `none`

### Service `0000180a-0000-1000-8000-00805f9b34fb` (handle `16`, Device Information)

- Characteristic `00002a29-0000-1000-8000-00805f9b34fb` (handle `17`): properties `read`
- Characteristic `00002a23-0000-1000-8000-00805f9b34fb` (handle `19`): properties `read`
- Characteristic `00002a24-0000-1000-8000-00805f9b34fb` (handle `21`): properties `read`
- Characteristic `00002a25-0000-1000-8000-00805f9b34fb` (handle `23`): properties `read`
- Characteristic `00002a26-0000-1000-8000-00805f9b34fb` (handle `25`): properties `read`
- Characteristic `00002a27-0000-1000-8000-00805f9b34fb` (handle `27`): properties `read`
- Characteristic `00002a28-0000-1000-8000-00805f9b34fb` (handle `29`): properties `read`
- Characteristic `00002a2a-0000-1000-8000-00805f9b34fb` (handle `31`): properties `read`

### Service `0000fe86-0000-1000-8000-00805f9b34fb` (handle `42`, HUAWEI Technologies Co.: Ltd.)

- Characteristic `0000fe01-0000-1000-8000-00805f9b34fb` (handle `43`): properties `write, write-without-response`
- Characteristic `0000fe02-0000-1000-8000-00805f9b34fb` (handle `45`): properties `notify`
  - Descriptor `00002902-0000-1000-8000-00805f9b34fb` (handle `47`): Client Characteristic Configuration
- Characteristic `0000fe03-0000-1000-8000-00805f9b34fb` (handle `48`): properties `write, write-without-response`
- Characteristic `0000fe04-0000-1000-8000-00805f9b34fb` (handle `50`): properties `notify`
  - Descriptor `00002902-0000-1000-8000-00805f9b34fb` (handle `52`): Client Characteristic Configuration

### Service `00003802-0000-1000-8000-00805f9b34fb` (handle `768`, Vendor specific)

- Characteristic `00004a02-0000-1000-8000-00805f9b34fb` (handle `769`): properties `notify, read, write, write-without-response`
  - Descriptor `00002902-0000-1000-8000-00805f9b34fb` (handle `771`): Client Characteristic Configuration

## Readable values

- `00002a29-0000-1000-8000-00805f9b34fb`: `48 55 41 57 45 49` (`HUAWEI`)
- `00002a23-0000-1000-8000-00805f9b34fb`: `01 02 03 04 05 5f 00 00`
- `00002a24-0000-1000-8000-00805f9b34fb`: `48 55 41 57 45 49` (`HUAWEI`)
- `00002a25-0000-1000-8000-00805f9b34fb`: `48 55 41 57 45 49` (`HUAWEI`)
- `00002a26-0000-1000-8000-00805f9b34fb`: `31 2e 30 2e 30 2e 31` (`1.0.0.1`)
- `00002a27-0000-1000-8000-00805f9b34fb`: `31 2e 30 2e 30 2e 31` (`1.0.0.1`)
- `00002a28-0000-1000-8000-00805f9b34fb`: `31 2e 30 2e 30 2e 31` (`1.0.0.1`)
- `00002a2a-0000-1000-8000-00805f9b34fb`: `00 00 00 00 00 00`
- `00004a02-0000-1000-8000-00805f9b34fb`: BleakError: Failed to read characteristic 769: Error Domain=CBATTErrorDomain Code=2 "Reading is not permitted." UserInfo={NSLocalizedDescription=Reading is not permitted.}

## Open questions

- The device advertises as `HUAWEI WATCH GT-E3A`; standard model/serial fields are generic `HUAWEI`, so FTN-B19 is not independently verified by GATT yet.
- Standard firmware, hardware, and software revision fields return `1.0.0.1`, not the supplied `1.0.12.26`; determine whether these are placeholders or a different version.
- Is the watch currently paired or connected to Huawei Health/another host?
- Which advertised manufacturer bytes identify FTN-B19 and firmware 1.0.12.26?
- Which writable/notify characteristics are protocol endpoints? They remain untouched in this phase.
- Does the device expose additional services only after pairing or an authenticated session?
