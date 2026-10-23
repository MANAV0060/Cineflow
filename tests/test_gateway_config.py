import base64
import hashlib
import hmac
import time
import urllib.request
import ssl
import json

SECRET_B64 = "76iRl07s0xSN9jqmEWAt79EBJZulIQIsV64FZr2O"
SECRET = base64.b64decode(SECRET_B64)
APPID = "4U01pxRu278GqCZKY9"

def sign_request(method, accept, content_type, content_length, timestamp, body_md5, path_and_query):
    # string to sign
    parts = [
        method.upper(),
        accept or "",
        content_type or "",
        str(content_length) if content_length else "",
        str(timestamp),
        body_md5 or "",
        path_and_query
    ]
    str_to_sign = "\n".join(parts)
    print(f"--- String to sign ---\n{repr(str_to_sign)}\n---")
    
    # HMAC-MD5
    h = hmac.new(SECRET, str_to_sign.encode('utf-8'), hashlib.md5)
    sig_b64 = base64.b64encode(h.digest()).decode('ascii')
    return f"{timestamp}|2|{sig_b64}"

ts = int(time.time() * 1000)
path = "/gateway/sdk/v1/config"
query = f"app={APPID}&configVersion=0"
full_path = f"{path}?{query}"
url = f"https://apigateway.tmctool.com{full_path}"

sig = sign_request("GET", "", "", "", ts, "", full_path)
print("Signature:", sig)

req = urllib.request.Request(url, headers={
    "x-tr-signature": sig,
    "Host": "apigateway.tmctool.com"
})

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

try:
    with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
        content = resp.read().decode('utf-8')
        print(f"Response ({resp.status}):\n{content}")
except urllib.error.HTTPError as e:
    err = e.read().decode('utf-8')
    print(f"HTTP Error {e.code}:\n{err}")
except Exception as e:
    print(f"Error: {e}")
