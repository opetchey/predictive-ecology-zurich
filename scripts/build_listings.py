#!/usr/bin/env python3
"""
Pre-render step (see `project: pre-render:` in _quarto.yml).

Each thematic page (research.qmd, education.qmd, ...) shows a feed of posts
from its matching posts/<tag>/ folder. This script builds that feed's file
list for each controlled tag, LEAVING OUT any post whose `categories:` list
also includes "archive" — so archiving a post is just adding one word to
its front matter, no moving files around and no `draft: true` (which would
also pull it out of site-wide search, which is not what we want).

The generated posts/<tag>/index.qmd listings never see archived posts at
all. The site-wide posts.qmd page is unaffected by this script — its
listing points straight at posts/, unfiltered, so archived posts still show
up there (and in on-site search, since draft: true is never used).

Output: one listings/<tag>.yml per controlled tag, each a plain list of
`- path: posts/<tag>/<slug>/index.qmd` entries, in the shape Quarto expects
for a listing's `contents:` (see https://quarto.org/docs/websites/website-listings.html#metadata-from-file).
No third-party YAML library is used (front matter is only ever read, not
rewritten) so this script has no dependencies beyond the standard library —
it runs the same way locally and in CI.
"""

import glob
import os
import re

CONTROLLED_TAGS = ["research", "education", "organising", "outreach", "join-us", "misc"]
ARCHIVE_TAG = "archive"

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
# categories: [a, b, c]  -- our posts always use this flow-list style
FLOW_LIST_RE = re.compile(r"^categories:\s*\[(.*?)\]\s*$", re.MULTILINE)
# categories:\n  - a\n  - b  -- a block-list fallback, in case anyone writes it that way
BLOCK_LIST_RE = re.compile(r"^categories:\s*\n((?:^\s*-\s*.+\n?)+)", re.MULTILINE)
BLOCK_ITEM_RE = re.compile(r"^\s*-\s*(.+?)\s*$", re.MULTILINE)


def read_categories(qmd_path):
    with open(qmd_path, encoding="utf-8") as f:
        text = f.read()
    m = FRONTMATTER_RE.match(text)
    if not m:
        return []
    front = m.group(1)

    flow = FLOW_LIST_RE.search(front)
    if flow:
        items = [item.strip().strip("'\"") for item in flow.group(1).split(",")]
        return [item for item in items if item]

    block = BLOCK_LIST_RE.search(front)
    if block:
        items = [item.strip().strip("'\"") for item in BLOCK_ITEM_RE.findall(block.group(1))]
        return [item for item in items if item]

    return []


def main():
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(repo_root)
    os.makedirs("listings", exist_ok=True)

    for tag in CONTROLLED_TAGS:
        post_files = sorted(glob.glob(os.path.join("posts", tag, "*", "index.qmd")))
        kept = []
        for path in post_files:
            categories = read_categories(path)
            if not categories:
                print(f"build_listings.py: warning: {path} has no categories: field")
                continue
            if categories[0] != tag:
                print(
                    f"build_listings.py: warning: {path} is in posts/{tag}/ but its "
                    f"first category is {categories[0]!r}, not {tag!r}"
                )
            if ARCHIVE_TAG in categories:
                continue  # archived -- leave out of this page's listing
            # Paths in a listing's contents-from-file YAML are resolved
            # relative to that YAML file's own directory (listings/), not
            # the project root, so go up one level.
            kept.append("../" + path.replace(os.sep, "/"))

        out_path = os.path.join("listings", f"{tag}.yml")
        with open(out_path, "w", encoding="utf-8") as f:
            if kept:
                for path in kept:
                    f.write(f"- path: {path}\n")
            else:
                # An empty YAML list, so the page renders an empty listing
                # instead of Quarto erroring on a missing/empty contents file.
                f.write("[]\n")
        print(f"build_listings.py: wrote {out_path} ({len(kept)} post(s))")


if __name__ == "__main__":
    main()
