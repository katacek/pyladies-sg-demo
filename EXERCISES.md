# Try it yourself 🚀

Three challenges, easy → hard. Fork the repo and give one a go this week.

## 1. Easy — change the feed
- Edit `02_devto_api.py`: swap `womenintech` for a tag you care about
  (`python`, `machinelearning`, `career`, `opensource`).
- Add a second tag and merge the results into one list.

## 2. Medium — enrich the data
- Dev.to's article list has no job **role** (e.g. "Data Engineer at…").
  It lives on the author's profile: `https://dev.to/api/users/by_username?url=<username>`.
- For each post, fetch the author's bio and add it to the output.
- Tip: be polite — add a small delay, and cache users you've already seen.

## 3. Hard — make it your own Actor
- In `03_apify_actor/`, add a new input field `keyword` and only keep posts
  whose title contains it.
- Add a third source (e.g. a conference speakers page) using BeautifulSoup,
  mapped to the same output shape.
- Deploy with `apify push`, then **schedule** it to run every Monday at 8am
  and email yourself the results.

## Stuck?
- Apify Academy → *Web scraping basics for Python devs*
- Apify docs & Discord
- The PyLadies community 💜
