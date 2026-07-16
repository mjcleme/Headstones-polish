#!/usr/bin/env python3
"""Repair Polish letters that the SOURCE data lost as literal '?' in the Given Name
and Surname columns of Krakow_all.csv.

The correct spelling survives in the Billiongraves URL (percent-encoded UTF-8), e.g.
  surname '?uczak'  <-  .../Zofia-%C5%81uczak/...  =>  Łuczak
For each name token containing '?', we align it against the URL's decoded name tokens
and substitute the recovered Polish letter (in the right case). Repaired letters are
written as UTF-8 bytes so they match the file's other (UTF-8-encoded) names and render
correctly in a UTF-8 viewer. The file is otherwise left byte-for-byte unchanged and
still round-trips as latin-1 for the helper scripts.
"""
import csv, re
from urllib.parse import unquote

SRC = "Krakow_all.csv"
ENC = "utf-8-sig"
GIVEN, SUR, URL = 1, 2, 5

def url_tokens(url):
    p = url.split("?")[0].rstrip("/")
    seg = p.split("/")
    name = seg[-2] if len(seg) >= 2 and seg[-1].isdigit() else seg[-1]
    # some URLs are double percent-encoded (%25C5%2582); unquote until stable
    decoded = name
    for _ in range(3):
        nxt = unquote(decoded, encoding="utf-8", errors="replace")
        if nxt == decoded:
            break
        decoded = nxt
    return [t for t in re.split(r"[-\s]+", decoded) if t]

def repair_token(tok, slug_tokens, unresolved):
    if "?" not in tok:
        return tok
    # build a same-length, case-insensitive pattern with '?' as wildcard
    pat = re.compile("^" + "".join("(.)" if c == "?" else re.escape(c) for c in tok) + "$",
                     re.IGNORECASE)
    for st in slug_tokens:
        if len(st) != len(tok):
            continue
        m = pat.match(st)
        if not m:
            continue
        # substitute each '?' with the recovered letter, matching the token's case
        all_upper = tok.replace("?", "").isupper()
        out, gi = [], 0
        for i, c in enumerate(tok):
            if c == "?":
                ch = m.group(gi + 1); gi += 1
                ch = ch.upper() if (i == 0 or all_upper) else ch.lower()
                out.append(ch)
            else:
                out.append(c)
        return "".join(out)
    unresolved.append(tok)
    return tok

def repair_cell(cell, slug_tokens, unresolved):
    if "?" not in cell:
        return cell
    return re.sub(r"[^\s()]+",
                  lambda mm: repair_token(mm.group(0), slug_tokens, unresolved),
                  cell)

def main():
    rows = list(csv.reader(open(SRC, newline="", encoding=ENC)))
    fixed_cells = 0
    unresolved = []
    for r in rows[1:]:
        if len(r) <= URL or ("?" not in r[GIVEN] and "?" not in r[SUR]):
            continue
        slug = url_tokens(r[URL])
        for ci in (GIVEN, SUR):
            if "?" in r[ci]:
                new = repair_cell(r[ci], slug, unresolved)
                if new != r[ci]:
                    r[ci] = new
                    fixed_cells += 1
    with open(SRC, "w", newline="", encoding=ENC) as f:
        csv.writer(f).writerows(rows)
    print(f"Repaired {fixed_cells} name cells. Unresolved '?' tokens: {len(unresolved)}")
    for t in unresolved:
        print("   could not resolve:", repr(t))

if __name__ == "__main__":
    main()
