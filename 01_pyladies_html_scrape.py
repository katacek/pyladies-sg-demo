"""Level 2 — parsing HTML with BeautifulSoup.

PyLadies has chapters all over the world. There's no API here, so we read
the page's HTML structure directly and pick out what we want with CSS selectors.

Run:  python 01_pyladies_html_scrape.py
"""

import requests
from bs4 import BeautifulSoup

URL = "https://pyladies.com/locations/"

resp = requests.get(URL, timeout=30)
resp.raise_for_status()

# Turn the raw HTML text into a tree we can query.
soup = BeautifulSoup(resp.text, "html.parser")

chapters = []
for div in soup.select("div.chapter_location"):  # <-- the selector we found in DevTools
    name = (div.get("data-chapter-name") or "").strip()
    link_el = div.select_one("h3.chapter-name a")
    link = link_el["href"] if link_el else None
    if name:
        chapters.append({"name": name, "link": link})

print(f"Found {len(chapters)} PyLadies chapters around the world\n")
for c in chapters[:15]:
    print(f"  • {c['name']:<35} {c['link']}")

print(
    "\nNow try breaking the selector (e.g. 'div.chapter_locationX') — "
    "you get 0 results.\nThat's how fragile HTML scraping is: change the design, break the scraper."
)
