"""whoop_protocol_PWT.py — verified WHOOP 4.0 command framing.

The frame layout was reverse-engineered from a real captured packet and
confirmed by reproducing it byte-for-byte (see build_packet self-test):

    0xAA | length(2, little-endian) | CRC8(length) | PAYLOAD | CRC32(PAYLOAD, LE)

    length  = len(PAYLOAD) + 4   (payload plus the trailing CRC32)
    CRC8    = poly 0x07, init 0x00, no reflection, over the 2 length bytes
    CRC32   = standard zlib.crc32 over PAYLOAD, stored little-endian
    PAYLOAD = [type][seq][cmd][data...]

Confidence: the *framing* above is empirically verified. The command IDs
below come from community write-ups and may need iteration on real hardware.
"""
import zlib

# --- BLE UUIDs (from our own gatt_explorer_PWT.py scan of the band) ---
SERVICE_UUID = "61080001-8d6d-82b8-614a-1c8cb0f8dcc6"
CMD_CHAR_UUID = "61080002-8d6d-82b8-614a-1c8cb0f8dcc6"          # write / write-no-response
NOTIFY_CHARS = [
    "61080003-8d6d-82b8-614a-1c8cb0f8dcc6",                     # events / responses
    "61080004-8d6d-82b8-614a-1c8cb0f8dcc6",                     # data
    "61080005-8d6d-82b8-614a-1c8cb0f8dcc6",                     # diagnostics
    "61080007-8d6d-82b8-614a-1c8cb0f8dcc6",
]
HR_CHAR_UUID = "00002a37-0000-1000-8000-00805f9b34fb"          # standard Heart Rate

# --- packet types ---
TYPE_COMMAND = 0x23

# --- command IDs (community-sourced; verify on hardware) ---
CMD_RT_HR_ON = 0x03    # begin real-time streaming
CMD_RT_HR_OFF = 0x04   # stop real-time streaming
COMMANDS = {"hr_on": CMD_RT_HR_ON, "hr_off": CMD_RT_HR_OFF}


def crc8(data: bytes) -> int:
    """CRC-8, poly 0x07, init 0x00, no reflection (verified against real packet)."""
    crc = 0
    for b in data:
        crc ^= b
        for _ in range(8):
            crc = ((crc << 1) ^ 0x07) & 0xFF if crc & 0x80 else (crc << 1) & 0xFF
    return crc


def build_packet(cmd: int, seq: int = 0, data: bytes = b"", pkt_type: int = TYPE_COMMAND) -> bytes:
    """Build a fully framed command packet ready to write to CMD_CHAR_UUID."""
    payload = bytes([pkt_type & 0xFF, seq & 0xFF, cmd & 0xFF]) + data
    length = len(payload) + 4
    len_le = length.to_bytes(2, "little")
    crc32 = (zlib.crc32(payload) & 0xFFFFFFFF).to_bytes(4, "little")
    return bytes([0xAA]) + len_le + bytes([crc8(len_le)]) + payload + crc32


def _self_test() -> None:
    """Reproduce the known-good reference packet exactly."""
    reference = bytes.fromhex("aa100057230423aa8ed469a96d0000005130fef3")
    built = build_packet(cmd=0x23, seq=0x04, data=bytes.fromhex("aa8ed469a96d000000"))
    assert built == reference, f"framing broken:\n exp {reference.hex()}\n got {built.hex()}"
    print("whoop_protocol_PWT self-test OK — framing reproduces reference packet.")


if __name__ == "__main__":
    _self_test()
    print("RT_HR_ON :", build_packet(CMD_RT_HR_ON).hex(" "))
    print("RT_HR_OFF:", build_packet(CMD_RT_HR_OFF).hex(" "))
