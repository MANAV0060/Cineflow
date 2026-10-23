import verify_playable_stream, urllib.request, re

play_data = verify_playable_stream.execute_request('/wefeed-tv-bff/subject/play-info/v2', 'subjectId=8906247916759695608')
stream = play_data['data']['streams'][0]
url = stream['url']
cookie = stream['signCookie']

print("Resolutions in stream object:", stream.get("resolutions"))

req = urllib.request.Request(url, headers={'User-Agent': 'okhttp/4.12.0', 'Cookie': cookie})
with urllib.request.urlopen(req, context=verify_playable_stream.ctx) as r:
    mpd = r.read().decode('utf-8')
    for line in mpd.splitlines():
        if '<Representation' in line:
            print("  ", line.strip())
