import base64
import hashlib
import hmac
import time
import urllib.request
import ssl
import json

SECRET_B64 = "76iRl07s0xSN9jqmEWAt79EBJZulIQIsV64FZr2O"
SECRET = base64.b64decode(SECRET_B64)

def sign_request(method, accept, content_type, content_length, timestamp, body_md5, path):
    parts = [
        method.upper(),
        accept or "",
        content_type or "",
        str(content_length) if content_length is not None else "",
        str(timestamp),
        body_md5 or "",
        path
    ]
    str_to_sign = "\n".join(parts)
    print(f"--- String to sign ---\n{repr(str_to_sign)}\n---")
    h = hmac.new(SECRET, str_to_sign.encode('utf-8'), hashlib.md5)
    sig_b64 = base64.b64encode(h.digest()).decode('ascii')
    return f"{timestamp}|2|{sig_b64}"

body = b"{}"
body_md5 = hashlib.md5(body).hexdigest()
ts = int(time.time() * 1000)
path = "/wefeed-tv-bff/user/visitor-login"

sig = sign_request("POST", "*/*", "application/json", len(body), ts, body_md5, path)

client_info = {
    "package_name": "com.moviebox.tv",
    "version_name": "1.0.0",
    "version_code": 100,
    "os": "android",
    "os_version": "13",
    "brand": "Google",
    "model": "Pixel 7",
    "system_language": "en",
    "region": "US"
}

headers = {
    "User-Agent": "okhttp/4.12.0",
    "accept": "*/*",
    "Content-Type": "application/json",
    "Content-Length": str(len(body)),
    "x-tr-signature": sig,
    "X-Client-Info": json.dumps(client_info),
    "X-Client-Status": "0"
}

url = f"https://tv.aoneroom.com{path}"
req = urllib.request.Request(url, data=body, headers=headers, method="POST")

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

try:
    with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
        res = json.loads(resp.read().decode('utf-8'))
        print("Response:", json.dumps(res, indent=2))
except urllib.error.HTTPError as e:
    print(f"HTTP {e.code}:", e.read().decode('utf-8'))
except Exception as e:
    print(f"Error:", e)
