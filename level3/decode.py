def decode(ciphertext, key):
    charset = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789{}_"
    shift = key
    plain = ""
    for char in ciphertext:
        index = charset.index(char)
        plain += charset[(index - shift) % len(charset)]
        shift = (shift + key) % len(charset)
    return plain

key = 7
print(decode("aWnegWRi18LwQXnXgxqEF}blhs6G2cVU_hOz3BEM2{fjTb4BI4VEovv8kISWcks4", key))