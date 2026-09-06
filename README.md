# The Morning Barrel

A daily energy market digest. Pulls prices and inventories from the EIA, grid
conditions from ERCOT, and headlines from a set of RSS feeds, then has Claude
write a short brief over the top of it. Emails you the result and publishes the
same page to GitHub Pages.

Runs on GitHub Actions, so there's no server and no hosting cost.

## Setup

**1. Get the keys.**

- EIA: free, instant — https://www.eia.gov/opendata/register.php
- Anthropic: https://console.anthropic.com
- Gmail: turn on 2FA, then create an App Password. Your normal password won't
  work for SMTP.

**2. Run it locally first.**

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env      # fill in your keys
python check_sources.py   # tells you what's alive and what needs fixing
python main.py --no-email # writes docs/index.html
open docs/index.html
```

**3. Put it on GitHub.**

Push the repo, then add each value from your `.env` under
Settings → Secrets and variables → Actions.

Turn on Pages under Settings → Pages, source `main` branch, folder `/docs`.
Your digest lives at `https://<you>.github.io/<repo>/`.

The workflow runs weekdays at 11:00 UTC and commits the new page back to the
repo. You can also trigger it by hand from the Actions tab.

## Run check_sources.py before you trust it

Two things in `config.py` are known to drift, and I'd verify both on your first
run rather than assume they work:

- **EIA series IDs.** The v2 API is stable but individual series get retired.
  If one fails, look up the replacement at
  https://www.eia.gov/opendata/browser/ and update the `series` field.
- **Publisher RSS URLs.** Sites move their feeds. The Google News entries at
  the bottom of `FEEDS` are there as the safety net — those always resolve, so
  the digest is never empty even if every direct feed breaks.

`check_sources.py` checks all of them and names anything broken.

## Files

| | |
|---|---|
| `config.py` | Series, feeds, and settings. The only file you'll edit often. |
| `sources.py` | EIA API v2 and ERCOT via `gridstatus`. |
| `news.py` | RSS collection, age filtering, dedup. |
| `brief.py` | The Claude prompt. Worth tuning as you learn what you want. |
| `render.py` | HTML for both the email and the web page. |
| `mailer.py` | SMTP delivery. |
| `check_sources.py` | Diagnostic. |

## Notes

The HTML is deliberately plain — no external fonts, no flexbox, no CSS
variables — because email clients mangle all three. If you only ever read the
web version, `render.py` can get much more ambitious.

`docs/latest.json` holds the raw payload from each run, so if you later want to
chart price history the data is already accumulating in `docs/archive/`.

## Things worth adding later

- Weight the feeds toward whatever you're interviewing for that week.
- Save the `talking_points` to a running file instead of only emailing them.
- Add EIA's Short-Term Energy Outlook (`steo` route) for forward projections.
- A second cron on Wednesday and Thursday at 10:35 ET, right after the
  petroleum status and gas storage reports land.
