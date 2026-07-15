#!/usr/bin/env python3
"""Normalize both date columns in Krakow_all.csv to full month names + 4-digit years.

Abbreviated cells like '7 Aug 51' are replaced with the authoritative full date
(e.g. '7 August 1951') looked up by the record's numeric ID in the caches.
Any cell whose ID isn't cached falls back to month-expansion + a year pivot and
is reported so it can be reviewed.
"""
import csv, re, json, datetime

SRC = "Krakow_all.csv"
ENC = "latin-1"
CACHES = ["dates_cache.json", "output_supporting_cache.json", "supporting_cache.json"]

MON_ABBR = {"jan": "January", "feb": "February", "mar": "March", "apr": "April",
            "may": "May", "jun": "June", "jul": "July", "aug": "August",
            "sep": "September", "oct": "October", "nov": "November", "dec": "December"}

ABBR_RE = re.compile(r"^(\d{1,2}) (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) (\d{2})$")
PIVOT = 25  # 2-digit year <= 25 -> 20xx, else 19xx

URLC = 5          # Billiongraves Link column (after leading ID column)
BI, DI = 6, 7     # Birth Date, Death Date columns


def rec_id(url):
    seg = url.strip().rstrip("/").split("/")[-1]
    seg = seg.split("?")[0]
    return seg if seg.isdigit() else None


def load_byid():
    byid = {}
    for fn in CACHES:
        try:
            data = json.load(open(fn, encoding="utf-8"))
        except FileNotFoundError:
            continue
        for u, v in data.items():
            i = rec_id(u)
            if i:
                byid.setdefault(i, v)  # first cache wins; they agree on shared ids
    return byid


def pivot_year(yy):
    n = int(yy)
    return 2000 + n if n <= PIVOT else 1900 + n


def main():
    byid = load_byid()
    rows = list(csv.reader(open(SRC, newline="", encoding=ENC)))

    from_cache = 0
    fallback = []  # (rownum, original, produced)
    for idx, r in enumerate(rows):
        if len(r) <= DI:
            continue
        iid = rec_id(r[URLC]) if len(r) > URLC else None
        cached = byid.get(iid)
        for ci in (BI, DI):
            cell = r[ci].strip()
            m = ABBR_RE.match(cell)
            if not m:
                continue
            # position 0 = birth (BI), 1 = death (DI)
            cval = cached[ci - BI] if cached else ""
            if cval:
                r[ci] = cval
                from_cache += 1
            else:
                d, mon, yy = m.groups()
                produced = f"{int(d)} {MON_ABBR[mon.lower()]} {pivot_year(yy)}"
                r[ci] = produced
                fallback.append((idx + 1, cell, produced))

    with open(SRC, "w", newline="", encoding=ENC) as f:
        csv.writer(f).writerows(rows)

    print(f"Normalized from authoritative cache: {from_cache}")
    print(f"Normalized by year-pivot fallback  : {len(fallback)}")
    for rownum, orig, prod in fallback[:40]:
        print(f"   row {rownum}: {orig!r} -> {prod!r}")
    if len(fallback) > 40:
        print(f"   ... and {len(fallback) - 40} more")


if __name__ == "__main__":
    main()
