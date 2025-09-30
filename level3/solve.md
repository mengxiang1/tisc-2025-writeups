# Level 3 `Rotary Precision`

**Flag:** `TISC{thr33_d33_pr1n71n9_15_FuN_4c3d74845bc30de033f2e7706b585456}`

---

## Challenge summary

- We are given a file `rotary-precision.txt` which appears to be a G-code file.

---

## Solution
- Using online viewers, it appeared to be a mostly normal 3D model, but there are some strange movements of the print head near the top of the model.
- By inspecting the file, there are many chunks of suspicious instructions. An example line:
   - `G0 X7.989824091696275e-39 Y9.275539254788188e-39`
- The very small floating point values appeared to be encoding some hidden message.
- By expressing it in binary, it appeared that it was encoding ASCII text in last 8 bits of each floating point value.
- Extracting it revealed the following:
```
aWnegWRi18LwQXnXgxqEF}blhs6G2cVU_hOz3BEM2{fjTb4BI4VEovv8kISWcks4
def rot_rot(plain, key):
        charset = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789{}_"
        shift = key
        cipher = ""
        for char in plain:
                index = charset.index(char)
                cipher += (charset[(index + shift) % len(charset)])
                shift = (shift + key) % len(charset)

        return cipher
```
- Reversing the cipher reveals the flag.