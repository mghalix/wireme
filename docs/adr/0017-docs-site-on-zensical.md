# ADR 0017: Publish the docs as a Zensical site at wireme.mghalix.com

- Status: Accepted
- Date: 2026-07-16

## Context

ADR 0014 structured user documentation as one-concept pages under
docs/guide, noting that a real site would be a scaffold task. The owner
approved the site and wants it in sync with the storix documentation
(zensical, Cloudflare Pages, mghalix.com subdomain), including recipes and
an explicit house-style page.

## Decision

The documentation lives in website/ following the storix layout:
zensical.toml, a pinned requirements.txt for reproducible Cloudflare Pages
builds, and website/docs as the content root. The guide pages moved from
docs/guide to website/docs/guide (single source of truth; docs/ keeps only
ADRs). Example links use absolute GitHub URLs so pages render on both
GitHub and the site; release notes snippet-include CHANGELOG.md rather
than duplicating it. The site adds three content layers on top of the
guide: a landing page, production recipes, and "The Wireme way" page that
states the house opinions (type-keyword aliases, keyword-only injected
parameters, named factories, FromWeb first) with links to their ADRs.
Build commands are just docs (serve) and just docs-build (strict build to
website/site, which is gitignored).

## Consequences

- Positive: navigable, searchable onboarding; identical tooling and style
  across the owner's projects; strict builds catch broken pages.
- Negative: repository links must use the website/docs path; the site
  requires one-time Cloudflare Pages and DNS provisioning by the owner.
- Follow-up: zensical is pinned pre-1.0 and bumped deliberately.
