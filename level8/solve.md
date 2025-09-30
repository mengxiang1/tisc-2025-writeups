# Level 7: `Virus Vault`

**Flag:** `TISC{pHp_d3s3ri4liz3_4_fil3_inc1us!0n}`

## TL;DR

- `mb_convert_encoding($quoted, 'UTF-8', 'ISO-8859-1')` expands some bytes, desynchronizing PHP serialized string lengths.
- This lets us craft a serialized blob that overwrites properties when `unserialize()` is called.
- `Virus::printInfo()` does `include $this->species . ".txt"`. 
- Set `species` to a `php://filter` chain that constructs `<?php phpinfo(); ?>` to read the environment flag.

---

## Challenge summary

- Web app lets you store and fetch `Virus` objects (name + species) in a SQLite DB.
- Objects are `serialize()`d, quoted for SQL, then passed through `mb_convert_encoding(..., 'UTF-8', 'ISO-8859-1')` before insertion.
- Fetching `unserialize()`s the DB value and calls `Virus::printInfo()`, which does `include $this->species . ".txt"`.
- The `.txt` files contain 
- The flag is stored in an environment variable.

---

## Deserialization vulnerability

- PHP serialized strings encode a length like `s:<len>:"...";`. `unserialize()` trusts that `<len>` to know how many bytes to read for the string.
- The program calls `mb_convert_encoding($quoted, 'UTF-8', 'ISO-8859-1')` **after** serialization. This conversion turns certain single-byte ISO-8859-1 characters into 2+ UTF-8 bytes.
- Because bytes expand during conversion, the actual number of bytes stored can be greater than the `<len>` specified by `serialize()`, desynchronizing the declared length and the stored bytes.
- When `unserialize()` is called on the desynchronized blob, it will the original number of bytes of the string. Since the string has expanded, the rest of the string becomes becomes treated as part of the serialized object, allowing us to inject fields.

---

## Next steps

- We can now overwrite arbitrary fields in the deserialized `Virus` object.
- `include $this->species . ".txt"` within `Virus::printInfo()` means controlling `species` allows arbitrary include (with `.txt` appended).
- If we control what is `include`d, we can potentially get PHP code execution.
- `open_basedir` is set to `getcwd()`, so includes are limited to the working directory. `.txt` is also appended automatically, so no arbitrary file reads.
- URLs and `file://` wrappers are also blocked.

---

## `php://filter` chaining

- `include` accepts wrappers like `php://filter`, which lets you transform the data before being passed to `include` (base64, convert encodings, etc.).
- These transformations can be chained to create any string we want, even if we start with an empty string.
- We are forced to append `.txt`, so we cannot start from an empty stream directly (e.g. `php://temp`). Instead:
  - Use one of the provided `.txt` files as the source.
  - Use a filter chain such as repeated `convert.base64-decode` to transform the `.txt` into an empty stream.
  - Use a tool like [php_chain_generator](https://github.com/synacktiv/php_filter_chain_generator/blob/main/php_filter_chain_generator.py) which can automatically generate chains to produce arbitrary bytes from an empty stream.
- Once `include` processes `php://filter/.../resource=IronHydra.txt`, the transformed contents are executed by the PHP engine.
- We can use `<?php phpinfo(); ?>` to get the flag, as it returns a lot of information about the PHP environment on the server, including the environment variable containing the flag. 