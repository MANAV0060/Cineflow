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

def call_api(name, path, query="", region="NG"):
    print(f"\n==================== {name} ====================")
    ts = int(time.time() * 1000)
    sig = sign_request("GET", "*/*", "", "", ts, "", path, query)
    client_token = get_client_token(ts)
    
    full_url = f"https://tv.aoneroom.com{path}"
    if query:
        full_url += f"?{query}"
        
    client_info = {
        "package_name": "com.community.mbox.tv",
        "version_name": "1.1.11.0915.03",
        "version_code": 50040017,
        "os": "android",
        "os_version": "13",
        "brand": "Transsion",
        "model": "Infinix X6833B",
        "system_language": "en",
        "region": region,
        "timezone": "Africa/Lagos",
        "sp_code": "621"
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
            res = json.loads(data)
            print(f"Status 200 OK | Code: {res.get('code')}")
            return res
    except urllib.error.HTTPError as e:
        err = e.read().decode('utf-8')
        print(f"HTTP {e.code}: {err}")
    except Exception as e:
        print(f"Error: {e}")
    return None

# Test 1: Operating Cards (Home Feed)
home_res = call_api("1. Home Operating Cards API", "/wefeed-tv-bff/home/operating", "page=1&perPage=10&tabId=1")
if home_res and "data" in home_res:
    items = home_res["data"].get("items", [])
    print(f"Home Cards Count: {len(items)}")
    for it in items[:3]:
        print(f"  Card: {it.get('title')} | Type: {it.get('cardType')} | SubjectId: {it.get('subjectId')}")

# Test 2: Search Everyone / Trending
trending = call_api("2. Search Everyone/Rank API", "/wefeed-tv-bff/search/everyone")
if trending and "data" in trending:
    print("Trending keywords/items:", json.dumps(trending["data"], indent=2)[:400])

# Test 3: Search Result (Movies / Series)
search_res = call_api("3. Search Result API", "/wefeed-tv-bff/search/result", "keyword=Iron%20Man&page=1&perPage=5&subjectType=0")
subject_id = None
if search_res and "data" in search_res:
    items = search_res["data"].get("items", [])
    print(f"Search Results Count: {len(items)}")
    for it in items:
        subject = it.get("subject", {})
        sid = subject.get("subjectId") or it.get("subjectId")
        title = subject.get("title") or it.get("title")
        print(f"  Subject: {title} (ID: {sid}) | Genre: {subject.get('genre')}")
        if sid and not subject_id:
            subject_id = sid

# Test 4: Subject Details & Stream Captions (Subtitles)
if subject_id:
    call_api("4. Subject Details API", "/wefeed-tv-bff/subject/get", f"subjectId={subject_id}")
    call_api("5. Stream Captions (Subtitles) API", "/wefeed-tv-bff/subject/stream-captions", f"subjectId={subject_id}")
    play_res = call_api("6. Video Streaming Play-Info API", "/wefeed-tv-bff/subject/play-info/v2", f"subjectId={subject_id}&se=1&ep=1")
    if play_res and "data" in play_res:
        streams = play_res["data"].get("streams", [])
        print(f"Playable Video Streams: {len(streams)}")
        for s in streams:
            print(f"  Resolution: {s.get('resolution')} | Format: {s.get('format')} | URL: {s.get('url')}")
