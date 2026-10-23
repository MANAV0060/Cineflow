import base64
import hashlib
import hmac
import time
import urllib.request
import ssl
import json
import urllib.parse

SECRET_B64 = "76iRl07s0xSN9jqmEWAt79EBJZulIQIsV64FZr2O"
SECRET = base64.b64decode(SECRET_B64)

def sort_query(query_str):
    if not query_str:
        return ""
    params = urllib.parse.parse_qsl(query_str, keep_blank_values=True)
    params.sort(key=lambda x: x[0])
    return urllib.parse.urlencode(params)

def sign_request(method, accept, content_type, content_length, timestamp, body_md5, path, query=""):
    formatted_path = path
    if query:
        formatted_path += "?" + sort_query(query)
    
    parts = [
        method.upper(),
        accept or "",
        content_type or "",
        str(content_length) if content_length else "",
        str(timestamp),
        body_md5 or "",
        formatted_path
    ]
    str_to_sign = "\n".join(parts)
    
    h = hmac.new(SECRET, str_to_sign.encode('utf-8'), hashlib.md5)
    sig_b64 = base64.b64encode(h.digest()).decode('ascii')
    return f"{timestamp}|2|{sig_b64}"

def get_client_token(ts):
    str_ts = str(ts)
    str_rev = str_ts[::-1]
    md5_hash = hashlib.md5(str_rev.encode('utf-8')).hexdigest()
    return f"{str_ts},{md5_hash}"

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def test_endpoint(name, path, query=""):
    print(f"\n=== Testing {name} ===")
    ts = int(time.time() * 1000)
    sig = sign_request("GET", "*/*", "", "", ts, "", path, query)
    client_token = get_client_token(ts)
    print(f"X-Client-Token: {client_token}")
    
    full_url = f"https://tv.aoneroom.com{path}"
    if query:
        full_url += f"?{query}"
        
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
        "x-tr-signature": sig,
        "X-Client-Token": client_token,
        "X-Client-Info": json.dumps(client_info),
        "X-Client-Status": "0"
    }
    
    req = urllib.request.Request(full_url, headers=headers)
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
            data = resp.read().decode('utf-8')
            print(f"Status: {resp.status}")
            print(f"Response: {data[:500]}")
            return json.loads(data)
    except urllib.error.HTTPError as e:
        err = e.read().decode('utf-8')
        print(f"HTTP {e.code}: {err}")
    except Exception as e:
        print(f"Error: {e}")
    return None

# Test 1: Tab List
test_endpoint("Tab List", "/wefeed-tv-bff/tab/list")

# Test 2: Search Suggest
test_endpoint("Search Suggest", "/wefeed-tv-bff/search/suggest", "keyword=avatar&perPage=5")

# Test 3: Search Result
test_endpoint("Search Result", "/wefeed-tv-bff/search/result", "keyword=avatar&page=1&perPage=5&subjectType=0")

# Test 4: Home Operating (Cards/Feed)
test_endpoint("Home Operating Cards", "/wefeed-tv-bff/home/operating", "page=1&perPage=5&tabId=1")
