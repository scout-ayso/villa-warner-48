#!/usr/bin/env python3
"""
Update the mortgage rates, dates, and rate-assumptions text on the Villa Warner
listing page from the Seven Gables morning report.

Source : https://morningreport.7gre.me/  (public, server-rendered HTML)
Target : index.html  — only the elements tagged data-rate="..." are touched.

Fail-safe by design: if the page can't be fetched, a value is missing, or any
number fails a sanity check, the script raises and exits non-zero WITHOUT
writing index.html. The GitHub Actions job then makes no commit, so the live
site simply keeps yesterday's good values (and emails you about the failed run).
"""

import html
import re
import sys
import urllib.request
from datetime import date, datetime
from pathlib import Path

try:
    from zoneinfo import ZoneInfo
    def pacific_today():
        return datetime.now(ZoneInfo("America/Los_Angeles")).date()
except Exception:  # tzdata missing — at the ~17-18h UTC run times, UTC date == Pacific date
    def pacific_today():
        return date.today()

SOURCE_URL = "https://morningreport.7gre.me/"
INDEX = Path(__file__).resolve().parent.parent / "index.html"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36")


def fail(msg):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def fetch_text(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        raw = r.read().decode("utf-8", "replace")
    # strip script/style, then all tags, then unescape + collapse whitespace
    t = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", raw, flags=re.S | re.I)
    t = re.sub(r"<[^>]+>", " ", t)
    t = html.unescape(t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def grab_rate(text, label):
    """label e.g. '15 Yr. Fixed'  ->  ('5.75', '5.829')"""
    m = re.search(re.escape(label) + r"\s*([0-9]+(?:\.[0-9]+)?)%\s*\|\s*"
                  r"([0-9]+(?:\.[0-9]+)?)%\s*APR", text)
    if not m:
        fail(f"could not find rate for '{label}'")
    return m.group(1), m.group(2)


def main():
    text = fetch_text(SOURCE_URL)

    rates = {
        "15yr":     grab_rate(text, "15 Yr. Fixed"),
        "30yr":     grab_rate(text, "30 Yr. Fixed"),
        "30yr-fha": grab_rate(text, "30 Yr. FHA"),
        "30yr-va":  grab_rate(text, "30 Yr. VA"),
    }

    # effective / as-of date
    dm = re.search(r"as of (\d{1,2})/(\d{1,2})/(\d{4})", text)
    if not dm:
        fail("could not find an 'as of M/D/YYYY' date")
    mo, da, yr = (int(x) for x in dm.groups())

    # rate-assumptions paragraph
    am = re.search(r"(Today.{0,3}s conforming 15 .*?subject to change without notice\.)",
                   text)
    if not am:
        fail("could not find the rate-assumptions paragraph")
    assumptions = am.group(1).strip()

    # ---- sanity checks (fail-safe) ----
    try:
        rep_date = date(yr, mo, da)
    except ValueError:
        fail(f"invalid report date {mo}/{da}/{yr}")

    # Only publish when the report is showing TODAY's date (Pacific). The schedule
    # fires at the PST and PDT equivalents of 10:31am; in the off-season one of
    # those is an hour early, so the report may still show an older date — in that
    # case skip cleanly (exit 0, no commit, no alarm) and let the on-time run do it.
    today = pacific_today()
    delta = (today - rep_date).days
    if delta < 0:
        fail(f"report date {rep_date} is in the future vs Pacific today {today}")
    if 1 <= delta <= 3:
        print(f"Report still shows {rep_date}; Pacific today is {today}. "
              f"Not posted yet — skipping with no changes.")
        sys.exit(0)
    if delta > 3:
        fail(f"report date {rep_date} is {delta} days stale vs {today}")

    for key, (rate, apr) in rates.items():
        rf, af = float(rate), float(apr)
        if not (1.0 <= rf <= 15.0):
            fail(f"{key} rate {rf}% outside sane range 1-15%")
        if not (1.0 <= af <= 15.0):
            fail(f"{key} APR {af}% outside sane range 1-15%")
        if af + 0.001 < rf:
            fail(f"{key} APR {af}% is below its rate {rf}%")
    if len(assumptions) < 120 or "$" not in assumptions:
        fail("assumptions paragraph looks too short / malformed")

    # ---- build the replacement values keyed by data-rate attribute ----
    date_long = f"{mo}/{da}/{yr}"             # 6/1/2026
    date_short = f"{mo:02d}/{da:02d}/{yr % 100:02d}"  # 06/01/26
    values = {
        "asof": date_long,
        "effective": date_short,
        "assumptions": html.escape(assumptions, quote=False),  # escapes & < >
    }
    for key, (rate, apr) in rates.items():
        values[key] = f"{rate}%"
        values[f"{key}-apr"] = f"{apr}%"

    # ---- patch index.html (only inside data-rate spans) ----
    doc = INDEX.read_text(encoding="utf-8")
    for key, val in values.items():
        pat = re.compile(r'(data-rate="' + re.escape(key) + r'"[^>]*>)(.*?)(</)',
                         flags=re.S)
        doc, n = pat.subn(lambda m: m.group(1) + val + m.group(3), doc)
        if n != 1:
            fail(f'data-rate="{key}" matched {n} times in index.html (expected 1)')

    INDEX.write_text(doc, encoding="utf-8")
    print(f"Updated rates as of {date_long}:")
    for key, (rate, apr) in rates.items():
        print(f"  {key:9s} {rate}% / {apr}% APR")


if __name__ == "__main__":
    main()
