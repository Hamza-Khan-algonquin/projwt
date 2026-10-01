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

# --- BLE UUIDs (from our own gatt_explorer_PWT.py scan of THIS band) ---
# Note: our hardware scan is authoritative. 61080001 is the SERVICE; the
# write characteristic is 61080002. (Some community repos label these
# differently / off-by-one — trust the scan.)
SERVICE_UUID = "61080001-8d6d-82b8-614a-1c8cb0f8dcc6"          # custom service (NOT a char)
CMD_CHAR_UUID = "61080002-8d6d-82b8-614a-1c8cb0f8dcc6"          # write / write-no-response
# IMPORTANT char-role mapping (corrected): our band has the service at ...0001,
# so every characteristic is shifted +1 vs community write-ups that assume the
# write char is ...0001. Aligned by ROLE (write + 4 notify, in handle order):
#   ref command(0001)  -> our 0002 (write)
#   ref response(0002) -> our 0003
#   ref event(0003)    -> our 0004   (command acks + tap/motion events seen here)
#   ref DATA(0004)     -> our 0005   (real-time 96-byte sensor stream !!)
#   ref diag(0005)     -> our 0007
RESP_CHAR_UUID = "61080003-8d6d-82b8-614a-1c8cb0f8dcc6"         # command responses / status beacon
EVENT_CHAR_UUID = "61080004-8d6d-82b8-614a-1c8cb0f8dcc6"        # async events (acks, taps/motion)
DATA_CHAR_UUID = "61080005-8d6d-82b8-614a-1c8cb0f8dcc6"         # REAL-TIME sensor stream (96-byte)
DIAG_CHAR_UUID = "61080007-8d6d-82b8-614a-1c8cb0f8dcc6"         # diagnostics
NOTIFY_CHARS = [RESP_CHAR_UUID, EVENT_CHAR_UUID, DATA_CHAR_UUID, DIAG_CHAR_UUID]
HR_CHAR_UUID = "00002a37-0000-1000-8000-00805f9b34fb"          # standard Heart Rate

# Short, UNAMBIGUOUS channel labels. NOTE: all WHOOP custom chars end in
# "...b0f8dcc6", so never label by the last bytes — they differ in the FIRST block.
CHAR_NAMES = {
    CMD_CHAR_UUID: "CMD(02)",
    RESP_CHAR_UUID: "RESP(03)",
    EVENT_CHAR_UUID: "EVT(04)",
    DATA_CHAR_UUID: "DATA(05)",
    DIAG_CHAR_UUID: "DIAG(07)",
    HR_CHAR_UUID: "HR(2a37)",
}


def cname(uuid: str) -> str:
    """Return a short, unambiguous label for a characteristic UUID."""
    return CHAR_NAMES.get(uuid.lower(), uuid[:8])

# --- packet types ---
TYPE_COMMAND = 0x23

# --- command IDs (community-sourced; verify on hardware) ---
CMD_GET_BATTERY = 0x01     # request battery level
CMD_GET_INFO = 0x02        # request device info (fw/serial/hw)
CMD_RT_HR_ON = 0x03        # begin real-time streaming (data on DATA_CHAR)
CMD_RT_HR_OFF = 0x04       # stop real-time streaming
CMD_HELLO = 0x05           # handshake / keep-alive (send this FIRST)
COMMANDS = {
    "battery": CMD_GET_BATTERY,
    "info": CMD_GET_INFO,
    "hr_on": CMD_RT_HR_ON,
    "hr_off": CMD_RT_HR_OFF,
    "hello": CMD_HELLO,
}

# Command IDs and the 96-byte real-time packet layout are informed by the
# MIT-licensed reference christianmeurer/whoop-reader and the community work it
# credits (jogolden/whoomp, bWanShiTong/reverse-engineering-whoop). The FRAMING
# here (CRC8 + zlib-CRC32) was independently verified against real packets.


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
