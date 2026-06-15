# Web scraping for PyLadies — demo code

Companion repo for the *"Apify Web Scraping & Parsing Workshop"*
(PyLadies @ PyCon Singapore).

We build a **Women in Tech Inspiration Feed**: recent posts about women in tech,
collected into one stream. Along the way we hit all **3 levels of getting data**:

| File | Level | What it shows |
|------|-------|---------------|
| `02_devto_api.py`   | 1 — API  | Use Dev.to's clean JSON API. The easy win. |
| `01_pyladies_html_scrape.py` | 2 — HTML | Parse a page with BeautifulSoup (PyLadies chapters). Fragile! |
| `03_apify_actor/`   | all      | Wrap it as a cloud Actor: input → dataset → schedule. |

> New here? Read top-to-bottom. The golden rule of the whole talk:
> **always check for an API before you parse HTML.**

---

## Prerequisites

- **Python 3.10+**
- For the two demo scripts: just `pip` (instructions below)
- For the Actor: an [Apify account](https://console.apify.com) (free) + the
  [Apify CLI](https://docs.apify.com/cli/) — see [`03_apify_actor/README.md`](03_apify_actor/README.md)

---

## Run the demo scripts locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-demo.txt

python 02_devto_api.py     # Level 1 — the API
python 01_pyladies_html_scrape.py   # Level 2 — HTML
```

`02` returns clean JSON with no parsing. `01` digs data out of HTML with a CSS selector —
then *try breaking the selector* and watch it return 0 results. That fragility is the whole
point: **HTML scrapers break when the site redesigns; APIs are far more stable.**

---

## ⭐ The key move: get JSON from an API instead of parsing HTML

If you can get data as JSON, you skip HTML parsing entirely — no fragile selectors, nothing to break when the site redesigns. Finding that API is the single most useful habit in the whole talk. There are two ways to do it.

### Way 1 — read the docs (the easy win): Dev.to

Dev.to publishes a **documented public API** — you don't need DevTools at all. Open this straight in your browser:

```
https://dev.to/api/articles?tag=womenintech&per_page=30
```

Clean JSON comes straight back, no key needed:

```json
[
  {
    "title": "How I got into tech",
    "user": { "name": "Ada L." },
    "public_reactions_count": 42,
    "tag_list": ["womenintech", "career"],
    "url": "https://dev.to/..."
  }
]
```

That's exactly what `02_devto_api.py` and the Actor call. 🎉

> 📚 **Where are the docs?** Dev.to runs on the open-source **Forem** platform, so its API isn't documented on dev.to itself — it lives at [developers.forem.com/api](https://developers.forem.com/api) (see the *Articles* endpoint).
> The docs describe the path (`/api/articles`); the host is just the Forem instance you hit — for us, `dev.to`.

> 💡 Dev.to actually **server-renders its pages** (the HTML already contains the posts, and even pagination loads a fresh HTML page), so you *won't* see this API fire in the Network tab — the site doesn't call it from the browser. We found it from the docs, not by hunting.
> That's a perfectly good outcome: **check for a documented API first.**

### Way 2 — hunt for a hidden API in DevTools

Many sites *don't* document an API but quietly call one in the background. You can watch it happen, then call that same endpoint yourself. **Mastodon** — a source in our Actor — is a perfect example, because its web app is client-rendered (it loads data with JavaScript):

1. Open [mastodon.social/tags/womenintech](https://mastodon.social/tags/womenintech)
2. Press **F12** → **Network** tab → filter **Fetch/XHR**
3. Reload, or scroll to load more posts
4. Watch a request to `/api/v1/timelines/tag/womenintech` appear — the site fetching its own posts as JSON. Open it in a new tab → clean JSON straight back:

```
GET https://mastodon.social/api/v1/timelines/tag/womenintech?limit=40
```
```json
[ { "account": {"display_name": "..."}, "content": "<p>...</p>", "url": "https://...", "tags": [{"name": "womenintech"}], "created_at": "2026-06-15T11:40:10Z" } ]
```

That's the whole skill — and the payoff: the endpoint you just found by hand is exactly the one `fetch_mastodon()` in the Actor calls. When a page feels dynamic, check **Network → Fetch/XHR** *before* you reach for BeautifulSoup. When a site has **no** API at all (like the PyLadies chapters page), *then* you fall back to parsing HTML — that's `01_pyladies_html_scrape.py`.

---

## The Actor (Level 3 finale)

`03_apify_actor/` wraps everything into a deployable cloud Actor that pulls from **Dev.to (API)**, **Mastodon (API)**, and **Medium (RSS)** at once, filters, dedupes, and saves the feed.

```bash
npm install -g apify-cli      # one-time
cd 03_apify_actor
apify run                     # runs locally; results in storage/datasets/default/
```

Deploy and schedule it for a weekly inspiration digest with `apify push`. Full input
reference, code walkthrough, deploy/schedule steps, and troubleshooting live in
**[`03_apify_actor/README.md`](03_apify_actor/README.md)**.

---

## The 3 sources = the 3 levels

- **Dev.to** publishes a documented JSON API → *Level 1 (API)*.
- **Mastodon** exposes a public JSON API (the one you can find live in DevTools) → *Level 1 (API)*.
- **PyLadies / conference pages** are plain HTML → *Level 2 (parse HTML)*.
- **Medium** is JS-heavy and blocks scrapers → *Level 3* → we use its **RSS feed**.

---

## Try it yourself 🚀

Three challenges, easy → hard (swap the feed, enrich the data, make it your own Actor):
see **[`EXERCISES.md`](EXERCISES.md)**. Fork the repo and give one a go this week.

---

## Be a good citizen

Public data, but: read `robots.txt`, don't hammer servers, always link back and
attribute, and never resell people's content.

---

## Glossary

**Web scraping** — Automatically collecting data from websites by sending requests and
extracting the relevant parts from the response (HTML or JSON).

**Server** — A computer (or program) that listens for requests over the internet and sends
back a response. Opening a website = your browser asks a server, the server replies with the page.

**API (Application Programming Interface)** — A formal agreement between two programs on how
to exchange data: what you can ask for, how to ask, and what format the answer comes in.
Dev.to's public API gives us clean JSON instead of HTML to dig through.

**Parsing** — Analyzing structured text (HTML or JSON) to pull out specific pieces of data.
With no API, you parse the raw HTML to find what you need (that's BeautifulSoup in `01`).

**CSS selector** — A pattern like `div.chapter_location` that points at elements in a page.
Parsing libraries use them to locate the data; they break when the site's markup changes.

**JS-rendered site** — A site that builds its content in the browser with JavaScript. A plain
HTTP request returns only an empty shell — the data isn't in the source HTML at all.

**Headless browser** — A real browser running with no visible window (loads pages, runs JS).
Used to scrape JS-rendered sites when there's no API and no RSS to fall back on.

**RSS feed** — A standardized XML feed of a site's latest content. When a site blocks scrapers
but still publishes RSS (like Medium), it's a clean, allowed way in.

**Proxy** — An intermediary server between you and the target site, so the site sees its IP
instead of yours. Used to avoid IP bans when scraping at scale.

**Actor** — Apify's name for a containerized program you can run in the cloud, give input, and
schedule. Our scraper is packaged as one in `03_apify_actor/`.

---

## Resources

- [Apify Academy — Web scraping for beginners](https://docs.apify.com/academy/web-scraping-for-beginners)
- [Apify Python SDK docs](https://docs.apify.com/sdk/python/)
- [Apify Store — thousands of ready-made Actors](https://apify.com/store)
- The PyLadies community 💜
