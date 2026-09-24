"""QuickXorHash: the checksum OneDrive and SharePoint store for every file. Pure Python, no dependencies.

Each byte at position p is rotated into a 160-bit register by (11 * p) mod 160 bits and XORed in; the file length
(little-endian, 8 bytes) is XORed into the last 8 bytes. Returned as lowercase hex, the form rclone reports.
Bytes whose positions share p mod 160 share a rotation, so they are XOR-folded 160 at a time with big integers.
"""
WIDTH = 160
MASK = (1 << WIDTH) - 1
ROW = WIDTH // 8 * 8  # 160 bytes: one full cycle of rotations


class QuickXorHash:
    def __init__(self):
        self.acc = 0         # byte i of acc = XOR of all bytes at positions ≡ i (mod 160)
        self.length = 0
        self.pending = b""   # bytes not yet forming a whole 160-byte row

    def update(self, data):
        data = self.pending + bytes(data)
        whole = len(data) - len(data) % ROW
        acc = self.acc
        for k in range(0, whole, ROW):
            acc ^= int.from_bytes(data[k:k + ROW], "little")
        self.acc, self.pending = acc, data[whole:]
        self.length += whole
        return self

    def hexdigest(self):
        acc = self.acc ^ int.from_bytes(self.pending, "little")
        total = self.length + len(self.pending)
        state = 0
        for i in range(ROW):
            b = (acc >> (8 * i)) & 0xFF
            if b:
                s = (11 * i) % WIDTH
                state ^= ((b << s) | (b >> (WIDTH - s))) & MASK
        out = bytearray(state.to_bytes(WIDTH // 8, "little"))
        for i, lb in enumerate(total.to_bytes(8, "little")):
            out[WIDTH // 8 - 8 + i] ^= lb
        return out.hex()
