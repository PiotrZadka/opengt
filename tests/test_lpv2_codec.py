import unittest

from huawei_lpv2.codec import (  # pyright: ignore[reportMissingImports]
    TLV,
    CrcMismatch,
    FrameStream,
    Packet,
    PacketReassembler,
    decode_frame,
    decode_packet,
    decode_tlvs,
    decode_varint,
    encode_varint,
    reassemble,
)

KNOWN_FRAME = bytes.fromhex("5A 00 08 00 01 02 03 03 61 62 63 E1 D3")


class CodecTests(unittest.TestCase):
    def test_known_public_packet_round_trips_byte_identically(self):
        packet = decode_packet(KNOWN_FRAME)
        self.assertEqual((1, 2), (packet.service_id, packet.command_id))
        self.assertEqual((TLV(3, b"abc"),), packet.tlvs)
        self.assertEqual(KNOWN_FRAME, packet.encode())

    def test_known_frame_crc_is_checked(self):
        broken = KNOWN_FRAME[:-1] + bytes((KNOWN_FRAME[-1] ^ 1,))
        with self.assertRaises(CrcMismatch):
            decode_frame(broken)

    def test_public_varint_examples(self):
        values = (0, 1, 127, 128, 8193, 16383, 16384)
        encoded = ("00", "01", "7f", "81 00", "c0 01", "ff 7f", "81 80 00")
        self.assertEqual(
            tuple(bytes.fromhex(item) for item in encoded),
            tuple(encode_varint(item) for item in values),
        )
        self.assertEqual(
            values, tuple(decode_varint(encode_varint(item))[0] for item in values)
        )

    def test_tlv_encoding_and_nested_raw_values(self):
        inner = TLV(1, b"abc")
        outer = TLV(0x8D, inner.encode())
        self.assertEqual((outer,), decode_tlvs(outer.encode()))
        self.assertEqual((inner,), decode_tlvs(decode_tlvs(outer.encode())[0].value))

    def test_stream_decoder_accepts_partial_ble_chunks(self):
        stream = FrameStream()
        frames = []
        for chunk in (KNOWN_FRAME[:2], KNOWN_FRAME[2:7], KNOWN_FRAME[7:]):
            frames.extend(stream.feed(chunk))
        self.assertEqual(1, len(frames))
        self.assertEqual(b"", stream.pending)
        self.assertEqual(Packet(1, 2, (TLV(3, b"abc"),)), reassemble(frames))

    def test_sliced_packet_reassembles_and_preserves_sequence(self):
        packet = Packet(1, 2, (TLV(3, b"x" * 80),))
        wire_frames = packet.encode_sliced(slice_size=24)
        decoded_frames = [decode_frame(frame) for frame in wire_frames]
        self.assertGreater(len(decoded_frames), 2)
        self.assertEqual(1, decoded_frames[0].slice_type)
        self.assertEqual(3, decoded_frames[-1].slice_type)
        self.assertEqual(
            list(range(len(decoded_frames))),
            [frame.sequence for frame in decoded_frames],
        )
        self.assertEqual(packet, reassemble(decoded_frames))

    def test_incremental_reassembler(self):
        packet = Packet(1, 2, (TLV(3, b"y" * 80),))
        reassembler = PacketReassembler()
        results = [reassembler.add(frame) for frame in packet.encode_sliced(24)]
        self.assertEqual([None] * (len(results) - 1) + [packet], results)


if __name__ == "__main__":
    unittest.main()
