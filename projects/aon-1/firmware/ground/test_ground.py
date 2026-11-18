"""Interop: the Python ground tool and the C flight code build identical TC frames; HK decodes. Run: python -m unittest -v (from firmware/ground)."""
import pathlib
import subprocess
import unittest

import aon_ground as G

FW = pathlib.Path(__file__).resolve().parents[1] / "eor1"
KEY = bytes(range(1, 33))


class Interop(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run(["make", "-C", str(FW), "build/test_eor"], check=True, capture_output=True)
        subprocess.run(["cc", "-std=c11", "-I", str(FW / "src"), "-o", str(FW / "build" / "tc_vector"), str(FW / "test" / "tc_vector.c"),
                        str(FW / "src" / "eor.c"), str(FW / "src" / "sha256.c"), str(FW / "test" / "hal_sim.c"), "-lm"], check=True)

    def c_frame(self, seq, cmd, args=""):
        return bytes.fromhex(subprocess.run([str(FW / "build" / "tc_vector"), str(seq), str(cmd), args], check=True, capture_output=True, text=True).stdout.strip())

    def test_ping(self):
        self.assertEqual(G.tc(KEY, 101, G.CMDS["PING"]), self.c_frame(101, 1))

    def test_store(self):
        self.assertEqual(G.tc(KEY, 70000, G.CMDS["SF_STORE"], b"hello from the ground"), self.c_frame(70000, 4, "hello from the ground"))

    def test_crc(self):
        self.assertEqual(G.crc16(b"123456789"), 0x29B1)

    def test_flight_tests_pass(self):
        r = subprocess.run([str(FW / "build" / "test_eor")], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout)


if __name__ == "__main__":
    unittest.main()
