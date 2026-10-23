import os
import sys
import json
import time
import base64
import hmac
import hashlib
import ssl
import urllib.request
import urllib.parse
import subprocess
import gzip
from flask import Flask, request, jsonify, Response, send_from_directory

app = Flask(__name__, static_folder="static")

@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, Range"
    response.headers["Access-Control-Expose-Headers"] = "Content-Length, Content-Range"
    return response

@app.route("/api/health")
def api_health():
    """Lightweight 0-CPU health endpoint for Autobot / Keep-Awake pingers."""
    return jsonify({
        "status": "online",
        "service": "CineFlow Streaming Engine",
        "timestamp": int(time.time()),
        "uptime": "active"
    })

SECRET_B64 = "76iRl07s0xSN9jqmEWAt79EBJZulIQIsV64FZr2O"
SECRET = base64.b64decode(SECRET_B64)
BASE_HOST = "https://tv.aoneroom.com"

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def get_client_token(ts):
    str_ts = str(ts)
    str_rev = str_ts[::-1]
    md5_hash = hashlib.md5(str_rev.encode("utf-8")).hexdigest()
    return f"{str_ts},{md5_hash}"

def execute_api(path, query=""):
    params = {}
    if isinstance(query, str) and query:
        for pair in urllib.parse.parse_qsl(query, keep_blank_values=True):
            params[pair[0]] = pair[1]
    elif isinstance(query, dict):
        params = query
        
    ts = int(time.time() * 1000)
    
    # Sort alphabetically by key
    if params:
        sorted_pairs = sorted(params.items(), key=lambda x: x[0])
        # In string-to-sign, parameter values are raw unencoded (per Transsion c.java)
        raw_query_str = "&".join(f"{k}={v}" for k, v in sorted_pairs)
        # In HTTP request URL, parameter values are percent-encoded
        encoded_query_str = "&".join(f"{k}={urllib.parse.quote(str(v))}" for k, v in sorted_pairs)
        formatted_sign_path = f"{path}?{raw_query_str}"
        full_url = f"{BASE_HOST}{path}?{encoded_query_str}"
    else:
        formatted_sign_path = path
        full_url = f"{BASE_HOST}{path}"
        
    parts = ["GET", "*/*", "", "", str(ts), "", formatted_sign_path]
    str_to_sign = "\n".join(parts)
    h = hmac.new(SECRET, str_to_sign.encode("utf-8"), hashlib.md5)
    sig = f"{ts}|2|{base64.b64encode(h.digest()).decode('ascii')}"
    client_token = get_client_token(ts)
    
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
    with urllib.request.urlopen(req, context=ctx, timeout=12) as resp:
        return json.loads(resp.read().decode("utf-8"))

def srt_to_vtt(srt_text):
    lines = srt_text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    vtt = ["WEBVTT\n"]
    for line in lines:
        if "-->" in line:
            line = line.replace(",", ".")
        vtt.append(line)
    return "\n".join(vtt)

# ==============================================================================
# ANILILI / MIRURO ANIME STREAMING ENGINE (DRAGON BALL & ANIME INTEGRATION)
# ==============================================================================
DRAGONBALL_IDS = {"dragonball", "223", "dragonball_dub", "dragonball_sub", "rqxAbYshiv3CtbJ4cetuZ-yKIe2Cyjqr"}

DRAGONBALL_CARD = {
    "subjectId": "dragonball",
    "title": "Dragon Ball",
    "subjectName": "Dragon Ball",
    "subjectType": 2,  # TV Series
    "year": "1986",
    "releaseDate": "1986-02-26",
    "genre": "Animation, Action & Adventure, Comedy, Anime",
    "genres": ["Animation", "Action & Adventure", "Comedy", "Anime"],
    "score": "8.8",
    "cover": {
        "url": "https://image.tmdb.org/t/p/w500/2RSrQ82HNbBBVM3omiHObQ0EvqI.jpg"
    },
    "thumbnail": "https://image.tmdb.org/t/p/w500/2RSrQ82HNbBBVM3omiHObQ0EvqI.jpg",
    "description": "Bulma is a girl in search of the legendary Dragon Balls that say when all seven are gathered, one's wish will come true. She meets Goku, an extraordinary boy living in Mount Paozu who possesses the four-star Dragon Ball. Together, they embark on an epic quest across the world.",
    "synopsis": "Bulma is a girl in search of the legendary Dragon Balls that say when all seven are gathered, one's wish will come true. She meets Goku, an extraordinary boy living in Mount Paozu who possesses the four-star Dragon Ball.",
    "duration": 1450,
    "corner": "Anime",
    "country": "Japan"
}

_db_stream_cache = {}

def resolve_dragonball_stream(ep=1, is_dub=True):
    """
    Dynamically resolves Dragon Ball episode stream from Miruro/Anilili reverse-engineered API with resilient fallback.
    """
    cache_key = f"{ep}_{is_dub}"
    now = time.time()
    if cache_key in _db_stream_cache:
        cached_time, cached_val = _db_stream_cache[cache_key]
        if now - cached_time < 1800:
            return cached_val
            
    try:
        host = "https://www.miruro.bz"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Referer": "https://www.miruro.bz/",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "cors",
            "Accept": "application/json, application/octet-stream;q=0.9, */*;q=0.8"
        }
        miruro_id = "rqxAbYshiv3CtbJ4cetuZ-yKIe2Cyjqr"
        url = f"{host}/api/v1/anime/{miruro_id}/episodes/{ep}/play"
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=7) as r:
            ct = r.headers.get("Content-Type", "")
            raw = r.read()
            if "application/octet-stream" in ct:
                key = b"miruro/catalog"
                decrypted = bytes([b ^ key[i % len(key)] for i, b in enumerate(raw)])
                payload_str = gzip.decompress(decrypted).decode("utf-8")
            else:
                payload_str = raw.decode("utf-8")
            payload = json.loads(payload_str)
            wanted_track = "dub" if is_dub else "sub"
            for t in payload.get("tracks", []):
                if t.get("track") == wanted_track:
                    for p in t.get("providers", []):
                        if p.get("provider") == "icarus":
                            for s in p.get("servers", []):
                                if s.get("streams"):
                                    st_url = s["streams"][0]["url"]
                                    h = s.get("headers", {})
                                    res = {
                                        "url": st_url,
                                        "origin": h.get("Origin", "https://ultracloud.cc"),
                                        "referer": h.get("Referer", "https://ultracloud.cc/")
                                    }
                                    _db_stream_cache[cache_key] = (now, res)
                                    return res
    except Exception as e:
        print(f"[Miruro API] Resolver fallback for Dragon Ball ep {ep}: {e}")
        
    fallback_url = (
        "https://fielddewice-31.trail29.top/m/ASBoHpTyH_HbHf1LpHCUWXZQ3NxDMFrGpi3cn8UMpHLxd2TW8nrT_jE_yWnSflFed1nr-Hv-wERqQclSHMZlN_Sj-nHE1ziZ23UupVFLjlIAcfmithVDi6hiUZXo-sLadDj90kQOda_LQAPOke5et4DOPla_O-w4joTGpkAHoChWdO3cp-TmbHfLpeaaurQoVBEcw7vQb9L3TcSdQNu0nzWpc-ZIPB1dXleliaRBMKXLQAvzQAokJ2Y9ZVyqATGFGFSy8wIy-ruVO4Z3D_dQcQw3n6IOHJY13ziXZvBfp6d_vOA9QIHNXAa6V7DBeokLLpT2StVW5bjBOA.m3u8"
        if is_dub else
        "https://fielddewice-31.trail29.top/m/AeqxIUu7M8m38YU__LyelHX8KQQH46IrAuoPcxord_g9333dUP7KWF4XrW2eRskRHVS5JoJj93gPDodBzZuwcXUibciMbtDXonFhRrZb1qHK3CiG6zNn5BmGUsC4JBDVZDjb4ab0PSwh-NmtRZB3DfFMouwmYtLgbeG-DRaK3N361W-xrEak0nm16Het8FY-fw_P8BzvAcOKRqFTsjoZW4aG09hjxVMhFYTcrbkCwBaf-JukPE8EFtqsRRCZeXf3cECTTX4qzj9jhjMLwR-AI1dGFbDv_pO1a1IdaB47yxTyUGk1SRkU6FX17m9syo4EwMC0c_mtUmrDYw.m3u8"
    )
    return {
        "url": fallback_url,
        "origin": "https://ultracloud.cc",
        "referer": "https://ultracloud.cc/"
    }

@app.route("/")
def index():
    if os.path.exists("index.html"):
        return send_from_directory(".", "index.html")
    return send_from_directory("static", "index.html")

@app.route("/api/search")
def api_search():
    keyword = request.args.get("keyword", "").strip()
    page = request.args.get("page", "1")
    per_page = request.args.get("perPage", "12")
    subject_type = request.args.get("subjectType", "0")
    
    if not keyword:
        return jsonify({"code": 0, "data": {"items": [], "relatedKeywords": [], "recommendations": []}})
        
    query = f"keyword={urllib.parse.quote(keyword)}&page={page}&perPage={per_page}&subjectType={subject_type}"
    try:
        data = execute_api("/wefeed-tv-bff/search/result", query)
        items = data.get("data", {}).get("items", [])
        
        # 1. Fetch related search keyword suggestions
        related_words = []
        try:
            suggest_data = execute_api("/wefeed-tv-bff/search/suggest", f"keyword={urllib.parse.quote(keyword)}&perPage=8")
            s_items = suggest_data.get("data", {}).get("items", [])
            related_words = [item.get("word") for item in s_items if item.get("word")]
        except Exception:
            pass
            
        # 2. Universal multi-facet language dub search:
        # Check if suggestions contain language indicators like [Hindi] or [English]
        seen_ids = {str(it.get("subjectId")) for it in items if it.get("subjectId")}
        candidate_queries = []
        # 1. Directly query "{keyword} hindi" as candidate #1 to immediately discover Hindi dubs
        if "hindi" not in keyword.lower():
            candidate_queries.append(f"{keyword} hindi")
            
        # 2. Add suggestions containing language indicators
        for w in related_words:
            if any(lang in w.lower() for lang in ["hindi", "dub", "dual", "tamil", "telugu"]) or "[" in w:
                if w not in candidate_queries:
                    candidate_queries.append(w)
            
        # Common phonetic transliterations (e.g. sin -> shin, doremon -> doraemon)
        kw_lower = keyword.lower()
        if kw_lower.startswith("sin"):
            sh_kw = "sh" + keyword[1:]
            candidate_queries.append(sh_kw)
            candidate_queries.append(f"{sh_kw} hindi")
        elif "doremon" in kw_lower:
            candidate_queries.append(kw_lower.replace("doremon", "doraemon") + " hindi")
            
        for cq in candidate_queries[:4]:
            try:
                cq_data = execute_api("/wefeed-tv-bff/search/result", f"keyword={urllib.parse.quote(cq)}&page=1&perPage=6&subjectType={subject_type}")
                cq_items = cq_data.get("data", {}).get("items", [])
                for cq_it in cq_items:
                    cq_id = str(cq_it.get("subjectId"))
                    if cq_id and cq_id not in seen_ids:
                        seen_ids.add(cq_id)
                        # Place language counterpart with priority right alongside the primary match
                        is_lang = str(cq_it.get("corner")).lower() == "hindi" or "[hindi]" in cq_it.get("title", "").lower()
                        insert_pos = 1 if (is_lang and len(items) >= 1) else len(items)
                        items.insert(insert_pos, cq_it)
            except Exception:
                pass

        # 3. Fetch related recommendations
        recommendations = []
        if items:
            first_id = items[0].get("subjectId")
            try:
                rec_data = execute_api("/wefeed-tv-bff/subject/detail-rec", f"subjectId={first_id}&page=1&perPage=12")
                recommendations = rec_data.get("data", {}).get("items", [])
            except Exception:
                pass
                
        # 4. If no recommendations or few items, add trending recommendations
        if len(items) < 3 or not recommendations:
            try:
                rank_data = execute_api("/wefeed-tv-bff/search/rank")
                hot_list = rank_data.get("data", {}).get("hot", [])
                for cat in hot_list:
                    recommendations.extend(cat.get("items", []))
            except Exception:
                pass
                
        # Inject Dragon Ball if searched or if related to anime / DB
        kw_l = keyword.lower()
        if any(term in kw_l for term in ["dragon", "ball", "db", "goku", "anime"]):
            if not any(it.get("subjectId") == "dragonball" for it in items):
                items.insert(0, DRAGONBALL_CARD)

        return jsonify({
            "code": 0,
            "data": {
                "items": items,
                "relatedKeywords": related_words[:6],
                "recommendations": recommendations[:12]
            }
        })
    except Exception as e:
        return jsonify({"code": 500, "message": str(e), "data": {"items": [DRAGONBALL_CARD] if any(term in keyword.lower() for term in ['dragon', 'ball', 'goku']) else [], "relatedKeywords": [], "recommendations": []}}), 500

@app.route("/api/search/suggest")
def api_search_suggest():
    keyword = request.args.get("keyword", "").strip()
    if not keyword:
        return jsonify({"code": 0, "suggestions": []})
    try:
        kw_lower = keyword.lower()
        lookup_kw = keyword
        if kw_lower.startswith("sin"):
            lookup_kw = "sh" + keyword[1:]
        elif "doremon" in kw_lower:
            lookup_kw = kw_lower.replace("doremon", "doraemon")
            
        data = execute_api("/wefeed-tv-bff/search/suggest", f"keyword={urllib.parse.quote(lookup_kw)}&perPage=8")
        words = [it.get("word") for it in data.get("data", {}).get("items", []) if it.get("word")]
        
        # Universally discover Hindi suggestions for ANY query
        if "hindi" not in kw_lower and len(keyword) >= 2:
            try:
                # 1. Direct query + hindi
                h_data = execute_api("/wefeed-tv-bff/search/suggest", f"keyword={urllib.parse.quote(lookup_kw + ' hindi')}&perPage=6")
                h_words = [it.get("word") for it in h_data.get("data", {}).get("items", []) if it.get("word") and "hindi" in it.get("word").lower()]
                
                # 2. If short prefix, also check top suggested word + hindi
                if not h_words and words:
                    top_title = words[0].split("[")[0].strip()
                    h_data2 = execute_api("/wefeed-tv-bff/search/suggest", f"keyword={urllib.parse.quote(top_title + ' hindi')}&perPage=4")
                    h_words = [it.get("word") for it in h_data2.get("data", {}).get("items", []) if it.get("word") and "hindi" in it.get("word").lower()]
                    
                inserted = 0
                for hw in h_words:
                    if hw not in words and inserted < 2:
                        words.insert(min(1 + inserted, len(words)), hw)
                        inserted += 1
            except Exception:
                pass

        if any(term in kw_lower for term in ["drag", "ball", "db", "goku", "anim"]):
            if "Dragon Ball" not in words:
                words.insert(0, "Dragon Ball")
            if "Dragon Ball English Dub" not in words:
                words.insert(1, "Dragon Ball English Dub")
                
        return jsonify({"code": 0, "suggestions": words[:8]})
    except Exception as e:
        return jsonify({"code": 500, "suggestions": []}), 500

@app.route("/api/catalog")
def api_catalog():
    page = request.args.get("page", "1")
    per_page = request.args.get("perPage", "18")
    genre = request.args.get("genre", "")
    channel_id = request.args.get("channelId", "")
    
    if channel_id:
        query_parts = [f"channelId={channel_id}", f"page={page}", f"perPage={per_page}"]
        if genre:
            query_parts.append(f"genre={urllib.parse.quote(genre)}")
        try:
            data = execute_api("/wefeed-tv-bff/filter/list", "&".join(query_parts))
            items = data.get("data", {}).get("items", [])
            if channel_id == "2" or (genre and "anim" in genre.lower()):
                if not any(it.get("subjectId") == "dragonball" for it in items):
                    items.insert(0, DRAGONBALL_CARD)
            return jsonify(data)
        except Exception as e:
            return jsonify({"code": 500, "message": str(e), "data": {"items": [DRAGONBALL_CARD]}}), 500
    else:
        # Fetch both movies and series for home feed
        try:
            movies_res = execute_api("/wefeed-tv-bff/filter/list", f"channelId=1&page={page}&perPage={per_page}")
            series_res = execute_api("/wefeed-tv-bff/filter/list", f"channelId=2&page={page}&perPage={per_page}")
            
            movies = movies_res.get("data", {}).get("items", [])
            series = series_res.get("data", {}).get("items", [])
            
            if not any(it.get("subjectId") == "dragonball" for it in series):
                series.insert(0, DRAGONBALL_CARD)
            combined = [DRAGONBALL_CARD] + [it for it in (movies + series) if it.get("subjectId") != "dragonball"]
            return jsonify({"code": 0, "data": {"items": combined, "movies": movies, "series": series}})
        except Exception as e:
            return jsonify({"code": 500, "message": str(e), "data": {"items": [DRAGONBALL_CARD], "movies": [], "series": [DRAGONBALL_CARD]}}), 500

@app.route("/api/subject/<subject_id>")
def api_subject(subject_id):
    if subject_id in DRAGONBALL_IDS:
        return jsonify({
            "code": 0,
            "data": {
                "subject": DRAGONBALL_CARD
            }
        })
    try:
        data = execute_api("/wefeed-tv-bff/subject/get", f"subjectId={subject_id}")
        return jsonify(data)
    except Exception as e:
        return jsonify({"code": 500, "message": str(e)}), 500

@app.route("/api/seasons/<subject_id>")
def api_seasons(subject_id):
    if subject_id in DRAGONBALL_IDS:
        return jsonify({
            "code": 0,
            "data": {
                "seasons": [
                    {
                        "se": 1,
                        "maxEp": 153,
                        "seasonName": "Season 1 (Classic)"
                    }
                ]
            }
        })
    try:
        data = execute_api("/wefeed-tv-bff/subject/season-info", f"subjectId={subject_id}")
        return jsonify(data)
    except Exception as e:
        return jsonify({"code": 500, "message": str(e)}), 500

@app.route("/api/subtitles/<subject_id>")
def api_subtitles(subject_id):
    if subject_id in DRAGONBALL_IDS:
        return jsonify({"code": 0, "captions": []})
    se = request.args.get("se", "")
    ep = request.args.get("ep", "")
    queries = []
    if se and ep:
        queries.append(f"page=1&perPage=5&subjectId={subject_id}&se={se}&epFrom={ep}&epTo={ep}")
    queries.append(f"page=1&perPage=5&subjectId={subject_id}")
    
    for query in queries:
        try:
            data = execute_api("/wefeed-tv-bff/subject/resource", query)
            items = data.get("data", {}).get("items", [])
            if items:
                captions = items[0].get("captions", [])
                if captions:
                    return jsonify({"code": 0, "captions": captions})
        except Exception:
            continue
            
    return jsonify({"code": 0, "captions": []})

@app.route("/api/vtt/<subject_id>/<lang>.vtt")
def api_vtt(subject_id, lang):
    se = request.args.get("se", "")
    ep = request.args.get("ep", "")
    queries = []
    if se and ep:
        queries.append(f"page=1&perPage=5&subjectId={subject_id}&se={se}&epFrom={ep}&epTo={ep}")
    queries.append(f"page=1&perPage=5&subjectId={subject_id}")
    
    captions = []
    for query in queries:
        try:
            data = execute_api("/wefeed-tv-bff/subject/resource", query)
            items = data.get("data", {}).get("items", [])
            if items:
                caps = items[0].get("captions", [])
                if caps:
                    captions = caps
                    break
        except Exception:
            continue
            
    try:
        target = next((c for c in captions if c.get("language") == lang), None)
        if not target and captions:
            target = captions[0]
            
        if not target:
            return "WEBVTT\n\n", 404
            
        url = target.get("url")
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, context=ctx, timeout=8) as r:
            srt_content = r.read().decode("utf-8", errors="ignore")
            vtt_content = srt_to_vtt(srt_content)
            return Response(vtt_content, mimetype="text/vtt")
    except Exception as e:
        return f"WEBVTT\n\nNOTE error: {e}\n", 500

_stream_cache = {}

def get_cached_play_info(subject_id, se="", ep=""):
    cache_key = f"{subject_id}_{se}_{ep}"
    now = time.time()
    if cache_key in _stream_cache:
        cached_time, cached_data = _stream_cache[cache_key]
        if now - cached_time < 3600:  # Cache for 1 hour
            return cached_data

    query = f"subjectId={subject_id}"
    if se and ep:
        query += f"&se={se}&ep={ep}"

    data = execute_api("/wefeed-tv-bff/subject/play-info/v2", query)
    streams = data.get("data", {}).get("streams", [])
    if not streams and not se and not ep:
        fallback_data = execute_api("/wefeed-tv-bff/subject/play-info/v2", f"subjectId={subject_id}&se=1&ep=1")
        if fallback_data.get("data", {}).get("streams"):
            data = fallback_data
            streams = data.get("data", {}).get("streams", [])

    if streams:
        _stream_cache[cache_key] = (now, data)
    return data

@app.route("/api/play-info/<subject_id>")
def api_play_info(subject_id):
    se = request.args.get("se", "")
    ep = request.args.get("ep", "")
    if subject_id in DRAGONBALL_IDS:
        is_dub = not (subject_id == "dragonball_sub")
        ep_val = 1
        try:
            ep_val = int(ep) if ep else 1
        except Exception:
            ep_val = 1
        st_info = resolve_dragonball_stream(ep_val, is_dub)
        return jsonify({
            "code": 0,
            "url": st_info["url"],
            "cookie": "",
            "duration": 1450,
            "resolutions": "1080p,720p,480p",
            "codec": "h264"
        })
    try:
        data = get_cached_play_info(subject_id, se, ep)
        streams = data.get("data", {}).get("streams", [])
        if not streams:
            return jsonify({"code": 404, "message": "No streams found"}), 404
        stream = streams[0]
        return jsonify({
            "code": 0,
            "url": stream.get("url"),
            "cookie": stream.get("signCookie"),
            "duration": stream.get("duration"),
            "resolutions": stream.get("resolutions"),
            "codec": stream.get("codecName")
        })
    except Exception as e:
        return jsonify({"code": 500, "message": str(e)}), 500

@app.route("/api/dubs/<subject_id>")
def api_dubs(subject_id):
    if subject_id in DRAGONBALL_IDS:
        return jsonify({
            "code": 0,
            "dubs": [
                {
                    "subjectId": "dragonball",
                    "lanName": "English Dub",
                    "lanCode": "en",
                    "original": True,
                    "type": 0
                },
                {
                    "subjectId": "dragonball_sub",
                    "lanName": "Japanese (English Sub)",
                    "lanCode": "ja",
                    "original": False,
                    "type": 0
                }
            ]
        })
    try:
        data = execute_api("/wefeed-tv-bff/subject/dub-info", f"subjectId={subject_id}")
        items = data.get("data", {}).get("items", [])
        
        # Check if Hindi dub is already in the list
        has_hindi = any(
            d.get("lanCode") == "hi" or "hindi" in (d.get("lanName") or "").lower()
            for d in items
        )
        
        if not has_hindi:
            try:
                sub_res = execute_api("/wefeed-tv-bff/subject/get", f"subjectId={subject_id}")
                sub_info = sub_res.get("data", {}).get("subject") or sub_res.get("data") or {}
                raw_title = sub_info.get("title") or sub_info.get("subjectName") or ""
                clean_title = raw_title.split("[")[0].strip()
                
                search_queries = []
                if clean_title:
                    search_queries.append(f"{clean_title} hindi")
                    if ":" in clean_title:
                        search_queries.append(f"{clean_title.split(':')[0].strip()} hindi")
                    if "-" in clean_title:
                        search_queries.append(f"{clean_title.split('-')[0].strip()} hindi")
                        
                matched = False
                for sq in search_queries:
                    search_data = execute_api("/wefeed-tv-bff/search/result", f"keyword={urllib.parse.quote(sq)}&page=1&perPage=5&subjectType=0")
                    found_items = search_data.get("data", {}).get("items", [])
                    for fit in found_items:
                        ftitle = fit.get("title", "")
                        fcorner = fit.get("corner", "")
                        if ("hindi" in ftitle.lower() or str(fcorner).lower() == "hindi") and str(fit.get("subjectId")) != str(subject_id):
                            h_sub_id = fit.get("subjectId")
                            h_dub_res = execute_api("/wefeed-tv-bff/subject/dub-info", f"subjectId={h_sub_id}")
                            h_items = h_dub_res.get("data", {}).get("items", [])
                            if any(d.get("lanCode") == "hi" or "hindi" in (d.get("lanName") or "").lower() for d in h_items):
                                items = h_items
                                matched = True
                                break
                            else:
                                items.append({
                                    "subjectId": str(h_sub_id),
                                    "lanName": "Hindi dub",
                                    "lanCode": "hi",
                                    "original": False,
                                    "type": 0
                                })
                                matched = True
                                break
                    if matched:
                        break
            except Exception:
                pass
                
        return jsonify({"code": 0, "dubs": items})
    except Exception as e:
        return jsonify({"code": 500, "message": str(e), "dubs": []}), 500

import threading

_active_stream_processes = {}
_stream_proc_lock = threading.Lock()

def terminate_previous_stream(subject_id):
    """Terminates any existing ffmpeg remuxing process for this subject to free bandwidth and CPU immediately."""
    with _stream_proc_lock:
        old_proc = _active_stream_processes.pop(subject_id, None)
        if old_proc:
            try:
                old_proc.kill()
                old_proc.wait(timeout=0.1)
            except Exception:
                pass

@app.route("/api/stream/<subject_id>/video.mp4")
def api_stream_mp4(subject_id):
    """
    Universal HTML5 Video Streamer:
    Remuxes CloudFront DASH stream into fragmented MP4 using optimized ffmpeg pipeline.
    Eliminates zombie processes, accelerates initial segment delivery, and enables smooth seeking.
    """
    se = request.args.get("se", "")
    ep = request.args.get("ep", "")
    start_time = request.args.get("ss", request.args.get("start", "0"))
    requested_res = request.args.get("res", "")
    adelay = request.args.get("adelay", "0")
    
    # Kill any previous ffmpeg process for this subject before starting a new seek
    terminate_previous_stream(subject_id)
    
    try:
        if subject_id in DRAGONBALL_IDS:
            is_dub = not (subject_id == "dragonball_sub")
            ep_val = 1
            try:
                ep_val = int(ep) if ep else 1
            except Exception:
                ep_val = 1
            st_info = resolve_dragonball_stream(ep_val, is_dub)
            url = st_info["url"]
            origin = st_info.get("origin", "https://ultracloud.cc")
            referer = st_info.get("referer", "https://ultracloud.cc/")
            res_list = ["1080p", "720p", "480p"]
            headers_flag = f"Origin: {origin}\r\nReferer: {referer}\r\nUser-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36\r\n"
        else:
            data = get_cached_play_info(subject_id, se, ep)
            streams = data.get("data", {}).get("streams", [])
            if not streams:
                return "Stream not found", 404
                
            stream = streams[0]
            url = stream.get("url")
            cookie = stream.get("signCookie")
            
            # Determine available resolutions
            res_list = [r.strip() for r in str(stream.get("resolutions", "")).split(",") if r.strip()]
            headers_flag = f"Cookie: {cookie}\r\nUser-Agent: okhttp/4.12.0\r\n"
        
        cmd = [
            "ffmpeg",
            "-headers", headers_flag,
            "-multiple_requests", "1",
            "-fflags", "+nobuffer+flush_packets+fastseek+discardcorrupt",
            "-analyzeduration", "100000",
            "-probesize", "100000",
            "-fpsprobesize", "0",
        ]
        
        seek_sec = 0.0
        try:
            val = float(start_time)
            if val > 0:
                seek_sec = val
                cmd += ["-ss", str(val)]
        except Exception:
            pass
            
        cmd += ["-i", url]

        # Post-input seek to discard pre-roll priming packets and align audio to 0.00
        if seek_sec > 0:
            cmd += ["-ss", "0"]
        
        # Map specific resolution if requested and available for DASH
        if subject_id not in DRAGONBALL_IDS:
            if requested_res and requested_res in res_list:
                v_idx = res_list.index(requested_res)
                cmd += ["-map", f"0:v:{v_idx}", "-map", "0:a:0?"]
            elif res_list:
                cmd += ["-map", "0:v:0", "-map", "0:a:0?"]
            
        # Base audio sync filter: aresample with async=1 dynamically locks audio PTS to video timeline,
        # preventing packet jitter and timeline gaps across DASH segments.
        af_filters = ["aresample=async=1"]

        # Handle fine-grained audio sync delay (in milliseconds)
        try:
            del_ms = int(adelay)
            if del_ms > 0:
                af_filters.append(f"adelay={del_ms}|{del_ms}")
            elif del_ms < 0:
                adv_s = abs(del_ms) / 1000.0
                af_filters.append(f"atrim=start={adv_s},asetpts=PTS-STARTPTS")
        except Exception:
            pass

        cmd += [
            "-c:v", "copy",
            "-af", ",".join(af_filters),
            "-c:a", "aac",
            "-b:a", "128k"
        ]

        cmd += [
            "-movflags", "frag_keyframe+empty_moov+default_base_moof",
            "-flush_packets", "1",
            "-f", "mp4",
            "pipe:1"
        ]
        
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=64*1024)
        
        with _stream_proc_lock:
            _active_stream_processes[subject_id] = proc
        
        def generate():
            try:
                # Deliver initial MP4 header immediately to unblock browser media engine
                first = proc.stdout.read1(64 * 1024) if hasattr(proc.stdout, "read1") else proc.stdout.read(4096)
                if first:
                    yield first
                while True:
                    chunk = proc.stdout.read(64 * 1024)
                    if not chunk:
                        break
                    yield chunk
            finally:
                with _stream_proc_lock:
                    if _active_stream_processes.get(subject_id) == proc:
                        _active_stream_processes.pop(subject_id, None)
                try:
                    proc.kill()
                    proc.wait(timeout=0.1)
                except Exception:
                    pass
                
        resp = Response(generate(), mimetype="video/mp4")
        resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        resp.headers["X-Content-Type-Options"] = "nosniff"
        resp.headers["Accept-Ranges"] = "none"
        return resp
    except Exception as e:
        return str(e), 500

if __name__ == "__main__":
    os.makedirs("static", exist_ok=True)
    port = int(os.environ.get("PORT", 5000))
    print("=" * 60)
    print("CineFlow Web Streaming Server")
    print(f"Serving at: http://localhost:{port}")
    print("=" * 60)
    app.run(host="0.0.0.0", port=port, debug=False)
