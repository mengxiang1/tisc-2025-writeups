# Level 11: `Ash Twin Project`

- **Flag 1:** `TISC{d0nt_l00k_aw4y_0r_1t5_g0n3_ea98b517efe292de1b3663a892c384c5}`
- **Flag 2:** `TISC{4r0und_th3_Un1v3r53_l1k3_4_r1_4x1s_cf47f7e49c6da010561866cda8f7d1c1}`
- **Flag 3:** Did not solve

## TL;DR
- The application exposes a PHP API that allows for sending HTTP `GET` requests, allowing SSRF to internal services.
- We can interact with the internal Redis server via SSRF, injecting Redis commands through HTTP headers.
- The `worker` container subscribes to the Redis server, and interacts with the GeoServer WMS running in the `geo` container, allowing us to arbitrarily interact with the WMS.
- The version of GeoServer used is vulnerable to CVE-2022-24816, allowing code injection via ras:jiffle process on the WMS.
- Using the RCE to interact with `the-eye`, we can get the `web` and `geo` flags.
- The `eye` flag requires exploiting Java deserialization in the custom eye program.

---

## Challenge summary
- The initial entry point is a `web` container running a PHP-based API. This API is the public-facing interface for the `orbital-probe-client` provided in the challenge files.
- The provided Go client `orbital-probe-client` implements the intended interactions with the API. It retrieves a proof-of-work, submits solutions, and polls for results. However it is mostly irrelevant to solving the challenge.
- The internal network consists of the following interconnected services:
    - A `redis` container that acts as a message queue.
    - A Python-based `worker` container that subscribes to a Redis channel `entries`. Upon receiving a message, it decodes it and sends a `POST` request to the `geo` service.
    - A `geo` container runs an instance of GeoServer and exposes a Web Map Service (WMS) endpoint that receives and processes XML data from `worker`.
    - A `the-eye` container runs a custom Java program listening on port `31337`. This is where the flags are stored and served. The first 2 flags can be through interacting with it through an intended protocol, sending it commands to retrieve either the `web` or `geo` flag. The last `eye` flag is not obtainable through interacting with it normally, and requires exploiting a vulnerability in the Java program itself.

---

## Initial observations
These were some of my initial observations when solving the challenge.
- The PHP API's `/api/check.php` endpoint is vulnerable to SSRF. It accepts a URL and custom headers, allowing us to send HTTP requests to services in the internal network.

```php
$json = file_get_contents('php://input');
$data = json_decode($json, true);

header('Content-Type: application/json');
$result = array(
    "result" => false
);

if (!isset($data["t"]) || !isset($data["h"])) {
    echo json_encode($result);
    return;
}

$t = $data["t"];
$h = $data["h"];

if (!str_starts_with($t, "http://")) {
    echo json_encode($result);
    return;
}

...

$c = stream_context_create(array(
    "http" => array(
        "ignore_errors" => true,
        "header" => implode("\r\n", $nh)
    )
));

$response = @file_get_contents($t, false, $c);
```

- I initially did not notice that the SSRF only allowed GET requests, so I assumed I could interact with any internal HTTP service.
- The GeoServer instance especially piqued my interest, as it was something new to me. Since I was under the assumption that I could interact with it via SSRF, I began focusing on finding vulnerabilities in the GeoServer service.

---

## GeoServer vulnerability research
After some research, I considered a few GeoServer-related CVEs:

- **CVE-2024-36401 - XPath/property-name evaluation RCE:** 
    - This was a promising CVE as it is possible to achieve RCE by sending a malicious OGC filter in an XML `POST` request. 
    - The vulnerability lies in how GeoServer processes these filters. However, a requirement for an OGC filter to be processed is that it must be applied to a valid, existing dataset or layer, referred to as a `typeName`. 
    - Since the challenge uses an fresh and empty GeoServer instance and no `typeName`s exists on the target server, GeoServer would reject the request with an error like `LayerNotDefined` before it ever reached the vulnerable filter evaluation code.
- **CVE-2022-24816 - Jiffle code injection (jt-jiffle extension):**
    - This was another promising CVE which also enables RCE, this time through the vulnerable Jiffle extension of GeoServer.
    - The vulnerability is in how Jiffle, a scripting language to work with raster images, parses Jiffle scripts, leading to code injection due to not properly escaping comments.
    - Jiffle interpolates the full user-supplied Jiffle script to the top of some Java source code within comments. However, it is possible to escape the comments and inject malicious Java code.

Since the version of GeoServer used in the challenge (2.20.3) is vulnerable to CVE-2022-24816, I worked on crafting an exploit to solve the challenge. 

## Crafting the RCE payload
- I mainly referred to this article, [Exploiting CVE-2022-24816: A code injection in the jt-jiffle extension of GeoServer](https://www.synacktiv.com/en/publications/exploiting-cve-2022-24816-a-code-injection-in-the-jt-jiffle-extension-of-geoserver), for more background and examples of the CVE.

- The most widely-used PoC is to override Java's `Double` class in the injected code and placing the code to run inside a `static` block. This is due to Jiffle accessing the `Double` class when initializing a variable in its own code: 
``` java
double result = Double.NaN;
```

- In the challenge’s Jiffle implementation that exact line was absent.

- While I initially tried to look for other possible attack vectors with the class injection, I eventually discovered that I can set a Jiffle variable to `NULL` (e.g. `dest = NULL;`). This compiles to `Double.NaN`, which again forces the initialization of our overriden `Double` class, triggering our `static` initializer.

With the RCE I could connect and interact with `the-eye` server, exfiltrating both the `web` and `geo` flags. [Injected Double Class](./files/Double.java)

---

## How the payload reaches GeoServer
- The SSRF endpoint only issues `GET` requests, so I could not directly `POST` XML containing the Jiffle payload to GeoServer.
- However, the `worker` listens to Redis and forwards messages to GeoServer via `POST`. This can be used to forward our malicious payload.
- Redis uses a simple plaintext protocol like HTTP. Since I can add custom headers in the SSRF request, I can inject CRLFs and craft a payload with Redis commands.
- My initial attempts were unsuccessful as Redis detected the HTTP `Host` header, indicating possible XSS or SSRF, thus closing the connection:
```
Possible SECURITY ATTACK detected. It looks like somebody is sending POST or Host: commands to Redis. This is likely due to an attacker attempting to use Cross Protocol Scripting to compromise your Redis instance.
```
- This was easily bypassed by appending a `Host` header after the Redis commands, as it results in the `Host` header arriving after the Redis commands, allowing the commands to be parsed before the connection is closed. 

Combining this with the Jiffle RCE payload, I am able to exfiltrate the flags to solve the first 2 challenges.

## The last flag
I was not manage to get the final `eye` during the duration of the CTF. To retrieve this flag, interacting with the internal `the-eye` program is not sufficient, as the source code itself never references this flag.

Instead, the intended solution is most likely involves the Java deserialization vulnerability in `Token.java`, where a user-supplied token is unsafely deserialized:

```java
public static Token deserializeFromBase64(String data) throws IOException, ClassNotFoundException {
    return deserializeFromBytes(Base64.getDecoder().decode(data));
}

public static Token deserializeFromBytes(byte[] data) throws IOException, ClassNotFoundException {
    byte[] decompressed = Snappy.uncompress(data);
    Input input = new Input(decompressed);
    Kryo kryo = createKryo();

    return kryo.readObject(input, Token.class);
}

public static Kryo createKryo() {
    Kryo kryo = new Kryo();
    kryo.setRegistrationRequired(false);
    kryo.setReferences(false);

    try {
        Class<?>[] f = Collections.class.getDeclaredClasses();
        Arrays.stream(f)
            .filter(cls -> MISSED_COLLECTION_CLASSES.stream().anyMatch(s -> cls.getName().contains(s)))
            .forEach(cls -> kryo.addDefaultSerializer(cls, new JavaSerializer()));
    } catch (Exception e) {
        e.printStackTrace();
    }
    kryo.addDefaultSerializer(UUID.class, new DefaultSerializers.UUIDSerializer());
    kryo.addDefaultSerializer(URI.class, new DefaultSerializers.URISerializer());
    kryo.addDefaultSerializer(Pattern.class, new DefaultSerializers.PatternSerializer());
    kryo.addDefaultSerializer(AtomicBoolean.class, new DefaultSerializers.AtomicBooleanSerializer());
    kryo.addDefaultSerializer(AtomicInteger.class, new DefaultSerializers.AtomicIntegerSerializer());
    kryo.addDefaultSerializer(AtomicLong.class, new DefaultSerializers.AtomicLongSerializer());
    kryo.addDefaultSerializer(AtomicReference.class, new DefaultSerializers.AtomicReferenceSerializer());

    return kryo;
}
```

I tried common, off-the-shelf tools like `ysoserial` and `marshalsec` without much success. Those tools primarily target Java's native ObjectInputStream or specific frameworks, and they also did not work on modern Java version like Java 21, where module encapsulation have made deserialization attacks more bulletproof.

# Conclusion
While I was not able to solve fully solve the challenge, it was still a fruitful and interesting experience, where I got to learn more about niche software like GeoServer, researching CVEs and Java deserialization. 