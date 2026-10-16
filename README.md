# Edmonton Civic Map

**Live:** https://peterfriedrich.github.io/edmonton-civic-map/

Type an Edmonton address, or click the map, to see who represents that place
at every level: City Council, the public and Catholic school boards, the
Legislative Assembly of Alberta and the House of Commons. Each card links the
office's own page, its source and the date it was last checked.

It is a lookup and explainer built from primary sources, not a politics
dashboard: no rankings, scores or evaluation of officials. Sources, currency
and known limits for readers are on the site's
[About page](https://peterfriedrich.github.io/edmonton-civic-map/about.html).

## How it works

```
publishers ──► src/download.py ──► data/raw/            (not committed)
                                      │
                 src/build_boundaries.py      five boundary layers, simplified at 5 m
                 src/build_address_index.py   districts for every address, at full resolution
                 src/build_officeholders.py   71 seats, each cross-checked against a second source
                                      │
                                      ▼
                             site/public/data/          (committed: every change is a reviewable diff)
                                      │
                       Vite ──► dist/ ──► GitHub Pages
```

- **Districts are worked out per address at build time**, against the
  full-resolution boundaries, and checked by two independent methods (shapely
  and the site's own `pip.js`). The browser only looks up one street's file;
  the house number never leaves the page.
- **Every published record carries its source and `last_verified` date.** The
  page warns when a record goes unchecked past its threshold
  (`site/public/data/staleness.json`).
- **A weekly refresh** (`.github/workflows/refresh.yml`) re-downloads every
  source and rebuilds. If nothing moved, it commits the new dates and deploys.
  If anything moved (a name, a seat, a boundary) it publishes nothing and files
  an issue for a person to check against the source. The rules are
  `src/diff_check.py` and `data/diff_rules.json`.

## Running it

Needs Python 3.12 and Node 22 (`.nvmrc`).

```bash
./bootstrap.sh                          # venv, hooks path, first test run
npm ci
.venv/bin/python -m pytest tests -q     # offline; reads committed files only
npm run test:js
npm run dev                             # the site, on the committed data
```

Rebuilding the data from the sources:

```bash
.venv/bin/python -m src.download        # all 13 sources into data/raw/
.venv/bin/python -m src.build_boundaries
.venv/bin/python -m src.build_address_index   # about 6 minutes
.venv/bin/python -m src.build_officeholders
```

Build on aarch64: the same sources rebuilt on x86_64 differ by float noise,
and the next refresh would hold on it (`data/DATA.md`).

## Where things are

| Path | What |
|---|---|
| `src/` | Downloader, the three builders, the diff check |
| `site/` | The Vite site: `index.html` (lookup), `about.html`, `src/` (app code), `public/data/` (published data) |
| `tests/`, `smoke/` | pytest guards; Playwright browser checks on the built site |
| `data/DATA.md` | Every source: URL, columns, quirks, what was verified |
| `docs/SPEC_civic_map.md` | The founding brief, with amendments |
| `docs/SPEC_data_schema.md` | The published files, the diff check, staleness, the refresh |
| `docs/DECISIONS.md` | Every locked decision, with the test that protects it |
| `docs/DATA_ISSUES.md` | Defects found in data we don't control, and whether the publisher has been told |
| `TODO.md` | What's left |
| `prototype/` | The measured proofs the build rests on; not the app |

The workflow apparatus (handoff notes, decision-log and citation guards, the
generated Claude web brief) comes from
[cc-data-project-template](https://github.com/PeterFriedrich/cc-data-project-template)
via copier; `docs/COPIER.md` says how updates are pulled. `CLAUDE.md` holds the
rules sessions work under.

## Data and licences

City of Edmonton data is used under the City's
[open data terms of use](https://data.edmonton.ca/stories/s/City-of-Edmonton-Open-Data-Terms-of-Use/msh8-if28).
Contains information licensed under the
[Open Government Licence – Canada](https://open.canada.ca/en/open-government-licence-canada).
Elections Alberta, the Legislative Assembly, the House of Commons and the two
school boards state no licence on the pages used; each record links back to
them as the source of record. Per-source detail: `data/DATA.md`.
