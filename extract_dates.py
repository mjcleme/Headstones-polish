#!/usr/bin/env python3
import csv, re, json, os, sys, time
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

SRC = "Krakow_output.csv"
OUT = "Krakow_output_with_dates.csv"
CACHE = "dates_cache.json"

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")
HEADERS = {
    "User-Agent": UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

birth_re = re.compile(r'"birthDate":"([^"]*)"')
death_re = re.compile(r'"deathDate":"([^"]*)"')

def norm(d):
    """Normalize a Y-M-D (not zero-padded) date to YYYY-MM-DD; keep partials."""
    if not d:
        return ""
    parts = d.split("-")
    try:
        if len(parts) == 3:
            y, m, day = parts
            return f"{int(y):04d}-{int(m):02d}-{int(day):02d}"
        if len(parts) == 2:
            y, m = parts
            return f"{int(y):04d}-{int(m):02d}"
        return f"{int(parts[0]):04d}"
    except ValueError:
        return d

def fetch(url):
    for attempt in range(3):
        try:
            r = requests.get(url, headers=HEADERS, timeout=30)
            if r.status_code == 200 and "Web Application Firewall" not in r.text:
                b = birth_re.search(r.text)
                d = death_re.search(r.text)
                return norm(b.group(1) if b else ""), norm(d.group(1) if d else "")
            time.sleep(1.5 * (attempt + 1))
        except Exception:
            time.sleep(1.5 * (attempt + 1))
    return None  # signal failure

def main():
    with open(SRC, newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))

    cache = {}
    if os.path.exists(CACHE):
        with open(CACHE, encoding="utf-8") as f:
            cache = json.load(f)

    # collect headstone URLs needing fetch
    todo = []
    for row in rows:
        url = row[-1] if row else ""
        if "/headstone/" in url and url not in cache:
            todo.append(url)
    todo = list(dict.fromkeys(todo))
    print(f"{len(todo)} URLs to fetch ({len(cache)} cached)", flush=True)

    done = 0
    fails = []
    with ThreadPoolExecutor(max_workers=10) as ex:
        futs = {ex.submit(fetch, u): u for u in todo}
        for fut in as_completed(futs):
            u = futs[fut]
            res = fut.result()
            if res is None:
                fails.append(u)
            else:
                cache[u] = res
            done += 1
            if done % 50 == 0:
                with open(CACHE, "w", encoding="utf-8") as f:
                    json.dump(cache, f)
                print(f"  {done}/{len(todo)} done, {len(fails)} fails", flush=True)

    with open(CACHE, "w", encoding="utf-8") as f:
        json.dump(cache, f)

    # write output with two extra columns
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        for row in rows:
            url = row[-1] if row else ""
            b, d = cache.get(url, ("", ""))
            w.writerow(row + [b, d])

    print(f"Wrote {OUT}. Fetched {len(cache)} records. Failures: {len(fails)}", flush=True)
    if fails:
        with open("failed_urls.txt", "w") as f:
            f.write("\n".join(fails))
        print("Failures written to failed_urls.txt", flush=True)

if __name__ == "__main__":
    main()
