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

@app.before_request
def handle_options():
    if request.method == "OPTIONS":
        res = Response(status=200)
        res.headers["Access-Control-Allow-Origin"] = "*"
        res.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        res.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, Range"
        res.headers["Access-Control-Expose-Headers"] = "Content-Length, Content-Range"
        return res

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
    last_err = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, context=ctx, timeout=12) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            last_err = e
            time.sleep(0.2)
    raise last_err

def srt_to_vtt(srt_text):
    if not srt_text:
        return "WEBVTT\n\n"
    clean = srt_text.lstrip("\ufeff").replace("\r\n", "\n").replace("\r", "\n")
    if clean.strip().startswith("WEBVTT"):
        return clean
    lines = clean.split("\n")
    vtt = ["WEBVTT\n"]
    for line in lines:
        if "-->" in line:
            line = line.replace(",", ".")
        vtt.append(line)
    return "\n".join(vtt)

# ==============================================================================
# ==============================================================================
# ANILILI / MIRURO ANIME STREAMING & METADATA ENGINE INTEGRATION
# ==============================================================================
import anime_engine
anime_engine.set_api_executor(execute_api)

DRAGONBALL_IDS = {"dragonball", "223", "dragonball_dub", "dragonball_sub", "rqxAbYshiv3CtbJ4cetuZ-yKIe2Cyjqr"}

DRAGONBALL_CARD = {
    "subjectId": "dragonball",
    "rawId": 223,
    "id": 223,
    "title": "Dragon Ball",
    "subjectName": "Dragon Ball",
    "subjectType": 2,
    "year": "1986",
    "duration": 1450,
    "score": 8.8,
    "cover": {"url": "https://image.tmdb.org/t/p/w500/2RSrQ82HNbBBVM3omiHObQ0EvqI.jpg"},
    "thumbnail": "https://image.tmdb.org/t/p/w500/2RSrQ82HNbBBVM3omiHObQ0EvqI.jpg",
    "description": "Bulma is a girl in search of the legendary Dragon Balls that say when all seven are gathered, one's wish will come true. She meets Goku, an extraordinary boy living in Mount Paozu who possesses the four-star Dragon Ball.",
    "isAnime": True
}

def is_anime_subject(subject_id: str) -> bool:
    s = str(subject_id).lower()
    if s.startswith("anime_") or s in DRAGONBALL_IDS or "dragonball" in s:
        return True
    if s.isdigit():
        num_id = int(s)
        if str(num_id) in DRAGONBALL_IDS or num_id == 223 or num_id in anime_engine._local_id_map:
            return True
    return False

def parse_anime_id(subject_id: str) -> int:
    s = str(subject_id).lower()
    if s in DRAGONBALL_IDS or "dragonball" in s:
        return 223
    cleaned = s.replace("anime_", "").replace("_dub", "").replace("_sub", "")
    try:
        return int(cleaned)
    except Exception:
        return 223

@app.route("/api/anime/catalog")
def api_anime_catalog():
    try:
        catalog = anime_engine.get_anime_catalog()
        return jsonify({"code": 0, "data": catalog})
    except Exception as e:
        return jsonify({"code": 500, "message": str(e)}), 500

@app.route("/api/anime/search")
def api_anime_search():
    keyword = request.args.get("keyword", request.args.get("q", "")).strip()
    genre = request.args.get("genre", "").strip()
    try:
        page = int(request.args.get("page", "1"))
    except Exception:
        page = 1
    try:
        per_page = int(request.args.get("perPage", "18"))
    except Exception:
        per_page = 18
        
    try:
        items = anime_engine.search_anime(keyword=keyword, genre=genre, page=page, per_page=per_page)
        return jsonify({"code": 0, "data": {"items": items, "results": items}})
    except Exception as e:
        return jsonify({"code": 500, "message": str(e), "data": {"items": [], "results": []}}), 500

@app.route("/api/anime/details/<path:subject_id>")
def api_anime_details(subject_id):
    try:
        aid = parse_anime_id(subject_id)
        details = anime_engine.get_anime_details(aid)
        return jsonify({"code": 0, "data": {"subject": details}})
    except Exception as e:
        return jsonify({"code": 500, "message": str(e)}), 500

@app.route("/api/anime/episodes/<path:subject_id>")
def api_anime_episodes(subject_id):
    try:
        aid = parse_anime_id(subject_id)
        eps = anime_engine.get_anime_episodes(aid)
        return jsonify({"code": 0, "data": {"episodes": eps, "total": len(eps)}})
    except Exception as e:
        return jsonify({"code": 500, "message": str(e), "data": {"episodes": []}}), 500

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
                
        # Enrich search with anime results from Anilili/Miruro catalog
        try:
            anime_matches = anime_engine.search_anime(keyword=keyword, per_page=6)
            for am in anime_matches:
                if not any(it.get("subjectId") == am.get("subjectId") for it in items):
                    items.append(am)
        except Exception as e:
            print(f"[AnimeEngine] Search enrichment error: {e}")

        return jsonify({
            "code": 0,
            "data": {
                "items": items,
                "relatedKeywords": related_words[:6],
                "recommendations": recommendations[:12]
            }
        })
    except Exception as e:
        anime_items = []
        try:
            anime_items = anime_engine.search_anime(keyword=keyword, per_page=6)
        except Exception:
            pass
        return jsonify({"code": 500, "message": str(e), "data": {"items": anime_items, "relatedKeywords": [], "recommendations": []}}), 500

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

        # Suggest matching anime titles from local index
        if anime_engine._local_index and len(keyword) >= 2:
            for it in anime_engine._local_index:
                t = it.get("title", "")
                if kw_lower in t.lower() and t not in words:
                    words.insert(0 if kw_lower in ["anim", "drag", "atta", "solo", "juju", "one", "nar"] else len(words), t)
                    if len(words) >= 10:
                        break
                
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
    if is_anime_subject(subject_id):
        aid = parse_anime_id(subject_id)
        details = anime_engine.get_anime_details(aid)
        return jsonify({
            "code": 0,
            "data": {
                "subject": details
            }
        })
    try:
        data = execute_api("/wefeed-tv-bff/subject/get", f"subjectId={subject_id}")
        return jsonify(data)
    except Exception as e:
        return jsonify({"code": 500, "message": str(e)}), 500

@app.route("/api/seasons/<subject_id>")
def api_seasons(subject_id):
    if is_anime_subject(subject_id):
        aid = parse_anime_id(subject_id)
        eps = anime_engine.get_anime_episodes(aid)
        return jsonify({
            "code": 0,
            "data": {
                "seasons": [
                    {
                        "se": 1,
                        "maxEp": len(eps),
                        "seasonName": "Season 1"
                    }
                ]
            }
        })
    try:
        data = execute_api("/wefeed-tv-bff/subject/season-info", f"subjectId={subject_id}")
        return jsonify(data)
    except Exception as e:
        return jsonify({"code": 500, "message": str(e)}), 500

_anime_sub_cache = {}
_vtt_file_cache = {}

KNOWN_ANIME_SIDS = {
    16498: ["7777395346602609920", "498748951932323152", "6223339262331832232", "1975770531236301600", "8411756968024720848"],  # Attack on Titan
    101922: ["8598130933641921616", "219436714593502288", "4260168667809336920", "5829592540739160760", "2463166384050702464", "3619725132714887968"],  # Demon Slayer
    223: ["490443602410232328", "5971941144341667848", "5616484647824673120"],  # Dragon Ball
    113415: ["1426983370449472560", "1992020214120170824"],  # Jujutsu Kaisen
    20: ["1975770531236301602", "56988683026712168"]  # Naruto
}

def get_anime_subtitles(aid, se="1", ep="1"):
    cache_key = f"{aid}_{se}_{ep}"
    if cache_key in _anime_sub_cache and _anime_sub_cache[cache_key]:
        return _anime_sub_cache[cache_key]

    candidate_sids = []
    if aid in KNOWN_ANIME_SIDS:
        candidate_sids.extend(KNOWN_ANIME_SIDS[aid])

    details = anime_engine.get_anime_details(aid)
    title = details.get("title", "")
    match = anime_engine.find_aoneroom_anime(title)
    if match and match.get("subjectId"):
        base_sid = str(match.get("subjectId"))
        if base_sid not in candidate_sids:
            candidate_sids.append(base_sid)

        # 1. Collect related SIDs from dub-info
        try:
            dub_data = execute_api("/wefeed-tv-bff/subject/dub-info", f"subjectId={base_sid}")
            for it in dub_data.get("data", {}).get("items", []):
                sid_str = str(it.get("subjectId"))
                if sid_str and sid_str not in candidate_sids:
                    candidate_sids.append(sid_str)
        except Exception:
            pass

    # 2. Collect search results for anime title
    if title:
        try:
            clean_t = anime_engine.get_clean_titles(title)[0]
            s_data = execute_api("/wefeed-tv-bff/search/result", f"keyword={urllib.parse.quote(clean_t)}&page=1&perPage=6&subjectType=0")
            for it in s_data.get("data", {}).get("items", []):
                sid_str = str(it.get("subjectId"))
                if sid_str and sid_str not in candidate_sids:
                    candidate_sids.append(sid_str)
        except Exception:
            pass

    # 3. Query resource for each candidate SID to find subtitles
    for sid in candidate_sids:
        queries = []
        if se and ep:
            queries.append(f"page=1&perPage=5&subjectId={sid}&se={se}&epFrom={ep}&epTo={ep}")
        queries.append(f"page=1&perPage=5&subjectId={sid}")
        for q in queries:
            try:
                res = execute_api("/wefeed-tv-bff/subject/resource", q)
                items = res.get("data", {}).get("items", [])
                if items and items[0].get("captions"):
                    captions = items[0].get("captions")
                    _anime_sub_cache[cache_key] = captions
                    _subtitles_cache[cache_key] = captions
                    _subtitles_cache[f"anime_{aid}_{se}_{ep}"] = captions
                    return captions
            except Exception:
                continue

    return []

_subtitles_cache = {}

@app.route("/api/subtitles/<subject_id>")
def api_subtitles(subject_id):
    se = request.args.get("se", "1")
    ep = request.args.get("ep", "1")
    cache_key = f"{subject_id}_{se}_{ep}"
    if cache_key in _subtitles_cache and _subtitles_cache[cache_key]:
        return jsonify({"code": 0, "captions": _subtitles_cache[cache_key]})

    captions = []
    if is_anime_subject(subject_id):
        aid = parse_anime_id(subject_id)
        captions = get_anime_subtitles(aid, se=se, ep=ep)
    else:
        queries = []
        if se and ep:
            queries.append(f"page=1&perPage=5&subjectId={subject_id}&se={se}&epFrom={ep}&epTo={ep}")
        queries.append(f"page=1&perPage=5&subjectId={subject_id}")
        
        for query in queries:
            try:
                data = execute_api("/wefeed-tv-bff/subject/resource", query)
                items = data.get("data", {}).get("items", [])
                if items:
                    for it in items:
                        caps = it.get("captions", [])
                        if caps:
                            captions = caps
                            break
                if captions:
                    break
            except Exception:
                continue
                
        # If this is an anime dub SID or related SID without its own captions, look in related SIDs
        if not captions:
            try:
                dub_data = execute_api("/wefeed-tv-bff/subject/dub-info", f"subjectId={subject_id}")
                for it in dub_data.get("data", {}).get("items", []):
                    rel_sid = str(it.get("subjectId"))
                    if rel_sid != str(subject_id):
                        res = execute_api("/wefeed-tv-bff/subject/resource", f"page=1&perPage=5&subjectId={rel_sid}&se={se}&epFrom={ep}&epTo={ep}")
                        r_items = res.get("data", {}).get("items", [])
                        if r_items and r_items[0].get("captions"):
                            captions = r_items[0].get("captions")
                            break
            except Exception:
                pass

    if captions:
        _subtitles_cache[cache_key] = captions
    return jsonify({"code": 0, "captions": captions or []})

@app.route("/api/subtitle-file")
def api_subtitle_file():
    sub_url = request.args.get("url", "").strip()
    if not sub_url:
        return "WEBVTT\n\n", 400

    if sub_url in _vtt_file_cache:
        return Response(_vtt_file_cache[sub_url], mimetype="text/vtt", headers={"Access-Control-Allow-Origin": "*"})

    try:
        req = urllib.request.Request(sub_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) CineFlow/2.0"})
        with urllib.request.urlopen(req, context=ctx, timeout=12) as r:
            raw = r.read().decode("utf-8", errors="ignore")
            vtt = srt_to_vtt(raw)
            _vtt_file_cache[sub_url] = vtt
            return Response(vtt, mimetype="text/vtt", headers={"Access-Control-Allow-Origin": "*"})
    except Exception as e:
        return f"WEBVTT\n\nNOTE Subtitle fetch error: {e}\n", 500, {"Content-Type": "text/vtt", "Access-Control-Allow-Origin": "*"}

@app.route("/api/vtt/<subject_id>/<lang>.vtt")
def api_vtt(subject_id, lang):
    direct_url = request.args.get("url", "").strip()
    if direct_url:
        if direct_url in _vtt_file_cache:
            return Response(_vtt_file_cache[direct_url], mimetype="text/vtt", headers={"Access-Control-Allow-Origin": "*"})
        try:
            req = urllib.request.Request(direct_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) CineFlow/2.0"})
            with urllib.request.urlopen(req, context=ctx, timeout=12) as r:
                srt_content = r.read().decode("utf-8", errors="ignore")
                vtt_content = srt_to_vtt(srt_content)
                _vtt_file_cache[direct_url] = vtt_content
                return Response(vtt_content, mimetype="text/vtt", headers={"Access-Control-Allow-Origin": "*"})
        except Exception as e:
            return f"WEBVTT\n\nNOTE direct url error: {e}\n", 500, {"Content-Type": "text/vtt", "Access-Control-Allow-Origin": "*"}

    se = request.args.get("se", "1")
    ep = request.args.get("ep", "1")
    cache_key = f"{subject_id}_{se}_{ep}"
    
    captions = []
    if cache_key in _subtitles_cache and _subtitles_cache[cache_key]:
        captions = _subtitles_cache[cache_key]
    elif is_anime_subject(subject_id):
        aid = parse_anime_id(subject_id)
        anime_key = f"{aid}_{se}_{ep}"
        if anime_key in _anime_sub_cache and _anime_sub_cache[anime_key]:
            captions = _anime_sub_cache[anime_key]
        elif f"anime_{aid}_{se}_{ep}" in _subtitles_cache:
            captions = _subtitles_cache[f"anime_{aid}_{se}_{ep}"]
        else:
            captions = get_anime_subtitles(aid, se=se, ep=ep)
    else:
        queries = []
        if se and ep:
            queries.append(f"page=1&perPage=5&subjectId={subject_id}&se={se}&epFrom={ep}&epTo={ep}")
        queries.append(f"page=1&perPage=5&subjectId={subject_id}")
        
        for query in queries:
            try:
                data = execute_api("/wefeed-tv-bff/subject/resource", query)
                items = data.get("data", {}).get("items", [])
                if items:
                    for it in items:
                        caps = it.get("captions", [])
                        if caps:
                            captions = caps
                            break
                if captions:
                    break
            except Exception:
                continue
                
        if not captions:
            try:
                dub_data = execute_api("/wefeed-tv-bff/subject/dub-info", f"subjectId={subject_id}")
                for it in dub_data.get("data", {}).get("items", []):
                    rel_sid = str(it.get("subjectId"))
                    if rel_sid != str(subject_id):
                        res = execute_api("/wefeed-tv-bff/subject/resource", f"page=1&perPage=5&subjectId={rel_sid}&se={se}&epFrom={ep}&epTo={ep}")
                        r_items = res.get("data", {}).get("items", [])
                        if r_items and r_items[0].get("captions"):
                            captions = r_items[0].get("captions")
                            break
            except Exception:
                pass
            
    try:
        lang_lower = str(lang).lower()
        target = next((c for c in captions if (c.get("language") or "").lower() == lang_lower or (c.get("languageCode") or "").lower() == lang_lower), None)
        if not target and captions:
            target = next((c for c in captions if (c.get("language") or "").lower() == "en"), captions[0])
            
        if not target:
            return "WEBVTT\n\n", 404, {"Content-Type": "text/vtt", "Access-Control-Allow-Origin": "*"}
            
        url = target.get("url")
        if url in _vtt_file_cache:
            return Response(_vtt_file_cache[url], mimetype="text/vtt", headers={"Access-Control-Allow-Origin": "*"})

        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) CineFlow/2.0"})
        with urllib.request.urlopen(req, context=ctx, timeout=12) as r:
            srt_content = r.read().decode("utf-8", errors="ignore")
            vtt_content = srt_to_vtt(srt_content)
            _vtt_file_cache[url] = vtt_content
            return Response(vtt_content, mimetype="text/vtt", headers={"Access-Control-Allow-Origin": "*"})
    except Exception as e:
        return f"WEBVTT\n\nNOTE error: {e}\n", 500, {"Content-Type": "text/vtt", "Access-Control-Allow-Origin": "*"}

_stream_cache = {}

def get_cached_play_info(subject_id, se="", ep=""):
    cache_key = f"{subject_id}_{se}_{ep}"
    now = time.time()
    if cache_key in _stream_cache:
        cached_time, cached_data = _stream_cache[cache_key]
        if now - cached_time < 1800:  # Cache for 30 minutes to prevent expired CloudFront signed cookies
            return cached_data

    query = f"subjectId={subject_id}"
    if se and ep:
        query += f"&se={se}&ep={ep}"

    data = execute_api("/wefeed-tv-bff/subject/play-info/v2", query)
    streams = data.get("data", {}).get("streams", [])

    # Defensive recovery: if se/ep was passed (e.g. state leak from a TV series to a movie)
    # and no streams were found, retry query without se/ep
    if not streams and (se or ep):
        fallback_data = execute_api("/wefeed-tv-bff/subject/play-info/v2", f"subjectId={subject_id}")
        if fallback_data.get("data", {}).get("streams"):
            data = fallback_data
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
    if is_anime_subject(subject_id):
        is_dub = str(subject_id).endswith("_dub")
        ep_val = 1
        try:
            ep_val = int(ep) if ep else 1
        except Exception:
            ep_val = 1
        aid = parse_anime_id(subject_id)
        st_info = anime_engine.resolve_anime_stream(aid, ep=ep_val, is_dub=is_dub)
        if not st_info or not st_info.get("url"):
            return jsonify({"code": 404, "message": "No streams found for this anime"}), 404
        raw_res = str(st_info.get("resolutions", "1080p,720p,480p"))
        clean_res = ", ".join([r.strip() + ("p" if not r.strip().endswith("p") else "") for r in raw_res.split(",") if r.strip()])
        return jsonify({
            "code": 0,
            "url": st_info["url"],
            "cookie": st_info.get("cookie", ""),
            "duration": st_info.get("duration", 1450),
            "resolutions": clean_res or "1080p, 720p, 480p",
            "codec": st_info.get("codec", "h264")
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

def get_anime_dubs(aid):
    # Special case: Dragon Ball
    if str(aid) in DRAGONBALL_IDS or aid == 223:
        return [
            {"subjectId": "5971941144341667848", "lanName": "Japanese (Original Audio)", "lanCode": "ja", "original": True, "type": 0},
            {"subjectId": "5616484647824673120", "lanName": "English Dub", "lanCode": "en", "original": False, "type": 0},
            {"subjectId": "2590127567235599160", "lanName": "Hindi Dub", "lanCode": "hi", "original": False, "type": 0},
            {"subjectId": "5515082806428323704", "lanName": "Portuguese Dub", "lanCode": "pt", "original": False, "type": 0}
        ]

    details = anime_engine.get_anime_details(aid)
    title = details.get("title", "")
    match = anime_engine.find_aoneroom_anime(title)
    if not match:
        return [{
            "subjectId": f"anime_{aid}",
            "lanName": "Japanese (Original Audio)",
            "lanCode": "ja",
            "original": True,
            "type": 0
        }]

    base_sid = str(match.get("subjectId"))
    try:
        data = execute_api("/wefeed-tv-bff/subject/dub-info", f"subjectId={base_sid}")
        items = data.get("data", {}).get("items", [])
    except Exception:
        items = []

    dubs = []
    seen_sids = set()
    orig_item = None

    for it in items:
        # Exclude pure subtitle tracks (type == 1)
        if it.get("type") == 1 or "sub" in (it.get("lanName") or "").lower():
            continue
        sid_str = str(it.get("subjectId"))
        if not sid_str or sid_str in seen_sids:
            continue
        seen_sids.add(sid_str)

        is_orig = it.get("original") is True or it.get("lanCode") == "ja"
        code = (it.get("lanCode") or ("ja" if is_orig else "en")).lower()
        raw_name = it.get("lanName") or ""

        if is_orig or code == "ja":
            label = "Japanese (Original Audio)"
            orig_item = {
                "subjectId": sid_str,
                "lanName": label,
                "lanCode": "ja",
                "original": True,
                "type": 0
            }
        else:
            if code == "en" or "english" in raw_name.lower():
                label = "English Dub"
                code = "en"
            elif code == "hi" or "hindi" in raw_name.lower():
                label = "Hindi Dub"
                code = "hi"
            elif code in ["es", "esla"] or "esla" in raw_name.lower() or "spanish" in raw_name.lower():
                label = "Spanish Dub"
                code = "es"
            elif code in ["pt", "ptbr"] or "ptbr" in raw_name.lower() or "portuguese" in raw_name.lower():
                label = "Portuguese Dub"
                code = "pt"
            elif code == "de" or "german" in raw_name.lower():
                label = "German Dub"
            elif code == "fr" or "french" in raw_name.lower():
                label = "French Dub"
            elif code == "it" or "italian" in raw_name.lower():
                label = "Italian Dub"
            elif code == "ru" or "russian" in raw_name.lower():
                label = "Russian Dub"
            elif code == "ar" or "arabic" in raw_name.lower():
                label = "Arabic Dub"
            else:
                label = f"{raw_name.strip()} Dub" if "dub" not in raw_name.lower() else raw_name.strip()

            dubs.append({
                "subjectId": sid_str,
                "lanName": label,
                "lanCode": code,
                "original": False,
                "type": 0
            })

    if not orig_item:
        orig_item = {
            "subjectId": base_sid,
            "lanName": "Japanese (Original Audio)",
            "lanCode": "ja",
            "original": True,
            "type": 0
        }
    dubs.insert(0, orig_item)

    # Check if Hindi dub is missing from dub-info but exists via title search
    has_hindi = any(d.get("lanCode") == "hi" for d in dubs)
    if not has_hindi:
        try:
            clean_title = anime_engine.get_clean_titles(title)[0]
            s_res = execute_api("/wefeed-tv-bff/search/result", f"keyword={urllib.parse.quote(clean_title + ' hindi')}&page=1&perPage=5&subjectType=0")
            s_items = s_res.get("data", {}).get("items", [])
            for fit in s_items:
                ftitle = fit.get("title", "")
                fcorner = fit.get("corner", "")
                if ("hindi" in ftitle.lower() or str(fcorner).lower() == "hindi") and fit.get("hasResource"):
                    h_sid = str(fit.get("subjectId"))
                    if h_sid not in seen_sids:
                        dubs.append({
                            "subjectId": h_sid,
                            "lanName": "Hindi Dub",
                            "lanCode": "hi",
                            "original": False,
                            "type": 0
                        })
                        break
        except Exception:
            pass

    return dubs

@app.route("/api/dubs/<subject_id>")
def api_dubs(subject_id):
    if is_anime_subject(subject_id):
        aid = parse_anime_id(subject_id)
        dubs = get_anime_dubs(aid)
        return jsonify({
            "code": 0,
            "dubs": dubs
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
_client_stream_processes = {}
_stream_proc_lock = threading.Lock()
_ffmpeg_hls_flags = None

def get_ffmpeg_hls_flags():
    """Detects and returns all supported HLS demuxer flags across FFmpeg 6 and 7+."""
    global _ffmpeg_hls_flags
    if _ffmpeg_hls_flags is not None:
        return _ffmpeg_hls_flags
    flags = ["-allowed_extensions", "ALL"]
    for opt in [["-allowed_segment_extensions", "ALL"], ["-extension_picky", "0"]]:
        try:
            res = subprocess.run(["ffmpeg"] + opt + ["-h"], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=2)
            if res.returncode == 0 or b"Unrecognized" not in res.stderr:
                flags.extend(opt)
        except Exception:
            pass
    _ffmpeg_hls_flags = flags
    return flags

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

def terminate_client_stream(client_id):
    """Terminates any existing ffmpeg remuxing process associated with this client/session."""
    if not client_id:
        return
    with _stream_proc_lock:
        old_proc = _client_stream_processes.pop(client_id, None)
        if old_proc:
            try:
                old_proc.kill()
                old_proc.wait(timeout=0.1)
            except Exception:
                pass

@app.route("/api/stream/stop", methods=["GET", "POST"])
def api_stream_stop():
    """Immediately stops and terminates any running ffmpeg stream process for a given client or subject."""
    client_id = request.args.get("client_id") or request.form.get("client_id")
    subject_id = request.args.get("subject_id") or request.form.get("subject_id")
    terminated = 0
    with _stream_proc_lock:
        if client_id and client_id in _client_stream_processes:
            p = _client_stream_processes.pop(client_id, None)
            if p:
                try:
                    p.kill()
                    p.wait(timeout=0.1)
                    terminated += 1
                except Exception:
                    pass
        if subject_id and subject_id in _active_stream_processes:
            p = _active_stream_processes.pop(subject_id, None)
            if p:
                try:
                    p.kill()
                    p.wait(timeout=0.1)
                    terminated += 1
                except Exception:
                    pass
    return jsonify({"status": "ok", "terminated": terminated})

@app.route("/api/stream/<subject_id>/video.mp4")
def api_stream_mp4(subject_id):
    """
    Universal HTML5 Video Streamer:
    Remuxes CloudFront DASH stream into fragmented MP4 using optimized ffmpeg pipeline.
    Eliminates zombie processes, accelerates initial segment delivery, and enables smooth seeking.
    """
    client_id = request.args.get("client_id", "")
    se = request.args.get("se", "")
    ep = request.args.get("ep", "")
    start_time = request.args.get("ss", request.args.get("start", "0"))
    requested_res = request.args.get("res", "")
    adelay = request.args.get("adelay", "0")
    
    # Kill any previous ffmpeg process for this client and subject before starting a new stream
    if client_id:
        terminate_client_stream(client_id)
    terminate_previous_stream(subject_id)
    
    try:
        if is_anime_subject(subject_id):
            is_dub = str(subject_id).endswith("_dub")
            ep_val = 1
            try:
                ep_val = int(ep) if ep else 1
            except Exception:
                ep_val = 1
            aid = parse_anime_id(subject_id)
            st_info = anime_engine.resolve_anime_stream(aid, ep=ep_val, is_dub=is_dub)
            if not st_info or not st_info.get("url"):
                return "Stream not found", 404
            url = st_info["url"]
            is_dash = ".mpd" in url
            cookie = st_info.get("cookie", "")
            if is_dash:
                headers_flag = f"Cookie: {cookie}\r\nUser-Agent: okhttp/4.12.0\r\n"
            else:
                origin = st_info.get("origin", "https://ultracloud.cc")
                referer = st_info.get("referer", "https://ultracloud.cc/")
                headers_flag = f"Origin: {origin}\r\nReferer: {referer}\r\nUser-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36\r\n"
            res_list = [r.strip() for r in str(st_info.get("resolutions", "1080p,720p,480p")).split(",") if r.strip()]
        else:
            data = get_cached_play_info(subject_id, se, ep)
            streams = data.get("data", {}).get("streams", [])
            if not streams:
                return "Stream not found", 404
                
            stream = streams[0]
            url = stream.get("url")
            cookie = stream.get("signCookie")
            is_dash = ".mpd" in url
            
            # Determine available resolutions
            res_list = [r.strip() for r in str(stream.get("resolutions", "")).split(",") if r.strip()]
            headers_flag = f"Cookie: {cookie}\r\nUser-Agent: okhttp/4.12.0\r\n"
        
        # For anime HLS streams, allocate sufficient analyzeduration & probesize so audio stream is detected with full codec parameters
        probe_val = "1500000" if (is_anime_subject(subject_id) and not is_dash) else "100000"
        cmd = [
            "ffmpeg",
            "-headers", headers_flag,
        ]
        if is_anime_subject(subject_id) and not is_dash:
            cmd += get_ffmpeg_hls_flags()
        elif is_dash:
            # DASH segment streaming flags: allow upstream segment keepalive and auto-reconnect
            cmd += [
                "-reconnect", "1",
                "-reconnect_streamed", "1",
                "-reconnect_delay_max", "4"
            ]
        cmd += [
            "-multiple_requests", "1",
            "-fflags", "+flush_packets+fastseek+discardcorrupt",
            "-analyzeduration", probe_val,
            "-probesize", probe_val,
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
        
        if is_anime_subject(subject_id) and not is_dash:
            # Explicitly map video 0 and audio 0 with bitstream filter for pristine, audible sound (HLS only)
            cmd += [
                "-map", "0:v:0",
                "-map", "0:a:0?",
                "-c:v", "copy",
                "-c:a", "copy",
                "-bsf:a", "aac_adtstoasc"
            ]
        else:
            # Map specific resolution if requested and available for DASH
            res_clean = [r.lower().rstrip("p") for r in res_list]
            req_clean = requested_res.lower().rstrip("p") if requested_res else ""
            if req_clean and req_clean in res_clean:
                v_idx = res_clean.index(req_clean)
                cmd += ["-map", f"0:v:{v_idx}", "-map", "0:a:0?"]
            elif res_list:
                cmd += ["-map", "0:v:0", "-map", "0:a:0?"]
            
            # Check fine-grained audio sync delay (in milliseconds)
            del_ms = 0
            try:
                del_ms = int(adelay)
            except Exception:
                del_ms = 0

            if del_ms != 0:
                af_filters = ["aresample=async=1"]
                if del_ms > 0:
                    af_filters.append(f"adelay={del_ms}|{del_ms}")
                elif del_ms < 0:
                    adv_s = abs(del_ms) / 1000.0
                    af_filters.append(f"atrim=start={adv_s},asetpts=PTS-STARTPTS")
                cmd += [
                    "-c:v", "copy",
                    "-af", ",".join(af_filters),
                    "-c:a", "aac",
                    "-b:a", "128k"
                ]
            else:
                # Direct stream copy: eliminates CPU bottlenecks, accelerates pipeline >3x real-time
                cmd += [
                    "-c:v", "copy",
                    "-c:a", "copy"
                ]

        cmd += [
            "-movflags", "frag_keyframe+empty_moov+default_base_moof",
            "-flush_packets", "1",
            "-f", "mp4",
            "pipe:1"
        ]
        
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=1024*1024)
        
        with _stream_proc_lock:
            _active_stream_processes[subject_id] = proc
            if client_id:
                _client_stream_processes[client_id] = proc
        
        def generate():
            try:
                # Deliver initial MP4 pre-roll burst immediately to prime HTML5 media buffer
                # This ensures the browser buffer never runs dry between initial DASH segment transitions
                burst = bytearray()
                burst_target = 768 * 1024  # ~6 seconds of 1080p video buffer
                while len(burst) < burst_target:
                    if proc.poll() is not None:
                        break
                    chunk = proc.stdout.read(128 * 1024)
                    if not chunk:
                        break
                    burst.extend(chunk)
                
                if burst:
                    yield bytes(burst)
                
                # Steady-state high-throughput stream pump
                while True:
                    if proc.poll() is not None:
                        break
                    chunk = proc.stdout.read(128 * 1024)
                    if not chunk:
                        break
                    yield chunk
            finally:
                with _stream_proc_lock:
                    if client_id and _client_stream_processes.get(client_id) == proc:
                        _client_stream_processes.pop(client_id, None)
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

@app.route("/api/debug/ffmpeg-test")
def api_debug_ffmpeg():
    aid = request.args.get("aid", "16498")
    try:
        st_info = anime_engine.resolve_anime_stream(int(aid), ep=1, is_dub=True)
        url = st_info["url"]
        origin = st_info.get("origin", "https://ultracloud.cc")
        referer = st_info.get("referer", "https://ultracloud.cc/")
        hdr = f"Origin: {origin}\r\nReferer: {referer}\r\nUser-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36\r\n"
        cmd = [
            "ffmpeg",
            "-headers", hdr,
        ] + get_ffmpeg_hls_flags() + [
            "-multiple_requests", "1",
            "-fflags", "+nobuffer+flush_packets+fastseek+discardcorrupt",
            "-analyzeduration", "1500000",
            "-probesize", "1500000",
            "-i", url,
            "-map", "0:v:0",
            "-map", "0:a:0?",
            "-c:v", "copy",
            "-c:a", "copy",
            "-bsf:a", "aac_adtstoasc",
            "-movflags", "frag_keyframe+empty_moov+default_base_moof",
            "-flush_packets", "1",
            "-t", "2",
            "-f", "mp4",
            "pipe:1"
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=12)
        return jsonify({
            "returncode": res.returncode,
            "stdout_len": len(res.stdout),
            "stderr": res.stderr.decode("utf-8", errors="ignore")
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
# ==============================================================================
# LIVE TV ENGINE INTEGRATION (TOP RATED CHANNELS & MULTI-SOURCE FAILOVER)
# ==============================================================================
import livetv_engine

@app.route("/api/livetv/channels")
def api_livetv_channels():
    category = request.args.get("category", "").strip().lower()
    channels = livetv_engine.get_channels_catalog()
    if category and category != "all":
        channels = [c for c in channels if c.get("category", "").lower() == category]
    return jsonify({
        "code": 200,
        "status": "success",
        "total": len(channels),
        "data": channels
    })

@app.route("/api/livetv/stream")
def api_livetv_stream():
    """
    Universal Live TV HLS & CORS Proxy.
    Resolves dynamic tokens (Sony Network), rewrites M3U8 master/child playlists
    to route all segments through HTTPS, and streams TS chunks with CORS: *.
    """
    key = request.args.get("key", "").strip()
    raw_url = request.args.get("url", "").strip()
    
    target_url = None
    if key:
        target_url = livetv_engine.resolve_stream_url(key)
    elif raw_url:
        target_url = urllib.parse.unquote(raw_url)
        
    if not target_url:
        return jsonify({"code": 400, "error": "Missing stream key or url"}), 400
        
    try:
        req = urllib.request.Request(target_url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Accept": "*/*",
            "Connection": "keep-alive"
        })
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
            content_type = resp.headers.get("Content-Type", "").lower()
            data = resp.read()
            
        # Check if response is an M3U8 playlist
        is_m3u8 = (
            target_url.endswith(".m3u8") or 
            "mpegurl" in content_type or 
            data.startswith(b"#EXTM3U")
        )
        
        if is_m3u8:
            text = data.decode("utf-8", errors="ignore")
            rewritten_lines = []
            for line in text.splitlines():
                sline = line.strip()
                if not sline:
                    rewritten_lines.append(line)
                elif sline.startswith("#"):
                    # Check for URI inside #EXT-X-KEY or #EXT-X-MEDIA
                    if 'URI="' in sline:
                        import re
                        def replace_uri(m):
                            original_uri = m.group(1)
                            abs_uri = urllib.parse.urljoin(target_url, original_uri)
                            return f'URI="/api/livetv/stream?url={urllib.parse.quote(abs_uri)}"'
                        sline = re.sub(r'URI="([^"]+)"', replace_uri, sline)
                    rewritten_lines.append(sline)
                else:
                    # Segment or child playlist URL
                    abs_url = urllib.parse.urljoin(target_url, sline)
                    rewritten_lines.append(f"/api/livetv/stream?url={urllib.parse.quote(abs_url)}")
                    
            res = Response("\n".join(rewritten_lines), mimetype="application/vnd.apple.mpegurl")
            res.headers["Access-Control-Allow-Origin"] = "*"
            res.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            return res
        else:
            # Binary media segment (.ts chunk or audio)
            mimetype = content_type or "video/MP2T"
            res = Response(data, mimetype=mimetype)
            res.headers["Access-Control-Allow-Origin"] = "*"
            res.headers["Cache-Control"] = "public, max-age=10"
            return res
            
    except Exception as e:
        return jsonify({"code": 502, "error": f"Failed fetching stream: {str(e)}", "target": target_url}), 502

# ============================================================================
# ANDROID TV IN-APP AUTO-UPDATE & DISTRIBUTION ENDPOINTS
# ============================================================================

TV_UPDATE_MANIFEST = {
    "latest_version_code": 1001,
    "latest_version_name": "1.0.0",
    "release_date": "2026-10-26",
    "apk_url": "/api/tv/download",
    "changelog": [
        "Native Android TV 10-foot user experience",
        "Reliable D-pad and remote-control navigation with focus feedback",
        "Hardware-accelerated Media3 ExoPlayer engine",
        "Integrated Live TV channels with auto-failover",
        "Anime universe with multi-track dubs and subtitles",
        "Seamless in-app over-the-air update delivery preserving user settings"
    ],
    "mandatory": False,
    "min_supported_version": 1000
}

@app.route("/api/tv/update")
def api_tv_update():
    """Return update metadata for Cineflow Android TV clients."""
    client_version = request.args.get("current_version", 0, type=int)
    response_data = dict(TV_UPDATE_MANIFEST)
    response_data["client_version"] = client_version
    response_data["has_update"] = response_data["latest_version_code"] > client_version
    return jsonify(response_data)

@app.route("/api/tv/download")
def api_tv_download():
    """Serve the latest signed release APK for Cineflow Android TV."""
    apk_candidates = [
        os.path.join(os.path.dirname(__file__), "android-tv", "app", "build", "outputs", "apk", "release", "app-release.apk"),
        os.path.join(os.path.dirname(__file__), "android-tv", "app", "build", "outputs", "apk", "debug", "app-debug.apk"),
        os.path.join(os.path.dirname(__file__), "static", "updates", "cineflow-tv-release.apk"),
        os.path.join(os.path.dirname(__file__), "cineflow-tv-release.apk")
    ]
    for apk_path in apk_candidates:
        if os.path.exists(apk_path):
            dir_name = os.path.dirname(apk_path)
            file_name = os.path.basename(apk_path)
            return send_from_directory(
                dir_name,
                file_name,
                mimetype="application/vnd.android.package-archive",
                as_attachment=True,
                download_name="cineflow-tv-release.apk"
            )
    return jsonify({"error": "Release APK not found. Please build the Android TV project first."}), 404

if __name__ == "__main__":
    os.makedirs("static", exist_ok=True)
    port = int(os.environ.get("PORT", 5000))
    print("=" * 60)
    print("CineFlow Web Streaming Server")
    print(f"Serving at: http://localhost:{port}")
    print("=" * 60)
    app.run(host="0.0.0.0", port=port, debug=False)

