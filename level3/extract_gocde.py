import struct

with open("rotary-precision.txt") as f:
    for line in f:
        if line.startswith("G0"):
            parts = line.split()
            x = float(parts[1][1:])
            y = float(parts[2][1:])

            bx = struct.pack('<f', x)
            by = struct.pack('<f', y)

            x1 = chr(bx[0] | (bx[1] << 8))
            x2 = chr(bx[2] | (bx[3] << 8))
            y1 = chr(by[0] | (by[1] << 8))
            y2 = chr(by[2] | (by[3] << 8))

            print(x1 + x2 + y1 + y2, end="")
