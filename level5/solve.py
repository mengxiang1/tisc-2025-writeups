import os
import struct
import requests

main_calibrationData = [0xd76ba478, 0xe8c2b755, 0x242670dc, 0xc1bfceee, 0xf5790fae, 0x4781c628, 0xa8314613, 0xfd439507, 0x698698dd, 0x8b47f7af, 0xfffa5bb5, 0x895ad7be]

main_correctionFactors = [0x0d76aa478, 0x0e8c7b756, 0x242070db, 0x0c1bdceee, 0x0f57c0faf, 0x4787c62a, 0x0a8304613, 0x0fd469501, 0x698098d8, 0x8b44f7af, 0xffff5bb1, 0x895cd7be]

raw_baseline = [c ^ f for c, f in zip(main_calibrationData, main_correctionFactors)]

events = []
for val in raw_baseline:
    type_id = (val >> 16) & 0xFFFF
    value = val & 0xFFFF
    events.append((type_id, value))

session_id = os.urandom(8)
payload = bytearray()
payload += session_id
payload += struct.pack("<I", len(events)) 

checksum = len(events)
for t, v in events:
    checksum ^= t ^ v ^ 0 # by right shld be timestamp but it cancels out + not checked
payload += struct.pack("<I", checksum)
payload += struct.pack("<I", len(events))

for t, v in events:
    payload += struct.pack("<I", t)
    payload += struct.pack("<I", v)
    payload += struct.pack("<I", 0)
print(payload)
headers = {
    "R": "application/octet-stream",
}
url = "http://chals.tisc25.ctf.sg:57190/"
r = requests.post(url, headers=headers, data=payload)

with open("flag.mp3", "wb") as f:
    f.write(r.content)