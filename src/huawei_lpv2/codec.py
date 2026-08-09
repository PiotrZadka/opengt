"""Huawei LPv2 framing, TLV, and slicing support.

This module intentionally contains no authentication or cryptography.  It only
handles the wire envelope needed to inspect captured FE02 bytes offline.
"""

from __future__ import annotations

import binascii
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Union

MAGIC = 0x5A
DEFAULT_SLICE_SIZE = 0xF4
UNSLICED = 0x00
SLICE_FIRST = 0x01
SLICE_MIDDLE = 0x02
SLICE_LAST = 0x03

BytesLike = Union[bytes, bytearray, memoryview]


class CodecError(ValueError):
    """Base class for malformed LPv2 data."""


class IncompleteFrame(CodecError):
    """More bytes are needed before a frame or TLV can be decoded."""


class MalformedFrame(CodecError):
    """A frame violates the LPv2 envelope rules."""


class CrcMismatch(MalformedFrame):
    """The frame CRC does not match its contents."""


def encode_varint(value: int) -> bytes:
    """Encode the big-endian base-128 length used by Huawei TLVs."""
    if value < 0:
        raise ValueError("varint value must be non-negative")

    encoded = [value & 0x7F]
    value >>= 7
    while value:
        encoded.append((value & 0x7F) | 0x80)
        value >>= 7
    return bytes(reversed(encoded))


def decode_varint(data: BytesLike, offset: int = 0) -> tuple[int, int]:
    """Return ``(value, next_offset)`` for one Huawei variable integer."""
    raw = bytes(data)
    if offset < 0 or offset > len(raw):
        raise ValueError("varint offset is outside the input")

    value = 0
    for index in range(offset, len(raw)):
        byte = raw[index]
        value = (value << 7) | (byte & 0x7F)
        if not byte & 0x80:
            return value, index + 1
    raise IncompleteFrame("unterminated TLV length")


@dataclass(frozen=True)
class TLV:
    """One Huawei tag-length-value item; nested values remain raw bytes."""

    tag: int
    value: bytes = b""

    def __post_init__(self) -> None:
        if not 0 <= self.tag <= 0xFF:
            raise ValueError("TLV tag must fit in one byte")
        object.__setattr__(self, "value", bytes(self.value))

    def encode(self) -> bytes:
        return bytes((self.tag,)) + encode_varint(len(self.value)) + self.value

    @classmethod
    def decode(cls, data: BytesLike, offset: int = 0) -> tuple[TLV, int]:
        raw = bytes(data)
        if offset >= len(raw):
            raise IncompleteFrame("missing TLV tag")
        tag = raw[offset]
        length, value_offset = decode_varint(raw, offset + 1)
        end = value_offset + length
        if end > len(raw):
            raise IncompleteFrame("TLV value is truncated")
        return cls(tag, raw[value_offset:end]), end


def encode_tlvs(tlvs: Iterable[TLV]) -> bytes:
    return b"".join(tlv.encode() for tlv in tlvs)


def decode_tlvs(data: BytesLike) -> tuple[TLV, ...]:
    raw = bytes(data)
    tlvs = []
    offset = 0
    while offset < len(raw):
        tlv, offset = TLV.decode(raw, offset)
        tlvs.append(tlv)
    return tuple(tlvs)


def crc16(data: BytesLike) -> int:
    """CRC-16 used by the public LPv2 implementations."""
    return binascii.crc_hqx(bytes(data), 0)


def _validate_identifier(value: int, name: str) -> None:
    if not 0 <= value <= 0xFF:
        raise ValueError(f"{name} must fit in one byte")


def _build_frame(slice_type: int, sequence: int | None, body: bytes) -> bytes:
    _validate_identifier(slice_type, "slice type")
    if slice_type not in (UNSLICED, SLICE_FIRST, SLICE_MIDDLE, SLICE_LAST):
        raise ValueError("unsupported slice type")
    if slice_type == UNSLICED and sequence is not None:
        raise ValueError("unsliced frames do not have a sequence byte")
    if slice_type != UNSLICED and sequence is None:
        raise ValueError("sliced frames require a sequence byte")
    if sequence is not None:
        _validate_identifier(sequence, "slice sequence")

    header = bytes((MAGIC, 0, 0, slice_type))
    if sequence is not None:
        header += bytes((sequence,))
    without_crc = header + body
    declared_length = len(without_crc) - 3
    if not 0 <= declared_length <= 0xFFFF:
        raise ValueError("frame is too large for the LPv2 length field")
    without_crc = without_crc[:1] + declared_length.to_bytes(2, "big") + without_crc[3:]
    return without_crc + crc16(without_crc).to_bytes(2, "big")


@dataclass(frozen=True)
class Frame:
    """One complete outer LPv2 frame or one slice of a packet."""

    slice_type: int
    sequence: int | None
    service_id: int | None
    command_id: int | None
    fragment: bytes
    declared_length: int

    @property
    def sliced(self) -> bool:
        return self.slice_type != UNSLICED


def decode_frame(data: BytesLike, *, allow_trailing: bool = False) -> Frame:
    """Decode and CRC-check one complete frame."""
    raw = bytes(data)
    if len(raw) < 3:
        raise IncompleteFrame("LPv2 frame header is truncated")
    if raw[0] != MAGIC:
        raise MalformedFrame(f"bad magic 0x{raw[0]:02x}, expected 0x{MAGIC:02x}")

    declared_length = int.from_bytes(raw[1:3], "big")
    total_length = declared_length + 5
    if total_length < 8:
        raise MalformedFrame("LPv2 frame is shorter than its service/command envelope")
    if len(raw) < total_length:
        raise IncompleteFrame("LPv2 frame is truncated")
    if not allow_trailing and len(raw) != total_length:
        raise MalformedFrame("extra bytes follow the LPv2 frame")
    raw = raw[:total_length]

    expected_crc = int.from_bytes(raw[-2:], "big")
    actual_crc = crc16(raw[:-2])
    if actual_crc != expected_crc:
        raise CrcMismatch(f"CRC mismatch: 0x{actual_crc:04x} != 0x{expected_crc:04x}")

    slice_type = raw[3]
    if slice_type == UNSLICED:
        sequence = None
        body = raw[4:-2]
        if len(body) < 2:
            raise MalformedFrame("unsliced frame lacks service/command IDs")
        service_id, command_id = body[:2]
        fragment = body[2:]
    elif slice_type in (SLICE_FIRST, SLICE_MIDDLE, SLICE_LAST):
        if len(raw) < 7:
            raise MalformedFrame("sliced frame lacks its sequence byte")
        sequence = raw[4]
        body = raw[5:-2]
        if slice_type == SLICE_FIRST:
            if len(body) < 2:
                raise MalformedFrame("first slice lacks service/command IDs")
            service_id, command_id = body[:2]
            fragment = body[2:]
        else:
            service_id = command_id = None
            fragment = body
    else:
        raise MalformedFrame(f"unsupported slice type 0x{slice_type:02x}")

    return Frame(
        slice_type=slice_type,
        sequence=sequence,
        service_id=service_id,
        command_id=command_id,
        fragment=fragment,
        declared_length=declared_length,
    )


@dataclass(frozen=True)
class Packet:
    """A complete Huawei service/command packet with decoded TLVs."""

    service_id: int
    command_id: int
    tlvs: tuple[TLV, ...] = ()

    def __post_init__(self) -> None:
        _validate_identifier(self.service_id, "service ID")
        _validate_identifier(self.command_id, "command ID")
        object.__setattr__(self, "tlvs", tuple(self.tlvs))

    @property
    def tlv_bytes(self) -> bytes:
        return encode_tlvs(self.tlvs)

    def encode(self) -> bytes:
        """Encode one unsliced frame."""
        return _build_frame(
            UNSLICED, None, bytes((self.service_id, self.command_id)) + self.tlv_bytes
        )

    def encode_sliced(self, slice_size: int = DEFAULT_SLICE_SIZE) -> tuple[bytes, ...]:
        """Encode using Gadgetbridge's first/middle/last slice format."""
        if slice_size < 9:
            raise ValueError("slice size is too small for the LPv2 envelope")

        max_body_size = slice_size - 7  # 5-byte sliced header + 2-byte CRC
        tlv = self.tlv_bytes
        packet_count = (len(tlv) + 2 + max_body_size - 1) // max_body_size
        if packet_count <= 1:
            return (self.encode(),)

        frames = []
        offset = 0
        for index in range(packet_count):
            slice_type = (
                SLICE_FIRST
                if index == 0
                else SLICE_LAST
                if index == packet_count - 1
                else SLICE_MIDDLE
            )
            capacity = max_body_size - 2 if index == 0 else max_body_size
            fragment = tlv[offset : offset + capacity]
            offset += len(fragment)
            body = (
                bytes((self.service_id, self.command_id)) + fragment
                if slice_type == SLICE_FIRST
                else fragment
            )
            frames.append(_build_frame(slice_type, index & 0xFF, body))
        return tuple(frames)


class FrameStream:
    """Extract complete LPv2 frames from arbitrary BLE/MTU-sized chunks."""

    def __init__(self) -> None:
        self._buffer = bytearray()

    @property
    def pending(self) -> bytes:
        return bytes(self._buffer)

    def feed(self, data: BytesLike) -> tuple[Frame, ...]:
        self._buffer.extend(bytes(data))
        frames = []
        while self._buffer:
            if self._buffer[0] != MAGIC:
                raise MalformedFrame("stream does not begin with LPv2 magic")
            if len(self._buffer) < 3:
                break
            total_length = int.from_bytes(self._buffer[1:3], "big") + 5
            if total_length < 8:
                raise MalformedFrame("stream contains an invalid LPv2 length")
            if len(self._buffer) < total_length:
                break
            raw = bytes(self._buffer[:total_length])
            del self._buffer[:total_length]
            frames.append(decode_frame(raw))
        return tuple(frames)


class PacketReassembler:
    """Reassemble one sliced packet at a time from decoded frames."""

    def __init__(self) -> None:
        self._service_id: int | None = None
        self._command_id: int | None = None
        self._next_sequence: int | None = None
        self._fragments = []

    def add(self, frame: Frame | BytesLike) -> Packet | None:
        if not isinstance(frame, Frame):
            frame = decode_frame(frame)

        if not self._fragments:
            if frame.slice_type == UNSLICED:
                assert frame.service_id is not None and frame.command_id is not None
                return Packet(
                    frame.service_id, frame.command_id, decode_tlvs(frame.fragment)
                )
            if frame.slice_type != SLICE_FIRST:
                raise MalformedFrame("sliced packet must begin with a first slice")
            assert frame.service_id is not None and frame.command_id is not None
            self._service_id = frame.service_id
            self._command_id = frame.command_id
            self._next_sequence = (frame.sequence + 1) & 0xFF  # type: ignore[operator]
            self._fragments.append(frame.fragment)
            return None

        if frame.slice_type not in (SLICE_MIDDLE, SLICE_LAST):
            raise MalformedFrame("unexpected frame while a sliced packet is pending")
        if frame.sequence != self._next_sequence:
            raise MalformedFrame(
                f"slice sequence mismatch: {frame.sequence} != {self._next_sequence}"
            )
        self._fragments.append(frame.fragment)
        self._next_sequence = (frame.sequence + 1) & 0xFF  # type: ignore[operator]
        if frame.slice_type != SLICE_LAST:
            return None

        assert self._service_id is not None and self._command_id is not None
        packet = Packet(
            self._service_id,
            self._command_id,
            decode_tlvs(b"".join(self._fragments)),
        )
        self._service_id = self._command_id = self._next_sequence = None
        self._fragments = []
        return packet


def reassemble(frames: Iterable[Frame | BytesLike]) -> Packet:
    """Decode/reassemble exactly one complete packet from frames."""
    reassembler = PacketReassembler()
    packet = None
    for frame in frames:
        result = reassembler.add(frame)
        if result is not None:
            if packet is not None:
                raise MalformedFrame("more than one packet was supplied")
            packet = result
    if packet is None:
        raise IncompleteFrame("sliced packet is incomplete")
    return packet


def decode_packet(data: BytesLike) -> Packet:
    """Decode exactly one packet, including sliced frames and stream chunks."""
    stream = FrameStream()
    frames = stream.feed(data)
    if stream.pending:
        raise IncompleteFrame("packet data ended before a complete frame")
    if not frames:
        raise IncompleteFrame("packet data is empty")
    return reassemble(frames)
