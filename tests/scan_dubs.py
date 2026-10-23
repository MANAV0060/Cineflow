import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import execute_api

def scan():
    print("Fetching catalog to inspect dub-info for various titles...")
    res = execute_api('/wefeed-tv-bff/filter/list', 'channelId=1&page=1&perPage=30')
    items = res.get('data', {}).get('items', [])
    
    found_dubs = 0
    for item in items:
        sid = item.get('subjectId')
        title = item.get('title')
        try:
            dub_res = execute_api('/wefeed-tv-bff/subject/dub-info', f'subjectId={sid}')
            dubs = dub_res.get('data', {}).get('items', [])
            if len(dubs) > 1:
                found_dubs += 1
                print(f"\n[FOUND MULTI-DUB] {title} (ID: {sid})")
                for d in dubs:
                    print(f"  -> Lan: {d.get('lanName')}, Code: {d.get('lanCode')}, SubjectId: {d.get('subjectId')}, Original: {d.get('original')}")
            elif len(dubs) == 1:
                d = dubs[0]
                # print(f"Single dub: {title} -> {d.get('lanName')} ({d.get('lanCode')})")
        except Exception as e:
            pass

    # Also check TV series
    res_tv = execute_api('/wefeed-tv-bff/filter/list', 'channelId=2&page=1&perPage=30')
    items_tv = res_tv.get('data', {}).get('items', [])
    for item in items_tv:
        sid = item.get('subjectId')
        title = item.get('title')
        try:
            dub_res = execute_api('/wefeed-tv-bff/subject/dub-info', f'subjectId={sid}')
            dubs = dub_res.get('data', {}).get('items', [])
            if len(dubs) > 1:
                found_dubs += 1
                print(f"\n[FOUND MULTI-DUB TV] {title} (ID: {sid})")
                for d in dubs:
                    print(f"  -> Lan: {d.get('lanName')}, Code: {d.get('lanCode')}, SubjectId: {d.get('subjectId')}, Original: {d.get('original')}")
        except Exception as e:
            pass

    print(f"\nTotal multi-dub titles found in page 1: {found_dubs}")

if __name__ == '__main__':
    scan()
