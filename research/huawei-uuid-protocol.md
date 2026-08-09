# Huawei BLE UUID research

Status: source research only. No characteristic write, firmware operation, pairing operation, or notification subscription was performed for this research pass.

## Sources checked

### Current Gadgetbridge

- Repository: <https://codeberg.org/Freeyourgadget/Gadgetbridge>
- Snapshot: `3f0bb26cc331aba34c8bbcea85b48b68d5b3e909` (`master`, fetched locally under `/tmp/gadgetbridge-current`)
- The source uses `BASE_UUID = "0000%s-0000-1000-8000-00805f9b34fb"`, so the full UUIDs are represented by short IDs in `HuaweiConstants.java`.

### Public Huawei/Honor protocol implementations

- `zyv/huawei-lpv2`, snapshot `22532a8c40293725ae27b92499c9aa51828e915a`:
  <https://github.com/zyv/huawei-lpv2>
- `psolyca/huawei-lpv2`, snapshot `38bf2fd7e5a21978ffacc4bc58923c7c2389c7ab`:
  <https://github.com/psolyca/huawei-lpv2>
- Honor Band 4 / Huawei LPv2/LPv3 reverse-engineering notes:
  <https://gist.github.com/psolyca/68fdfee0960737c1234f8d7f7a6c143a>
- Public GATT transcript for a Huawei Watch GT-DEE:
  <https://stackoverflow.com/questions/64659988/how-to-read-a-bmp-packet-from-huawei-watch-gt-dee-by-gatttool>

The two `huawei-lpv2` repositories contain the same FE01/FE02 transport constants and code pattern. The Gist documents FE03/FE04 but does not implement them.

## Match inventory

| UUID | Current Gadgetbridge | Public protocol/code matches | Local watch observation |
| --- | --- | --- | --- |
| `0000fe86-0000-1000-8000-00805f9b34fb` | Yes, as `FE86` service | GATT transcript; not a `huawei-lpv2` constant | Huawei service, handle 42 |
| `0000fe01-0000-1000-8000-00805f9b34fb` | Yes, as `FE01` write characteristic | `huawei-lpv2` `GATT_WRITE` | write + write-without-response, handle 43 |
| `0000fe02-0000-1000-8000-00805f9b34fb` | Yes, as `FE02` notify characteristic | `huawei-lpv2` `GATT_READ` | notify, handle 45 |
| `0000fe03-0000-1000-8000-00805f9b34fb` | No relevant current-source match | Gist and GATT transcript | write + write-without-response, handle 48 |
| `0000fe04-0000-1000-8000-00805f9b34fb` | No relevant current-source match | Gist and GATT transcript | notify, handle 50 |
| `00003802-0000-1000-8000-00805f9b34fb` | No relevant current-source match | GATT transcript | vendor service, handle 768 |
| `00004a02-0000-1000-8000-00805f9b34fb` | No relevant current-source match | GATT transcript | read/write/write-without-response/notify, handle 769; read returned ATT error 2 |

The current-source search excluded incidental numeric substrings in test vectors and checksum tables; those are not UUID matches.

## Per-UUID source map

### FE86 service

#### Current Gadgetbridge matches

- `app/src/main/java/nodomain/freeyourgadget/gadgetbridge/devices/huawei/HuaweiConstants.java:25`
  - `UUID_SERVICE_HUAWEI_SERVICE = BASE_UUID("FE86")`.
- `.../devices/huawei/HuaweiCoordinator.java:117-119`, `createBLEScanFilters()`
  - Uses FE86 as the Android BLE service scan filter.
- `.../service/devices/huawei/HuaweiLESupport.java:59-64`, constructor
  - Registers FE86 as a supported GATT service.
- `.../devices/huawei/huaweiwatchgt/HuaweiWatchGTCoordinator.java:28-32`, `getSupportedDeviceName()`
  - The first-generation GT coordinator matches the advertised prefix `huawei watch gt-`; it inherits the FE86 scan filter and BLE support.

#### Known purpose/direction

FE86 is the Huawei vendor-specific GATT service that carries the LPv2-style Huawei transport. The service itself has no packet direction; FE01 and FE02 provide the primary command/response paths. The public GT-DEE transcript reports FE86 as service handle range `0x002a-0x0034`.

### FE01 characteristic

#### Current Gadgetbridge matches

- `.../devices/huawei/HuaweiConstants.java:26`
  - `UUID_CHARACTERISTIC_HUAWEI_WRITE = BASE_UUID("FE01")`.
- `.../service/devices/huawei/requests/Request.java:347-353`, `builderWrite()`
  - Serializes every Huawei request and writes it to FE01 for the normal Huawei protocol. The Honor protocol selects a different UUID.

#### Public implementation matches

- `zyv/huawei-lpv2/huawei/protocol.py:66`, `GATT_WRITE`.
- `zyv/huawei-lpv2/band_lpv2.py:91-99`, `Band._send_data()` calls `BleakClient.write_gatt_char(GATT_WRITE, ...)`.
- The `psolyca/huawei-lpv2` fork has the same map at `huawei/protocol.py:39` and `band_lpv2.py:93-101`.
- The Gist's GATT section identifies FE01 as the characteristic used to send messages.

#### Known purpose/direction

Phone/client -> watch command and data transport. The observed properties are write and write-without-response. FE01 is not a readable value channel in the observed watch.

### FE02 characteristic

#### Current Gadgetbridge matches

- `.../devices/huawei/HuaweiConstants.java:27`
  - `UUID_CHARACTERISTIC_HUAWEI_READ = BASE_UUID("FE02")`.
- `.../service/devices/huawei/HuaweiSupportProvider.java:491-506`, BLE `initializeDevice()`
  - Enables notifications on FE02 before sending link-parameter/authentication traffic.
- `.../service/devices/huawei/HuaweiSupportProvider.java:727-735`, `initializeDeviceConfigure()`
  - Enables FE02 again during post-authentication configuration unless the new protocol is forced.
- `.../service/devices/huawei/HuaweiSupportProvider.java:1176-1179`, `onCharacteristicChanged()`
  - Hands notification bytes to `ResponseManager` for packet matching/parsing.
- `.../service/devices/huawei/HuaweiLESupport.java:86-88`, `onCharacteristicChanged()`
  - Forwards Android GATT characteristic-change data to the support provider.

#### Public implementation matches

- `zyv/huawei-lpv2/huawei/protocol.py:67`, `GATT_READ`.
- `zyv/huawei-lpv2/band_lpv2.py:101-103`, `_receive_data()` parses incoming bytes.
- `zyv/huawei-lpv2/band_lpv2.py:128-138`, `connect()`/`disconnect()` enable and disable FE02 notifications.
- The Gist identifies FE02 as the received-message characteristic.

#### Known purpose/direction

Watch -> phone response/notification transport. Despite the name `READ`, the public implementation uses notifications, not GATT reads. The observed property is notify and a CCCD descriptor is present.

### FE03 characteristic

There is no relevant FE03 constant or use in the current Gadgetbridge Huawei source, and no FE03 code path in either `huawei-lpv2` repository.

The public GATT transcript reports FE03 with properties `0x0c`, i.e. write + write-without-response. The reverse-engineering Gist loosely labels FE03 as `notify`, which conflicts with both the transcript and this watch's live GATT properties. Treat the transcript/live properties as device-specific evidence and the Gist label as unconfirmed. Purpose and packet framing are not established by the searched code.

### FE04 characteristic

There is no relevant FE04 constant or use in the current Gadgetbridge Huawei source, and no FE04 code path in either `huawei-lpv2` repository.

The public GATT transcript reports FE04 with properties `0x10` (notify); the Gist calls it unknown. This watch also exposes FE04 as notify-only with a CCCD. It is therefore a plausible alternate notification channel, but no searched implementation identifies its payload or proves that it carries the same LPv2 framing as FE02.

### 3802 service

There is no relevant `00003802` UUID match in current Gadgetbridge or the `huawei-lpv2` code. The GT-DEE GATT transcript reports it as a second primary service beginning at handle `0x0300`. This watch exposes the same service at handle 768 and also advertises service data under that UUID.

Its purpose is not established by the searched implementations. Do not assume it is interchangeable with FE86 or that it uses the LPv2 packet format.

### 4A02 characteristic

There is no relevant `00004a02` UUID match in current Gadgetbridge or the `huawei-lpv2` code. The GT-DEE transcript reports value handle `0x0302`, under 3802, with properties `0x1e` (read, write, write-without-response, notify). This watch exposes the same property set at handle 769 and a CCCD at handle 771.

The Stack Overflow question was looking for heart-rate/BMP data but has no authoritative protocol answer; its comments explicitly say that a Huawei-specific protocol or a BLE capture would be needed. Therefore the characteristic's purpose is unknown. On this watch the explicit read attempt returned `CBATTErrorDomain Code=2` (`Reading is not permitted`), so no value was obtained. No write or notification subscription was attempted.

## Framing and packet direction

The FE01/FE02 path is the only path for which the searched implementations provide a complete framing model:

1. Magic byte `0x5A`.
2. Two-byte big-endian length field.
3. One-byte slice/control field (`0x00` for an unsliced packet).
4. One-byte service ID and one-byte command ID.
5. Variable-length TLV command body.
6. Two-byte big-endian CRC-16 over the packet before the CRC.

Evidence:

- `zyv/huawei-lpv2/huawei/protocol.py:212-250`, `Packet.__bytes__()` and `Packet.from_bytes()`.
- Current Gadgetbridge `.../devices/huawei/HuaweiPacket.java:335-430`, `parseData()`.
- Current Gadgetbridge `.../devices/huawei/HuaweiPacket.java:875-934`, `serializeSliced()` and `serializeUnsliced()`.

Large messages can be split at two layers: the Huawei sliced-packet scheme and BLE/MTU chunks. In the sliced scheme, the current code uses `0x01` for the first slice, `0x02` for intermediate slices, and `0x03` for the final slice, with an additional sequence/flag byte. `Request.doPerform()` writes each resulting chunk to FE01; FE02 notifications are accumulated and parsed on receipt.

The TLV body can be wrapped in encryption tags 124 (encryption flag), 125 (IV), and 126 (ciphertext). Current Gadgetbridge's `HuaweiPacket.serialize()` encrypts by default when the negotiated/settings policy says transactions are encrypted (`HuaweiPacket.java:1087-1110`; `HuaweiTLV.java:394-429`). This framing statement is **not** established for FE03, FE04, 3802, or 4A02.

## Pairing, authentication, and bonding requirements

### LPv2 public implementation

`zyv/huawei-lpv2/band_lpv2.py:142-166`, `Band.handshake()`, performs this sequence over FE01/FE02:

1. Link parameters: service `1`, command `1`; obtains protocol/MTU/frame parameters and a server nonce.
2. Authentication: service `1`, command `19`; sends a client nonce and challenge, then verifies the device response.
3. Bond parameters: service `1`, command `15`; sends client serial/MAC metadata and receives an encryption counter.
4. Bond: service `1`, command `14`; sends an encrypted bonding key and IV.

The corresponding packet builders/parsers are in `huawei/services/device_config.py:148-293`. The implementation derives an authentication response from the negotiated auth version and client/server nonces, then uses a master/secret key and IV for bonding and encrypted transactions.

The Gist describes the same four-step handshake and says communication is encrypted after bonding. It also documents multiple authentication versions (LPv2/LPv3-era devices differ).

### Current Gadgetbridge

- `HuaweiSupportProvider.java:491-506` subscribes to FE02 and starts the link-parameter request.
- `HuaweiSupportProvider.java:516-573` starts authentication setup and status handling.
- `HuaweiSupportProvider.java:600-626` negotiates HiChain/HiChain Lite versus normal mode.
- `HuaweiSupportProvider.java:667-720` performs HiChain, HiChain Lite, or normal auth/bond request chains.
- `HuaweiSupportProvider.java:790-818` creates or loads a per-device secret key.
- `GetHiChainRequest.java:44-74` states that first authentication requires user confirmation on the device; its steps derive/verify tokens and a session key.
- `HuaweiLECoordinator.java:31-42` reports Android link-layer bonding style `BONDING_STYLE_NONE`; this is distinct from Huawei's protocol-level `Bond`/`BondParams` messages.
- `HuaweiCoordinator.java:104-108` defaults transactions to encrypted and selects the original Huawei protocol rather than the newer Honor UUIDs.

This means a plain BLE connection can expose the GATT map, as it did here, but meaningful Huawei protocol traffic is expected to require the Huawei authentication/bonding exchange and then encryption. The exact branch depends on link parameters, auth mode/version, firmware, and whether this is a first connection. The searched code does not prove that the 3802/4A02 channel accepts or requires the same handshake.

## Conclusions for FTN-B19 phase 1

1. FE86/FE01/FE02 are strongly corroborated as the original Huawei LPv2-style transport and match the live GATT map.
2. Current Gadgetbridge directly supports only FE86 plus the FE01/FE02 transport for this protocol family; it does not use FE03, FE04, 3802, or 4A02.
3. Public evidence disagrees about the FE03 label. The live properties and the GT-DEE transcript agree: FE03 is write-capable and FE04 is notify-capable.
4. 3802/4A02 are a separate, currently undocumented path. Their presence and properties match a public GT-DEE transcript, but no searched implementation establishes purpose or framing.
5. No write should be attempted merely because a characteristic is writable. The next safe step is passive capture of existing notifications or an externally supplied Huawei Health/Gadgetbridge trace, not replaying the handshake or sending guessed packets.
