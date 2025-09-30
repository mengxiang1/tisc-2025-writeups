# Level 5 `SYNTRA`

**Flag:** `TISC{PR3551NG_BUTT0N5_4ND_TURN1NG_KN0B5_4_S3CR3T_S0NG_FL4G}`

## TL;DR

* The web UI POSTs a binary “event” blob to `/` (8‑byte session, 4‑byte count, 4‑byte checksum, then events of 12 bytes each: type/value/timestamp).
* The Go server computes a secret "baseline" from embedded `main_calibrationData` XOR `main_correctionFactors`, turns each 32‑bit word into `(type, value)`, and checks an incoming event stream for an exact match.
* Reconstructing the baseline, serializing it exactly like the frontend, and POSTing it to `/` causes the server to serve `assets/flag.mp3` which contains the flag.

---

## Challenge summary

- A "jukebox" frontend sends user events (play/pause/next/volume/speed) as a binary metrics payload to the server.
- From reverse engineering the server in IDA, I discovered that the backend parses the payload and decides which audio resource to return. 
- If the payload passes certain checks, `flag.mp3` is served.

---

## Reversing

- The server stores the expected event sequence (baseline) inside the binary: `main_calibrationData` and a `main_correctionFactors` table.
- `main_computeMetricsBaseline()` parses calibration data, XORs it with `main_correctionFactors`, then extracts `(type, value)` from each resulting 32‑bit word (HIWORD = type, LOWORD = value).
- `main_evaluateMetricsQuality()` compares the parsed client events to that baseline: types must match; for types 5 (volume) and 6 (speed) values must match exactly.
- Because the baseline is static and embedded, an attacker can extract it and replay it exactly.

---

## Solution

1. Extract arrays from the binary (from IDA):

   - `main_calibrationData`
   - `main_correctionFactors`

2. Compute the true baseline:

```py
raw_baseline = [c ^ f for c, f in zip(main_calibrationData, main_correctionFactors)]
events = []
for val in raw_baseline:
    type_id = (val >> 16) & 0xFFFF
    value = val & 0xFFFF
    events.append((type_id, value))
```

3. Build the POST body like what the frontend does:

   - 8 random bytes session ID
   - 4‑byte little‑endian event count
   - 4‑byte checksum: `checksum = N; for each e: checksum ^= e.type ^ e.value ^ (timestamp & 0xFF)`
   - For each event pack 3 x 4‑byte LE ints: `type`, `value`, `timestamp` (timestamp can be 0)

4. POST to `/` with headers:

```
R: application/octet-stream
H: <payload length>
```

5. Save response body to `flag.mp3`. The flag is read out by a voice in the audio file.