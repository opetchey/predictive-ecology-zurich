# Predictive Ecology Group website

Source for the Predictive Ecology Group website (University of Zurich),
built with [Quarto](https://quarto.org), served by GitHub Pages at
**predictiveecologyzurich.org**.

## Structure

- `index.qmd`, `people.qmd`, `research.qmd`, `education.qmd`,
  `organising.qmd`, `outreach.qmd`, `join-us.qmd`, `contact.qmd`,
  `imprint.qmd` — the static pages.
- `posts/` — all blog-style content, one subfolder per **controlled tag**:
  `research`, `education`, `organising`, `outreach`, `join-us`. Each of
  those five subfolders feeds the matching page's listing automatically —
  a post appears on e.g. the Research page because it lives in
  `posts/research/` and its `categories:` starts with `research`.
- `assets/` — theme SCSS, shared CSS, self-hosted fonts, and images
  (banner placeholders, People-page placeholders, favicon).
- `.github/workflows/publish.yml` — GitHub Actions workflow that renders
  the site and deploys it to the `gh-pages` branch on every push to `main`.

## Adding a post

1. Pick the controlled tag that matches the page it should appear on:
   `research`, `education`, `organising`, `outreach`, or `join-us`.
2. Create a new folder under `posts/<that tag>/`, named
   `YYYY-MM-DD-short-slug/`, containing an `index.qmd`.
3. In the YAML front matter, set `categories:` to a list starting with the
   controlled tag, followed by any freeform topic tags, e.g.
   `categories: [research, food webs, Lake Zurich]`.
4. Every post needs exactly one controlled tag (the first entry) — the
   freeform tags after it are open-ended.
5. `.qmd` posts can contain executable R code chunks (see the example
   research post) — they run at render time, both locally and in CI.

## Archiving a post

Adding `archive` (or any second word) to `categories:` does **not** hide a
post — the page listings are driven by which `posts/<tag>/` folder a post
lives in, not by its category values, so an `[research, archive]` post in
`posts/research/` still shows up on the Research page.

To actually take a post out of circulation while keeping it online at its
existing URL (so old links/citations keep working), add `draft: true` to
its YAML front matter:

```yaml
categories: [research, archive]
draft: true
```

This removes it from the page listing, the RSS feed, and the on-site
search index, while still rendering its own page — reachable only by
whoever already has the direct link. Nothing else on the site links to
it once it's out of the listing. The `archive` category is then just a
label for your own reference; `draft: true` is what actually does the
hiding.

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
