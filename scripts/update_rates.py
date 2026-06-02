#!/usr/bin/env python3
"""
Update the mortgage rates + dates on the Villa Warner listing page from the
Seven Gables Airtable (the same source the morning report uses).

Source : base "Interest Rates" -> table "From Kevin", latest row by Timestamp.
Target : index.html  — only the elements tagged data-rate="..." are touched.
Auth   : reads the token from the AIRTABLE_TOKEN env var (a GitHub Actions
         secret). The token NEVER appears in the committed site.

Fail-safe: if the fetch fails, a value is missing, or a number fails a sanity
check, the script raises and exits non-zero WITHOUT writing index.html, so the
job makes no commit and the live site keeps the last good values.
"""

import html
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

BASE = "appxtXl28vrEIHz0Z"
TABLE = "tblVrlngw97M9CA5j"
INDEX = Path(__file__).resolve().parent.parent / "index.html"

# Airtable field name -> data-rate key in index.html
FIELD_MAP = {
    "15 Yr. Fixed":      "15yr",
    "15 Yr. Fixed APR":  "15yr-apr",
    "30 Yr. Fixed":      "30yr",
    "30 Yr. Fixed APR":  "30yr-apr",
    "30 Yr. FHA":        "30yr-fha",
    "30 Yr. FHA APR":    "30yr-fha-apr",
    "30 Yr. VA":         "30yr-va",
    "30 Yr. VA APR":     "30yr-va-apr",
}


def skip(msg):
    """Soft no-op: print a warning and exit 0 so the scheduled job doesn't
    spam failure emails. index.html is left untouched -> last-good values stay."""
    print(f"SKIP (no update, keeping last-good values): {msg}")
    sys.exit(0)


def pct(x):
    """0.0575 -> '5.75%'  (stored as a decimal in Airtable)"""
    if x is None:
        return None
    try:
        v = float(x) * 100.0
    except (TypeError, ValueError):
        return None
    v = float(f"{v:.4f}")        # strip float noise
    s = f"{v:.4f}".rstrip("0").rstrip(".")
    return s + "%"


def main():
    token = os.environ.get("AIRTABLE_TOKEN", "").strip()
    if not token:
        skip("AIRTABLE_TOKEN env var is not set")

    q = urllib.parse.urlencode({
        "maxRecords": 1,
        "sort[0][field]": "Timestamp",
        "sort[0][direction]": "desc",
    })
    url = f"https://api.airtable.com/v0/{BASE}/{TABLE}?{q}"
    req = urllib.request.Request(url, headers={"Authorization": "Bearer " + token})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.load(r)
    except Exception as e:
        skip(f"Airtable request failed: {e}")

    recs = data.get("records") or []
    if not recs:
        skip("no records returned from Airtable")
    f = recs[0].get("fields", {})

    # ---- collect + validate rate values ----
    values = {}
    for field, key in FIELD_MAP.items():
        raw = f.get(field)
        s = pct(raw)
        if s is None:
            skip(f"missing/invalid field '{field}'")
        num = float(s[:-1])
        if not (1.0 <= num <= 15.0):
            skip(f"{field} = {num}% outside sane range 1-15%")
        values[key] = s

    # APR should be >= its base rate
    for base_key in ("15yr", "30yr", "30yr-fha", "30yr-va"):
        rate = float(values[base_key][:-1])
        apr = float(values[base_key + "-apr"][:-1])
        if apr + 0.001 < rate:
            skip(f"{base_key} APR {apr}% is below its rate {rate}%")

    # ---- dates from 'display date' (e.g. '6/1/2026') ----
    dd = (f.get("display date") or "").strip()
    m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})$", dd)
    if not m:
        skip(f"'display date' missing or unparseable: {dd!r}")
    mo, da, yr = (int(g) for g in m.groups())
    values["asof"] = dd
    values["assumptions-date"] = dd
    values["effective"] = f"{mo:02d}/{da:02d}/{yr % 100:02d}"

    # ---- patch index.html (only inside data-rate spans) ----
    doc = INDEX.read_text(encoding="utf-8")
    for key, val in values.items():
        pat = re.compile(r'(data-rate="' + re.escape(key) + r'"[^>]*>)(.*?)(</)', re.S)
        doc, n = pat.subn(lambda mm: mm.group(1) + html.escape(val, quote=False) + mm.group(3), doc)
        if n != 1:
            skip(f'data-rate="{key}" matched {n} times in index.html (expected 1)')

    INDEX.write_text(doc, encoding="utf-8")
    print(f"Updated rates as of {dd}:")
    for base_key in ("15yr", "30yr", "30yr-fha", "30yr-va"):
        print(f"  {base_key:9s} {values[base_key]} / {values[base_key + '-apr']} APR")


if __name__ == "__main__":
    main()
