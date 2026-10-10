# SCOPE — what this project deliberately does not do

The one hand-kept input to the Claude web brief (`scripts/make_brief.py`, setup
in `docs/CLAUDE_WEB.md`). Everything else in the brief is generated from files
the repo already maintains; this is the list an outside reviewer can't derive —
ideas that were considered and turned down, so they stop coming back as
recommendations.

One bullet each: **the thing**, then why not, and a pointer if a decision row
or doc holds the argument. A turned-down idea that has a locked decision needs
no bullet here — the brief already carries `docs/DECISIONS.md`.

## Out of scope

- **A third-party "who represents this point" API** (Open North's Represent, a commercial geocoder) — it sends a resident's location to someone else; needs the owner's decision first. `docs/SPEC_civic_map.md` §5.
- **Scores of any kind about officials** — attendance, voting records, alignment, responsiveness. Locked out; see `docs/DECISIONS.md`.
- **Wikipedia, news sites or community wikis as data** — primary sources only; they may be linked as context.
- **Names, emails or phone numbers of City staff** — roles and departments only, unless the City publishes the person as a public contact.
- **Merging with `edmonton-tax-viz`** — separate repo and deployment by decision.
