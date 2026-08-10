"""Build the stock-format OpenGT GT1 watchface.

The GT1 renderer has no custom quota variable. OpenGT sends the exact remaining
percentage through the proven maximum-temperature binding and a decile through
the current-temperature binding. The latter selects one of eleven ring states.
"""

from __future__ import annotations

import hashlib
import math
import struct
import zipfile
from pathlib import Path
from typing import Iterable, cast

from PIL import Image, ImageDraw, ImageFont

PROJECT_ROOT = Path(__file__).resolve().parents[2]
WATCHFACE_ROOT = PROJECT_ROOT / "watchfaces" / "OpenGT"
RESOURCES = WATCHFACE_ROOT / "watchface" / "res"
EXPORTS = WATCHFACE_ROOT / "export"
BASE_BINARY = WATCHFACE_ROOT / "base" / "OpenGT_0.1.0.bin"
BINARY_OUTPUT = EXPORTS / "OpenGT.bin"
PACKAGE_OUTPUT = EXPORTS / "OpenGT.hwt"

VERSION = "0.8.0"
SIZE = 454
CENTER = SIZE // 2
BACKGROUND = (2, 3, 3, 255)
ORANGE = (255, 105, 18, 255)
ORANGE_LIGHT = (255, 139, 45, 255)
RING_TRACK = (55, 22, 7, 255)
RING_INNER_RADIUS = 195
RING_OUTER_RADIUS = 226
BATTERY_ORANGE = (255, 166, 52, 255)
BATTERY_TRACK = (39, 21, 10, 255)
BATTERY_INNER_RADIUS = 188
BATTERY_OUTER_RADIUS = RING_INNER_RADIUS
FONT_BOLD = Path("/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf")

# Temperature identifiers are confirmed from compiled GT1 text controls. Current
# temperature carries the ring decile, max carries the exact quota, and min carries
# reset days. Battery ratio comes from a compiled GT1 round-progress control.
DATA_TEMPERATURE_MAX = 20
DATA_TEMPERATURE_MIN = 21
DATA_TEMPERATURE = 4
DATA_POWER_RATIO = 163


def quota_decile(remaining_percent: int) -> int:
    """Return the nearest 10% ring state as an integer from zero to ten."""
    bounded = max(0, min(100, remaining_percent))
    return (bounded + 5) // 10


def font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_BOLD), size)


def draw_centered(
    draw: ImageDraw.ImageDraw,
    position: tuple[int, int],
    text: str,
    selected_font: ImageFont.FreeTypeFont,
    fill: tuple[int, int, int, int],
) -> None:
    draw.text(position, text, font=selected_font, fill=fill, anchor="mm")


def draw_centered_on_baseline(
    draw: ImageDraw.ImageDraw,
    position: tuple[int, int],
    text: str,
    selected_font: ImageFont.FreeTypeFont,
    fill: tuple[int, int, int, int],
) -> None:
    """Draw centered horizontally with a shared typographic baseline."""
    draw.text(position, text, font=selected_font, fill=fill, anchor="ms")


def polar_point(angle: float, radius: float) -> tuple[float, float]:
    """Map clockwise degrees from twelve o'clock to an image coordinate."""
    radians = math.radians(angle - 90)
    return (
        CENTER + radius * math.cos(radians),
        CENTER + radius * math.sin(radians),
    )


def ring_image(remaining_percent: int) -> Image.Image:
    """Render a reference-style thick quota bezel with permanent black ticks."""
    percentage = max(0, min(100, remaining_percent))
    image = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    outer_box = (
        CENTER - RING_OUTER_RADIUS,
        CENTER - RING_OUTER_RADIUS,
        CENTER + RING_OUTER_RADIUS,
        CENTER + RING_OUTER_RADIUS,
    )
    inner_box = (
        CENTER - RING_INNER_RADIUS,
        CENTER - RING_INNER_RADIUS,
        CENTER + RING_INNER_RADIUS,
        CENTER + RING_INNER_RADIUS,
    )

    draw.ellipse(outer_box, fill=RING_TRACK)
    if percentage == 100:
        draw.ellipse(outer_box, fill=ORANGE)
    elif percentage > 0:
        draw.pieslice(
            outer_box,
            start=-90,
            end=-90 + percentage * 3.6,
            fill=ORANGE,
        )
    draw.ellipse(inner_box, fill=(0, 0, 0, 0))

    # The screenshot uses short minute ticks and heavier five-minute blocks.
    # Drawing them after the progress arc keeps the scale visible at every state.
    for minute in range(60):
        angle = minute * 6
        if minute % 15 == 0:
            inner_radius, width = RING_INNER_RADIUS, 9
        elif minute % 5 == 0:
            inner_radius, width = RING_INNER_RADIUS + 3, 7
        else:
            inner_radius, width = RING_OUTER_RADIUS - 13, 2
        draw.line(
            (
                polar_point(angle, inner_radius),
                polar_point(angle, RING_OUTER_RADIUS + 1),
            ),
            fill=BACKGROUND,
            width=width,
        )
    return image


def battery_ring_image(battery_percent: int) -> Image.Image:
    """Render the thin stock-battery ring immediately inside the quota bezel."""
    percentage = max(0, min(100, battery_percent))
    image = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    outer_box = (
        CENTER - BATTERY_OUTER_RADIUS,
        CENTER - BATTERY_OUTER_RADIUS,
        CENTER + BATTERY_OUTER_RADIUS,
        CENTER + BATTERY_OUTER_RADIUS,
    )
    inner_box = (
        CENTER - BATTERY_INNER_RADIUS,
        CENTER - BATTERY_INNER_RADIUS,
        CENTER + BATTERY_INNER_RADIUS,
        CENTER + BATTERY_INNER_RADIUS,
    )
    draw.ellipse(outer_box, fill=BATTERY_TRACK)
    if percentage == 100:
        draw.ellipse(outer_box, fill=BATTERY_ORANGE)
    elif percentage > 0:
        draw.pieslice(
            outer_box,
            start=-90,
            end=-90 + percentage * 3.6,
            fill=BATTERY_ORANGE,
        )
    draw.ellipse(inner_box, fill=(0, 0, 0, 0))
    return image


def background_image() -> Image.Image:
    image = Image.new("RGBA", (SIZE, SIZE), BACKGROUND)
    image.alpha_composite(ring_image(0))
    image.alpha_composite(battery_ring_image(0))
    draw = ImageDraw.Draw(image)

    # Keep the center deliberately quiet; progress controls paint over the dim tracks.
    draw.ellipse((37, 37, 417, 417), outline=(26, 14, 8, 255), width=1)

    draw_centered_on_baseline(draw, (CENTER, 168), ":", font(54), ORANGE_LIGHT)

    # Both information rows share true baselines. The dynamic values are inserted
    # between these fixed labels by the GT1 text controls.
    draw_centered_on_baseline(draw, (151, 245), "CODEX", font(18), ORANGE)
    draw_centered_on_baseline(draw, (286, 245), "%", font(22), ORANGE)
    draw_centered_on_baseline(
        draw, (316, 245), "LEFT", font(14), (211, 80, 12, 255)
    )
    draw_centered_on_baseline(
        draw, (178, 306), "RESET IN", font(15), (225, 88, 14, 255)
    )
    draw_centered_on_baseline(
        draw, (287, 306), "DAYS", font(15), (225, 88, 14, 255)
    )
    return image


def write_digit_images() -> None:
    selected_font = font(68)
    for digit in range(10):
        image = Image.new("RGBA", (54, 80), (0, 0, 0, 0))
        draw_centered(
            ImageDraw.Draw(image),
            (27, 39),
            str(digit),
            selected_font,
            ORANGE_LIGHT,
        )
        image.save(RESOURCES / f"A100_{digit + 1:03}.png", optimize=True)


def write_ring_images() -> None:
    for path in RESOURCES.glob("A100_*.png"):
        try:
            number = int(path.stem.split("_")[1])
        except (IndexError, ValueError) as error:
            raise ValueError(f"invalid watchface resource name: {path.name}") from error
        if number >= 12:
            path.unlink()

    for state in range(11):
        ring_image(state * 10).save(
            RESOURCES / f"A100_{state + 12:03}.png",
            optimize=True,
        )
    battery_ring_image(100).save(RESOURCES / "A100_023.png", optimize=True)


def render_preview(
    remaining_percent: int,
    reset_days: int,
    displayed_time: str = "10:37",
    battery_percent: int = 80,
) -> Image.Image:
    image = background_image()
    image.alpha_composite(ring_image(quota_decile(remaining_percent) * 10))
    image.alpha_composite(battery_ring_image(battery_percent))
    for x, character in zip((107, 161, 239, 293), displayed_time.replace(":", "")):
        if character < "0" or character > "9":
            raise ValueError(f"invalid preview time: {displayed_time}")
        digit = ord(character) - ord("0")
        image.alpha_composite(
            Image.open(RESOURCES / f"A100_{digit + 1:03}.png").convert("RGBA"),
            (x, 104),
        )
    draw = ImageDraw.Draw(image)
    draw_centered_on_baseline(
        draw, (232, 245), str(remaining_percent), font(42), ORANGE
    )
    draw_centered_on_baseline(
        draw, (239, 306), str(reset_days), font(22), (240, 116, 43, 255)
    )
    return image


def encode_varint(value: int) -> bytes:
    if value < 0:
        value = (1 << 64) + value
    encoded = bytearray()
    while value > 127:
        encoded.append((value & 127) | 128)
        value >>= 7
    encoded.append(value)
    return bytes(encoded)


def protobuf_key(field: int, wire_type: int) -> bytes:
    return encode_varint((field << 3) | wire_type)


def protobuf_integer(field: int, value: int) -> bytes:
    return protobuf_key(field, 0) + encode_varint(value)


def protobuf_blob(field: int, value: bytes) -> bytes:
    return protobuf_key(field, 2) + encode_varint(len(value)) + value


def protobuf_text(field: int, value: str) -> bytes:
    return protobuf_blob(field, value.encode())


def circle_progress_widget(
    resource_number: int,
    data_type: int,
    radius: int,
    width: int,
) -> bytes:
    circle = (
        protobuf_text(1, f"{resource_number:03}")
        + protobuf_integer(2, 0)
        + protobuf_integer(3, 0)
        + protobuf_integer(4, SIZE)
        + protobuf_integer(5, SIZE)
        + protobuf_integer(6, CENTER)
        + protobuf_integer(7, CENTER)
        + protobuf_integer(8, radius)
        + protobuf_integer(9, width)
        + protobuf_integer(10, 0)
        + protobuf_integer(11, 360)
        + protobuf_integer(12, 0)
        + protobuf_integer(13, 5)
        + protobuf_integer(14, data_type)
    )
    widget = protobuf_integer(1, 2) + protobuf_blob(4, circle)
    return (
        protobuf_blob(1, widget)
        + protobuf_text(2, "OpenGT")
        + protobuf_text(3, "OpenGT")
    )


def selected_image_widget(data_type: int, resource_numbers: range) -> bytes:
    names = [f"{number:03}" for number in resource_numbers]
    images = b"".join(
        protobuf_text(index + 1, names[index] if index < len(names) else "")
        for index in range(15)
    )
    selected_image = (
        protobuf_integer(1, 0)
        + protobuf_integer(2, 0)
        + protobuf_integer(3, data_type)
        + protobuf_integer(4, 5)
        + protobuf_blob(10, images)
    )
    widget = protobuf_integer(1, 6) + protobuf_blob(8, selected_image)
    return (
        protobuf_blob(1, widget)
        + protobuf_text(2, "OpenGT")
        + protobuf_text(3, "OpenGT")
    )


def ring_widgets() -> bytes:
    quota = selected_image_widget(DATA_TEMPERATURE, range(12, 23))
    battery = circle_progress_widget(23, DATA_POWER_RATIO, 192, 7)
    return quota + battery


def _read_varint(payload: bytes, position: int) -> tuple[int, int]:
    value = 0
    shift = 0
    while True:
        byte = payload[position]
        position += 1
        value |= (byte & 127) << shift
        if byte < 128:
            return value, position
        shift += 7


def patch_protobuf(payload: bytes) -> bytes:
    # Insert the quota ring after the first (background) widget and its labels.
    position = 0
    for _ in range(3):
        tag, position = _read_varint(payload, position)
        wire_type = tag & 7
        if wire_type == 2:
            size, position = _read_varint(payload, position)
            position += size
        elif wire_type == 0:
            _, position = _read_varint(payload, position)
        else:
            raise ValueError(f"unsupported protobuf wire type: {wire_type}")
    payload = payload[:position] + ring_widgets() + payload[position:]

    # Preserve the proven temperature bindings while moving/resizing their text.
    old_quota = bytes.fromhex(
        "08a70110d50118782032283a30dc0138eb01400448005001588b0160ff01"
    )
    new_quota = bytes.fromhex(
        "08be0110d1011854203c28ff013069389200401448005001588b0160ff01"
    )
    old_days = bytes.fromhex(
        "08cf0110d2021836201a28f00130f40138f80140144800500158860160ff01"
    )
    new_days = bytes.fromhex(
        "08db01109c021828201c28f00130f40038ab0040154800500158860160ff01"
    )
    if payload.count(old_quota) != 1 or payload.count(old_days) != 1:
        raise ValueError("base watchface text layout did not match the known GT1 payload")
    payload = payload.replace(old_quota, new_quota).replace(old_days, new_days)

    digit_positions = (
        (111, 107, 59),
        (165, 161, 60),
        (243, 239, 61),
        (297, 293, 62),
    )
    for old_x, new_x, data_type in digit_positions:
        old_position = (
            protobuf_integer(1, old_x)
            + protobuf_integer(2, 54)
            + protobuf_integer(3, data_type)
        )
        new_position = (
            protobuf_integer(1, new_x)
            + protobuf_integer(2, 104)
            + protobuf_integer(3, data_type)
        )
        if payload.count(old_position) != 1:
            raise ValueError(f"base watchface digit at x={old_x} was not found")
        payload = payload.replace(old_position, new_position)
    return payload


def encode_image(path: Path) -> bytes:
    image = Image.open(path).convert("RGBA")
    width, height = image.size
    encoded = bytearray(b"\x45\x23\x88\x88" + struct.pack("<HH", width, height))
    pixel_data = cast(Iterable[tuple[int, int, int, int]], image.getdata())
    pixels = list(pixel_data)
    sentinel = b"\x89\x67\x45\x23"
    position = 0
    while position < len(pixels):
        pixel = pixels[position]
        end = position + 1
        while end < len(pixels) and pixels[end] == pixel and end - position < 0xFFFFFFFF:
            end += 1
        count = end - position
        raw = bytes((pixel[2], pixel[1], pixel[0], pixel[3]))
        if count >= 2 or raw == sentinel:
            encoded += sentinel + raw + struct.pack("<I", count)
        else:
            encoded += raw
        position = end
    return bytes(encoded)


def build_binary() -> Path:
    base = BASE_BINARY.read_bytes()
    protobuf_size = struct.unpack_from("<H", base, 2)[0]
    protobuf = patch_protobuf(base[16 : 16 + protobuf_size])

    image_stream = bytearray(b"UUUU\x01\x00\x00\x01")
    image_table = bytearray()
    offset = 8
    resource_paths: Iterable[Path] = sorted(RESOURCES.glob("A100_*.png"))
    for path in resource_paths:
        record = encode_image(path)
        image_table += struct.pack("<II", offset, len(record))
        image_stream += record
        offset += len(record)

    header = struct.pack(
        "<BBHIII", 1, 0, len(protobuf), len(image_table), len(image_stream), 0
    )
    BINARY_OUTPUT.write_bytes(header + protobuf + image_table + image_stream)
    return BINARY_OUTPUT


def write_metadata() -> None:
    metadata = f"""<?xml version="1.0" encoding="UTF-8"?>
<HwTheme>
    <title>OpenGT</title>
    <title-cn>OpenGT</title-cn>
    <author>OpenGT</author>
    <designer>OpenGT</designer>
    <screen>HWHD02</screen>
    <version>{VERSION}</version>
    <font>Default</font>
    <font-cn>Default</font-cn>
    <briefinfo>Codex tactical desk companion</briefinfo>
</HwTheme>
"""
    (WATCHFACE_ROOT / "description.xml").write_text(metadata, encoding="utf-8")
    (WATCHFACE_ROOT / "watchface" / "watch_face_info.xml").write_text(
        metadata, encoding="utf-8"
    )


def write_previews() -> None:
    preview = render_preview(74, 6)
    preview.convert("RGB").save(WATCHFACE_ROOT / "preview" / "cover.jpg", quality=92)
    preview.resize((300, 300), Image.Resampling.LANCZOS).convert("RGB").save(
        WATCHFACE_ROOT / "preview" / "icon_small.jpg", quality=90
    )


def build_hwt(binary_path: Path) -> Path:
    with zipfile.ZipFile(PACKAGE_OUTPUT, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.write(binary_path, "com.huawei.watchface")
        archive.write(WATCHFACE_ROOT / "description.xml", "description.xml")
        archive.writestr("preview/", "")
        archive.write(WATCHFACE_ROOT / "preview" / "cover.jpg", "preview/cover.jpg")
        archive.write(
            WATCHFACE_ROOT / "preview" / "icon_small.jpg", "preview/icon_small.jpg"
        )
    return PACKAGE_OUTPUT


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    RESOURCES.mkdir(parents=True, exist_ok=True)
    EXPORTS.mkdir(parents=True, exist_ok=True)
    write_metadata()
    background_image().save(RESOURCES / "A100_011.png", optimize=True)
    write_digit_images()
    write_ring_images()
    write_previews()
    binary = build_binary()
    package = build_hwt(binary)
    print(f"built {binary} ({binary.stat().st_size} bytes)")
    print(f"built {package} ({package.stat().st_size} bytes)")
    print(f"sha256 {sha256(package)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
