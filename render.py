"""Render the digest to a single HTML document.

The same markup is emailed and published, so it stays deliberately
conservative: no external fonts, no flexbox, no CSS variables. Email
clients mangle all three. Styling lives in a <style> block with inline
fallbacks on anything that carries meaning (the direction of a change).
"""

from datetime import datetime
from html import escape

PAPER = "#f4f5f2"
INK = "#17201b"
MUTED = "#5c6660"
RULE = "#cdd3cc"
UP = "#1b6b41"
DOWN = "#9e3223"

SERIF = "Georgia, 'Iowan Old Style', 'Times New Roman', serif"
SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"

CSS = f"""
body {{
  margin: 0;
  padding: 24px 16px 64px;
  background: {PAPER};
  color: {INK};
  font-family: {SANS};
  -webkit-text-size-adjust: 100%;
}}
.wrap {{ max-width: 640px; margin: 0 auto; }}

.masthead {{ border-bottom: 2px solid {INK}; padding-bottom: 10px; margin-bottom: 28px; }}
.masthead h1 {{
  font-family: {SERIF};
  font-size: 26px; font-weight: normal; letter-spacing: -0.01em;
  margin: 0 0 4px;
}}
.masthead .date {{ font-size: 13px; color: {MUTED}; margin: 0; }}

.lede {{
  font-family: {SERIF};
  font-size: 21px; line-height: 1.35; margin: 0 0 14px;
}}
.brief {{
  font-family: {SERIF};
  font-size: 16px; line-height: 1.6; color: {INK};
  margin: 0 0 34px;
}}

h2 {{
  font-family: {SANS};
  font-size: 13px; font-weight: 600; color: {MUTED};
  margin: 0 0 12px; padding-bottom: 6px;
  border-bottom: 1px solid {RULE};
}}
section {{ margin-bottom: 34px; }}

table.data {{ width: 100%; border-collapse: collapse; }}
table.data td {{
  padding: 9px 0; border-bottom: 1px solid {RULE};
  font-size: 14px; vertical-align: baseline;
}}
table.data td.label {{ color: {INK}; }}
table.data td.period {{ color: {MUTED}; font-size: 12px; }}
table.data td.value {{
  text-align: right; font-variant-numeric: tabular-nums;
  font-feature-settings: "tnum"; white-space: nowrap;
}}
table.data td.delta {{
  text-align: right; font-variant-numeric: tabular-nums;
  font-size: 13px; white-space: nowrap; padding-left: 14px;
}}

ul {{ margin: 0; padding-left: 20px; }}
li {{ font-size: 15px; line-height: 1.55; margin-bottom: 9px; }}

.points li {{ font-family: {SERIF}; font-size: 15.5px; line-height: 1.6; }}

.story {{ margin-bottom: 16px; }}
.story a {{ color: {INK}; text-decoration: none; border-bottom: 1px solid {RULE}; font-size: 15px; line-height: 1.45; }}
.story .src {{ display: block; font-size: 12px; color: {MUTED}; margin-top: 3px; }}

.mix {{ font-size: 14px; line-height: 1.7; margin: 0; }}
.mix .fuel {{ color: {MUTED}; }}

footer {{ border-top: 1px solid {RULE}; padding-top: 12px; font-size: 12px; color: {MUTED}; }}
a:focus {{ outline: 2px solid {INK}; outline-offset: 2px; }}
"""


def _fmt(value, decimals):
    return f"{value:,.{decimals}f}"


def _delta_cell(row):
    if row["change"] is None:
        return f'<td class="delta" style="color:{MUTED}">—</td>'
    color = UP if row["change"] > 0 else DOWN if row["change"] < 0 else MUTED
    text = f"{row['change']:+,.{row['decimals']}f}"
    if row["pct_change"] is not None:
        text += f"  {row['pct_change']:+.1f}%"
    return f'<td class="delta" style="color:{color}">{escape(text)}</td>'


def _market_section(market_data):
    if not market_data:
        return ""
    rows = []
    for row in market_data:
        rows.append(
            "<tr>"
            f'<td class="label">{escape(row["label"])}'
            f'<div class="period" style="color:{MUTED};font-size:12px">{escape(str(row["period"]))}</div></td>'
            f'<td class="value">{_fmt(row["value"], row["decimals"])} '
            f'<span style="color:{MUTED};font-size:12px">{escape(row["unit"])}</span></td>'
            f"{_delta_cell(row)}"
            "</tr>"
        )
    return f"""<section>
  <h2>Prices and inventories</h2>
  <table class="data">{''.join(rows)}</table>
</section>"""


def _ercot_section(ercot):
    if not ercot:
        return ""
    parts = []
    if ercot.get("load_mw"):
        parts.append(
            f'<p class="mix">Current load '
            f'<strong>{ercot["load_mw"]:,.0f} MW</strong></p>'
        )
    mix = ercot.get("fuel_mix")
    if mix:
        items = "<br>".join(
            f'<span class="fuel" style="color:{MUTED}">{escape(f["fuel"])}</span> '
            f'{f["share"]:.1f}%'
            for f in mix["breakdown"][:6]
            if f["mw"] > 0
        )
        parts.append(f'<p class="mix">{items}</p>')
    if not parts:
        return ""
    return f'<section><h2>ERCOT right now</h2>{"".join(parts)}</section>'


def _stories_section(brief, headlines):
    blocks = []
    if brief.get("stories"):
        bullets = "".join(f"<li>{escape(s)}</li>" for s in brief["stories"])
        blocks.append(f"<section><h2>What matters today</h2><ul>{bullets}</ul></section>")

    if brief.get("talking_points"):
        bullets = "".join(f"<li>{escape(p)}</li>" for p in brief["talking_points"])
        blocks.append(
            f'<section><h2>Threads worth following</h2>'
            f'<ul class="points">{bullets}</ul></section>'
        )

    if headlines:
        stories = "".join(
            f'<div class="story">'
            f'<a href="{escape(h["url"])}">{escape(h["title"])}</a>'
            f'<span class="src">{escape(h["source"])}</span>'
            f"</div>"
            for h in headlines[:20]
        )
        blocks.append(f"<section><h2>Everything else</h2>{stories}</section>")

    return "".join(blocks)


def render(brief, market_data, ercot, headlines, now=None):
    now = now or datetime.now()
    date_line = now.strftime("%A, %B %-d, %Y")

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Energy digest — {escape(date_line)}</title>
<style>{CSS}</style>
</head>
<body>
<div class="wrap">

  <div class="masthead">
    <h1>The Morning Barrel</h1>
    <p class="date">{escape(date_line)} — Houston</p>
  </div>

  <p class="lede">{escape(brief.get("headline", ""))}</p>
  <p class="brief">{escape(brief.get("market", ""))}</p>

  {_market_section(market_data)}
  {_ercot_section(ercot)}
  {_stories_section(brief, headlines)}

  <footer>
    Data from the U.S. Energy Information Administration and ERCOT.
    Summary written by Claude, so check anything before you repeat it.
  </footer>

</div>
</body>
</html>"""
