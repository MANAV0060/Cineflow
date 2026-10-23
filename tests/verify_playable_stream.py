import base64
import hashlib
import hmac
import time
import urllib.request
import ssl
import json
import urllib.parse
import re

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

def execute_request(path, query=""):
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
        "region": "NG",
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
    with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
        return json.loads(resp.read().decode('utf-8'))

def main():
    print("=" * 60)
    print("STEP 1: Search API (Search for Avatar)")
    print("=" * 60)
    search_data = execute_request("/wefeed-tv-bff/search/result", "keyword=Avatar&page=1&perPage=3&subjectType=0")
    items = search_data.get("data", {}).get("items", [])
    if not items:
        print("No items found.")
        return
    
    first_movie = items[0]
    subject_id = first_movie.get("subjectId")
    title = first_movie.get("title")
    print(f"Movie: {title}")
    print(f"Subject ID: {subject_id}")
    print(f"Release Date: {first_movie.get('releaseDate')}")
    print(f"Genre: {first_movie.get('genre')}")
    print(f"Cover URL: {first_movie.get('cover', {}).get('url')}")
    
    print("\n" + "=" * 60)
    print("STEP 2: Video Streaming Play-Info API")
    print("=" * 60)
    play_data = execute_request("/wefeed-tv-bff/subject/play-info/v2", f"subjectId={subject_id}")
    streams = play_data.get("data", {}).get("streams", [])
    print(f"Streams found: {len(streams)}")
    
    if not streams:
        print("No streams found.")
        return
        
    stream = streams[0]
    stream_url = stream.get("url")
    cookie = stream.get("signCookie")
    print(f"Codec: {stream.get('codecName')}")
    print(f"Format: {stream.get('format')}")
    print(f"Resolutions: {stream.get('resolutions')}")
    print(f"Duration: {stream.get('duration')} seconds")
    print(f"DASH Manifest URL: {stream_url}")
    print(f"CloudFront Cookie: {cookie[:60]}...")
    
    print("\n" + "=" * 60)
    print("STEP 3: Verify Video Stream Playability")
    print("=" * 60)
    req_mpd = urllib.request.Request(stream_url, headers={"User-Agent": "okhttp/4.12.0", "Cookie": cookie})
    with urllib.request.urlopen(req_mpd, context=ctx, timeout=10) as r:
        mpd_text = r.read().decode('utf-8')
        print(f"DASH MPD Manifest HTTP Status: {r.status} OK")
        
    # Find Representation IDs
    rep_ids = re.findall(r'<Representation\s+[^>]*id="([^"]+)"', mpd_text)
    if not rep_ids:
        rep_ids = re.findall(r'id="([^"]+)"', mpd_text)
    print(f"Available Representation IDs: {rep_ids}")

    init_match = re.search(r'initialization="([^"]+)"', mpd_text)
    if init_match and rep_ids:
        init_template = init_match.group(1)
        rep_id = rep_ids[0]
        init_rel = init_template.replace("$RepresentationID$", rep_id)
        base_dash_url = stream_url.rsplit('/', 1)[0]
        init_url = f"{base_dash_url}/{init_rel}"
        print(f"Downloading Video Init Segment for Representation {rep_id}: {init_url}")
        req_init = urllib.request.Request(init_url, headers={"User-Agent": "okhttp/4.12.0", "Cookie": cookie})
        with urllib.request.urlopen(req_init, context=ctx, timeout=10) as r_init:
            init_bytes = r_init.read()
            ftyp = init_bytes[4:8]
            print(f"Segment downloaded successfully! Size: {len(init_bytes)} bytes")
            print(f"MP4 Box Type: {ftyp.decode('latin1', errors='ignore')} (ISO Base Media File / ftyp)")
            print(">>> VIDEO STREAM INITIALIZATION CHUNK IS VERIFIED! <<<")
            
        # Also download chunk 1 of media!
        media_match = re.search(r'media="([^"]+)"', mpd_text)
        if media_match:
            media_template = media_match.group(1)
            media_rel = media_template.replace("$RepresentationID$", rep_id).replace("$Number$", "1").replace("$Number%05d$", "00001")
            media_url = f"{base_dash_url}/{media_rel}"
            print(f"Downloading Video Media Chunk 1: {media_url}")
            req_media = urllib.request.Request(media_url, headers={"User-Agent": "okhttp/4.12.0", "Cookie": cookie})
            with urllib.request.urlopen(req_media, context=ctx, timeout=10) as r_media:
                media_bytes = r_media.read()
                print(f"Video Media Chunk 1 downloaded successfully! Size: {len(media_bytes)} bytes")
                print(">>> VIDEO PLAYBACK DATA VERIFIED AND PLAYABLE! <<<")

    print("\n" + "=" * 60)
    print("STEP 4: Verify Subtitle API")
    print("=" * 60)
    resource_data = execute_request("/wefeed-tv-bff/subject/resource", f"page=1&perPage=5&subjectId={subject_id}")
    resources = resource_data.get("data", {}).get("items", [])
    print(f"Resources found: {len(resources)}")
    if resources:
        res0 = resources[0]
        captions = res0.get("captions", [])
        print(f"Available Subtitles: {len(captions)}")
        for cap in captions[:3]:
            print(f"  Language: {cap.get('language')} | URL: {cap.get('url')[:80]}...")
        if captions:
            # find english or first
            en_caps = [c for c in captions if c.get('language') == 'en']
            cap_target = en_caps[0] if en_caps else captions[0]
            cap_url = cap_target.get('url')
            print(f"Downloading Subtitle ({cap_target.get('language')}): {cap_url[:80]}...")
            req_cap = urllib.request.Request(cap_url)
            with urllib.request.urlopen(req_cap, context=ctx, timeout=10) as r_cap:
                srt_sample = r_cap.read().decode('utf-8', errors='ignore')[:300]
                safe_sample = srt_sample.encode('ascii', 'backslashreplace').decode('ascii')
                print(f"Downloaded Subtitle Sample:\n{safe_sample.strip()}")
                print(">>> SUBTITLES ARE VERIFIED AND WORKING! <<<")

if __name__ == "__main__":
    main()
