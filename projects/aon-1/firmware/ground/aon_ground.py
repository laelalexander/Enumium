"""AON-1 ground tools: build authenticated TC frames and decode TM (HK beacon, ACK, store-and-forward), matching EOR-1 (firmware/eor1/src/eor.h).

  python aon_ground.py tc --key-file key.bin --seq 101 --cmd PING
  python aon_ground.py decode 0b1ac000002e01414f4e31...
The command key never leaves the mission-control host; keep it in an HSM or at least a 0600 file.
"""
import argparse
import hashlib
import hmac
import struct
import sys

APID_TC, APID_HK, APID_SF, APID_ACK = 0x0A1, 0x0B1, 0x0B2, 0x0B3
CMDS = dict(PING=1, SET_MODE=2, GET_HK=3, SF_STORE=4, SF_FETCH=5, SF_DELETE=6, SF_COUNT=7, DEPLOY_ARM=8, DEPLOY_FIRE=9, SET_TIME=10, TX_ENABLE=11)
MODES = ["BOOT", "WAIT_DEPLOY", "DEPLOY", "WAIT_RF", "DETUMBLE", "NOMINAL", "SAFE"]
STATUS = ["OK", "AUTH", "REPLAY", "FORMAT", "STATE", "FULL", "NOTFOUND"]
MAC_LEN = 16


def crc16(d: bytes) -> int:
    c = 0xFFFF
    for b in d:
        c ^= b << 8
        for _ in range(8):
            c = ((c << 1) ^ 0x1021) & 0xFFFF if c & 0x8000 else (c << 1) & 0xFFFF
    return c


def tc(key: bytes, seq: int, cmd: int, args: bytes = b"") -> bytes:
    body = bytes([cmd]) + args + struct.pack(">I", seq)
    total = 6 + len(body) + MAC_LEN
    hdr = struct.pack(">HHH", 0x1000 | APID_TC, 0xC000 | (seq & 0x3FFF), total - 7)
    mac = hmac.new(key, hdr + body, hashlib.sha256).digest()[:MAC_LEN]
    return hdr + body + mac


def decode(f: bytes) -> dict:
    w0, w1, ln = struct.unpack(">HHH", f[:6])
    apid = w0 & 0x7FF
    if ln + 7 != len(f):
        raise ValueError("length field mismatch")
    if crc16(f[:-2]) != struct.unpack(">H", f[-2:])[0]:
        raise ValueError("CRC mismatch")
    p = f[6:-2]
    if apid == APID_HK:
        (typ, call, mode, t, v, i, tb, to, s1, s2, s3, s4, boots, safes, rxok, bad, sfc, flags) = struct.unpack(">B4sBIHhhhHHHHIHIHIB", p)
        return dict(kind="HK", call=call.decode(), mode=MODES[mode], t_s=t, vbatt=v / 1000, ibatt=i / 1000, tbatt=tb / 10, tobc=to / 10,
                    isolar=[x / 1000 for x in (s1, s2, s3, s4)], boots=boots, safe=safes, rx_ok=rxok, bad_auth=bad, sf_count=sfc,
                    deployed=[bool(flags & 1), bool(flags & 2)], heater=bool(flags & 4), tx_enabled=bool(flags & 8), seq=w1 & 0x3FFF)
    if apid == APID_ACK:
        name = {v: k for k, v in CMDS.items()}.get(p[0], str(p[0]))
        return dict(kind="ACK", cmd=name, status=STATUS[p[1]] if p[1] < len(STATUS) else p[1], data=p[2:].hex())
    return dict(kind=f"APID {apid:#x}", data=p.hex())


def main(argv=None):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="op", required=True)
    a = sub.add_parser("tc"); a.add_argument("--key-file", required=True); a.add_argument("--seq", type=int, required=True)
    a.add_argument("--cmd", required=True, choices=CMDS); a.add_argument("--args", default="", help="hex")
    d = sub.add_parser("decode"); d.add_argument("hex")
    o = ap.parse_args(argv)
    if o.op == "tc":
        key = open(o.key_file, "rb").read()
        if len(key) != 32:
            sys.exit("key must be 32 bytes")
        print(tc(key, o.seq, CMDS[o.cmd], bytes.fromhex(o.args)).hex())
    else:
        print(decode(bytes.fromhex(o.hex)))


if __name__ == "__main__":
    main()
