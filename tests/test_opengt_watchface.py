import math
import struct
import unittest
import zipfile
from pathlib import Path
from typing import Iterator, Union, cast

from opengt_watchface import builder  # pyright: ignore[reportMissingImports]

ProtobufValue = Union[int, bytes]


def protobuf_fields(payload: bytes) -> Iterator[tuple[int, int, ProtobufValue]]:
    position = 0
    while position < len(payload):
        tag, position = builder._read_varint(payload, position)
        field_number = tag >> 3
        wire_type = tag & 7
        if wire_type == 0:
            value, position = builder._read_varint(payload, position)
        elif wire_type == 2:
            size, position = builder._read_varint(payload, position)
            value = payload[position : position + size]
            position += size
        else:
            raise AssertionError(f"unexpected protobuf wire type: {wire_type}")
        yield field_number, wire_type, value


def compiled_circle_properties(path: Path) -> dict[str, tuple[int, int, int]]:
    payload = path.read_bytes()
    protobuf_size = struct.unpack_from("<H", payload, 2)[0]
    protobuf = payload[16 : 16 + protobuf_size]
    circles: dict[str, tuple[int, int, int]] = {}

    for field_number, wire_type, value in protobuf_fields(protobuf):
        if field_number != 1 or wire_type != 2 or not isinstance(value, bytes):
            continue
        widget_fields = list(protobuf_fields(value))
        is_circle = any(
            field == 1 and wire == 0 and item == 2
            for field, wire, item in widget_fields
        )
        if not is_circle:
            continue
        circle = next(
            item
            for field, wire, item in widget_fields
            if field == 4 and wire == 2 and isinstance(item, bytes)
        )
        circle_fields = list(protobuf_fields(circle))
        resource = next(
            item.decode()
            for field, wire, item in circle_fields
            if field == 1 and wire == 2 and isinstance(item, bytes)
        )
        integers = {
            field: item
            for field, wire, item in circle_fields
            if wire == 0 and isinstance(item, int)
        }
        data_type = integers[14]
        start_angle = integers[10]
        end_angle = integers[11]
        if start_angle >= 1 << 63:
            start_angle -= 1 << 64
        if end_angle >= 1 << 63:
            end_angle -= 1 << 64
        circles[resource] = (data_type, start_angle, end_angle)
    return circles


def compiled_quota_selected_data_type(path: Path) -> int:
    payload = path.read_bytes()
    protobuf_size = struct.unpack_from("<H", payload, 2)[0]
    protobuf = payload[16 : 16 + protobuf_size]
    for field_number, wire_type, value in protobuf_fields(protobuf):
        if field_number != 1 or wire_type != 2 or not isinstance(value, bytes):
            continue
        widget_fields = list(protobuf_fields(value))
        if not any(
            field == 1 and wire == 0 and item == 6
            for field, wire, item in widget_fields
        ):
            continue
        selected = next(
            (
                item
                for field, wire, item in widget_fields
                if field == 8 and wire == 2 and isinstance(item, bytes)
            ),
            b"",
        )
        selected_fields = list(protobuf_fields(selected))
        resources = next(
            (
                item
                for field, wire, item in selected_fields
                if field == 10 and wire == 2 and isinstance(item, bytes)
            ),
            b"",
        )
        if b"012" in resources and b"022" in resources:
            return next(
                item
                for field, wire, item in selected_fields
                if field == 3 and wire == 0 and isinstance(item, int)
            )
    raise AssertionError("compiled quota selected-image widget was not found")


def compiled_text_data_types(path: Path) -> dict[int, int]:
    payload = path.read_bytes()
    protobuf_size = struct.unpack_from("<H", payload, 2)[0]
    protobuf = payload[16 : 16 + protobuf_size]
    result: dict[int, int] = {}
    for field_number, wire_type, value in protobuf_fields(protobuf):
        if field_number != 1 or wire_type != 2 or not isinstance(value, bytes):
            continue
        widget_fields = list(protobuf_fields(value))
        if not any(
            field == 1 and wire == 0 and item == 3
            for field, wire, item in widget_fields
        ):
            continue
        text = next(
            (
                item
                for field, wire, item in widget_fields
                if field == 5 and wire == 2 and isinstance(item, bytes)
            ),
            b"",
        )
        integers = {
            field: item
            for field, wire, item in protobuf_fields(text)
            if wire == 0 and isinstance(item, int)
        }
        if integers.get(1) in (163, 215):
            result[integers[1]] = integers[8]
    return result


class OpenGTWatchfaceTests(unittest.TestCase):
    def test_quota_is_rounded_to_nearest_ring_decile(self):
        self.assertEqual(0, builder.quota_decile(0))
        self.assertEqual(4, builder.quota_decile(43))
        self.assertEqual(7, builder.quota_decile(66))
        self.assertEqual(10, builder.quota_decile(100))

    def test_ring_is_a_thick_continuous_bezel_with_dark_ticks(self):
        image = builder.ring_image(40)

        def radial_pixels(angle: float) -> Iterator[tuple[int, int, int, int]]:
            for radius in range(190, 227):
                radians = math.radians(angle - 90)
                x = round(builder.CENTER + radius * math.cos(radians))
                y = round(builder.CENTER + radius * math.sin(radians))
                pixel = image.getpixel((x, y))
                if not isinstance(pixel, tuple) or len(pixel) != 4:
                    raise AssertionError("ring image is not RGBA")
                yield cast(tuple[int, int, int, int], pixel)

        bright_clockwise_from_north = sum(
            alpha > 0 and red > 220 and 50 < green < 180 and blue < 80
            for red, green, blue, alpha in radial_pixels(45)
        )
        bright_counterclockwise_from_north = sum(
            alpha > 0 and red > 220 and 50 < green < 180 and blue < 80
            for red, green, blue, alpha in radial_pixels(315)
        )
        dark_major_tick = sum(
            alpha == 255 and red < 10 and green < 10 and blue < 10
            for red, green, blue, alpha in radial_pixels(30)
        )

        self.assertGreaterEqual(bright_clockwise_from_north, 24)
        self.assertEqual(0, bright_counterclockwise_from_north)
        self.assertGreaterEqual(dark_major_tick, 24)

    def test_battery_ring_is_thinner_and_touches_quota_ring(self):
        image = builder.battery_ring_image(80)
        self.assertEqual(builder.RING_INNER_RADIUS, builder.BATTERY_OUTER_RADIUS)
        self.assertLess(
            builder.BATTERY_OUTER_RADIUS - builder.BATTERY_INNER_RADIUS,
            builder.RING_OUTER_RADIUS - builder.RING_INNER_RADIUS,
        )
        active_x, active_y = builder.polar_point(90, 191)
        inactive_x, inactive_y = builder.polar_point(330, 191)
        active = image.getpixel((round(active_x), round(active_y)))
        inactive = image.getpixel((round(inactive_x), round(inactive_y)))
        self.assertEqual(builder.BATTERY_ORANGE, active)
        self.assertEqual(builder.BATTERY_TRACK, inactive)

    def test_compiled_rings_use_temperature_selection_and_battery_progress(self):
        binary = builder.BINARY_OUTPUT
        self.assertEqual(
            builder.DATA_TEMPERATURE,
            compiled_quota_selected_data_type(binary),
        )
        self.assertEqual(
            {"023": (builder.DATA_POWER_RATIO, 0, 360)},
            compiled_circle_properties(binary),
        )
        self.assertEqual(
            {
                163: builder.DATA_TEMPERATURE_MAX,
                215: builder.DATA_TEMPERATURE_MIN,
            },
            compiled_text_data_types(binary),
        )
        self.assertEqual(20, builder.DATA_TEMPERATURE_MAX)
        self.assertEqual(21, builder.DATA_TEMPERATURE_MIN)
        self.assertEqual(4, builder.DATA_TEMPERATURE)
        self.assertEqual(163, builder.DATA_POWER_RATIO)

    def test_hwt_contains_gt1_payload_and_matching_version(self):
        package = builder.PACKAGE_OUTPUT
        with zipfile.ZipFile(package) as archive:
            self.assertEqual(
                {
                    "com.huawei.watchface",
                    "description.xml",
                    "preview/",
                    "preview/cover.jpg",
                    "preview/icon_small.jpg",
                },
                set(archive.namelist()),
            )
            description = archive.read("description.xml").decode()
        self.assertIn("<screen>HWHD02</screen>", description)
        self.assertIn(f"<version>{builder.VERSION}</version>", description)


if __name__ == "__main__":
    unittest.main()
