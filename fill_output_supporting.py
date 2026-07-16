#!/usr/bin/env python3
import csv, json, os
from concurrent.futures import ThreadPoolExecutor, as_completed
from extract_supporting import fetch

SRC = "Krakow_output.csv"
CACHE = "output_supporting_cache.json"

def main():
    with open(SRC, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.reader(f))

    cache = {}
    if os.path.exists(CACHE):
        with open(CACHE, encoding="utf-8") as f:
            cache = json.load(f)

    todo = []
    for r in rows:
        if len(r) < 3:
            continue
        url = r[-3]
        if "/supporting-record/" in url and not r[-2].strip() and not r[-1].strip():
            if url not in cache:
                todo.append(url)
    todo = list(dict.fromkeys(todo))
    print(f"{len(todo)} supporting-record URLs to fetch ({len(cache)} cached)", flush=True)

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
    for r in rows:
        if len(r) < 3:
            continue
        url = r[-3]
        if "/supporting-record/" in url and not r[-2].strip() and not r[-1].strip():
            b, d = cache.get(url, ("", ""))
            r[-2], r[-1] = b, d
            if b or d:
                filled += 1

    with open(SRC, "w", newline="", encoding="utf-8-sig") as f:
        csv.writer(f).writerows(rows)

    print(f"Filled dates into {filled} rows. Failures: {len(fails)}", flush=True)
    if fails:
        with open("failed_output_supporting.txt", "w") as f:
            f.write("\n".join(fails))

if __name__ == "__main__":
    main()
