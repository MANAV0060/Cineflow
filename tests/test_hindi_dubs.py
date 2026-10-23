import sys
import os
import urllib.request
import json
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import execute_api

def test():
    # 1. Search for Hindi / Dual Audio movies
    queries = ["Dual Audio", "Hindi", "Bollywood", "KGF"]
    for q in queries:
        print(f"\n=================== SEARCH: {q} ===================")
        res = execute_api('/wefeed-tv-bff/search/result', f'keyword={q}&page=1&perPage=3')
        items = res.get('data', {}).get('items', [])
        print(f"Found {len(items)} items:")
        for item in items:
            sid = item.get('subjectId')
            title = item.get('title')
            stype = item.get('subjectType')
            print(f"\n* Title: {title} (ID: {sid}, Type: {stype})")
            
            # Check subject details
            try:
                sub_detail = execute_api('/wefeed-tv-bff/subject/get', f'subjectId={sid}')
                sub = sub_detail.get('data', {}).get('subject', {})
                print(f"  Languages in detail: {sub.get('languages')}, country: {sub.get('country')}")
                print(f"  Available keys in detail: {list(sub.keys())}")
            except Exception as e:
                print(f"  Detail error: {e}")

            # Check dub-info endpoint
            try:
                dub_data = execute_api('/wefeed-tv-bff/subject/dub-info', f'subjectId={sid}')
                print(f"  /subject/dub-info: {dub_data}")
            except Exception as e:
                print(f"  /subject/dub-info error: {e}")

            # Check play-info/v2
            try:
                play_data = execute_api('/wefeed-tv-bff/subject/play-info/v2', f'subjectId={sid}')
                streams = play_data.get('data', {}).get('streams', [])
                print(f"  Streams count: {len(streams)}")
                for idx, s in enumerate(streams):
                    print(f"    Stream #{idx}:")
                    for k, v in s.items():
                        if k != 'url' and k != 'signCookie':
                            print(f"      {k}: {v}")
                    mpd_url = s.get('url')
                    cookie = s.get('signCookie')
                    
                    # Fetch and inspect MPD manifest for audio adaptation sets
                    if mpd_url and cookie:
                        try:
                            req = urllib.request.Request(mpd_url, headers={
                                "Cookie": cookie,
                                "User-Agent": "okhttp/4.12.0"
                            })
                            with urllib.request.urlopen(req, timeout=10) as r:
                                mpd_content = r.read().decode('utf-8')
                                root = ET.fromstring(mpd_content)
                                # Inspect adaptation sets
                                for period in root.findall('{urn:mpeg:dash:schema:mpd:2011}Period'):
                                    ad_sets = period.findall('{urn:mpeg:dash:schema:mpd:2011}AdaptationSet')
                                    print(f"      MPD AdaptationSets: {len(ad_sets)}")
                                    for a_idx, ad in enumerate(ad_sets):
                                        mime = ad.attrib.get('mimeType', '')
                                        lang = ad.attrib.get('lang', '')
                                        content_type = ad.attrib.get('contentType', '')
                                        reps = ad.findall('{urn:mpeg:dash:schema:mpd:2011}Representation')
                                        rep_ids = [r.attrib.get('id') for r in reps]
                                        print(f"        Set #{a_idx}: mime={mime}, lang={lang}, type={content_type}, reps={rep_ids}")
                        except Exception as err:
                            print(f"      Failed to parse MPD: {err}")
            except Exception as e:
                print(f"  play-info error: {e}")

if __name__ == '__main__':
    test()
