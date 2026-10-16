"""Build site/public/data/officeholders.json: one row per seat for every district
in site/public/data/layers.json (docs/SPEC_data_schema.md §4 and §7 point 1).

Reads the office-holder sources that src.download put in data/raw/. Stops,
writing nothing, when a district has no seat, a seat matches no district, two
rows claim one seat, a parser finds the wrong number of rows, or a cross-check
disagrees on a name that data/name_variants.csv does not list. A name pair in
that file is one a person has approved (data/DATA.md, "Name variants").

    python -m src.build_officeholders [--raw data/raw] [--out site/public/data]
"""
import argparse
import csv
import html
import io
import json
import logging
import re
import sys
import unicodedata
from pathlib import Path

log = logging.getLogger("build_officeholders")

REPO = Path(__file__).resolve().parents[1]
VARIANTS = REPO / "data" / "name_variants.csv"
EPSB_URL = "https://www.epsb.ca"
ASSEMBLY_URL = "https://www.assembly.ab.ca"
COMMONS_MEMBER_URL = "https://www.ourcommons.ca/Members/en/{}"


class BuildError(Exception):
    pass


def norm(s):
    """Join key for names across sources: no accents, case, dash or apostrophe
    style, or Canadian syllabics (the contacts table appends them to two wards)."""
    s = "".join(c for c in s if not "᐀" <= c <= "ᙿ")
    s = unicodedata.normalize("NFKD", s.replace("’", "'"))
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[‐-―-]", " ", s.lower())
    return " ".join(s.split())


def _text(fragment):
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", fragment)).split())


# --- parsers: each returns every row it finds; callers check the count ---------

def parse_epsb(page):
    """{ward letter: (name, page url)} from the EPSB trustees page.
    The page lists each as a link "Ward A - Trustee <name>"."""
    out = {}
    for href, label in re.findall(r'<a[^>]+href="(/ourdistrict/board/trustees/ward-[a-i]/)"[^>]*>(.*?)</a>', page, re.S):
        m = re.fullmatch(r"Ward ([A-I]) - Trustee (.+)", _text(label))
        if m:
            out[m.group(1)] = (m.group(2), EPSB_URL + href)
    return out


def parse_ecsd(page):
    """{ward number: (name, page url)} from the ECSD trustees page: each card is
    an h3 holding the name, then a "WARD 7x" line, then a link to /ward-7x."""
    out = {}
    for m in re.finditer(r"<h3[^>]*>(.*?)</h3>(.*?)href=\"(https://www\.ecsd\.net/ward-(7\d))\"", page, re.S):
        name, between, url, ward = _text(m.group(1)), m.group(2), m.group(3), m.group(4)
        if re.search(rf"WARD {ward}\b", _text(between)) and name:
            out[ward] = (name, url)
    return out


def parse_mla_csv(body):
    """[row dict] from the Assembly's contacts.csv. It opens with a "Date file
    created" banner (two lines and a blank one), then the header (data/DATA.md).
    Address columns repeat names (two offices); only the first seven are read."""
    lines = body.decode("utf-8-sig").splitlines()
    start = next((i for i, l in enumerate(lines) if l.lstrip('"').startswith("Constituency Number")), None)
    if start is None:
        raise BuildError("contacts.csv: no 'Constituency Number' header")
    return [r for r in csv.DictReader(io.StringIO("\n".join(lines[start:]))) if (r["Constituency Number"] or "").isdigit()]


def parse_mp_csv(body):
    return list(csv.DictReader(io.StringIO(body.decode("utf-8-sig"))))


def parse_assembly_list(page):
    """{normalised division name: (mid, listed name)} for current members on the
    Assembly's members page; former members are listed with no division."""
    out = {}
    for mid, name, caucus, division in re.findall(
            r'member-information\?mid=(\d+)[^"]*"[^>]*>(.*?)</a>\s*</td>\s*<td>(.*?)</td>\s*<td>(.*?)</td>', page, re.S):
        division = _text(division)
        if division and "Former Member" not in division:
            out[norm(division)] = (mid, _text(name))
    return out


def results_winners(rows):
    """{(contest, wardname): candidatename} from the 2025 official results. An
    acclaimed candidate has 0 votes, so acclaimed wins before vote count."""
    by = {}
    for r in rows:
        by.setdefault((r["contest"], r["wardname"]), []).append(r)
    return {k: max(v, key=lambda r: (r["acclaimed"] == "Yes", int(r["votes"] or 0)))["candidatename"]
            for k, v in by.items()}


def given_surname(s):
    """'SURNAME, Given' (election results) -> 'Given Surname'."""
    last, _, first = s.partition(",")
    return f"{first.strip()} {last.strip().title()}"


# --- build ----------------------------------------------------------------------

def _load(raw, sid):
    meta = json.loads((raw / sid / "fetch.json").read_text(encoding="utf-8"))
    return meta, (raw / sid / meta["file"]).read_bytes()


def _csv_rows(body):
    return list(csv.DictReader(io.StringIO(body.decode("utf-8"))))


def _expect(what, got, want):
    if len(got) != want:
        raise BuildError(f"{what}: parsed {len(got)} rows, expected {want}")


def load_variants(path=VARIANTS):
    """{(seat_id, norm name A, norm name B)} approved as the same person."""
    if not path.exists():
        return set()
    with open(path, newline="", encoding="utf-8") as f:
        return {(r["seat_id"], norm(r["name"]), norm(r["cross_check_name"])) for r in csv.DictReader(f)}


def same_person(seat_id, a, b, variants):
    a, b = norm(a), norm(b)
    return a == b or (seat_id, a, b) in variants


def build(raw, layers, variants):
    districts = {l["id"]: l for l in layers}
    names = {}  # district_id -> boundary name
    for l in layers:
        fc = json.loads((Path(l["_path"])).read_text(encoding="utf-8"))
        for f in fc["features"]:
            names[f["properties"]["district_id"]] = f["properties"]["name"]

    wards_meta, wards_body = _load(raw, "coe_wards")
    contacts_meta, contacts_body = _load(raw, "coe_council_contacts")
    results_meta, results_body = _load(raw, "coe_election_results_2025")
    epsb_meta, epsb_body = _load(raw, "epsb_trustees")
    ecsd_meta, ecsd_body = _load(raw, "ecsd_trustees")
    mla_meta, mla_body = _load(raw, "ab_mlas")
    alist_meta, alist_body = _load(raw, "ab_mla_list")
    mp_meta, mp_body = _load(raw, "ca_mps")

    winners = results_winners(_csv_rows(results_body))
    contacts = _csv_rows(contacts_body)
    _expect("e9qt-cc3j contacts", contacts, 13)
    contact_by_area = {norm(r["electoral_area"].removeprefix("Ward ")): r for r in contacts}

    rows, problems = [], []

    def row(seat_id, body, role, district_id, name, contact_url, src_meta, xcheck, affiliation=None, aff_src=None):
        rows.append({
            "seat_id": seat_id, "body": body, "role": role, "district_id": district_id,
            "name": name, "vacant": name is None, "contact_url": contact_url,
            "source_id": src_meta["id"], "source_url": src_meta["landing_url"],
            "cross_check": xcheck,
            "affiliation": affiliation, "affiliation_source_id": aff_src,
            "last_verified": src_meta["retrieved_at"][:10],
        })

    def check(seat_id, name, other, other_meta):
        """cross_check record; a disagreement is a problem, never published."""
        if other is None:
            problems.append(f"{seat_id}: {other_meta['id']} has no entry")
            return {"source_id": other_meta["id"], "agrees": False}
        agrees = same_person(seat_id, name, other, variants)
        if not agrees:
            problems.append(f"{seat_id}: '{name}' ({rows_src}) against '{other}' ({other_meta['id']})")
        return {"source_id": other_meta["id"], "agrees": agrees}

    # Council: mayor from contacts, councillors from the ward layer.
    rows_src = contacts_meta["id"]
    mayor = contact_by_area.get("city wide")
    if mayor is None:
        raise BuildError("e9qt-cc3j: no City-Wide (mayor) row")
    mayor_name = f"{mayor['first_name']} {mayor['last_name']}"
    won = winners.get(("Mayor", "City-Wide"))
    row("edmonton_council:mayor", "edmonton_council", "Mayor", None, mayor_name, mayor["url"], contacts_meta,
        check("edmonton_council:mayor", mayor_name, given_surname(won) if won else None, results_meta))

    rows_src = wards_meta["id"]
    ward_layer = {norm(f["properties"]["name_1"]): f["properties"]["councillor"]
                  for f in json.loads(wards_body)["features"]}
    for did, bname in names.items():
        if not did.startswith("council_ward:"):
            continue
        key = norm(bname)
        name = ward_layer.get(key) or None
        c = contact_by_area.get(key)
        row(did, "edmonton_council", "Councillor", did, name, c["url"] if c else None, wards_meta,
            check(did, name, f"{c['first_name']} {c['last_name']}" if c else None, contacts_meta) if name else None)

    # School boards: the boards' own pages, checked against the 2025 results.
    rows_src = epsb_meta["id"]
    epsb = parse_epsb(epsb_body.decode("utf-8"))
    _expect("EPSB trustees page", epsb, 9)
    for did in [d for d in names if d.startswith("public_school_ward:")]:
        w = did.split(":")[1]
        name, url = epsb.get(w, (None, None))
        won = winners.get(("Edmonton School Division", f"Ward {w}"))
        row(did, "edmonton_public_schools", "Trustee", did, name, url, epsb_meta,
            check(did, name, given_surname(won) if won else None, results_meta) if name else None)

    rows_src = ecsd_meta["id"]
    ecsd = parse_ecsd(ecsd_body.decode("utf-8"))
    _expect("ECSD trustees page", ecsd, 7)
    for did in [d for d in names if d.startswith("catholic_school_ward:")]:
        w = did.split(":")[1]
        name, url = ecsd.get(w, (None, None))
        won = winners.get(("Edmonton Catholic Separate School Division", f"Ward {w}"))
        row(did, "edmonton_catholic_schools", "Trustee", did, name, url, ecsd_meta,
            check(did, name, given_surname(won) if won else None, results_meta) if name else None)

    # MLAs: contacts.csv joined on division number; the members page gives the
    # member's own page and a second listing to check the surname against.
    rows_src = mla_meta["id"]
    mlas = {r["Constituency Number"]: r for r in parse_mla_csv(mla_body)}
    listed = parse_assembly_list(alist_body.decode("utf-8"))
    for did in [d for d in names if d.startswith("provincial_riding:")]:
        r = mlas.get(did.split(":")[1])
        if r is None:
            row(did, "legislative_assembly_of_alberta", "Member of the Legislative Assembly", did, None, None, mla_meta, None)
            continue
        if norm(r["Constituency Name"]) != norm(names[did]):
            problems.append(f"{did}: contacts.csv names division {r['Constituency Name']!r}, the boundary file {names[did]!r}")
        name = " ".join(p for p in (r["MLA First Name"], r["MLA Last Name"]) if p)
        mid, listed_name = listed.get(norm(names[did]), (None, None))
        # The members page lists "Last, Honorific First", so the surname is what compares.
        agrees = listed_name is not None and norm(r["MLA Last Name"]) in norm(listed_name)
        if not agrees:
            problems.append(f"{did}: '{name}' (ab_mlas) against {listed_name!r} (ab_mla_list)")
        url = f"{ASSEMBLY_URL}/members/members-of-the-legislative-assembly/member-information?mid={mid}&legl=31" if mid else None
        row(did, "legislative_assembly_of_alberta", "Member of the Legislative Assembly", did, name, url, mla_meta,
            {"source_id": alist_meta["id"], "agrees": agrees}, r["Caucus"] or None, mla_meta["id"])

    # MPs: the House of Commons list joined on constituency name; no second source.
    mps = {}
    for r in parse_mp_csv(mp_body):
        if not r["End Date"]:
            mps.setdefault(norm(r["Constituency"]), []).append(r)
    for did in [d for d in names if d.startswith("federal_riding:")]:
        found = mps.get(norm(names[did]), [])
        if len(found) > 1:
            problems.append(f"{did}: {len(found)} sitting members listed")
        r = found[0] if found else None
        name = " ".join(p for p in (r["First Name"], r["Last Name"]) if p) if r else None
        row(did, "house_of_commons", "Member of Parliament", did, name,
            COMMONS_MEMBER_URL.format(r["Person ID"]) if r else None, mp_meta, None,
            (r["Political Affiliation"] or None) if r else None, mp_meta["id"] if r else None)

    # Every district has exactly one seat; nothing else does.
    seat_districts = [r["district_id"] for r in rows if r["district_id"]]
    missing = sorted(set(names) - set(seat_districts))
    dupes = sorted({d for d in seat_districts if seat_districts.count(d) > 1})
    if missing:
        problems.append(f"districts without a seat: {missing}")
    if dupes:
        problems.append(f"districts with more than one seat: {dupes}")
    for r in rows:
        if r["vacant"]:
            log.warning("%s: no holder found, published as vacant", r["seat_id"])
        if not r["vacant"] and not r["contact_url"]:
            problems.append(f"{r['seat_id']}: no official contact page")
    if problems:
        raise BuildError(f"{len(problems)} problem(s):\n  " + "\n  ".join(problems))
    return rows


def write(rows, out):
    order = {"edmonton_council": 0, "edmonton_public_schools": 1, "edmonton_catholic_schools": 2,
             "legislative_assembly_of_alberta": 3, "house_of_commons": 4}
    rows = sorted(rows, key=lambda r: (order[r["body"]], r["district_id"] is not None, r["seat_id"]))
    text = "[\n" + ",\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n]\n"
    tmp = out / "officeholders.json.partial"
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(out / "officeholders.json")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--raw", type=Path, default=REPO / "data" / "raw")
    ap.add_argument("--out", type=Path, default=REPO / "site" / "public" / "data")
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    layers = json.loads((args.out / "layers.json").read_text(encoding="utf-8"))
    for l in layers:
        l["_path"] = args.out / l["file"]
    try:
        rows = build(args.raw, layers, load_variants())
    except BuildError as e:
        log.error("FAILED: %s", e)
        return 1
    write(rows, args.out)
    log.info("wrote %d seats (%d vacant) to %s", len(rows), sum(r["vacant"] for r in rows), args.out / "officeholders.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
