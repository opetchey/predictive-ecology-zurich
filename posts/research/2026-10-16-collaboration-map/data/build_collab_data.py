#!/usr/bin/env python3
"""
Build the data behind the collaboration-map post.

Two steps, both standard library only:

  1. fetch  - download Owen's works and his co-authors' institutions from
              OpenAlex (https://openalex.org) into data/openalex_raw.json
  2. build  - turn that raw snapshot into data/collaborations.json, the
              compact file the map reads

Usage (run from this post's folder or anywhere):

  python3 data/build_collab_data.py            # fetch + build
  python3 data/build_collab_data.py build      # rebuild from the existing raw snapshot

The site build never runs this script: the committed JSON is a snapshot,
so rendering the website needs no network. Re-run it when you want to
refresh the map, then commit both JSON files.

OpenAlex now asks for a (free) API key for heavier use. Without one this
script still works because it avoids cursor paging (it splits requests by
publication year so each request returns <= 200 works). If you have a key,
set it in the environment: OPENALEX_API_KEY=... python3 data/build_collab_data.py
"""

import json
import os
import re
import sys
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

# --- configuration ---------------------------------------------------------

AUTHOR_ID = "A5028533498"            # Owen L. Petchey in OpenAlex
ORCID = "0000-0002-7724-1633"
MAILTO = "owen.petchey@uzh.ch"

# Work types that count as a publication. Datasets and "other" mostly
# duplicate a paper; preprints are kept only when no published version
# with the same title exists (see dedupe below).
KEEP_TYPES = {"article", "review", "book", "book-chapter", "editorial", "letter", "preprint"}
TYPE_RANK = {"article": 0, "review": 0, "book": 0, "book-chapter": 1,
             "letter": 2, "editorial": 2, "preprint": 9}

# An institution counts as one of Owen's "home" institutions (shown with a
# distinct style, and hideable) when he lists it on at least this many papers.
HOME_MIN_PAPERS = 20

# OpenAlex sometimes gives one author every institution on a paper (a
# misread affiliation list). An author's affiliations on a paper are
# ignored when they list more than MAX_AFFILIATIONS institutions, or when
# they hold more than MAX_SHARE of the paper's institutions and the paper
# has at least MIN_INSTITUTIONS_FOR_SHARE_RULE of them. The thresholds are
# deliberately loose: French researchers, for example, often legitimately
# list four or five partner institutions of one joint lab (CNRS, university,
# IRD, ...). Each build prints what it ignored, so the rule can be checked.
MAX_AFFILIATIONS = 6
MAX_SHARE = 0.75
MIN_INSTITUTIONS_FOR_SHARE_RULE = 6

HERE = Path(__file__).resolve().parent
RAW = HERE / "openalex_raw.json"
OUT = HERE / "collaborations.json"
API = "https://api.openalex.org"


# --- step 1: fetch ---------------------------------------------------------

def _get(path, **params):
    params.setdefault("mailto", MAILTO)
    key = os.environ.get("OPENALEX_API_KEY")
    if key:
        params["api_key"] = key
    url = f"{API}/{path}?{urllib.parse.urlencode(params, safe=':|,<>')}"
    with urllib.request.urlopen(url, timeout=60) as r:
        return json.load(r)


def fetch():
    flt = f"author.id:{AUTHOR_ID}"
    # Count works per year, then pack years into ranges of <= 200 works.
    years = _get("works", filter=flt, group_by="publication_year")["group_by"]
    counts = sorted((int(g["key"]), g["count"]) for g in years if g["key"].isdigit())
    ranges, cur, n = [], [], 0
    for y, c in counts:
        if cur and n + c > 200:
            ranges.append((cur[0], cur[-1]))
            cur, n = [], 0
        cur.append(y)
        n += c
    if cur:
        ranges.append((cur[0], cur[-1]))

    sel = "id,doi,display_name,publication_year,type,authorships,primary_location"
    works = []
    for lo, hi in ranges:
        d = _get("works", filter=f"{flt},publication_year:{lo}-{hi}",
                 select=sel, **{"per-page": 200})
        works.extend(d["results"])
        print(f"  {lo}-{hi}: {len(d['results'])} works")

    ids = sorted({i["id"].rsplit("/", 1)[-1]
                  for w in works for a in w["authorships"]
                  for i in (a.get("institutions") or []) if i.get("id")})
    insts = {}
    for k in range(0, len(ids), 50):
        d = _get("institutions", filter="openalex:" + "|".join(ids[k:k + 50]),
                 select="id,display_name,country_code,geo,type", **{"per-page": 50})
        for x in d["results"]:
            g = x.get("geo") or {}
            insts[x["id"].rsplit("/", 1)[-1]] = {
                "n": x["display_name"], "cc": x.get("country_code"),
                "city": g.get("city"), "country": g.get("country"),
                "lat": g.get("latitude"), "lng": g.get("longitude"), "t": x.get("type")}

    def short(w):
        src = (w.get("primary_location") or {}).get("source") or {}
        return {"id": w["id"].rsplit("/", 1)[-1],
                "doi": (w.get("doi") or "").replace("https://doi.org/", "") or None,
                "t": w["display_name"], "y": w["publication_year"], "ty": w["type"],
                "v": src.get("display_name"),
                "a": [[a["author"]["display_name"],
                       (a["author"].get("id") or "").rsplit("/", 1)[-1] or None,
                       [i["id"].rsplit("/", 1)[-1] for i in (a.get("institutions") or []) if i.get("id")]]
                      for a in w["authorships"]]}

    raw = {"meta": {"source": "OpenAlex API", "author": AUTHOR_ID, "orcid": ORCID,
                    "retrieved": datetime.now(timezone.utc).isoformat(timespec="seconds")},
           "institutions": insts, "works": [short(w) for w in works]}
    RAW.write_text(json.dumps(raw, ensure_ascii=False))
    print(f"Wrote {RAW.name}: {len(works)} works, {len(insts)} institutions")


# --- step 2: build ---------------------------------------------------------

def _norm(title):
    return re.sub(r"[^a-z0-9]", "", (title or "").lower())


def _clean_affiliations(work, dropped):
    """Blank out implausible affiliation lists (see MAX_AFFILIATIONS)."""
    on_paper = {i for a in work["a"] for i in a[2]}
    cleaned = []
    for name, aid, iids in work["a"]:
        iids = sorted(set(iids))
        too_many = len(iids) > MAX_AFFILIATIONS
        most_of_paper = (len(on_paper) >= MIN_INSTITUTIONS_FOR_SHARE_RULE
                         and len(iids) > MAX_SHARE * len(on_paper))
        if too_many or most_of_paper:
            dropped.append((work["y"], name, len(iids), len(on_paper), work["t"]))
            iids = []
        cleaned.append([name, aid, iids])
    return {**work, "a": cleaned}


def build():
    raw = json.loads(RAW.read_text())
    insts = raw["institutions"]
    dropped = []
    raw["works"] = [_clean_affiliations(w, dropped) for w in raw["works"]]

    # Keep publication types, then collapse duplicates (preprint + article,
    # repeated records) by normalised title, preferring the published version.
    best = {}
    for w in raw["works"]:
        if w["ty"] not in KEEP_TYPES or not _norm(w["t"]):
            continue
        k = _norm(w["t"])
        rank = (TYPE_RANK.get(w["ty"], 5), w["v"] is None, w["y"] or 9999)
        if k not in best or rank < best[k][0]:
            best[k] = (rank, w)
    works = sorted((w for _, w in best.values()), key=lambda w: (-(w["y"] or 0), w["t"]))

    # Owen's own affiliations -> home institutions
    own = defaultdict(int)
    for w in works:
        for name, aid, iids in w["a"]:
            if aid == AUTHOR_ID:
                for i in set(iids):
                    own[i] += 1
    home = {i for i, n in own.items() if n >= HOME_MIN_PAPERS}

    papers = []
    by_inst = defaultdict(lambda: {"p": set(), "c": defaultdict(set)})
    unaffiliated = set()
    for w in works:
        coauthors = [a for a in w["a"] if a[1] != AUTHOR_ID]
        if not coauthors:
            continue  # single-author work: no collaboration to map
        idx = len(papers)
        papers.append([w["doi"], w["t"], w["y"], w["v"], len(w["a"])])
        for name, aid, iids in coauthors:
            if not iids:
                unaffiliated.add(aid or name)
            for i in set(iids):
                by_inst[i]["p"].add(idx)
                by_inst[i]["c"][name].add(idx)

    out_insts, unmapped = [], 0
    for iid, d in by_inst.items():
        meta = insts.get(iid)
        if not meta or meta.get("lat") is None:
            unmapped += 1
            continue
        out_insts.append({
            "id": iid, "n": meta["n"], "city": meta.get("city"),
            "country": meta.get("country"), "cc": meta.get("cc"),
            "lat": round(meta["lat"], 4), "lng": round(meta["lng"], 4),
            "home": iid in home,
            "p": sorted(d["p"]),
            "c": sorted(([n, sorted(ps)] for n, ps in d["c"].items()),
                        key=lambda x: (-len(x[1]), x[0])),
        })
    out_insts.sort(key=lambda x: -len(x["p"]))

    coauthor_ids = {a[1] or a[0] for w in works for a in w["a"] if a[1] != AUTHOR_ID}
    out = {
        "meta": {**raw["meta"], "built": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                 "n_works": len(works), "n_collab_papers": len(papers),
                 "n_coauthors": len(coauthor_ids),
                 "n_coauthors_without_affiliation": len(unaffiliated),
                 "n_institutions_without_location": unmapped,
                 "n_affiliation_lists_ignored": len(dropped),
                 "home": [insts[i]["n"] for i in home if i in insts]},
        "papers": papers,
        "institutions": out_insts,
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")))
    m = out["meta"]
    print(f"Wrote {OUT.name}: {len(out_insts)} institutions, {m['n_collab_papers']} co-authored "
          f"papers, {m['n_coauthors']} co-authors; home = {m['home']}")
    if dropped:
        print(f"Ignored {len(dropped)} implausible affiliation list(s) "
              f"(author: institutions given / on paper):")
        for y, name, k, n, t in sorted(dropped):
            print(f"  {y}  {name}: {k}/{n}  {t[:70]}")


if __name__ == "__main__":
    step = sys.argv[1] if len(sys.argv) > 1 else "all"
    if step in ("all", "fetch"):
        fetch()
    if step in ("all", "build"):
        build()
