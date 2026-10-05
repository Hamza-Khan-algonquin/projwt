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
BATTERY_LEVEL_UUID = "00002a19-0000-1000-8000-00805f9b34fb"    # standard Battery Level (read)

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
# VERIFIED on fw 17.2.2.0: real-time streaming starts with cmd 0x03 AND payload
# 0x01 (bare 0x03 does nothing). Data then flows on DATA_CHAR_UUID (61080005) as
# ~1 Hz type-0x28 packets.
RT_START_PAYLOAD = bytes([0x01])
RT_PACKET_TYPE = 0x28
ACCEL_PACKET_TYPE = 0x2f   # 96-byte packets: accel X/Y/Z as float32 (g) at payload[36]

# --- raw/IMU enable commands (from community RE: github.com/tanarchytan/whoop-rs) ---
# All session-scoped, write no flash config, and are NOT in that project's forbidden
# /destructive lists. Payload is [revision, state]; revision 0x01, state 1=on/0=off.
CMD_SET_IMU_STREAM = 0x6A     # 106 — enable live IMU (accel+gyro) stream (Gen5/R22)
CMD_SEND_OPTICAL = 0x6B       # 107 — enable raw optical collection ([revision,state], no ACK)
CMD_R10_R11_REALTIME = 0x3F   # 63  — richer realtime stream, payload [0x00]
# --- historical offload (the Gen4 path to banked raw: gravity/PPG/SpO2/temp) ---
# raw is BANKED, not a live firehose on Gen4. Sequence: SEND_OPTICAL [01,01] (enable
# collection, no ACK) -> SEND_HISTORICAL [00] (kick the drain) -> for each METADATA
# HistoryEnd, write HISTORICAL_RESULT [01]+end_data so the strap advances -> stop on
# HistoryComplete. ABORT cleanly cancels an in-flight drain.
CMD_SEND_HISTORICAL = 0x16    # 22 — start historical drain, payload [0x00]
CMD_HISTORICAL_RESULT = 0x17  # 23 — ACK a chunk: payload [0x01]+end_data(8) (write confirmed)
CMD_ABORT_HISTORICAL = 0x14   # 20 — abort an in-flight historical drain

# --- haptics (the buzz motor) ---  Gen4 preset buzz, from whoop-rs haptic.rs
CMD_RUN_HAPTICS = 0x4F        # 79 — body [pattern_id, loops, 0, 0, 0]
CMD_STOP_HAPTICS = 0x7A       # 122 — stop an in-progress buzz
HAPTIC_ALARM_PATTERN = 2      # the 4.0 graduated-alarm buzz preset

# --- packet types (inner byte 0; VERIFIED against whoop-rs packet.rs) ---
PKT_REALTIME_HR = 0x28        # 40 REALTIME_DATA (HR/RR)
PKT_REALTIME_RAW = 0x2B       # 43 REALTIME_RAW_DATA (some raw frames arrive live)
PKT_HISTORICAL = 0x2F         # 47 HISTORICAL_DATA (banked records: v24/v25/v5 on Gen4)
PKT_EVENT = 0x30              # 48 EVENT (taps/motion)
PKT_METADATA = 0x31           # 49 METADATA (HistoryStart/End/Complete)
PKT_CONSOLE_LOGS = 0x32       # 50 CONSOLE_LOGS (firmware debug strings; NOT historical!)
PKT_REALTIME_IMU = 0x33       # 51 REALTIME_IMU_DATA_STREAM (100 Hz 6-axis; Gen5/R22)
# metadata subtypes (inner byte 2 of a METADATA frame)
META_HISTORY_START = 1
META_HISTORY_END = 2
META_HISTORY_COMPLETE = 3
# IMU scales (int16 -> units)
IMU_ACCEL_SCALE_G = 1.0 / 4096.0
IMU_GYRO_SCALE_DPS = 2000.0 / 32768.0
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


def unframe(data: bytes):
    """Validate the 0xAA frame and return the inner payload bytes, or None."""
    if len(data) < 8 or data[0] != 0xAA:
        return None
    length = int.from_bytes(data[1:3], "little")
    if crc8(data[1:3]) != data[3]:
        return None
    return bytes(data[4:4 + (length - 4)])  # length counts payload + 4-byte CRC32


def parse_rt(data: bytes):
    """Parse a real-time stream packet (type 0x28, ~1 Hz) off DATA_CHAR_UUID.

    Verified layout (payload, after unframing):
        [0]      packet type (0x28)
        [1]      subtype (0x02 = realtime metrics)
        [2:6]    timestamp, uint32 LE (device uptime seconds)
        [6:8]    aux, uint16 LE (not yet decoded; PPG/activity related)
        [8]      heart rate, bpm (uint8)
        [9]      N = number of RR intervals that follow
        [10:10+2N] N RR intervals, uint16 LE, milliseconds (beat-to-beat; HRV)
    """
    p = unframe(data)
    if p is None or len(p) < 10 or p[0] != RT_PACKET_TYPE:
        return None
    n = p[9]
    rr = [int.from_bytes(p[10 + 2 * i:12 + 2 * i], "little")
          for i in range(n) if 12 + 2 * i <= len(p)]
    return {
        "ts": int.from_bytes(p[2:6], "little"),
        "sub": p[1],
        "aux": int.from_bytes(p[6:8], "little"),
        "hr": p[8],
        "rr": rr,
    }


def parse_accel(data: bytes):
    """Parse a type-0x2f sensor packet: accelerometer X/Y/Z as float32 (g).

    Verified: payload[36:48] is a 3xfloat32 (x,y,z) gravity/acceleration vector in
    g units (|rest| ~= 1.0). A second copy sits at payload[52:64] (filtered vs raw).
    """
    import struct
    p = unframe(data)
    if p is None or len(p) < 48 or p[0] != ACCEL_PACKET_TYPE:
        return None
    x, y, z = struct.unpack_from("<fff", p, 36)
    mag = (x * x + y * y + z * z) ** 0.5
    # a uint32 near the header is a unix timestamp for HISTORICAL records; live
    # packets carry device-uptime ticks (a small number) instead.
    tsval = struct.unpack_from("<I", p, 7)[0] if len(p) >= 11 else 0
    historical = 1_500_000_000 < tsval < 2_200_000_000  # ~2017..2039 in unix secs
    return {"sub": p[1], "x": x, "y": y, "z": z, "mag": mag,
            "ts": tsval, "historical": historical}


GRAVITY_SCALE = 1.0 / 16384.0   # i16 gravity vector -> g (Q1.14, 16384 == 1.0 g)


def decode_historical(data: bytes):
    """Decode a type-0x2f HISTORICAL_DATA record (WHOOP 4.0 / Gen4).

    Offsets are INNER-relative (the inner record is [type][seq][cmd][payload...]),
    pinned against real 4.0 captures in tanarchytan/whoop-rs (records/gen4.rs). The
    record VERSION is carried in the seq byte (inner[1]):
        v24/v12 : full DSP  -> HR, R-R, gravity@36, SpO2 red/IR@64/66, skin-temp@68, resp@76
        v25     : PPG + gravity@69 (i16/16384), no per-second HR
        v5/v7/v9: HR + R-R only
    Returns a dict of whatever that version carries (missing fields -> None), or None
    if the frame isn't a historical record.
    """
    import struct
    p = unframe(data)
    if p is None or len(p) < 11 or p[0] != PKT_HISTORICAL:
        return None
    ver = p[1]
    unix = struct.unpack_from("<I", p, 7)[0]

    def i16(off):
        return struct.unpack_from("<h", p, off)[0] if off + 2 <= len(p) else None

    def u16(off):
        return struct.unpack_from("<H", p, off)[0] if off + 2 <= len(p) else None

    def _accept(g):
        mag = (g[0] ** 2 + g[1] ** 2 + g[2] ** 2) ** 0.5
        # same gate as whoop-rs accept_gravity: a real gravity vector sits near 1 g
        return {"x": g[0], "y": g[1], "z": g[2], "mag": mag} if 0.5 <= mag <= 1.5 else None

    def grav_f32(off):
        """v24/v12: three consecutive float32 (g) at off, off+4, off+8."""
        if off + 12 > len(p):
            return None
        g = list(struct.unpack_from("<fff", p, off))
        return _accept(g) if all(v == v and abs(v) < 1e6 for v in g) else None

    def grav_i16(off):
        """v25: three int16 scaled by 1/16384 (g) at off, off+2, off+4."""
        xs = [i16(off), i16(off + 2), i16(off + 4)]
        if any(v is None for v in xs):
            return None
        return _accept([v * GRAVITY_SCALE for v in xs])

    rec = {"version": ver, "unix": unix, "hr": None, "gravity": None}
    if ver in (24, 12):
        hr = p[17] if len(p) > 17 else 0
        rec["hr"] = hr or None
        rec["rr_count"] = p[18] if len(p) > 18 else None
        rec["gravity"] = grav_f32(36)         # float32 x/y/z (g)
        rec["skin_temp_raw"] = u16(68)
        rec["spo2_red"], rec["spo2_ir"] = u16(64), u16(66)
        rec["resp_raw"] = u16(76)
    elif ver == 25:
        rec["gravity"] = grav_i16(69)
    elif ver in (5, 7, 9):
        hr = p[17] if len(p) > 17 else 0
        rec["hr"] = hr or None
    return rec


EVENT_PACKET_TYPE = 0x30   # discrete events on EVENT_CHAR (taps/motion/status)


def parse_event(data: bytes):
    """Parse a type-0x30 event packet off EVENT_CHAR_UUID (61080004).

    Observed layout (payload, after unframing):
        [0]    type (0x30)
        [1]    sequence (increments per event)
        [2]    report id / size hint
        [3]    (usually 0x00)
        [4:8]  timestamp, uint32 LE (device uptime ticks)
        [8:]   event body (varies by report id)
    The body is returned raw plus as int16 LE values to help spot motion fields.
    """
    import struct
    p = unframe(data)
    if p is None or len(p) < 8 or p[0] != EVENT_PACKET_TYPE:
        return None
    body = p[8:]
    ints = [struct.unpack_from("<h", body, i)[0] for i in range(0, len(body) - 1, 2)]
    return {"seq": p[1], "report": p[2], "ts": int.from_bytes(p[4:8], "little"),
            "body": body.hex(), "ints": ints}


def _self_test() -> None:
    """Reproduce the known-good reference packet exactly."""
    reference = bytes.fromhex("aa100057230423aa8ed469a96d0000005130fef3")
    built = build_packet(cmd=0x23, seq=0x04, data=bytes.fromhex("aa8ed469a96d000000"))
    assert built == reference, f"framing broken:\n exp {reference.hex()}\n got {built.hex()}"
    # real-time parser: a captured packet with HR=76 and a single RR of 789ms
    # (60000/789 = 76.0, so HR and RR are internally consistent).
    rt = parse_rt(bytes.fromhex("aa1800ff2802f091e201e0264c0115030000000000000101"))
    assert rt and rt["hr"] == 76 and rt["rr"] == [789], f"rt parse broke: {rt}"
    # accelerometer: a captured 0x2f packet whose rest vector is ~1 g
    ac = parse_accel(bytes.fromhex(
        "aa5c00f02f0c05d8cf21009196ea6648568054"
        "2c012e01d4040000000000000060914aff006cc73bb8"
        "7effbd5c8fbb3e8ffe6e3f00000000b87effbd5c8fbb3e8ffe6e3f3502450252034402"
        "3301a00a010c020c2000000000000001cd16550f"))
    assert ac and 0.8 < ac["mag"] < 1.3, f"accel parse broke: {ac}"
    print("whoop_protocol_PWT self-test OK — framing + HR + accel parse verified.")


if __name__ == "__main__":
    _self_test()
    print("RT_START (0x03+01):", build_packet(CMD_RT_HR_ON, data=RT_START_PAYLOAD).hex(" "))
    print("RT_STOP  (0x04)   :", build_packet(CMD_RT_HR_OFF).hex(" "))
