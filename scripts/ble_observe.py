#!/usr/bin/env python3
"""Read-only BLE discovery and GATT observation for the Huawei Watch GT."""

from __future__ import annotations

import argparse
import asyncio
import json
import platform
import re
import subprocess
import sys
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path
from typing import Any

from bleak import BleakClient, BleakScanner  # pyright: ignore[reportMissingImports]
from bleak.exc import BleakError  # pyright: ignore[reportMissingImports]

PROJECT_SRC = Path(__file__).resolve().parents[1] / "src"
if str(PROJECT_SRC) not in sys.path:
    sys.path.insert(0, str(PROJECT_SRC))

from huawei_lpv2.codec import (  # pyright: ignore[reportMissingImports]
    CodecError,
    FrameStream,
    PacketReassembler,
)

WATCH_TERMS = ("FTN-B19", "WATCH GT", "HUAWEI WATCH")
DEVICE_INFORMATION_UUID = "0000180a-0000-1000-8000-00805f9b34fb"
HUAWEI_FE02_UUID = "0000fe02-0000-1000-8000-00805f9b34fb"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def hex_bytes(value: bytes | bytearray | None) -> str | None:
    return bytes(value).hex(" ") if value is not None else None


def printable_utf8(value: bytes | bytearray | None) -> str | None:
    if value is None:
        return None
    try:
        text = bytes(value).decode("utf-8")
    except UnicodeDecodeError:
        return None
    return text if text.isprintable() else None


def json_safe(value: Any) -> Any:
    if isinstance(value, (bytes, bytearray)):
        return hex_bytes(value)
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    try:
        json.dumps(value)
    except TypeError:
        return str(value)
    return value


def attr(obj: Any, name: str, default: Any = None) -> Any:
    return getattr(obj, name, default)


def advertisement_record(device: Any, advertisement: Any) -> dict[str, Any]:
    manufacturer_data = {
        str(key): hex_bytes(value)
        for key, value in (attr(advertisement, "manufacturer_data", {}) or {}).items()
    }
    service_data = {
        str(key): hex_bytes(value)
        for key, value in (attr(advertisement, "service_data", {}) or {}).items()
    }
    name = attr(device, "name") or attr(advertisement, "local_name")
    return {
        "seen_at": utc_now(),
        "identifier": attr(device, "address"),
        "identifier_note": "On macOS this is commonly a CoreBluetooth UUID, not a MAC address.",
        "name": name,
        "device_name": attr(device, "name"),
        "local_name": attr(advertisement, "local_name"),
        "rssi": attr(advertisement, "rssi"),
        "tx_power": attr(advertisement, "tx_power"),
        "service_uuids": list(attr(advertisement, "service_uuids", []) or []),
        "manufacturer_data": manufacturer_data,
        "service_data": service_data,
        "appearance": attr(advertisement, "appearance"),
    }


def looks_like_watch(record: dict[str, Any]) -> bool:
    haystack = " ".join(
        str(record.get(key) or "")
        for key in ("identifier", "name", "device_name", "local_name")
    ).upper()
    return any(term in haystack for term in WATCH_TERMS)


def safe_filename(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value)


def save_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def run_command(*command: str) -> str | None:
    try:
        return subprocess.run(
            command, capture_output=True, text=True, check=False
        ).stdout.strip()
    except OSError:
        return None


def environment() -> dict[str, Any]:
    homebrew = run_command("brew", "--version")
    return {
        "macos": run_command("sw_vers", "-productVersion"),
        "macos_build": run_command("sw_vers", "-buildVersion"),
        "architecture": platform.machine(),
        "python": sys.version,
        "python_executable": sys.executable,
        "homebrew": homebrew.splitlines()[0] if homebrew else None,
        "bleak": version("bleak"),
        "bluetooth_summary": run_command("system_profiler", "SPBluetoothDataType"),
    }


def choose_device(
    devices: list[tuple[Any, dict[str, Any]]], target: str | None
) -> tuple[Any, dict[str, Any]] | None:
    if target:
        target_upper = target.upper()
        matches = [
            item
            for item in devices
            if target_upper
            in " ".join(
                str(item[1].get(key) or "")
                for key in ("identifier", "name", "device_name", "local_name")
            ).upper()
        ]
    else:
        matches = [item for item in devices if looks_like_watch(item[1])]

    if not matches:
        return None
    if len(matches) > 1:
        print("Multiple possible watch advertisements; refusing to guess:")
        for _, record in matches:
            print(f"  {record['identifier']}  {record.get('name') or '(unnamed)'}")
        return None
    return matches[0]


def characteristic_record(characteristic: Any) -> dict[str, Any]:
    descriptors = []
    for descriptor in attr(characteristic, "descriptors", []) or []:
        descriptors.append(
            {
                "uuid": attr(descriptor, "uuid"),
                "handle": attr(descriptor, "handle"),
                "description": attr(descriptor, "description"),
            }
        )
    return {
        "uuid": attr(characteristic, "uuid"),
        "handle": attr(characteristic, "handle"),
        "description": attr(characteristic, "description"),
        "properties": sorted(
            str(item).lower() for item in (attr(characteristic, "properties", []) or [])
        ),
        "descriptors": descriptors,
    }


def markdown_value(value: dict[str, Any]) -> str:
    raw = value.get("value_hex") or ""
    text = value.get("value_utf8")
    return f"`{raw}`" + (f" (`{text}`)" if text else "")


def frame_record(frame: Any) -> dict[str, Any]:
    return {
        "slice_type": frame.slice_type,
        "sequence": frame.sequence,
        "service_id": frame.service_id,
        "command_id": frame.command_id,
        "fragment_hex": hex_bytes(frame.fragment),
    }


def packet_record(packet: Any) -> dict[str, Any]:
    return {
        "service_id": packet.service_id,
        "command_id": packet.command_id,
        "tlvs": [
            {"tag": tlv.tag, "value_hex": hex_bytes(tlv.value)}
            for tlv in packet.tlvs
        ],
    }


def write_baseline(
    path: Path,
    env: dict[str, Any],
    scan: dict[str, Any],
    gatt: dict[str, Any] | None,
) -> None:
    lines = [
        "# Hardware and BLE baseline",
        "",
        "> Observation-only baseline. No firmware update, flash write, undocumented write, or factory reset was attempted.",
        "",
        "## Target",
        "",
        "- User-reported device: Huawei Watch GT first generation, model `FTN-B19`, firmware `1.0.12.26`.",
        "",
        "## macOS environment",
        "",
        f"- macOS: `{env.get('macos') or 'unknown'}` (build `{env.get('macos_build') or 'unknown'}`)",
        f"- Architecture: `{env.get('architecture') or 'unknown'}`",
        f"- Python: `{sys.version.split()[0]}` (`{env.get('python_executable') or 'unknown'}`)",
        f"- Homebrew: `{env.get('homebrew') or 'not found'}`",
        f"- Bleak: `{env.get('bleak') or 'unknown'}`",
        "",
        "### Bluetooth controller",
        "",
        "```text",
        env.get("bluetooth_summary") or "Bluetooth status unavailable",
        "```",
        "",
        "## Discovery",
        "",
    ]
    selected = scan.get("selected_device")
    if selected:
        lines.extend(
            [
                f"- Detected identifier: `{selected.get('identifier')}`",
                "- Identifier type: macOS CoreBluetooth identifiers are UUID-style and should not be treated as a Bluetooth MAC address.",
                f"- Advertised name: `{selected.get('name') or selected.get('local_name') or 'unknown'}`",
                f"- RSSI: `{selected.get('rssi')}` dBm",
                f"- TX power: `{selected.get('tx_power')}`",
                f"- Service UUIDs: `{', '.join(selected.get('service_uuids') or []) or 'none reported'}`",
                f"- Manufacturer data: `{json.dumps(selected.get('manufacturer_data') or {}, sort_keys=True)}`",
                f"- Service data: `{json.dumps(selected.get('service_data') or {}, sort_keys=True)}`",
            ]
        )
    else:
        lines.append("- Watch not detected in the completed scan.")
    lines += ["", "## GATT map", ""]
    if not gatt:
        lines.append("GATT was not enumerated because no target was connected.")
    else:
        lines.append(f"- Connected identifier: `{gatt.get('identifier')}`")
        lines.append(
            f"- Notification subscriptions: `{gatt.get('notification_subscriptions') or 'none'}`"
        )
        for service in gatt.get("services", []):
            lines.append(
                f"### Service `{service.get('uuid')}` (handle `{service.get('handle')}`, {service.get('description') or 'no description'})"
            )
            for characteristic in service.get("characteristics", []):
                properties = ", ".join(characteristic.get("properties") or []) or "none"
                lines.append(
                    f"- Characteristic `{characteristic.get('uuid')}` (handle `{characteristic.get('handle')}`): properties `{properties}`"
                )
                for descriptor in characteristic.get("descriptors", []):
                    lines.append(
                        f"  - Descriptor `{descriptor.get('uuid')}` (handle `{descriptor.get('handle')}`): {descriptor.get('description') or 'no description'}"
                    )
        lines += ["", "## Readable values", ""]
        if gatt.get("readable_values"):
            for value in gatt["readable_values"]:
                status = value.get("error") or markdown_value(value)
                lines.append(f"- `{value.get('uuid')}`: {status}")
        else:
            lines.append("No readable characteristics were reported.")
    lines += [
        "",
        "## Open questions",
        "",
        "- The device advertises as `HUAWEI WATCH GT-E3A`; standard model/serial fields are generic `HUAWEI`, so FTN-B19 is not independently verified by GATT yet.",
        "- Standard firmware, hardware, and software revision fields return `1.0.0.1`, not the supplied `1.0.12.26`; determine whether these are placeholders or a different version.",
        "- Is the watch currently paired or connected to Huawei Health/another host?",
        "- Which advertised manufacturer bytes identify FTN-B19 and firmware 1.0.12.26?",
        "- Which writable/notify characteristics are protocol endpoints? They remain untouched in this phase.",
        "- Does the device expose additional services only after pairing or an authenticated session?",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


async def scan(
    seconds: float,
) -> tuple[list[tuple[Any, dict[str, Any]]], dict[str, Any]]:
    print(f"Scanning for BLE advertisements for {seconds:g}s …")
    try:
        discovered = await BleakScanner.discover(timeout=seconds, return_adv=True)
    except PermissionError as exc:
        raise RuntimeError(
            "Bluetooth permission was denied. Approve Bluetooth access for the app launching this process "
            "(usually Terminal.app), then retry."
        ) from exc
    devices = []
    for device, advertisement in discovered.values():
        devices.append((device, advertisement_record(device, advertisement)))
    devices.sort(
        key=lambda item: (item[1].get("name") or "", item[1].get("identifier") or "")
    )
    records = [record for _, record in devices]
    selected = choose_device(devices, None)
    scan_record = {
        "captured_at": utc_now(),
        "scan_seconds": seconds,
        "device_count": len(records),
        "devices": records,
        "selected_device": selected[1] if selected else None,
    }
    return devices, scan_record


async def observe_gatt(
    device: Any,
    scan_record: dict[str, Any],
    subscribe_notifications: bool,
    notification_seconds: float,
) -> dict[str, Any]:
    identifier = attr(device, "address")
    print(f"Connecting to {scan_record.get('name') or identifier} ({identifier}) …")
    disconnected = asyncio.Event()

    def on_disconnect(_: Any) -> None:
        disconnected.set()

    client = BleakClient(device, disconnected_callback=on_disconnect, pair=False)
    try:
        await client.connect()
        services = []
        readable_values = []
        notification_subscriptions = []
        notification_events = []
        notification_stream = FrameStream()
        notification_reassembler = PacketReassembler()
        for service in client.services:
            service_record = {
                "uuid": attr(service, "uuid"),
                "handle": attr(service, "handle"),
                "description": attr(service, "description"),
                "characteristics": [],
            }
            for characteristic in service.characteristics:
                record = characteristic_record(characteristic)
                service_record["characteristics"].append(record)
                if (
                    service_record["uuid"].lower() == DEVICE_INFORMATION_UUID
                    and "read" in record["properties"]
                ):
                    result = {
                        "uuid": record["uuid"],
                        "handle": record["handle"],
                        "value_hex": None,
                        "value_utf8": None,
                    }
                    try:
                        value = await client.read_gatt_char(characteristic)
                        result["value_hex"] = hex_bytes(value)
                        result["value_utf8"] = printable_utf8(value)
                    except (
                        BleakError,
                        OSError,
                    ) as exc:  # device-specific read failures are captured, not retried
                        result["error"] = f"{type(exc).__name__}: {exc}"
                    readable_values.append(result)

                safe_notify = (
                    record["uuid"].lower() == HUAWEI_FE02_UUID
                    and "notify" in record["properties"]
                )
                if subscribe_notifications and safe_notify:

                    def callback(sender: Any, data: bytearray) -> None:
                        event = {
                            "captured_at": utc_now(),
                            "characteristic": str(sender),
                            "value_hex": hex_bytes(data),
                            "frames": [],
                            "packets": [],
                        }
                        try:
                            frames = notification_stream.feed(data)
                            event["frames"] = [frame_record(frame) for frame in frames]
                            for frame in frames:
                                packet = notification_reassembler.add(frame)
                                if packet is not None:
                                    event["packets"].append(packet_record(packet))
                        except CodecError as exc:
                            event["decode_error"] = f"{type(exc).__name__}: {exc}"
                        notification_events.append(event)

                    try:
                        await client.start_notify(characteristic, callback)
                        notification_subscriptions.append(record["uuid"])
                    except (BleakError, OSError) as exc:
                        record["notification_error"] = f"{type(exc).__name__}: {exc}"
            services.append(service_record)

        if notification_subscriptions and notification_seconds > 0:
            print(
                f"Listening for notifications on {len(notification_subscriptions)} characteristic(s) "
                f"for {notification_seconds:g}s …"
            )
            try:
                await asyncio.wait_for(
                    disconnected.wait(), timeout=notification_seconds
                )
            except TimeoutError:
                print("Notification listen timed out.")
            for uuid in notification_subscriptions:
                try:
                    await client.stop_notify(uuid)
                except (BleakError, OSError) as exc:
                    print(
                        f"Could not stop notification on {uuid}: {exc}", file=sys.stderr
                    )

        return {
            "captured_at": utc_now(),
            "identifier": identifier,
            "connected": True,
            "services": services,
            "readable_values": readable_values,
            "notification_subscriptions": notification_subscriptions,
            "notification_events": notification_events,
        }
    finally:
        if client.is_connected:
            await client.disconnect()


async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scan-seconds", type=float, default=20.0)
    parser.add_argument(
        "--target", help="macOS UUID, advertised name, or substring to select"
    )
    parser.add_argument(
        "--connect",
        action="store_true",
        help="connect to one matching Huawei Watch advertisement",
    )
    parser.add_argument(
        "--subscribe-notifications",
        action="store_true",
        help="temporarily enable only FE02 notifications via its standard CCCD",
    )
    parser.add_argument("--notification-seconds", type=float, default=5.0)
    parser.add_argument("--captures", type=Path, default=Path("captures"))
    parser.add_argument(
        "--baseline", type=Path, default=Path("docs/hardware-and-ble-baseline.md")
    )
    args = parser.parse_args()

    args.captures.mkdir(parents=True, exist_ok=True)
    args.baseline.parent.mkdir(parents=True, exist_ok=True)
    started = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    env = environment()
    try:
        devices, scan_record = await scan(args.scan_seconds)
    except (BleakError, RuntimeError) as exc:
        print(f"BLE scan failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        print(
            "Check System Settings > Privacy & Security > Bluetooth and approve access for the app "
            "that launched Python (usually Terminal.app).",
            file=sys.stderr,
        )
        return 2

    scan_path = args.captures / f"scan-{started}.json"
    save_json(scan_path, {"environment": env, **scan_record})
    print(f"Saved scan: {scan_path}")
    for record in scan_record["devices"]:
        marker = "  <-- Huawei Watch candidate" if looks_like_watch(record) else ""
        print(
            f"  {record['identifier']}  {record.get('name') or '(unnamed)'}  RSSI={record.get('rssi')}{marker}"
        )

    gatt_record = None
    if args.connect:
        target = choose_device(devices, args.target)
        if target is None:
            if args.target:
                print(
                    f"No advertisement matched target {args.target!r}; not connecting.",
                    file=sys.stderr,
                )
            else:
                print(
                    "No unique Huawei Watch candidate; not connecting.", file=sys.stderr
                )
        else:
            device, record = target
            try:
                gatt_record = await observe_gatt(
                    device,
                    record,
                    args.subscribe_notifications,
                    args.notification_seconds,
                )
                gatt_path = args.captures / f"gatt-{started}.json"
                save_json(
                    gatt_path,
                    {"environment": env, "advertisement": record, **gatt_record},
                )
                print(f"Saved GATT observation: {gatt_path}")
            except (BleakError, OSError, asyncio.TimeoutError) as exc:
                gatt_record = {
                    "captured_at": utc_now(),
                    "identifier": record.get("identifier"),
                    "connected": False,
                    "error": f"{type(exc).__name__}: {exc}",
                }
                print(
                    f"GATT observation failed: {type(exc).__name__}: {exc}",
                    file=sys.stderr,
                )

    write_baseline(args.baseline, env, scan_record, gatt_record)
    print(f"Updated baseline: {args.baseline}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
