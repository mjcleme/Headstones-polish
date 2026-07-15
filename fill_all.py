#!/usr/bin/env python3
import csv, json, os, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from extract_supporting import fetch

SRC = "Krakow_all.csv"
CACHE = "supporting_cache.json"
ENC = "latin-1"          # lossless round-trip for this file's bytes
MAX_ROW = 302            # process data rows 1..302 only
URLC = 5                 # Billiongraves Link column index (after leading ID column)
BI, DI = 6, 7            # Birth Date, Death Date column indexes

def main():
    with open(SRC, newline="", encoding=ENC) as f:
        rows = list(csv.reader(f))

    cache = {}
    if os.path.exists(CACHE):
        with open(CACHE, encoding="utf-8") as f:
            cache = json.load(f)

    todo = []
    for idx in range(1, min(MAX_ROW, len(rows) - 1) + 1):
        r = rows[idx]
        if len(r) <= DI:
            continue
        if r[BI].strip() or r[DI].strip():
            continue  # already has a date -> skip
        url = r[URLC].strip()
        if "billiongraves.com" in url and url not in cache:
            todo.append(url)
    todo = list(dict.fromkeys(todo))
    print(f"{len(todo)} URLs to fetch ({len(cache)} cached)", flush=True)

    done, fails = 0, []
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
            if done % 40 == 0:
                with open(CACHE, "w", encoding="utf-8") as f:
                    json.dump(cache, f)
                print(f"  {done}/{len(todo)} done, {len(fails)} fails", flush=True)

    with open(CACHE, "w", encoding="utf-8") as f:
        json.dump(cache, f)

    filled = 0
    for idx in range(1, min(MAX_ROW, len(rows) - 1) + 1):
        r = rows[idx]
        if len(r) <= DI:
            continue
        if r[BI].strip() or r[DI].strip():
            continue
        url = r[URLC].strip()
        if url in cache:
            b, d = cache[url]
            r[BI], r[DI] = b, d
            if b or d:
                filled += 1

    with open(SRC, "w", newline="", encoding=ENC) as f:
        csv.writer(f).writerows(rows)

    print(f"Filled dates into {filled} rows. Failures: {len(fails)}", flush=True)
    if fails:
        with open("failed_supporting.txt", "w") as f:
            f.write("\n".join(fails))

if __name__ == "__main__":
    main()
