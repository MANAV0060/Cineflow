import json
import urllib.request
import urllib.parse
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# Test 1: Subtitle Search API (vip-api.opensubtitles.com)
print("=== Testing Subtitle Search API ===")
sub_url = "https://vip-api.opensubtitles.com/api/v1/subtitles?query=inception&languages=en"
req = urllib.request.Request(sub_url, headers={
    "User-Agent": "player2024",
    "Api-Key": "ZRN9QpqcTxje5UH3bV1RuugwitxkqB53"
})
try:
    with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        print(f"Status: {resp.status}")
        total = data.get("total", len(data.get("data", [])))
        print(f"Subtitles found: {total}")
        if data.get("data"):
            first = data["data"][0]
            attrs = first.get("attributes", {})
            files = attrs.get("files", [{}])
            file_id = files[0].get("file_id") if files else None
            print(f"Sample Subtitle: {attrs.get('release')} | Language: {attrs.get('language')} | file_id: {file_id}")
            
            # Test Subtitle Download API
            if file_id:
                print("\n=== Testing Subtitle Download API ===")
                dl_req = urllib.request.Request(
                    "https://vip-api.opensubtitles.com/api/v1/download",
                    data=json.dumps({"file_id": file_id}).encode('utf-8'),
                    headers={
                        "User-Agent": "player2024",
                        "Api-Key": "ZRN9QpqcTxje5UH3bV1RuugwitxkqB53",
                        "Content-Type": "application/json",
                        "Accept": "application/json"
                    }
                )
                with urllib.request.urlopen(dl_req, context=ctx, timeout=10) as dl_resp:
                    dl_data = json.loads(dl_resp.read().decode('utf-8'))
                    print(f"Subtitle Download URL: {dl_data.get('link')}")
except Exception as e:
    print(f"Subtitle API Error: {e}")

print("\n" + "="*40 + "\n")

# Test 2: Search API & Home Card API (api6.aoneroom.com)
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
    "X-Client-Info": json.dumps(client_info),
    "X-Client-Status": "0"
}

# Test Tab List
print("=== Testing Tab List API ===")
tab_url = "https://api6.aoneroom.com/wefeed-tv-bff/tab/list"
try:
    req = urllib.request.Request(tab_url, headers=headers)
    with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
        res = json.loads(resp.read().decode('utf-8'))
        print(f"Tab List Response Code: {res.get('code')}, Message: {res.get('message')}")
        tabs = res.get("data", {}).get("list", [])
        print(f"Tabs count: {len(tabs)}")
        for t in tabs[:5]:
            print(f"  Tab: {t.get('title')} (id: {t.get('id')})")
except Exception as e:
    print(f"Tab List API Error: {e}")

# Test Search Result API
print("\n=== Testing Search Result API ===")
search_url = "https://api6.aoneroom.com/wefeed-tv-bff/search/result?keyword=avatar&page=1&perPage=5&subjectType=0"
try:
    req = urllib.request.Request(search_url, headers=headers)
    with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
        res = json.loads(resp.read().decode('utf-8'))
        print(f"Search Response Code: {res.get('code')}, Message: {res.get('message')}")
        results = res.get("data", {}).get("list", [])
        print(f"Search items returned: {len(results)}")
        subject_id = None
        for item in results[:3]:
            subject_id = item.get("subjectId") or item.get("id")
            print(f"  Title: {item.get('title')} | ID: {subject_id} | Type: {item.get('subjectType')}")
            
        # Test Play Info API if subject_id found
        if subject_id:
            print("\n=== Testing Video Streaming Play-Info API ===")
            play_url = f"https://api6.aoneroom.com/wefeed-tv-bff/subject/play-info/v2?subjectId={subject_id}&se=1&ep=1"
            req_play = urllib.request.Request(play_url, headers=headers)
            with urllib.request.urlopen(req_play, context=ctx, timeout=10) as play_resp:
                play_res = json.loads(play_resp.read().decode('utf-8'))
                print(f"Play-Info Response Code: {play_res.get('code')}, Message: {play_res.get('message')}")
                data_play = play_res.get("data", {})
                streams = data_play.get("streams", [])
                print(f"Streams found: {len(streams)}")
                for s in streams:
                    print(f"  Quality: {s.get('resolution')} | URL: {s.get('url')[:60]}... | Format: {s.get('format')}")
except Exception as e:
    print(f"Search / Play API Error: {e}")
