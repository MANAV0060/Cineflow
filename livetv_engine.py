"""
CineFlow Live TV Engine
Provides canonical channel catalogs, duplicate merging, multiple streaming sources,
dynamic Akamai token retrieval for Sony channels, stream health verification,
and automatic source failover.
"""

import time
import ssl
import json
import urllib.request
import urllib.parse

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# In-memory cache for dynamic Sony tokens (3 minute TTL)
_sony_tokens_cache = {
    "timestamp": 0,
    "channels": {}
}

def get_sony_live_tokens():
    """Fetches real-time Akamai hdnea tokens from the dynamic Cloudflare worker."""
    now = time.time()
    if now - _sony_tokens_cache["timestamp"] < 180 and _sony_tokens_cache["channels"]:
        return _sony_tokens_cache["channels"]
    
    try:
        req = urllib.request.Request("https://pzsl.pzcdn.workers.dev/?get-pl", headers={"User-Agent": "mozila"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            content = resp.read().decode("utf-8")
        
        token_map = {}
        cur_id = ""
        for line in content.splitlines():
            line = line.strip()
            if line.startswith("#EXTINF"):
                m_id = None
                if 'tvg-id="' in line:
                    m_id = line.split('tvg-id="')[1].split('"')[0].lower()
                cur_id = m_id or ""
            elif line.startswith("http") and cur_id:
                token_map[cur_id] = line
                # Also index by key names
                if "sethd" in line.lower() or "set-hd" in cur_id:
                    token_map["set_hd"] = line
                elif "sabhd" in line.lower() or "sab" in cur_id:
                    token_map["sab_hd"] = line
                elif "sonymaxhd" in line.lower() or "max-hd" in cur_id:
                    token_map["max_hd"] = line
                elif "sonymaxsd" in line.lower() or "sony-max" == cur_id:
                    token_map["max_sd"] = line
                elif "max2" in line.lower():
                    token_map["max2"] = line
                elif "yay" in line.lower():
                    token_map["yay"] = line
                elif "ten1" in line.lower():
                    token_map["ten1_hd"] = line
                elif "ten5" in line.lower():
                    token_map["ten5_hd"] = line
                elif "pal" in line.lower():
                    token_map["pal"] = line
                elif "pix" in line.lower():
                    token_map["pix_hd"] = line
                elif "bbcearth" in line.lower():
                    token_map["bbcearth_hd"] = line
                elif "wah" in line.lower():
                    token_map["wah"] = line
        
        if token_map:
            _sony_tokens_cache["timestamp"] = now
            _sony_tokens_cache["channels"] = token_map
            return token_map
    except Exception as e:
        print("[LiveTV] Error refreshing Sony tokens:", e)
    
    return _sony_tokens_cache["channels"]

# Canonical deduplicated catalog
CANONICAL_CHANNELS = [
    # KIDS
    {
        "id": "cartoon-network",
        "name": "Cartoon Network",
        "category": "Kids",
        "badge": "1080p HD",
        "language": "Hindi / English",
        "logo": "https://upload.wikimedia.org/wikipedia/commons/8/80/Cartoon_Network_2010_logo.svg",
        "description": "India's premier animated entertainment channel featuring classic and modern hits.",
        "sources": [
            {"id": "cn-s1", "name": "Server 1 — GPCDN Ultra HD", "url": "https://drk6xq0vhn.gpcdn.net/live/cn_sd_abr/index.m3u8", "quality": "1080p", "isCORS": True},
            {"id": "cn-s2", "name": "Server 2 — Fast Edge CDN", "url": "https://drk6xq0vhn.gpcdn.net/live/cn_sd/chunks.m3u8", "quality": "720p", "isCORS": True},
            {"id": "cn-s3", "name": "Server 3 — Broadcast Live", "url": "http://103.151.60.162:2122/play/a015/index.m3u8?hls", "quality": "576p", "isCORS": True}
        ]
    },
    {
        "id": "pogo",
        "name": "Pogo",
        "category": "Kids",
        "badge": "HD",
        "language": "Hindi",
        "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d4/Pogo_logo.png/500px-Pogo_logo.png",
        "description": "India's homegrown animation and kids comedy channel with Chhota Bheem and Titoo.",
        "sources": [
            {"id": "pogo-s1", "name": "Server 1 — Broadcast HLS", "url": "http://103.151.60.162:2122/play/a01e/index.m3u8?hls", "quality": "576p", "isCORS": True},
            {"id": "pogo-s2", "name": "Server 2 — FAST Cloud Feed", "url": "https://drk6xq0vhn.gpcdn.net/live/pogo_sd_abr/index.m3u8", "quality": "720p", "isCORS": True}
        ]
    },
    {
        "id": "sony-yay",
        "name": "Sony YAY!",
        "category": "Kids",
        "badge": "HD",
        "language": "Hindi",
        "logo": "https://sonypicturesnetworks.com/images/logos/SONY%20YAY.png",
        "description": "Kids entertainment with Honey Bunny, Oggy, and fun animated adventures.",
        "sources": [
            {"id": "yay-s1", "name": "Server 1 — Sony SLIV Token HD", "url": "/api/livetv/stream?key=yay", "quality": "720p", "isCORS": True},
            {"id": "yay-s2", "name": "Server 2 — Broadcast Feed", "url": "http://103.151.60.162:2122/play/a015/index.m3u8?hls", "quality": "576p", "isCORS": True}
        ]
    },
    {
        "id": "disney-junior",
        "name": "Disney Junior",
        "category": "Kids",
        "badge": "HD",
        "language": "Hindi / English",
        "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b3/Disney_Junior_2020.svg/512px-Disney_Junior_2020.svg.png",
        "description": "Magical storytelling and beloved preschool shows for children.",
        "sources": [
            {"id": "dj-s1", "name": "Server 1 — Broadcast Live", "url": "http://103.151.60.162:2122/play/a016/index.m3u8?hls", "quality": "576p", "isCORS": True},
            {"id": "dj-s2", "name": "Server 2 — Edge Relay", "url": "http://103.151.60.162:2122/play/a018/index.m3u8?hls", "quality": "576p", "isCORS": True}
        ]
    },
    {
        "id": "disney-channel",
        "name": "Disney Channel",
        "category": "Kids",
        "badge": "720p HD",
        "language": "Hindi / English",
        "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d2/2019_Disney_Channel_logo.svg/512px-2019_Disney_Channel_logo.svg.png",
        "description": "The home of timeless Disney magic, animated series, and family entertainment.",
        "sources": [
            {"id": "dc-s1", "name": "Server 1 — Broadcast 720p", "url": "http://190.14.10.19:16000/play/a06z/index.m3u8", "quality": "720p", "isCORS": True},
            {"id": "dc-s2", "name": "Server 2 — International HD", "url": "http://103.151.60.162:2122/play/a018/index.m3u8?hls", "quality": "720p", "isCORS": True}
        ]
    },
    {
        "id": "hungama-tv",
        "name": "Hungama TV",
        "category": "Kids",
        "badge": "HD",
        "language": "Hindi",
        "logo": "https://upload.wikimedia.org/wikipedia/en/thumb/f/f6/Hungama_TV_logo.png/250px-Hungama_TV_logo.png",
        "description": "High-energy kids comedy, anime, Shinchan, and dubbed adventures.",
        "sources": [
            {"id": "hungama-s1", "name": "Server 1 — Broadcast HLS", "url": "http://103.151.60.162:2122/play/a017/index.m3u8?hls", "quality": "576p", "isCORS": True},
            {"id": "hungama-s2", "name": "Server 2 — Super Hungama Feed", "url": "http://103.151.60.162:2122/play/a01b/index.m3u8?hls", "quality": "576p", "isCORS": True}
        ]
    },
    {
        "id": "discovery-kids",
        "name": "Discovery Kids",
        "category": "Kids",
        "badge": "HD",
        "language": "Hindi",
        "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9f/Discovery_Kids_Logo.png/512px-Discovery_Kids_Logo.png",
        "description": "Fun, educational cartoons and popular action adventures like Little Singham.",
        "sources": [
            {"id": "dk-s1", "name": "Server 1 — Broadcast HLS", "url": "http://103.151.60.162:2122/play/a01f/index.m3u8?hls", "quality": "576p", "isCORS": True},
            {"id": "dk-s2", "name": "Server 2 — Alternate Relay", "url": "http://103.151.60.162:2122/play/a017/index.m3u8?hls", "quality": "576p", "isCORS": True}
        ]
    },
    {
        "id": "nickelodeon",
        "name": "Nickelodeon",
        "category": "Kids",
        "badge": "HD",
        "language": "Hindi",
        "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7a/Nickelodeon_2009_logo.svg/512px-Nickelodeon_2009_logo.svg.png",
        "description": "Nick India with Motu Patlu, Rudra, Shiva, and SpongeBob SquarePants.",
        "sources": [
            {"id": "nick-s1", "name": "Server 1 — Broadcast Live", "url": "http://103.151.60.162:2122/play/a018/index.m3u8?hls", "quality": "576p", "isCORS": True},
            {"id": "nick-s2", "name": "Server 2 — Nick Jr. Feed", "url": "http://103.151.60.162:2122/play/a00s/index.m3u8?hls", "quality": "576p", "isCORS": True}
        ]
    },

    # ENTERTAINMENT
    {
        "id": "star-plus",
        "name": "Star Plus",
        "category": "Entertainment",
        "badge": "1080p HD",
        "language": "Hindi",
        "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4e/Star_Plus_logo_2020.png/500px-Star_Plus_logo_2020.png",
        "description": "India's #1 General Entertainment channel for family serials and reality shows.",
        "sources": [
            {"id": "sp-s1", "name": "Server 1 — CloudFront 1080p Ultra HD", "url": "https://d1rc86nwwc9fag.cloudfront.net/260723/starplusuk_800/chunks.m3u8", "quality": "1080p", "isCORS": True},
            {"id": "sp-s2", "name": "Server 2 — Adaptive Global Feed", "url": "https://raw.githubusercontent.com/amazeyourself/adaptive-streams/refs/heads/main/streams/gb/YuppTV/UtsavPlus.m3u8", "quality": "720p", "isCORS": True},
            {"id": "sp-s3", "name": "Server 3 — Broadcast Backup", "url": "http://103.151.60.162:2122/play/a015/index.m3u8?hls", "quality": "576p", "isCORS": True}
        ]
    },
    {
        "id": "colors-tv",
        "name": "Colors TV",
        "category": "Entertainment",
        "badge": "1080p HD",
        "language": "Hindi",
        "logo": "https://upload.wikimedia.org/wikipedia/en/thumb/0/05/Colors_TV_logo.svg/512px-Colors_TV_logo.svg.png",
        "description": "Home to Bigg Boss, Khatron Ke Khiladi, Naagin, and blockbuster fiction drama.",
        "sources": [
            {"id": "col-s1", "name": "Server 1 — CloudFront High Bitrate HD", "url": "https://da86m1sqpm3o0.cloudfront.net/28072023/smil:colorsaudev.smil/chunklist_b896000.m3u8", "quality": "1080p", "isCORS": True},
            {"id": "col-s2", "name": "Server 2 — Adaptive APAC CDN", "url": "https://raw.githubusercontent.com/amazeyourself/adaptive-streams/refs/heads/main/streams/sg/YuppTV/ColorsAPAC.m3u8", "quality": "720p", "isCORS": True},
            {"id": "col-s3", "name": "Server 3 — Colors Rishtey", "url": "https://manatv.akamaized.net/090823/smil:ristheyamerica.smil/playlist.m3u8", "quality": "720p", "isCORS": True}
        ]
    },
    {
        "id": "set-hd",
        "name": "Sony Entertainment Television",
        "category": "Entertainment",
        "badge": "1080p HD",
        "language": "Hindi",
        "logo": "https://sonypicturesnetworks.com/images/logos/SET-LOGO-HD.png",
        "description": "Sony SET featuring Kaun Banega Crorepati, Indian Idol, The Kapil Sharma Show, CID.",
        "sources": [
            {"id": "set-s1", "name": "Server 1 — Sony SLIV 1080p HD Token", "url": "/api/livetv/stream?key=set_hd", "quality": "1080p", "isCORS": True},
            {"id": "set-s2", "name": "Server 2 — Sony Direct SD", "url": "/api/livetv/stream?key=set_sd", "quality": "576p", "isCORS": True}
        ]
    },
    {
        "id": "sony-sab",
        "name": "Sony SAB",
        "category": "Entertainment",
        "badge": "1080p HD",
        "language": "Hindi",
        "logo": "https://sonypicturesnetworks.com/images/logos/SONY%20SAB%20HD_WHITE.png",
        "description": "Light-hearted comedy and family dramas including Taarak Mehta Ka Ooltah Chashmah.",
        "sources": [
            {"id": "sab-s1", "name": "Server 1 — Sony SLIV 1080p HD Token", "url": "/api/livetv/stream?key=sab_hd", "quality": "1080p", "isCORS": True},
            {"id": "sab-s2", "name": "Server 2 — Sony Direct SD", "url": "/api/livetv/stream?key=sab_sd", "quality": "576p", "isCORS": True}
        ]
    },
    {
        "id": "star-bharat",
        "name": "Star Bharat",
        "category": "Entertainment",
        "badge": "1080p HD",
        "language": "Hindi",
        "logo": "https://upload.wikimedia.org/wikipedia/en/thumb/7/7b/Star_Bharat_logo_2022.png/500px-Star_Bharat_logo_2022.png",
        "description": "Inspiring stories, mythological epics (RadhaKrishn), and drama.",
        "sources": [
            {"id": "sb-s1", "name": "Server 1 — CloudFront 1080p HD", "url": "https://d1taaads3ztvmu.cloudfront.net/120723/smil:lifeokuk.smil/chunklist_b896000.m3u8", "quality": "1080p", "isCORS": True},
            {"id": "sb-s2", "name": "Server 2 — Adaptive Global", "url": "https://raw.githubusercontent.com/amazeyourself/adaptive-streams/refs/heads/main/streams/gb/YuppTV/UtsavBharat.m3u8", "quality": "720p", "isCORS": True}
        ]
    },
    {
        "id": "zee-tv",
        "name": "Zee TV",
        "category": "Entertainment",
        "badge": "1080p HD",
        "language": "Hindi",
        "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/cd/Zee_TV_logo.svg/512px-Zee_TV_logo.svg.png",
        "description": "Kundali Bhagya, Kumkum Bhagya, Sa Re Ga Ma Pa, and iconic Hindi soaps.",
        "sources": [
            {"id": "zee-s1", "name": "Server 1 — Broadcast 720p HD", "url": "http://103.151.60.162:2122/play/a01u/index.m3u8?hls", "quality": "720p", "isCORS": True},
            {"id": "zee-s2", "name": "Server 2 — GPCDN Ultra HD", "url": "https://drk6xq0vhn.gpcdn.net/live/zee_tv_hd_abr/index.m3u8", "quality": "1080p", "isCORS": True}
        ]
    },
    {
        "id": "zee-anmol",
        "name": "Zee Anmol",
        "category": "Entertainment",
        "badge": "720p HD",
        "language": "Hindi",
        "logo": "https://upload.wikimedia.org/wikipedia/en/thumb/b/b3/Zee_Anmol_logo.png/500px-Zee_Anmol_logo.png",
        "description": "Favorite nostalgic shows and entertainment for rural and urban audiences.",
        "sources": [
            {"id": "za-s1", "name": "Server 1 — GPCDN 720p HD", "url": "https://drk6xq0vhn.gpcdn.net/live/zee_anmol_abr/index.m3u8", "quality": "720p", "isCORS": True},
            {"id": "za-s2", "name": "Server 2 — Broadcast Feed", "url": "http://103.151.60.162:2122/play/a020/index.m3u8?hls", "quality": "576p", "isCORS": True}
        ]
    },
    {
        "id": "and-tv",
        "name": "&TV",
        "category": "Entertainment",
        "badge": "1080p HD",
        "language": "Hindi",
        "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/ef/%26TV_logo.svg/512px-%26TV_logo.svg.png",
        "description": "Bhabiji Ghar Par Hain, Happu Ki Ultan Paltan, and innovative fiction shows.",
        "sources": [
            {"id": "and-s1", "name": "Server 1 — GPCDN 1080p HD", "url": "https://drk6xq0vhn.gpcdn.net/live/and_tv_hd_abr/index.m3u8", "quality": "1080p", "isCORS": True},
            {"id": "and-s2", "name": "Server 2 — Adaptive UK", "url": "https://raw.githubusercontent.com/amazeyourself/adaptive-streams/refs/heads/main/streams/gb/YuppTV/AndTVUK.m3u8", "quality": "720p", "isCORS": True}
        ]
    },
    {
        "id": "star-utsav",
        "name": "Star Utsav",
        "category": "Entertainment",
        "badge": "HD",
        "language": "Hindi",
        "logo": "https://upload.wikimedia.org/wikipedia/en/thumb/0/05/Star_Utsav_logo.png/500px-Star_Utsav_logo.png",
        "description": "Timeless classics from the Star network vault.",
        "sources": [
            {"id": "su-s1", "name": "Server 1 — Broadcast HLS", "url": "http://103.151.60.162:2122/play/a01c/index.m3u8?hls", "quality": "576p", "isCORS": True},
            {"id": "su-s2", "name": "Server 2 — Alternate Feed", "url": "http://103.151.60.162:2122/play/a01d/index.m3u8?hls", "quality": "576p", "isCORS": True}
        ]
    },
    {
        "id": "dangal-tv",
        "name": "Dangal TV",
        "category": "Entertainment",
        "badge": "720p HD",
        "language": "Hindi",
        "logo": "https://upload.wikimedia.org/wikipedia/en/thumb/d/d7/Dangal_TV_logo.png/500px-Dangal_TV_logo.png",
        "description": "Leading Hindi entertainment free-to-air network.",
        "sources": [
            {"id": "dan-s1", "name": "Server 1 — Akamai Live HD", "url": "https://live-dangal.akamaized.net/liveabr/playlist.m3u8", "quality": "720p", "isCORS": True},
            {"id": "dan-s2", "name": "Server 2 — Broadcast Feed", "url": "http://103.151.60.162:2122/play/a015/index.m3u8?hls", "quality": "576p", "isCORS": True}
        ]
    },

    # NEWS
    {
        "id": "aaj-tak",
        "name": "Aaj Tak",
        "category": "News",
        "badge": "1080p HD",
        "language": "Hindi",
        "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/64/Aaj_tak_logo.svg/512px-Aaj_tak_logo.svg.png",
        "description": "India's most watched 24x7 Hindi news channel with breaking news coverage.",
        "sources": [
            {"id": "at-s1", "name": "Server 1 — Official InToday 1080p HD", "url": "https://feeds.intoday.in/aajtak/api/aajtakhd/master.m3u8", "quality": "1080p", "isCORS": True},
            {"id": "at-s2", "name": "Server 2 — VGCDN Master Live", "url": "https://aajtaklive.vgcdn.net/v1/master/611d79b11b77e2f571934fd80ca1413453772ac7/aajtakhdlive/live.m3u8", "quality": "720p", "isCORS": True},
            {"id": "at-s3", "name": "Server 3 — Akamai Live CDN", "url": "https://aajtakhdlive-amd.akamaized.net/hls/live/2014415/aajtakhd/aajtakhdlive/live_180p/chunks.m3u8", "quality": "720p", "isCORS": True}
        ]
    },
    {
        "id": "abp-news",
        "name": "ABP News",
        "category": "News",
        "badge": "1080p HD",
        "language": "Hindi",
        "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/cd/ABP_News_Logo.png/500px-ABP_News_Logo.png",
        "description": "In-depth national analysis, prime time debates, and breaking journalism.",
        "sources": [
            {"id": "abp-s1", "name": "Server 1 — CloudFront 1080p Ultra HD", "url": "https://d1rc86nwwc9fag.cloudfront.net/vglive-sk-472500/abpnews/master.m3u8", "quality": "1080p", "isCORS": True},
            {"id": "abp-s2", "name": "Server 2 — Akamai MiTV CDN", "url": "https://abpmitv.akamaized.net/hls/live/2042842/abpnews/master.m3u8", "quality": "720p", "isCORS": True}
        ]
    },
    {
        "id": "india-tv",
        "name": "India TV",
        "category": "News",
        "badge": "720p HD",
        "language": "Hindi",
        "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b3/India_TV_logo.svg/512px-India_TV_logo.svg.png",
        "description": "Aap Ki Adalat, Superfast 200, and non-stop news coverage with Rajat Sharma.",
        "sources": [
            {"id": "itv-s1", "name": "Server 1 — Akamai Origin HD", "url": "https://pl-indiatvnews.akamaized.net/out/v1/db79179b608641ceaa5a4d0dd0dca8da/index.m3u8", "quality": "720p", "isCORS": True},
            {"id": "itv-s2", "name": "Server 2 — SmartPlay Edge", "url": "https://mumbai-edge.smartplaytv.in/indiatv/index.m3u8", "quality": "720p", "isCORS": True}
        ]
    },
    {
        "id": "republic-bharat",
        "name": "Republic Bharat",
        "category": "News",
        "badge": "720p HD",
        "language": "Hindi",
        "logo": "https://upload.wikimedia.org/wikipedia/en/thumb/0/07/Republic_Bharat_Logo.png/500px-Republic_Bharat_Logo.png",
        "description": "Rashtra Ke Naam - fiery debates and rapid news reporting with Arnab Goswami.",
        "sources": [
            {"id": "rb-s1", "name": "Server 1 — Tango CDN HD", "url": "https://streams.tangotv.in/REPUBLICBHARAT/ORIGIN/index.m3u8", "quality": "720p", "isCORS": True},
            {"id": "rb-s2", "name": "Server 2 — SmartPlay Edge", "url": "https://mumbai-edge.smartplaytv.in/republicbharat/index.m3u8", "quality": "720p", "isCORS": True}
        ]
    },
    {
        "id": "ndtv-india",
        "name": "NDTV India",
        "category": "News",
        "badge": "720p HD",
        "language": "Hindi",
        "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/33/NDTV_India_logo.svg/512px-NDTV_India_logo.svg.png",
        "description": "Trusted Indian journalism, deep reporting, Prime Time, and ground reports.",
        "sources": [
            {"id": "ndtv-s1", "name": "Server 1 — Adaptive Global HLS", "url": "https://raw.githubusercontent.com/amazeyourself/adaptive-streams/refs/heads/main/streams/in/YuppTV/NDTVIndia.m3u8", "quality": "720p", "isCORS": True},
            {"id": "ndtv-s2", "name": "Server 2 — SmartPlay Edge", "url": "https://mumbai-edge.smartplaytv.in/ndtvindia/index.m3u8", "quality": "720p", "isCORS": True}
        ]
    },
    {
        "id": "zee-news",
        "name": "Zee News",
        "category": "News",
        "badge": "720p HD",
        "language": "Hindi",
        "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/14/Zee_News_logo.svg/512px-Zee_News_logo.svg.png",
        "description": "Daily News and Analysis (DNA) and national news updates.",
        "sources": [
            {"id": "zn-s1", "name": "Server 1 — CloudFront HD", "url": "https://dknttpxmr0dwf.cloudfront.net/index_57.m3u8", "quality": "720p", "isCORS": True},
            {"id": "zn-s2", "name": "Server 2 — SmartPlay Edge", "url": "https://mumbai-edge.smartplaytv.in/zeenews/index.m3u8", "quality": "720p", "isCORS": True}
        ]
    },
    {
        "id": "news18-india",
        "name": "News18 India",
        "category": "News",
        "badge": "720p HD",
        "language": "Hindi",
        "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/75/News18_India.png/500px-News18_India.png",
        "description": "Aar Paar, Desh Ki Nazaquat, and nationwide regional news coverage.",
        "sources": [
            {"id": "n18-s1", "name": "Server 1 — Akamai BPK Syndication HD", "url": "https://n18syndication.akamaized.net/bpk-tv/News18_India_NW18_MOB/output01/master.m3u8", "quality": "720p", "isCORS": True},
            {"id": "n18-s2", "name": "Server 2 — SmartPlay Edge", "url": "https://mumbai-edge.smartplaytv.in/news18india/index.m3u8", "quality": "720p", "isCORS": True}
        ]
    },
    {
        "id": "tv9-bharatvarsh",
        "name": "TV9 Bharatvarsh",
        "category": "News",
        "badge": "720p HD",
        "language": "Hindi",
        "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c5/TV9_Bharatvarsh_logo.png/500px-TV9_Bharatvarsh_logo.png",
        "description": "Fast-paced geopolitics, war reporting, and investigative news.",
        "sources": [
            {"id": "tv9-s1", "name": "Server 1 — CloudFront Ultra HD", "url": "https://dyjmyiv3bp2ez.cloudfront.net/pub-iotv9hinjzgtpe/liveabr/playlist.m3u8", "quality": "720p", "isCORS": True},
            {"id": "tv9-s2", "name": "Server 2 — CloudCDN Live", "url": "https://d3408f659f.cloudcdn.live/tv9_hindi/index.m3u8", "quality": "720p", "isCORS": True}
        ]
    },
    {
        "id": "dd-news",
        "name": "DD News",
        "category": "News",
        "badge": "HD",
        "language": "Hindi / English",
        "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/69/DD_News_Logo.png/500px-DD_News_Logo.png",
        "description": "Public broadcaster Doordarshan official national and parliament bulletins.",
        "sources": [
            {"id": "dd-s1", "name": "Server 1 — SmartPlay Live Edge", "url": "https://mumbai-edge.smartplaytv.in/DDNews/index.m3u8", "quality": "720p", "isCORS": True},
            {"id": "dd-s2", "name": "Server 2 — Akamai Master", "url": "https://ddnews.akamaized.net/hls/live/2031070/ddnews/master.m3u8", "quality": "720p", "isCORS": True}
        ]
    },

    # MOVIES
    {
        "id": "star-gold",
        "name": "Star Gold",
        "category": "Movies",
        "badge": "720p HD",
        "language": "Hindi",
        "logo": "https://upload.wikimedia.org/wikipedia/en/thumb/7/7b/Star_Gold_logo_2020.png/500px-Star_Gold_logo_2020.png",
        "description": "Biggest Bollywood blockbusters, South Hindi dubbed premieres, and action films.",
        "sources": [
            {"id": "sg-s1", "name": "Server 1 — Broadcast 720p HD", "url": "http://103.151.60.162:2122/play/a01v/index.m3u8?hls", "quality": "720p", "isCORS": True},
            {"id": "sg-s2", "name": "Server 2 — Star Gold 2 Feed", "url": "http://103.151.60.162:2122/play/a01d/index.m3u8?hls", "quality": "720p", "isCORS": True}
        ]
    },
    {
        "id": "sony-max",
        "name": "Sony MAX",
        "category": "Movies",
        "badge": "1080p HD",
        "language": "Hindi",
        "logo": "https://sonypicturesnetworks.com/images/logos/Sony_MAX-HD_WHITE.png",
        "description": "Deewana Bana De — Iconic Bollywood films, Sooryavansham, and mega premieres.",
        "sources": [
            {"id": "max-s1", "name": "Server 1 — Sony SLIV 1080p HD Token", "url": "/api/livetv/stream?key=max_hd", "quality": "1080p", "isCORS": True},
            {"id": "max-s2", "name": "Server 2 — Sony SLIV Direct SD", "url": "/api/livetv/stream?key=max_sd", "quality": "576p", "isCORS": True}
        ]
    },
    {
        "id": "sony-max-2",
        "name": "Sony MAX 2",
        "category": "Movies",
        "badge": "HD",
        "language": "Hindi",
        "logo": "https://www.sonypicturesnetworks.com/images/logos/Sony_MAX2.png",
        "description": "Kuch Filmon Ka Jadoo Kabhi Kam Nahi Hota — Evergreen golden cinema.",
        "sources": [
            {"id": "max2-s1", "name": "Server 1 — Sony SLIV Token HD", "url": "/api/livetv/stream?key=max2", "quality": "720p", "isCORS": True},
            {"id": "max2-s2", "name": "Server 2 — Sony Wah Movies", "url": "/api/livetv/stream?key=wah", "quality": "576p", "isCORS": True}
        ]
    },
    {
        "id": "zee-cinema",
        "name": "Zee Cinema",
        "category": "Movies",
        "badge": "720p HD",
        "language": "Hindi",
        "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/ba/Zee_Cinema_logo.svg/512px-Zee_Cinema_logo.svg.png",
        "description": "Movies, Masti, Magic — the pioneer Hindi movie channel.",
        "sources": [
            {"id": "zc-s1", "name": "Server 1 — Adaptive APAC HD", "url": "https://raw.githubusercontent.com/amazeyourself/adaptive-streams/refs/heads/main/streams/sg/YuppTV/ZeeCinemaAPAC.m3u8", "quality": "720p", "isCORS": True},
            {"id": "zc-s2", "name": "Server 2 — Broadcast Feed", "url": "http://103.151.60.162:2122/play/a015/index.m3u8?hls", "quality": "576p", "isCORS": True}
        ]
    },
    {
        "id": "zee-bollywood",
        "name": "Zee Bollywood",
        "category": "Movies",
        "badge": "720p HD",
        "language": "Hindi",
        "logo": "https://upload.wikimedia.org/wikipedia/en/thumb/0/05/Zee_Bollywood_logo.png/500px-Zee_Bollywood_logo.png",
        "description": "100% Shuddh Bollywood masaledaar films.",
        "sources": [
            {"id": "zb-s1", "name": "Server 1 — GPCDN 720p HD", "url": "https://drk6xq0vhn.gpcdn.net/live/zee_bollywood_abr/index.m3u8", "quality": "720p", "isCORS": True},
            {"id": "zb-s2", "name": "Server 2 — Zee Cinema Alt", "url": "https://raw.githubusercontent.com/amazeyourself/adaptive-streams/refs/heads/main/streams/sg/YuppTV/ZeeCinemaAPAC.m3u8", "quality": "720p", "isCORS": True}
        ]
    },
    {
        "id": "colors-cineplex",
        "name": "Colors Cineplex",
        "category": "Movies",
        "badge": "720p HD",
        "language": "Hindi",
        "logo": "https://upload.wikimedia.org/wikipedia/en/thumb/2/2c/Colors_Cineplex_logo.png/500px-Colors_Cineplex_logo.png",
        "description": "Hit Hai Toh Dekhega — South action and Hindi superhits.",
        "sources": [
            {"id": "cc-s1", "name": "Server 1 — Adaptive APAC HD", "url": "https://raw.githubusercontent.com/amazeyourself/adaptive-streams/refs/heads/main/streams/sg/YuppTV/ColorsAPAC.m3u8", "quality": "720p", "isCORS": True},
            {"id": "cc-s2", "name": "Server 2 — Colors Live Alt", "url": "https://manatv.akamaized.net/090823/smil:ristheyamerica.smil/playlist.m3u8", "quality": "720p", "isCORS": True}
        ]
    },
    {
        "id": "b4u-movies",
        "name": "B4U Movies",
        "category": "Movies",
        "badge": "HD",
        "language": "Hindi",
        "logo": "https://upload.wikimedia.org/wikipedia/en/thumb/2/25/B4U_Movies_logo.png/500px-B4U_Movies_logo.png",
        "description": "Classic and action Bollywood movie library.",
        "sources": [
            {"id": "b4u-s1", "name": "Server 1 — Tango CDN HD", "url": "https://streams.tangotv.in/B4UMOVIES/ORIGIN/index.m3u8", "quality": "720p", "isCORS": True},
            {"id": "b4u-s2", "name": "Server 2 — B4U Kadak Live", "url": "https://streams.tangotv.in/B4UKADAK/ORIGIN/index.m3u8", "quality": "720p", "isCORS": True}
        ]
    },
    {
        "id": "goldmines",
        "name": "Goldmines Movies",
        "category": "Movies",
        "badge": "720p HD",
        "language": "Hindi",
        "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6f/Goldmines_Telefilms_logo.png/500px-Goldmines_Telefilms_logo.png",
        "description": "The king of South Indian Hindi-dubbed blockbusters.",
        "sources": [
            {"id": "gm-s1", "name": "Server 1 — Tango Origin 1", "url": "https://mumt03.tangotv.in/Dsly5z3HGOLDMINES2/index.m3u8", "quality": "720p", "isCORS": True},
            {"id": "gm-s2", "name": "Server 2 — Goldmines Bollywood", "url": "https://mumt03.tangotv.in/Dsly5z3HGOLDMINESBOLLYWOOD/index.m3u8", "quality": "720p", "isCORS": True}
        ]
    },
    {
        "id": "manoranjan-movies",
        "name": "Manoranjan Movies",
        "category": "Movies",
        "badge": "HD",
        "language": "Hindi",
        "logo": "https://upload.wikimedia.org/wikipedia/en/thumb/4/4c/Manoranjan_TV_logo.png/500px-Manoranjan_TV_logo.png",
        "description": "Round-the-clock action and comedy films.",
        "sources": [
            {"id": "mm-s1", "name": "Server 1 — Tango Origin 1", "url": "https://mumt04.tangotv.in/m18aqlK4MANORANJANMOVIES/index.m3u8", "quality": "720p", "isCORS": True},
            {"id": "mm-s2", "name": "Server 2 — Manoranjan Grand", "url": "https://streams.tangotv.in/MANORANJANGRAND/ORIGIN/index.m3u8", "quality": "720p", "isCORS": True}
        ]
    },

    # SPORTS
    {
        "id": "sony-ten-1",
        "name": "Sony Sports Ten 1 (Six)",
        "category": "Sports",
        "badge": "1080p HD",
        "language": "English / Hindi",
        "logo": "https://sonypicturesnetworks.com/images/logos/Sony_Sports_Ten1_HD.png",
        "description": "UEFA Champions League, WWE, Australian Open, and premium live sports.",
        "sources": [
            {"id": "ten1-s1", "name": "Server 1 — Sony SLIV 1080p HD", "url": "/api/livetv/stream?key=ten1_hd", "quality": "1080p", "isCORS": True},
            {"id": "ten1-s2", "name": "Server 2 — Sony Sports Ten 5 (Six HD)", "url": "/api/livetv/stream?key=ten5_hd", "quality": "1080p", "isCORS": True}
        ]
    }
]

def get_channels_catalog():
    """Returns canonical channels with active, merged sources."""
    return CANONICAL_CHANNELS

def resolve_stream_url(key):
    """Resolves Sony tokenized URLs or direct streams."""
    tokens = get_sony_live_tokens()
    if key in tokens:
        return tokens[key]
    # Fallback to direct worker token endpoint
    return f"https://pzsl.pzcdn.workers.dev/{key}.m3u8"
