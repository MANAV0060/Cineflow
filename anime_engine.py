import os
import sys
import json
import time
import gzip
import re
import urllib.request
import urllib.parse
from typing import Dict, List, Any, Optional

ANILIST_GQL = "https://graphql.anilist.co"
MIRURO_HOST = "https://www.miruro.bz"

# External API executor hook (connected from app.py)
_api_executor = None

def set_api_executor(func):
    global _api_executor
    _api_executor = func

# In-memory caches
_catalog_cache = None
_catalog_cache_time = 0
_anime_details_cache: Dict[int, Any] = {}
_anime_aoneroom_cache: Dict[str, Any] = {}
_miruro_id_cache: Dict[int, str] = {}
_episodes_cache: Dict[str, Any] = {}
_play_stream_cache: Dict[str, Any] = {}

# Pre-indexed local database stores
_local_index: List[Dict[str, Any]] = []
_local_id_map: Dict[str, Any] = {}
_dub_set: set = set()
_local_loaded = False

def load_local_data():
    global _local_index, _local_id_map, _dub_set, _local_loaded
    if _local_loaded:
        return

    data_dir = os.path.join(os.path.dirname(__file__), "data")
    idx_path = os.path.join(data_dir, "index.json")
    id_map_path = os.path.join(data_dir, "id-map.json")
    dub_path = os.path.join(data_dir, "dub-index.json")

    # Fallback to reverse_engineering directory if not in data
    if not os.path.exists(idx_path):
        idx_path = os.path.join(os.path.dirname(__file__), "reverse_engineering", "decompiled_anilili", "resources", "assets", "index.json")
    if not os.path.exists(id_map_path):
        id_map_path = os.path.join(os.path.dirname(__file__), "reverse_engineering", "decompiled_anilili", "resources", "assets", "id-map.json")
    if not os.path.exists(dub_path):
        dub_path = os.path.join(os.path.dirname(__file__), "reverse_engineering", "decompiled_anilili", "resources", "assets", "dub-index.json")

    try:
        if os.path.exists(idx_path):
            with open(idx_path, "r", encoding="utf-8") as f:
                _local_index = json.load(f)
        if os.path.exists(id_map_path):
            with open(id_map_path, "r", encoding="utf-8") as f:
                _local_id_map = json.load(f)
        if os.path.exists(dub_path):
            with open(dub_path, "r", encoding="utf-8") as f:
                _dub_set = set(json.load(f))
        _local_loaded = True
        print(f"[AnimeEngine] Loaded {_local_loaded} - Index: {len(_local_index)}, ID Map: {len(_local_id_map)}, Dubs: {len(_dub_set)}")
    except Exception as e:
        print(f"[AnimeEngine] Local data load warning: {e}")

load_local_data()

def query_anilist(query: str, variables: Optional[dict] = None) -> dict:
    payload = {"query": query}
    if variables:
        payload["variables"] = variables
    data = json.dumps(payload).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) CineFlow/2.0"
    }
    req = urllib.request.Request(ANILIST_GQL, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read().decode("utf-8"))

def decode_miruro_payload(data: bytes, content_type: str) -> str:
    if "application/octet-stream" in content_type:
        key = b"miruro/catalog"
        decrypted = bytes([b ^ key[i % len(key)] for i, b in enumerate(data)])
        return gzip.decompress(decrypted).decode("utf-8")
    return data.decode("utf-8", errors="ignore")

def miruro_headers() -> dict:
    return {
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36",
        "Referer": f"{MIRURO_HOST}/",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "cors",
        "Accept": "application/json, application/octet-stream;q=0.9, */*;q=0.8"
    }

def format_anime_card(item: dict) -> dict:
    """Standardizes AniList GraphQL media or local index card to CineFlow card model."""
    # AniList format
    if "title" in item and isinstance(item["title"], dict):
        title_dict = item.get("title", {})
        title = title_dict.get("english") or title_dict.get("userPreferred") or title_dict.get("romaji") or "Anime"
        cover = item.get("coverImage", {}).get("extraLarge") or item.get("coverImage", {}).get("large") or ""
        banner = item.get("bannerImage") or cover
        score_val = item.get("averageScore")
        score = f"{score_val / 10.0:.1f}" if score_val else "8.5"
        year = str(item.get("seasonYear") or (item.get("startDate", {}).get("year")) or "2024")
        aid = item.get("id")
        episodes = item.get("episodes") or 0
        genres = item.get("genres") or []
        format_type = item.get("format") or "TV"
        status = item.get("status") or "FINISHED"
    else:
        # Local index format
        title = item.get("title") or "Anime"
        cover = item.get("poster") or ""
        banner = cover
        score_val = item.get("score")
        score = f"{score_val / 10.0:.1f}" if score_val else "8.5"
        year = str(item.get("year") or "2024")
        aid = item.get("id")
        episodes = item.get("episodes") or 0
        genres = item.get("genres") or []
        format_type = item.get("format") or "TV"
        status = item.get("status") or "FINISHED"

    has_dub = aid in _dub_set if _dub_set else True

    return {
        "subjectId": f"anime_{aid}",
        "rawId": aid,
        "id": aid,
        "title": title,
        "subjectName": title,
        "subjectType": 2,  # TV Series / Episodic
        "year": year,
        "score": score,
        "cover": {"url": cover},
        "thumbnail": cover,
        "banner": banner,
        "genre": ", ".join(genres[:4]),
        "genres": genres,
        "corner": "DUB" if has_dub else "ANIME",
        "episodes": episodes,
        "format": format_type,
        "status": status,
        "isAnime": True
    }

def get_anime_catalog() -> dict:
    """Returns curated spotlight, trending, popular, top-rated, airing, and upcoming anime."""
    global _catalog_cache, _catalog_cache_time
    now = time.time()
    if _catalog_cache and (now - _catalog_cache_time < 1800):  # 30 min cache
        return _catalog_cache

    query = """
    query {
      spotlight: Page(page: 1, perPage: 1) {
        media(type: ANIME, sort: TRENDING_DESC, isAdult: false) {
          id
          title { english userPreferred romaji }
          description(asHtml: false)
          coverImage { extraLarge color }
          bannerImage
          averageScore
          format
          episodes
          seasonYear
          genres
        }
      }
      trending: Page(page: 1, perPage: 12) {
        media(type: ANIME, sort: TRENDING_DESC, isAdult: false) {
          id
          title { english userPreferred romaji }
          coverImage { extraLarge color }
          bannerImage
          averageScore
          format
          episodes
          seasonYear
          genres
        }
      }
      popular: Page(page: 1, perPage: 12) {
        media(type: ANIME, sort: POPULARITY_DESC, isAdult: false) {
          id
          title { english userPreferred romaji }
          coverImage { extraLarge color }
          bannerImage
          averageScore
          format
          episodes
          seasonYear
          genres
        }
      }
      topRated: Page(page: 1, perPage: 12) {
        media(type: ANIME, sort: SCORE_DESC, isAdult: false) {
          id
          title { english userPreferred romaji }
          coverImage { extraLarge color }
          bannerImage
          averageScore
          format
          episodes
          seasonYear
          genres
        }
      }
      airing: Page(page: 1, perPage: 12) {
        media(type: ANIME, status: RELEASING, sort: POPULARITY_DESC, isAdult: false) {
          id
          title { english userPreferred romaji }
          coverImage { extraLarge color }
          bannerImage
          averageScore
          format
          episodes
          seasonYear
          genres
        }
      }
      upcoming: Page(page: 1, perPage: 12) {
        media(type: ANIME, status: NOT_YET_RELEASED, sort: POPULARITY_DESC, isAdult: false) {
          id
          title { english userPreferred romaji }
          coverImage { extraLarge color }
          bannerImage
          averageScore
          format
          episodes
          seasonYear
          genres
        }
      }
    }
    """
    try:
        data = query_anilist(query)
        gql_data = data.get("data", {})
        
        spot_list = gql_data.get("spotlight", {}).get("media", [])
        spotlight = None
        if spot_list:
            s = spot_list[0]
            spotlight = format_anime_card(s)
            spotlight["synopsis"] = s.get("description") or "Trending anime sensation taking the world by storm."
            spotlight["banner"] = s.get("bannerImage") or s.get("coverImage", {}).get("extraLarge")
            
        trending = [format_anime_card(m) for m in gql_data.get("trending", {}).get("media", [])]
        popular = [format_anime_card(m) for m in gql_data.get("popular", {}).get("media", [])]
        top_rated = [format_anime_card(m) for m in gql_data.get("topRated", {}).get("media", [])]
        airing = [format_anime_card(m) for m in gql_data.get("airing", {}).get("media", [])]
        upcoming = [format_anime_card(m) for m in gql_data.get("upcoming", {}).get("media", [])]

        result = {
            "spotlight": spotlight,
            "trending": trending,
            "popular": popular,
            "topRated": top_rated,
            "airing": airing,
            "upcoming": upcoming
        }
        _catalog_cache = result
        _catalog_cache_time = now
        return result
    except Exception as e:
        print(f"[AnimeEngine] Anilili Catalog remote query failed, fallback to local: {e}")
        # Build from local _local_index
        sorted_popular = sorted(_local_index, key=lambda x: x.get("popularity", 0), reverse=True)[:18]
        sorted_top = sorted(_local_index, key=lambda x: x.get("score", 0), reverse=True)[:18]
        
        cards_pop = [format_anime_card(x) for x in sorted_popular]
        cards_top = [format_anime_card(x) for x in sorted_top]
        
        spotlight = cards_pop[0] if cards_pop else None
        if spotlight:
            spotlight["synopsis"] = "Immerse yourself in epic animation, breathtaking worlds, and iconic adventures."
            
        return {
            "spotlight": spotlight,
            "trending": cards_pop[:12],
            "popular": cards_pop[6:18],
            "topRated": cards_top[:12],
            "airing": cards_pop[:12],
            "upcoming": cards_top[6:18]
        }

def search_anime(keyword: str = "", genre: str = "", sort: str = "POPULARITY_DESC", page: int = 1, per_page: int = 18) -> List[dict]:
    """Universal search supporting both keyword title match and genre filtering."""
    if not keyword and not genre:
        catalog = get_anime_catalog()
        return catalog.get("trending", [])

    # If keyword is given, search fast in-memory local index first
    kw_lower = keyword.strip().lower()
    genre_lower = genre.strip().lower()

    if kw_lower and _local_index:
        local_matches = []
        for a in _local_index:
            title_match = kw_lower in a.get("title", "").lower() or kw_lower in a.get("slug", "").lower()
            genre_match = True
            if genre_lower:
                genre_match = any(genre_lower in g.lower() for g in a.get("genres", []))
            if title_match and genre_match:
                local_matches.append(format_anime_card(a))
                if len(local_matches) >= per_page:
                    break
        if len(local_matches) >= 8:
            return local_matches

    # AniList GraphQL Search Query
    query = """
    query ($search: String, $genre: String, $page: Int, $perPage: Int) {
      Page(page: $page, perPage: $perPage) {
        media(search: $search, genre: $genre, type: ANIME, isAdult: false, sort: POPULARITY_DESC) {
          id
          title { english userPreferred romaji }
          coverImage { extraLarge color }
          bannerImage
          averageScore
          format
          episodes
          seasonYear
          genres
        }
      }
    }
    """
    variables = {
        "page": page,
        "perPage": per_page
    }
    if keyword:
        variables["search"] = keyword
    if genre and genre.lower() != "all":
        variables["genre"] = genre

    try:
        data = query_anilist(query, variables)
        media_items = data.get("data", {}).get("Page", {}).get("media", [])
        return [format_anime_card(m) for m in media_items]
    except Exception as e:
        print(f"[AnimeEngine] Search remote query error: {e}")
        # Fallback local index search
        matches = []
        for a in _local_index:
            if kw_lower and kw_lower not in a.get("title", "").lower():
                continue
            if genre_lower and not any(genre_lower in g.lower() for g in a.get("genres", [])):
                continue
            matches.append(format_anime_card(a))
            if len(matches) >= per_page:
                break
        return matches

def get_anime_details(anilist_id: int) -> dict:
    """Retrieves full anime metadata, relations, recommendations, and banner artwork."""
    if anilist_id in _anime_details_cache:
        return _anime_details_cache[anilist_id]

    query = """
    query ($id: Int) {
      Media(id: $id, type: ANIME) {
        id
        idMal
        title { english romaji native userPreferred }
        description(asHtml: false)
        coverImage { extraLarge color }
        bannerImage
        format
        season
        seasonYear
        episodes
        duration
        status
        averageScore
        popularity
        countryOfOrigin
        genres
        studios(isMain: true) { nodes { id name isAnimationStudio } }
        trailer { id site thumbnail }
        startDate { year month day }
        recommendations(page: 1, perPage: 12, sort: RATING_DESC) {
          nodes {
            mediaRecommendation {
              id
              title { english romaji userPreferred }
              coverImage { extraLarge color }
              bannerImage
              format
              episodes
              averageScore
              genres
            }
          }
        }
        relations {
          edges {
            relationType
            node {
              id
              title { english romaji userPreferred }
              coverImage { extraLarge color }
              bannerImage
              format
              seasonYear
              episodes
              averageScore
              genres
            }
          }
        }
      }
    }
    """
    try:
        res = query_anilist(query, {"id": anilist_id})
        media = res.get("data", {}).get("Media")
        if media:
            title_dict = media.get("title", {})
            title = title_dict.get("english") or title_dict.get("userPreferred") or title_dict.get("romaji") or "Anime"
            cover = media.get("coverImage", {}).get("extraLarge") or ""
            banner = media.get("bannerImage") or cover
            score_val = media.get("averageScore")
            score = f"{score_val / 10.0:.1f}" if score_val else "8.5"
            duration = (media.get("duration") or 24) * 60
            genres = media.get("genres") or []
            studios = [s.get("name") for s in media.get("studios", {}).get("nodes", []) if s.get("name")]
            studio_str = ", ".join(studios) if studios else "Animation Studio"

            # Parse recommendations
            recs = []
            for n in media.get("recommendations", {}).get("nodes", []):
                rec_m = n.get("mediaRecommendation")
                if rec_m:
                    recs.append(format_anime_card(rec_m))

            # Parse relations
            relations = []
            for edge in media.get("relations", {}).get("edges", []):
                r_type = edge.get("relationType", "RELATED").replace("_", " ").title()
                r_node = edge.get("node")
                if r_node:
                    r_card = format_anime_card(r_node)
                    r_card["relationType"] = r_type
                    relations.append(r_card)

            ep_count = media.get("episodes") or 12

            details = {
                "subjectId": f"anime_{anilist_id}",
                "rawId": anilist_id,
                "id": anilist_id,
                "title": title,
                "subjectName": title,
                "subjectType": 2,
                "year": str(media.get("seasonYear") or "2024"),
                "score": score,
                "cover": {"url": cover},
                "thumbnail": cover,
                "banner": banner,
                "backdrop": banner,
                "description": media.get("description") or "Follow this legendary journey in cinematic animation.",
                "synopsis": media.get("description") or "Follow this legendary journey in cinematic animation.",
                "genres": genres,
                "genre": ", ".join(genres[:4]),
                "studio": studio_str,
                "duration": duration,
                "episodes": ep_count,
                "status": media.get("status") or "FINISHED",
                "format": media.get("format") or "TV",
                "recommendations": recs,
                "relations": relations,
                "isAnime": True
            }
            _anime_details_cache[anilist_id] = details
            return details
    except Exception as e:
        print(f"[AnimeEngine] Error fetching anime details for {anilist_id}: {e}")

    # Fallback to local index
    found = next((x for x in _local_index if x.get("id") == anilist_id), None)
    if found:
        card = format_anime_card(found)
        card["description"] = "A premier anime production featuring remarkable characters and thrilling animation."
        card["synopsis"] = card["description"]
        card["duration"] = 1440
        card["recommendations"] = []
        card["relations"] = []
        return card

    return {
        "subjectId": f"anime_{anilist_id}",
        "rawId": anilist_id,
        "title": "Anime Series",
        "subjectType": 2,
        "year": "2024",
        "score": "8.5",
        "cover": {"url": "https://image.tmdb.org/t/p/w500/2RSrQ82HNbBBVM3omiHObQ0EvqI.jpg"},
        "thumbnail": "https://image.tmdb.org/t/p/w500/2RSrQ82HNbBBVM3omiHObQ0EvqI.jpg",
        "description": "Streaming in high definition on CineFlow.",
        "genres": ["Anime", "Action"],
        "episodes": 12,
        "duration": 1440,
        "recommendations": [],
        "relations": []
    }

def get_clean_titles(title: str) -> List[str]:
    candidates = []
    cleaned = title.strip()
    candidates.append(cleaned)
    
    # 1. Season/part removal: "Attack on Titan Season 3 Part 2" -> "Attack on Titan"
    season_clean = re.sub(r'(?i)\s+(season|part|arc|cour|the final season|\d+(st|nd|rd|th)\s+season).*', '', cleaned).strip()
    if len(season_clean) >= 3 and season_clean not in candidates:
        candidates.append(season_clean)

    # 2. Parentheses removal: "Hunter x Hunter (2011)" -> "Hunter x Hunter"
    paren_clean = re.sub(r'[\(\[\{].*?[\)\]\}]', '', cleaned).strip()
    if len(paren_clean) >= 3 and paren_clean not in candidates:
        candidates.append(paren_clean)

    # 3. Colon subtitle removal: "BLEACH: Thousand-Year Blood War" -> "BLEACH"
    if ":" in cleaned:
        prefix = cleaned.split(":")[0].strip()
        if len(prefix) >= 3 and prefix not in candidates:
            candidates.append(prefix)
            
    # 4. Dash removal: "One Piece - Fishman Island" -> "One Piece"
    if " - " in cleaned:
        prefix = cleaned.split(" - ")[0].strip()
        if len(prefix) >= 3 and prefix not in candidates:
            candidates.append(prefix)

    return candidates

def find_aoneroom_anime(title: str, is_dub: bool = False) -> Optional[dict]:
    if not _api_executor:
        return None
    cache_key = f"{title.lower()}_{is_dub}"
    if cache_key in _anime_aoneroom_cache:
        return _anime_aoneroom_cache[cache_key]

    if is_dub:
        # 1. First locate canonical base anime
        base = find_aoneroom_anime(title, is_dub=False)
        if base and base.get("subjectId"):
            base_sid = str(base.get("subjectId"))
            try:
                dub_data = _api_executor('/wefeed-tv-bff/subject/dub-info', f'subjectId={base_sid}')
                items = dub_data.get('data', {}).get('items', [])
                en_match = next((
                    it for it in items 
                    if (it.get('lanCode') == 'en' or 'english' in (it.get('lanName') or '').lower())
                    and it.get('type') == 0
                ), None)
                if en_match and en_match.get('subjectId'):
                    res_item = {
                        "subjectId": str(en_match.get("subjectId")),
                        "subjectType": base.get("subjectType", 2),
                        "title": f"{base.get('title', title)} [English]",
                        "hasResource": True,
                        "is_dub": True,
                        "lanCode": "en",
                        "lanName": "English Dub"
                    }
                    _anime_aoneroom_cache[cache_key] = res_item
                    return res_item
            except Exception as e:
                print(f"[AnimeEngine] Error resolving dub-info for {title} (SID {base_sid}): {e}")

        # 2. Fallback to searching explicit English title queries ONLY
        candidates = get_clean_titles(title)
        for c in candidates:
            q = f"{c} English"
            try:
                res = _api_executor('/wefeed-tv-bff/search/result', f'keyword={urllib.parse.quote(q)}&page=1&perPage=5&subjectType=0')
                items = res.get('data', {}).get('items', [])
                for it in items:
                    if not it.get('hasResource'):
                        continue
                    it_title = it.get('title', '')
                    it_corner = it.get('corner', '')
                    if 'english' in it_title.lower() or str(it_corner).lower() == 'english':
                        _anime_aoneroom_cache[cache_key] = it
                        return it
            except Exception as e:
                print(f"[AnimeEngine] Error searching AoneRoom for {q}: {e}")
                continue

        # Explicitly do NOT return Japanese stream when English dub was requested!
        _anime_aoneroom_cache[cache_key] = None
        return None

    # Base (Original) resolution
    candidates = get_clean_titles(title)
    seen = set()
    for q in candidates:
        if q.lower() in seen:
            continue
        seen.add(q.lower())
        try:
            res = _api_executor('/wefeed-tv-bff/search/result', f'keyword={urllib.parse.quote(q)}&page=1&perPage=5&subjectType=0')
            items = res.get('data', {}).get('items', [])
            for it in items:
                if not it.get('hasResource'):
                    continue
                it_title = it.get('title', '')
                for c in candidates:
                    if c.lower() in it_title.lower() or it_title.lower() in c.lower():
                        _anime_aoneroom_cache[cache_key] = it
                        return it
        except Exception as e:
            print(f"[AnimeEngine] Error searching AoneRoom for {q}: {e}")
            continue

    _anime_aoneroom_cache[cache_key] = None
    return None

def resolve_miruro_id(anilist_id: int) -> Optional[str]:
    """Compatibility stub."""
    return None

def get_anime_episodes(anilist_id: int, fallback_poster: str = "") -> List[dict]:
    """Fetches full episode roster instantly without blocking timeouts."""
    cache_key = str(anilist_id)
    if cache_key in _episodes_cache:
        return _episodes_cache[cache_key]

    details = get_anime_details(anilist_id)
    title = details.get("title", "Anime")
    episodes = []

    # 1. Try to fetch real episode metadata from native AoneRoom CDN
    if _api_executor:
        # Dragon Ball Special Case
        if anilist_id == 223 or "dragonball" in title.lower():
            db_sid = "5616484647824673120"
            try:
                s_info = _api_executor('/wefeed-tv-bff/subject/season-info', f'subjectId={db_sid}')
                seasons = s_info.get('data', {}).get('seasons', [])
                max_eps = seasons[0].get('maxEp', 153) if seasons else 153
                thumb = details.get("cover", {}).get("url") or fallback_poster or "https://image.tmdb.org/t/p/w500/2RSrQ82HNbBBVM3omiHObQ0EvqI.jpg"
                for i in range(1, max_eps + 1):
                    episodes.append({
                        "se": 1,
                        "epNumber": i,
                        "title": f"{String_pad(i)}. Secret of the Dragon Balls" if i == 1 else f"{String_pad(i)}. Episode {i}",
                        "runtime": "24 MIN",
                        "synopsis": f"Episode {i} of Dragon Ball",
                        "thumbnail": thumb,
                        "skip_times": []
                    })
            except Exception as e:
                print(f"[AnimeEngine] Error resolving Dragon Ball episodes: {e}")

        if not episodes:
            match = find_aoneroom_anime(title, is_dub=False)
            if match:
                sid = match.get("subjectId")
                try:
                    s_info = _api_executor('/wefeed-tv-bff/subject/season-info', f'subjectId={sid}')
                    seasons = s_info.get('data', {}).get('seasons', [])
                    max_eps = 0
                    for s in seasons:
                        max_eps = max(max_eps, s.get('maxEp', 0))
                    if max_eps == 0 and seasons:
                        max_eps = seasons[0].get('maxEp', 0)
                    
                    if max_eps > 0:
                        thumb = details.get("cover", {}).get("url") or fallback_poster
                        for i in range(1, max_eps + 1):
                            ep_title = f"{String_pad(i)}. Episode {i}"
                            episodes.append({
                                "se": 1,
                                "epNumber": i,
                                "title": ep_title,
                                "runtime": "24 MIN",
                                "synopsis": f"Episode {i} of {title}",
                                "thumbnail": thumb,
                                "skip_times": []
                            })
                except Exception as e:
                    print(f"[AnimeEngine] Error resolving AoneRoom episodes for {title}: {e}")

    # Fallback: Instant generation using anime details or local index count (0ms)
    if not episodes:
        max_eps = details.get("episodes") or 12
        thumb = details.get("cover", {}).get("url") or fallback_poster or "https://images.unsplash.com/photo-1536440136628-849c177e76a1?w=400"
        for i in range(1, max_eps + 1):
            episodes.append({
                "se": 1,
                "epNumber": i,
                "title": f"{String_pad(i)}. Episode {i}",
                "runtime": "24 MIN",
                "synopsis": f"Episode {i} of {title}",
                "thumbnail": thumb,
                "skip_times": []
            })

    _episodes_cache[cache_key] = episodes
    return episodes

def String_pad(n: int) -> str:
    return str(n).zfill(2)

def resolve_anime_stream(anilist_id: int, ep: int = 1, is_dub: bool = True) -> Optional[dict]:
    """Dynamically resolves fresh playable stream from native high-speed CDN without freezing."""
    cache_key = f"{anilist_id}_{ep}_{is_dub}"
    now = time.time()
    if cache_key in _play_stream_cache:
        cached_time, cached_val = _play_stream_cache[cache_key]
        if now - cached_time < 1800:
            return cached_val

    # 1. Dragon Ball Special Handling
    if anilist_id == 223:
        if _api_executor:
            db_sid = "5616484647824673120" if is_dub else "5971941144341667848"
            try:
                p = _api_executor('/wefeed-tv-bff/subject/play-info/v2', f'subjectId={db_sid}&se=1&ep={ep}')
                streams = p.get('data', {}).get('streams', [])
                if streams:
                    st = streams[0]
                    res = {
                        "url": st.get("url"),
                        "cookie": st.get("signCookie", ""),
                        "format": "DASH" if ".mpd" in st.get("url", "") else "HLS",
                        "resolutions": st.get("resolutions", "1080p,720p,480p"),
                        "provider": "aoneroom-native",
                        "server": "cdn-1",
                        "track": "dub" if is_dub else "sub"
                    }
                    _play_stream_cache[cache_key] = (now, res)
                    return res
            except Exception as e:
                print(f"[AnimeEngine] Error resolving Dragon Ball AoneRoom stream: {e}")

        # Dragon Ball verified stream fallback (ONLY for Dragon Ball)
        fallback_url = (
            "https://fielddewice-31.trail29.top/m/ASBoHpTyH_HbHf1LpHCUWXZQ3NxDMFrGpi3cn8UMpHLxd2TW8nrT_jE_yWnSflFed1nr-Hv-wERqQclSHMZlN_Sj-nHE1ziZ23UupVFLjlIAcfmithVDi6hiUZXo-sLadDj90kQOda_LQAPOke5et4DOPla_O-w4joTGpkAHoChWdO3cp-TmbHfLpeaaurQoVBEcw7vQb9L3TcSdQNu0nzWpc-ZIPB1dXleliaRBMKXLQAvzQAokJ2Y9ZVyqATGFGFSy8wIy-ruVO4Z3D_dQcQw3n6IOHJY13ziXZvBfp6d_vOA9QIHNXAa6V7DBeokLLpT2StVW5bjBOA.m3u8"
            if is_dub else
            "https://fielddewice-31.trail29.top/m/AeqxIUu7M8m38YU__LyelHX8KQQH46IrAuoPcxord_g9333dUP7KWF4XrW2eRskRHVS5JoJj93gPDodBzZuwcXUibciMbtDXonFhRrZb1qHK3CiG6zNn5BmGUsC4JBDVZDjb4ab0PSwh-NmtRZB3DfFMouwmYtLgbeG-DRaK3N361W-xrEak0nm16Het8FY-fw_P8BzvAcOKRqFTsjoZW4aG09hjxVMhFYTcrbkCwBaf-JukPE8EFtqsRRCZeXf3cECTTX4qzj9jhjMLwR-AI1dGFbDv_pO1a1IdaB47yxTyUGk1SRkU6FX17m9syo4EwMC0c_mtUmrDYw.m3u8"
        )
        return {
            "url": fallback_url,
            "origin": "https://ultracloud.cc",
            "referer": "https://ultracloud.cc/",
            "provider": "icarus-fallback",
            "server": "icarus-1",
            "track": "dub" if is_dub else "sub"
        }

    # 2. Universal Anime Stream Resolution via AoneRoom CDN
    if _api_executor:
        details = get_anime_details(anilist_id)
        title = details.get("title", "")
        match = find_aoneroom_anime(title, is_dub=is_dub)
        if match:
            sid = match.get("subjectId")
            try:
                p = _api_executor('/wefeed-tv-bff/subject/play-info/v2', f'subjectId={sid}&se=1&ep={ep}')
                streams = p.get('data', {}).get('streams', [])
                if not streams and ep != 1:
                    p = _api_executor('/wefeed-tv-bff/subject/play-info/v2', f'subjectId={sid}&se=1&ep=1')
                    streams = p.get('data', {}).get('streams', [])
                if streams:
                    st = streams[0]
                    res = {
                        "url": st.get("url"),
                        "cookie": st.get("signCookie", ""),
                        "format": "DASH" if ".mpd" in st.get("url", "") else "HLS",
                        "resolutions": st.get("resolutions", "1080p,720p,480p"),
                        "provider": "aoneroom-native",
                        "server": "cdn-1",
                        "track": "dub" if is_dub else "sub"
                    }
                    _play_stream_cache[cache_key] = (now, res)
                    return res
            except Exception as e:
                print(f"[AnimeEngine] Error resolving AoneRoom play stream for {title} (SID {sid}): {e}")

    # No stream found for this anime: Return None (NEVER Dragon Ball for unrelated anime!)
    return None
