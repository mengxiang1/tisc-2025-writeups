# Level 9: `HWisntThatHardv2`

**Flag:** `TISC{3mul4t3d_uC_pwn3d}`

## TL;DR
An emulator runs vulnerable STM32 firmware with a buffer overflow vulnerability, allowing us to overwrite the return address. The emulator does not enforce memory checks, so we can execute shellcode on the stack and write to any address, including where the ROM is loaded, allowing us to patch the code and retrieve the flag.

---

## Challenge summary
An STM32 emulator is provided together with a firmware binary and an external flash image file. The emulator loads the firmware at a fixed memory address, emulates an SPI interface to communicate with the external flash, and exposes a UART interface over stdin/stdout to interact with the firmware. 

By reversing the firmware in IDA, I found that it supports 2 main commands in JSON form:
- `{"slot":x}` (where 1 <= x <= 15): Retrieves and outputs the 32 bytes of data with the provided offset (slot) from the flash
- `{"slot":x,"data":[...]}` (where data is a list of decimal integers of arbitrary length): Appears to count the number of elements in the list that match the corresponding bytes in that slot

By inspecting the flash image, the flag is stored in the first 32 bytes of the flash, aka slot 0. However trying to simply read slot 0 gives an out of bounds error.

---

## Vulnerability analysis
From further fuzzing and reversing, I discovered that when the firmware parses the second type of command, there is an unsafe `memcpy` that copies the `data` array from the JSON command into a fixed buffer on the stack. This creates a buffer overflow vulnerability, allowing us to overwrite the return address.

The firmware architecture is ARM, but exploiting buffer overflows is more or less similar to x86. There is no ASLR as everything is loaded at a fixed address and ROP chains are possible, albeit being slightly more complex due to ARM calling conventions. 

To assist in debugging, I found the original source code of the emulator [here](https://github.com/nviennot/stm32-emulator/), made some patches to ensure the SPI and UART worked correctly and added more verbose logging.

I attempted to use ROP to call the functions that interacted with the SPI interface to read from the flash and print the results, but I quickly ran out of stack space. I tried a few other target addresses to jump to but was unsuccessful in retrieving the flag.

---

## Solution
I eventually discovered that the emulator could jump to any address, including the stack, and it would execute the instructions as usual. This behaviour did make sense as there is no underlying OS to enforce memory protections and the emulator does not enforce it either.

Having no memory protections also meant that I could write to where the firmware is loaded in memory, patching the firmware itself. By writing shellcode to patch out the instructions that prevented reading slot 0, I managed to successfully retrieve the flag.

[Solve script](solve.py)
