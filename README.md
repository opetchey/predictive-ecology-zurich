# Predictive Ecology Group website

Source for the Predictive Ecology Group website (University of Zurich),
built with [Quarto](https://quarto.org), served by GitHub Pages at
**predictiveecologyzurich.org**.

## Structure

- `index.qmd`, `team.qmd`, `research.qmd`, `education.qmd`,
  `organising.qmd`, `outreach.qmd`, `join-us.qmd`, `misc.qmd`,
  `contact.qmd`, `imprint.qmd` — the static pages.
- `posts/` — all blog-style content, one subfolder per **controlled tag**:
  `research`, `education`, `organising`, `outreach`, `join-us`, `misc`,
  `team`. Each of those seven subfolders feeds the matching page's listing
  automatically — a post appears on e.g. the Research page because it
  lives in `posts/research/` and its `categories:` starts with `research`.
  `misc` is the catch-all for content that doesn't fit the other pages —
  personal reflections, opinions, and practical tips — distinguished on
  the Misc page by freeform tags like `thoughts` or `tips`. `team` is
  different from the rest: each post is a group member's profile (photo
  + short bio) shown on the Team page, tagged `team` plus a role like
  `group-leader`, `postdoc`, or `phd-student`.
- `posts.qmd` — the "All posts" page: every post ever published, unfiltered
  (including archived ones), with search/sort/category-filter controls.
- `scripts/build_listings.py` — a pre-render step (see "Archiving a post")
  that builds each page's post list, leaving out anything tagged `archive`.
- `assets/` — theme SCSS, shared CSS, self-hosted fonts, and images
  (banner placeholders, favicon). Team-member and post photos live
  alongside their own `index.qmd` under `posts/`, not here.
- `.github/workflows/publish.yml` — GitHub Actions workflow that renders
  the site and deploys it to the `gh-pages` branch on every push to `main`.

## Adding a post

1. Pick the controlled tag that matches the page it should appear on:
   `research`, `education`, `organising`, `outreach`, `join-us`, `misc`, or
   `team` (see below for `team`, which works a bit differently).
2. Create a new folder under `posts/<that tag>/`, named
   `YYYY-MM-DD-short-slug/`, containing an `index.qmd`.
3. In the YAML front matter, set `categories:` to a list starting with the
   controlled tag, followed by any freeform topic tags, e.g.
   `categories: [research, food webs, Lake Zurich]`.
4. Every post needs exactly one controlled tag (the first entry) — the
   freeform tags after it are open-ended.
5. `.qmd` posts can contain executable R code chunks (see the example
   research post) — they run at render time, both locally and in CI.

## Adding a team member

Copy `posts/team/2026-09-05-example-team-member/` (or any real member's
folder), rename it to the person's name, replace `cover.jpg` with their
photo, and set `categories: [team, <role>]` — e.g. `group-leader`,
`postdoc`, `phd-student`, or `msc-student`. The body is a short bio and a
link to the person's own page (for their contact details — see the
"no email addresses" note above). They'll appear on the [Team](team.qmd)
page automatically, grouped/filterable by role via the category list.

## Archiving a post

Add `archive` to a post's `categories:` list to retire it from its page's
own feed, without deleting it or touching `draft:`:

```yaml
categories: [research, archive]
```

Before each render, `scripts/build_listings.py` runs as a Quarto
[pre-render step](https://quarto.org/docs/projects/scripts.html) (wired up
in `_quarto.yml`). It reads every post's front matter and writes
`listings/<tag>.yml` for each controlled tag — the file each page's
`listing.contents` actually points to — leaving out anything tagged
`archive`. So:

- The post disappears from its page's listing (e.g. Research) and that
  page's RSS feed.
- It stays fully visible, findable and filterable on the
  [All posts](posts.qmd) page, which points straight at `posts/`,
  unfiltered.
- It stays in the site-wide search index, and its own page keeps
  rendering at its existing URL — nothing about the post itself changes,
  only which page's feed includes it.

`listings/` is generated on every render (see `.gitignore`) — never edit
those files directly, edit the posts' `categories:` instead.

## Local preview

Requires [Quarto](https://quarto.org/docs/get-started/) and R installed
locally:

```sh
quarto preview
```

## Publishing

Every push to `main` triggers the GitHub Actions workflow, which renders
the site and pushes the result to the `gh-pages` branch. GitHub Pages is
configured (Settings → Pages) to serve from `gh-pages` / `root`, with the
custom domain `predictiveecologyzurich.org` (see the `CNAME` file).

## Licence

- Website source code: [MIT](LICENSE).
- Written content and photographs: [CC BY 4.0](LICENSE-CONTENT.md).

## Privacy

No analytics, no cookies, no third-party trackers or font/script CDNs —
see the [Imprint & privacy](imprint.qmd) page for details.
