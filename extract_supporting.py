#!/usr/bin/env python3
import re, requests, time

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")
HEADERS = {
    "User-Agent": UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

MONTHS = {
    "jan": "January", "feb": "February", "mar": "March", "apr": "April",
    "may": "May", "jun": "June", "jul": "July", "aug": "August",
    "sep": "September", "sept": "September", "oct": "October",
    "nov": "November", "dec": "December",
}

bd_re = re.compile(r'"birth_date":"([^"]*)"')
dd_re = re.compile(r'"death_date":"([^"]*)"')

def fmt(v):
    """Normalize 'Not Available' -> '', '9 Jun 1953' -> '9 June 1953', keep years."""
    if not v or v.strip().lower() in ("not available", "unknown", "null"):
        return ""
    v = v.strip()
    parts = v.split()
    out = []
    for p in parts:
        key = p.lower().rstrip(".")
        out.append(MONTHS.get(key, p))
    return " ".join(out)

def fetch(url):
    """Return (birth, death) for the PRIMARY record (first pair in HTML), or None on failure."""
    for attempt in range(3):
        try:
            r = requests.get(url, headers=HEADERS, timeout=30)
            if r.status_code == 200 and "Web Application Firewall" not in r.text:
                b = bd_re.search(r.text)
                d = dd_re.search(r.text)
                return fmt(b.group(1) if b else ""), fmt(d.group(1) if d else "")
            if r.status_code in (404, 410):
                return ("", "")  # gone / not found -> no data, don't retry
            time.sleep(1.5 * (attempt + 1))
        except Exception:
            time.sleep(1.5 * (attempt + 1))
    return None

if __name__ == "__main__":
    tests = [
        "https://map.billiongraves.com/supporting-record/Salomea-Skoczek/100012999",
        "https://map.billiongraves.com/supporting-record/Ludwik-Skoczek/100013000",
        "https://map.billiongraves.com/supporting-record/Zygmunt-Michalowski/100013013",
        "https://map.billiongraves.com/supporting-record/Maria-Michalowski/100013014",
        "https://map.billiongraves.com/supporting-record/Andrzej-Marekowski/100013101",
    ]
    for u in tests:
        print(u.split("/")[-2], "->", fetch(u))
