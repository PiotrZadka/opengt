# Capture publication policy

Raw Bluetooth scans can contain stable identifiers and advertisement data from unrelated
nearby devices. They remain local and `captures/scan-*.json` is intentionally ignored.

`gatt-20260808T192145Z.json` is a reviewed, sanitized derivative of the model-specific
GATT observation. Host, watch, and unrelated-device addresses are redacted while service,
characteristic, handle, and property evidence is preserved.

Future public captures must be reviewed for Bluetooth addresses, CoreBluetooth UUIDs,
device names, absolute host paths, account data, and secrets before being committed.
