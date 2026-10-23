import urllib.request, urllib.parse, json

def test_search(query):
    url = f"http://127.0.0.1:5000/api/search?keyword={urllib.parse.quote(query)}"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=10) as r:
        d = json.loads(r.read().decode("utf-8"))
        data = d.get("data", {})
        items = data.get("items", [])
        chips = data.get("relatedKeywords", [])
        recs = data.get("recommendations", [])
        print(f"=== Query: '{query}' ===")
        print(f"Hits ({len(items)}):", [i.get("title") for i in items[:3]])
        print(f"Related Searches ({len(chips)}):", chips[:4])
        print(f"Recommendations ({len(recs)}):", [r.get("title") for r in recs[:3]])
        print()

test_search("Avatar")
test_search("Spiderman")
test_search("non_existent_query_xyz")
