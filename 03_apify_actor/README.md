# Women in Tech Inspiration Feed — Apify Actor

A small [Apify Actor](https://apify.com/actors) (in Python) that collects recent posts
about **women in tech** into one stream, then lets you export or schedule them.

It's the Level-3 finale of the *"Apify Web Scraping & Parsing Workshop"*
(PyLadies @ PyCon Singapore). The two scripts one level up (`../01_pyladies_html_scrape.py`,
`../02_devto_api.py`) teach the moves; this Actor wraps them into something you can
deploy to the cloud and run on a schedule. ← **start with the [demo hub README](../README.md)** if you haven't.

---

## What does it do?

You give it a few **tags** and it pulls recent posts from two sources, normalizes them
into one shape, drops stale/duplicate ones, and saves the rest to a dataset:

- **Dev.to** → official JSON API → *Level 1* (`source: "dev.to"`)
- **Medium** → blocks scrapers, so we read its RSS feed → *Level 3* (`source: "medium"`)

The result is a tidy, exportable feed of inspiration you could email yourself every Monday.

---

## Prerequisites

- [Apify account](https://console.apify.com) (free tier is plenty) — only needed to deploy
- Python 3.10+ (the Docker image uses 3.13)
- [Apify CLI](https://docs.apify.com/cli/) for the cloud parts:

```bash
npm install -g apify-cli
apify login
```

---

## Input

Configure these in the Apify Console UI, or in a local `INPUT.json` (see below).

| Field | Type | Default | What it does |
|---|---|---|---|
| `tags` | string[] | `["womenintech", "pyladies"]` | Topics to follow. Each becomes a Dev.to tag **and** a Medium RSS feed. |
| `sources` | string[] | `["devto", "medium"]` | Where to collect from: `devto`, `medium`, or both. |
| `maxAgeDays` | integer | `30` | Keep only posts newer than this. #womenintech/#pyladies are sparse — bump to 90 if the feed looks empty. |
| `minReactions` | integer | `0` | Drop Dev.to posts below this many reactions. (Medium has no count → always kept.) |
| `limit` | integer | `50` | Max posts to save. |

> ⚠️ **Tags are a union (OR), not an intersection.** `["womenintech", "python"]` returns
> women-in-tech posts **and** every recent Python post — not their overlap. A busy tag
> like `#python` will flood and bury the on-theme posts, so keep this list focused.

## Output

One item per post, every source normalized to the same shape:

| Field | Example |
|---|---|
| `name` | author / publication name |
| `excerpt` | short summary (HTML stripped) |
| `link` | URL to the post |
| `tags` | `["womenintech", "career"]` |
| `source` | `"dev.to"` or `"medium"` |
| `published_at` | ISO 8601 timestamp |
| `reactions` | integer (Dev.to) or `null` (Medium) |
| `cover_image` | URL or `null` |

---

## Run it locally

No cloud account needed — the SDK uses a local `./storage` folder.

```bash
cd 03_apify_actor
pip install -r requirements.txt

# Option A: via the Apify CLI (uses input_schema.json defaults)
apify run

# Option B: plain Python (set your own input first — see below)
python -m src
```

To customize the input for `python -m src`, create
`storage/key_value_stores/default/INPUT.json`:

```json
{ "tags": ["womenintech", "pyladies"], "sources": ["devto", "medium"], "maxAgeDays": 90 }
```

Results land in `storage/datasets/default/*.json` — one file per post.

> **Tip:** the dataset *appends*. Delete `storage/datasets/default/` between runs if you
> don't want old items mixed with new ones.

---

## How the code works

The whole Actor is in [`src/main.py`](src/main.py), and `main()` reads as a 4-step pipeline:

```
COLLECT  → for each tag, fetch each source (Dev.to API + Medium RSS) into one list
FILTER   → drop posts older than maxAgeDays, and Dev.to posts below minReactions
DEDUPE   → same post can appear under two tags; keep one, sort newest-first
OUTPUT   → Actor.push_data() writes each item to the dataset
```

Three building blocks, mirroring the two teaching scripts:

```python
# Level 1 — the easy win: data already arrives as clean JSON
resp = await client.get(DEVTO_API, params={"tag": tag, "per_page": 30})
posts = resp.json()

# Level 3 — Medium blocks scrapers, so we read its RSS feed instead
resp = await client.get(MEDIUM_FEED.format(tag=tag))   # custom User-Agent!
feed = feedparser.parse(resp.content)
```

`async with Actor:` is the Apify lifecycle — it reads the run's input, wires up logging,
and finalizes the run on exit. Everything else is plain Python you already understand.

---

## Deploy to Apify

```bash
apify push
```

Your Actor is now live at [console.apify.com](https://console.apify.com/actors) under
**My Actors**. Run it from the UI, tweak the input, and watch the dataset fill up.

## Schedule & export

**Run on a schedule** — e.g. every Monday at 8:00 for a weekly digest:
1. Open your Actor in the Apify Console
2. **Schedules** → **+ New schedule**
3. Cron: `0 8 * * 1` (Mondays at 08:00)

**Export the results:**
- Dataset → **Export** → CSV / JSON / Excel
- Or pipe it straight to **Gmail/Slack/Google Sheets** via
  [Apify integrations](https://docs.apify.com/platform/integrations)

---

## Troubleshooting

| Symptom | Cause / fix |
|---|---|
| Import error `cannot specify both default and default_factory` | An old `apify<3` resolved. Pin **`apify~=3.4`** (already in `requirements.txt`). |
| Medium returns nothing | Medium blocks `feedparser`'s default User-Agent. We fetch the RSS with `httpx` (custom UA) first, then parse the bytes — don't hand a URL straight to `feedparser`. |
| Feed is empty / too small | `#womenintech` and `#pyladies` are sparse (often 0 posts in a 7-day window). Raise `maxAgeDays` (try 90) or add `devto`+`medium` both. |
| Feed full of off-topic posts | A broad tag like `#python` is in `tags` — remember tags are OR'd. Trim to on-theme tags. |

---

## Where to next

- **Try the exercises:** [`../EXERCISES.md`](../EXERCISES.md) — easy → hard, including
  "add a `keyword` input" and "add a third source."
- [Apify Academy — Web scraping for Python devs](https://docs.apify.com/academy)
- [Apify Python SDK docs](https://docs.apify.com/sdk/python/)
- [Browse thousands of ready-made Actors](https://apify.com/store)
