# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A Twitter/X downloader (images, videos/GIFs, tweet text, replies, profile info) that scrapes X's private web GraphQL API (`https://twitter.com/i/api/graphql/...`) with cookie auth — not the official API. Comments, config values, and console output are in Chinese; match that when editing existing code.

## Running

```
pip3 install -r requirements.txt   # Python >= 3.8; httpx pinned to 0.28.1
python3 main.py
```

- `main.py` is the primary entry point and needs two config files:
  - `settings.json` (in repo; edit values — the `*_info` keys serve as comments)
  - `download_info.json` (**not** in repo): a list of `{id, cookie, user_list, user_media_url}` objects. The GitHub Actions workflow fetches it from a remote URL; `main.py` crashes at startup without it.
- Every other entry point is a standalone script configured by editing the `##########配置区域##########` (config region) block at the top of the file:
  - `tag_down.py` — download by tag / advanced search ("swiss army knife": most requests the main flow can't handle are solved via its `_filter`, see README)
  - `text_down.py` — text-only tweets per user
  - `reply_down.py` — replies to given tweets/users. Its main loop runs at module top level (no `__main__` guard), but it imports helpers from `tag_down`, which is guarded.
  - `profile_down.py` — avatar/banner/bio per user
- `exiftool` (external binary) is needed at runtime by `main.py` for mp4 metadata; images use piexif.
- No tests and no linter are configured.
- API rate limits: each account has a daily API-call cap (`Rate limit exceeded`). Including retweets costs ~1 call per 19 tweets; media downloads themselves don't count.

## Architecture

### Shared modules (used by main.py; other scripts are mostly self-contained)

- `user_info.py` — `User_info` class (screen_name, rest_id, cursor, counters)
- `csv_gen.py` / `md_gen.py` — per-user CSV / Markdown stats writers; other scripts define their own local `csv_gen` variants with different columns
- `cache_gen.py` — dedup set for `down_log` mode, seeded from `download_info.json`'s `user_media_url`
- `url_utils.py` — `quote_url()` escapes `{`/`}` in GraphQL URLs
- `transaction_generate.py` — generates the `x-client-transaction-id` header via the XClientTransaction lib; required by `tag_down.py`/`reply_down.py` (search & tweet-detail endpoints) but not currently by `main.py`/`text_down.py`. It occasionally fails (`获取数据失败`) — rerunning is the documented fix.

### API request pattern (common across scripts)

1. Headers: hardcoded public web Bearer token + user cookie (`auth_token=...; ct0=...;`); `x-csrf-token` is regex-extracted from the ct0 cookie.
2. GraphQL URLs are built by string concatenation (variables/features JSON inline), then passed through `quote_url()`.
3. Pagination via `cursor` values read from response entries (`cursor-bottom`). Response shapes differ per endpoint and between first/subsequent pages (`First_Page` flag in `main.py`).
4. Tweet timestamp is derived as `edit_control.editable_until_msecs - 3600000` (editable_until = creation + 1h).
5. Media downloads are async (`httpx.AsyncClient` gated by `asyncio.Semaphore(max_concurrent_requests)`, default 8) with retry loops; API timeline calls are synchronous `httpx.get`.

### main.py modes

`has_retweet` / `high_lights` / `likes` in settings.json are mutually exclusive tab selections that switch which GraphQL endpoint is called (UserTweets / UserHighlightsTweets / Likes vs. default UserMedia) and which response shape is parsed; `likes` reuses the retweet code path. `autoSync` narrows the time range by scanning existing output filenames.

### Output files

Media is saved as `md5(media_url).ext` in a per-user folder; creation dates are backdated to the tweet date (piexif for jpg, exiftool for mp4; PNG is converted to JPEG when `image_format` is `jpg`). CSV/MD reports are written to the same folder.

## CI

`.github/workflows/run.yml` — manual trigger (workflow_dispatch): downloads `download_info.json`, patches `settings.json`, runs `main.py`, rsyncs the `twitter/` output folder to a server, and reports `error_user` via `GITHUB_OUTPUT`.
