# Level 10: `countle-secured-storage`
**Flag:** `TISC{1t_w45_7h3_f1r57_g00gl3_r35ul7_f0r_c55_54n171z3r}`

## TL;DR
Registering a user implicitly creates an `admin_{user}` account whose vault contains the flag. The server unsafely derives the AES-GCM token key using the first 8 bytes of the flag and a predictable `math/rand` sequence, letting us forge admin tokens. The admin bot (headless browser) solves 2FA puzzles but did not submit. As there is a CSS injection vulnerability, the bot’s button clicks can be logged via profile-view timestamps to recover the OTPs. With two consecutive OTPs recovered we accessed the admin vault and read the flag.

---

## Challenge summary
A web service with user registration, a personal vault, and a 2FA puzzle that must be solved twice to view vault contents. An admin bot exists that loads the 2FA page in a headless browser and clicks the UI buttons (but never submits).

Key features:
- Endpoints:
  - `POST /api/register` create accounts
  - `POST /api/login` obtain token
  - `POST /api/vault/check` trigger admin bot to log in as current user and solve 2FA puzzle (this endpoint was found through reversing the server binary)
  - `POST /api/update_style` set `style_color` (hex) for profile color
  - `GET /api/profile/{username}` view profile (server logs view timestamp)
  - `GET /api/views` see own profile access logs with timestamps

---

## 2FA puzzle
- The 2FA page: server generates a **4-digit OTP** per attempt, not shown to the user.
- The page presents a countle-inspired puzzle: Use displayed numbers and operators to form equations and produce the 4-digit OTP.
- If the user fails, a new OTP is generated (so brute forcing is not feasible).
- To access vault data, the user must solve the puzzle **twice in a row**.

---

## Binary analysis
The binary is written in Go (unstripped), using Gin for HTTP server. Findings from IDA:

- `main.HandleCheckSecret` reads `os.Getenv("ADMIN_BOT_ADDRESS")` and is registered at `/api/vault/check`. Sending a `POST` with `Authorization: <token>` triggers the admin bot to visit the 2FA page as that user.
- `main.HandleRegister` (called by `POST /api/register`) creates an user account as usual, but also creates a secondary admin account named `admin_{username}`. The server:
  - generates a random password for this admin account, and
  - **reads the `FLAG` environment variable** and stores it in that admin account’s vault (which we need to leak).
- `main.generateKey` (called in `main.init`) **reads the `FLAG` and derives `main_key`**, which is used by `main.encrypt` / `main.decrypt` as the AES-GCM key for tokens.

### `generateKey` behavior
From decompilation and GDB runs, the function does:

1. Read `FLAG` bytes from environment variable.
2. Take the first 8 bytes of the flag as a little-endian `uint64` and call `math/rand.Seed(uint64)`.
3. Discard 256 calls to `rand.Int63()`.
4. Call `rand.Int63()` 16 times and use the low 8 bits of each call to form the 128-bit `main_key`.

This use of `math/rand` seeded from the flag makes `main_key` deterministic and brute-forcible, especially since 5 out of the first 8 bytes of the flag (`TISC{`) are known.

**Recreation of generateKey:**
```go
func genKey(flag []byte) []byte {
	seed := binary.LittleEndian.Uint64(flag[:8])
	src := rand.NewSource(int64(seed))
	for i := 0; i < 256; i++ {
		_ = src.Int63()
	}
	key := make([]byte, 16)
	for j := 0; j < 16; j++ {
		v := src.Int63()
		key[j] = byte(v & 0xff)
	}
	return key
}
```

---

## Forging admin token
- Tokens are AES-GCM encrypted blobs using `main_key` and the decrypted plaintext contains the username.
- A Go program ([bruteKey.go](files/bruteKey.go)) was used to brute force the seed and it was found to be `TISC{1t_`. Using this we can encrypt/decrypt tokens and forge tokens for any `admin_{username}` ([genToken.go](files/genToken.go)).

---

## CSS injection and exfiltration

### Summary
`POST /api/update_style` allows users to set `style_color` to change the color of their username. However the user input is unsafely interpolated as inline CSS after passing through a relatively weak sanitization process. This allows for CSS injection

By uploading a crafted `style_color` containing `:active { content: url("/api/profile/{dummy}?c=<nonce>") }`, each clicked button caused the bot to fetch a dummy profile when the selected elements are clicked. The server logs profile views with timestamps (`GET /api/views`), so collecting and sorting those timestamps reveals the click order. 

This approach does create some ambiguity due to the fact that the initial number buttons are shuffled and it is difficult to distinguish between buttons with the same number of digits. Operators were also ambiguous, as subsequent clicks couldn't be detected due to browser caching. This can be overcome by exfiltrating multiple times, and using a local brute force script to filter the possible candidates.

### Details
- Select classes:
  - 1-digit numbers: `.number-card:not([class*="chars"])` (three possiblities)
  - 2-digit: `.number-card--2-chars` (two possiblities)
  - 3/4-digit: `.number-card--3-chars`, `.number-card--4-chars`
  - operators: `.operators :nth-child(n)`
  - result slots: `.board .operation :nth-child(5)` (results 1 to 5)
- Use relative `content: url("/api/profile/{username}?c=...")` so sanitizer accepts it.
- Add cache busting `?c=<nonce>` to detect clicks from different numbers of same digit length.

### Recovering OTP and retrieving flag
- Register dummy accounts ([register.py](files/register.py))
- Send CSS payload ([set_style.py](files/set_style.py))
- Retrieve and reconstruct exfiltrated data ([scrape.py](files/scrape.py))
- Solve equations for OTP ([solve.py](files/solve.py))
- Enter the equations on the site to retrieve flag.

