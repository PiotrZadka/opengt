# LPv2 codec notes

`src/huawei_lpv2/codec.py` implements framing only. It deliberately does not implement Huawei authentication, bonding, AES, or any BLE transport.

## Field map

| Field | Meaning | Source |
| --- | --- | --- |
| `0x5A` | LPv2 magic byte | `zyv/huawei-lpv2/huawei/protocol.py:224-250`, `Packet.__bytes__()` / `Packet.from_bytes()`; Gadgetbridge `HuaweiPacket.java:354` |
| 2-byte big-endian length | Frame length value; total wire length is `length + 5` | `protocol.py:224-234`; Gadgetbridge `HuaweiPacket.java:380-394` |
| `0x00` slice byte | Unsliced packet marker | Gadgetbridge `HuaweiPacket.java:936-949`, `serializeUnsliced()` |
| `0x01` / `0x02` / `0x03` | First / middle / final slice markers | Gadgetbridge `HuaweiPacket.java:875-929`, `serializeSliced()` |
| Slice sequence byte | Incrementing per-slice sequence/flag; not a generic request ID | Gadgetbridge `serializeSliced()` lines 895-907; Gist section “On sliced packets” |
| Service ID | Outer protocol service identifier | `protocol.py:216-225`; `huawei/services/device_config.py:26-99` |
| Command ID | Command within the service | `protocol.py:216-225`; `device_config.py:148-293` |
| TLV tag + VarInt length + value | Command payload encoding; values may contain nested TLVs | `protocol.py:100-210`; Gadgetbridge `HuaweiTLV.java:49-164` and `VarInt` at lines 426-494 |
| CRC-16 | CRC over all preceding frame bytes, initial value zero | `protocol.py:233-234`, `binascii.crc_hqx`; Gadgetbridge `HuaweiPacket.java:392-395`, `927-929` |

The public test packet is:

```text
5A 00 08 00 01 02 03 03 61 62 63 E1 D3
```

It is `service=1`, `command=2`, and TLV `tag=3, value=abc`. This exact example is from `zyv/huawei-lpv2/huawei/test_protocol.py:181-182`; `tests/test_lpv2_codec.py` decodes and re-encodes it byte-identically.

## Slicing and reassembly

Gadgetbridge's negotiated default slice size is `0xF4` (`HuaweiPacket.ParamsProvider.slicesize`, line 68). `Packet.encode_sliced()` follows `serializeSliced()`:

- the first slice carries service and command IDs;
- middle and final slices carry continuation payload only;
- each slice has its own length and CRC;
- `PacketReassembler` checks slice order and sequence, joins TLV bytes, then decodes the complete TLV list.

`FrameStream` additionally accepts arbitrary BLE/MTU chunks and emits complete CRC-checked frames. No generic request identifier exists in the outer frame; service/command IDs and the protocol's request/response sequencing identify transactions. Request-specific identifiers, when present, live in service-specific TLVs.

## Crypto boundary

The public implementations wrap TLV data in encryption tags 124 (flag), 125 (IV), and 126 (ciphertext). Those fields are intentionally outside this first codec. Authentication/bonding must be implemented and reviewed separately before any FE01 traffic is considered.
