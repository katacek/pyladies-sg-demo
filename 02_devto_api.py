"""Level 1 — the easy win: an official JSON API.

Dev.to publishes a documented, public API. No HTML parsing, no API key needed.
The data already comes back as clean JSON — this is always what to look for first.

Run:  python 02_devto_api.py
"""

import requests

API = "https://dev.to/api/articles"
TAG = "womenintech"

resp = requests.get(API, params={"tag": TAG, "per_page": 15}, timeout=30)
resp.raise_for_status()
articles = resp.json()  # <-- already structured. No parsing!

print(f"Found {len(articles)} posts tagged #{TAG}\n")
for a in articles:
    print(f"  • {a['title'][:65]}")
    print(
        f"      by {a['user']['name']}  ·  ❤️ {a['public_reactions_count']}"
        f"  ·  {a['readable_publish_date']}"
    )
    print(f"      tags: {', '.join(a['tag_list'])}")
    print(f"      {a['url']}\n")
