"""Turn raw numbers and headlines into a short written brief."""

import json
import logging

import config

log = logging.getLogger(__name__)

SYSTEM = """You write a daily energy industry brief for an engineer in Houston who \
wants to stay genuinely current on the sector — oil and gas, power and \
renewables, and the technology in between.

What he wants to know is what is new. New projects and final investment \
decisions, initiatives and partnerships, technology and breakthroughs, \
policy and regulatory shifts, notable operational news, and who is building \
what where. Prices are context, not the point.

He can already see the raw numbers, so do not just restate them. Give the \
price move a sentence or two of explanation, then spend the rest of your \
attention on what is actually happening in the industry.

Prefer concrete specifics over general statements: name the companies, the \
projects, the capacities, the locations. A reader should finish knowing \
things, not impressions.

Write plainly. No hype, no filler, no hedging language like "it is worth \
noting". If the day is quiet, say so rather than inflating it.

Return ONLY a JSON object, no markdown fences and no preamble:
{
  "headline": "one sentence, under 15 words, on the most significant development",
  "market": "2-3 sentences on prices, storage, and grid conditions",
  "stories": ["3-5 bullets, one sentence each, on the developments that matter — projects, deals, technology, policy"],
  "talking_points": ["2-3 threads worth following, each saying why it matters beyond today"]
}"""


def _fallback(market_data, headlines):
    """Used when the API is unavailable, so the digest still ships."""
    return {
        "headline": "Summary unavailable — raw data below.",
        "market": f"{len(market_data)} series and {len(headlines)} headlines collected.",
        "stories": [h["title"] for h in headlines[:4]],
        "talking_points": [],
    }


def _format_market(market_data):
    lines = []
    for row in market_data:
        change = (
            f"{row['change']:+.{row['decimals']}f}"
            if row["change"] is not None
            else "n/a"
        )
        lines.append(
            f"- {row['label']}: {row['value']:.{row['decimals']}f} {row['unit']} "
            f"(prev period {change}) as of {row['period']}"
        )
    return "\n".join(lines) or "- no market data available"


def _format_ercot(ercot):
    if not ercot:
        return "- no ERCOT data available"
    lines = []
    if ercot.get("load_mw"):
        lines.append(f"- ERCOT load: {ercot['load_mw']:,.0f} MW")
    mix = ercot.get("fuel_mix")
    if mix:
        top = ", ".join(
            f"{f['fuel']} {f['share']:.0f}%" for f in mix["breakdown"][:5] if f["mw"] > 0
        )
        lines.append(f"- ERCOT fuel mix: {top}")
    return "\n".join(lines) or "- no ERCOT data available"


def _format_news(headlines):
    return "\n".join(
        f"- [{h['source']}] {h['title']}: {h['summary'][:200]}" for h in headlines[:30]
    ) or "- no headlines collected"


def write_brief(market_data, ercot, headlines):
    if not config.ANTHROPIC_API_KEY:
        log.warning("ANTHROPIC_API_KEY not set — using fallback brief")
        return _fallback(market_data, headlines)

    try:
        import anthropic
    except ImportError:
        log.warning("anthropic package not installed — using fallback brief")
        return _fallback(market_data, headlines)

    prompt = f"""MARKET DATA
{_format_market(market_data)}

GRID
{_format_ercot(ercot)}

HEADLINES (last 48h)
{_format_news(headlines)}"""

    try:
        client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        response = client.messages.create(
            model=config.ANTHROPIC_MODEL,
            max_tokens=1500,
            system=SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )
        text = "".join(
            block.text for block in response.content if block.type == "text"
        ).strip()
        text = text.removeprefix("```json").removeprefix("```").removesuffix("```")
        return json.loads(text.strip())
    except Exception as exc:
        log.warning("Brief generation failed: %s", exc)
        return _fallback(market_data, headlines)
