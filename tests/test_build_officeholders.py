"""src/build_officeholders.py: the parsers against markup copied from the live
pages (2026-10-16), each failing to an empty result when the layout changes, and
the committed officeholders.json against the committed boundary files."""
import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
from src import build_officeholders as bo  # noqa: E402
from src import download  # noqa: E402

DATA = REPO / "site" / "public" / "data"

EPSB = ('<h3>WARDS</h3>\n<p><a href="/ourdistrict/board/trustees/ward-a/">Ward A - Trustee Sherri O\'Keefe</a><br />'
        '<a href="/ourdistrict/board/trustees/ward-b/">Ward B - Trustee Linda Lindsay</a></p>'
        # the side menu links the same pages with ward letters only
        '<li><a href="/ourdistrict/board/trustees/ward-a/">Ward A</a></li>')
ECSD = ('<div class="editor-layoutItem"><p class="editor-paragraph"><img src="/images/x" alt="Trustee - Leah Fiorillo"/></p>'
        '<h3 class="editor-heading-h3" dir="ltr"><span style="white-space: pre-wrap;">Leah Fiorillo</span></h3>'
        '<p class="editor-paragraph" dir="ltr"><a class="editor-link" href="https://x.sharepoint.com/y"><b>'
        '<strong class="editor-text-bold">WARD 71</strong></b></a></p><div monaco-code-embed=""> <div class="row no-gutters">\n'
        '<a class="btn btn-primary btn-block btn-lg" href="https://www.ecsd.net/ward-71" style="display:block">Learn More</a>')
ASSEMBLY = ('<tr>\n<td>\n<img class="MemPhoto" src="/x/ph-mla0911.jpg" alt="Rakhi Pancholi"></td>\n<td>\n'
            '<a href="/members/members-of-the-legislative-assembly/member-information?mid=0911&legl=31&from=mla_home">'
            'Pancholi, Ms. Rakhi </a></td>\n<td>\nNDP</td>\n<td>\nEdmonton-Whitemud</td>\n</tr>'
            '<tr>\n<td>\n<img class="MemPhoto" src="/x/ph-mla0791.jpg" alt="Rachel Notley"></td>\n<td>\n'
            '<a href="/members/members-of-the-legislative-assembly/member-information?mid=0791&legl=31&from=mla_home">'
            'Notley, ECA, The Honourable Rachel </a></td>\n<td>\n&nbsp;</td>\n<td>\n'
            '<i style="color:brown"><span style="color:#fff;">z</span>Former Member</i></td>\n</tr>')
MLA_CSV = ('Date file created\r\n"2026-Oct-15 17:59:39 -06:00"\r\n\r\n'
           '"Constituency Number","Constituency Name","MLA Title","MLA First Name","MLA Middle Names","MLA Last Name","Caucus","Address Type","Address Type"\r\n'
           '"46","Edmonton-Whitemud","Ms.","Rakhi","","Pancholi","NDP","Legislature Office","Constituency Office"\r\n').encode()


def test_parse_epsb_reads_trustee_links_and_ignores_the_menu():
    assert bo.parse_epsb(EPSB) == {
        "A": ("Sherri O'Keefe", "https://www.epsb.ca/ourdistrict/board/trustees/ward-a/"),
        "B": ("Linda Lindsay", "https://www.epsb.ca/ourdistrict/board/trustees/ward-b/"),
    }


def test_parse_ecsd_pairs_the_name_heading_with_its_ward():
    assert bo.parse_ecsd(ECSD) == {"71": ("Leah Fiorillo", "https://www.ecsd.net/ward-71")}


def test_parse_assembly_list_skips_former_members():
    assert bo.parse_assembly_list(ASSEMBLY) == {"edmonton whitemud": ("0911", "Pancholi, Ms. Rakhi")}


def test_parse_mla_csv_skips_the_banner():
    rows = bo.parse_mla_csv(MLA_CSV)
    assert [(r["Constituency Number"], r["MLA Last Name"], r["Caucus"]) for r in rows] == [("46", "Pancholi", "NDP")]


@pytest.mark.parametrize("parse, page", [
    (bo.parse_epsb, EPSB.replace(" - Trustee ", ": ")),
    (bo.parse_ecsd, ECSD.replace("<h3", "<h4").replace("</h3>", "</h4>")),
    (bo.parse_assembly_list, ASSEMBLY.replace("<td>", "<td class='x'>")),
])
def test_parsers_find_nothing_when_the_layout_changes(parse, page):
    assert parse(page) == {}


def test_page_download_fails_on_a_changed_layout(tmp_path, monkeypatch):
    monkeypatch.setattr(download, "_get", lambda url: (EPSB.replace(" - Trustee ", ": ").encode(), {}))
    with pytest.raises(download.DownloadError, match="zero rows"):
        download.download("epsb_trustees", tmp_path)
    assert not (tmp_path / "epsb_trustees").exists()


def test_results_winners_counts_an_acclaimed_candidate_with_zero_votes():
    rows = [{"contest": "C", "wardname": "Ward 75", "candidatename": "SMITH, Ann", "votes": "0", "acclaimed": "Yes"},
            {"contest": "M", "wardname": "City-Wide", "candidatename": "A, B", "votes": "5", "acclaimed": "No"},
            {"contest": "M", "wardname": "City-Wide", "candidatename": "C, D", "votes": "9", "acclaimed": "No"}]
    assert bo.results_winners(rows) == {("C", "Ward 75"): "SMITH, Ann", ("M", "City-Wide"): "C, D"}
    assert bo.given_surname("O'KEEFE, Sherri") == "Sherri O'Keefe"


def test_norm_joins_the_spellings_sources_use():
    assert bo.norm("Ward pihêsiwin ᐱᐦᐁᓯᐏᐣ".removeprefix("Ward ")) == bo.norm("pihêsiwin")
    assert bo.norm("O-day’min") == bo.norm("O-day'min")
    assert bo.norm("Sherwood Park—Fort Saskatchewan") == bo.norm("Sherwood Park-Fort Saskatchewan")


def test_a_name_mismatch_passes_only_when_approved():
    variants = bo.load_variants()
    assert bo.same_person("council_ward:pihesiwin", "Mike Elliott", "Michael Elliott", variants)
    assert not bo.same_person("council_ward:dene", "Mike Elliott", "Michael Elliott", variants)
    assert not bo.same_person("council_ward:pihesiwin", "Mike Elliott", "Someone Else", variants)


def test_committed_officeholders_cover_every_district_once():
    rows = json.loads((DATA / "officeholders.json").read_text(encoding="utf-8"))
    districts = set()
    for layer in json.loads((DATA / "layers.json").read_text(encoding="utf-8")):
        fc = json.loads((DATA / layer["file"]).read_text(encoding="utf-8"))
        districts |= {f["properties"]["district_id"] for f in fc["features"]}
    seats = [r["district_id"] for r in rows if r["district_id"]]
    assert sorted(seats) == sorted(districts)
    assert [r["seat_id"] for r in rows if r["district_id"] is None] == ["edmonton_council:mayor"]
    assert len({r["seat_id"] for r in rows}) == len(rows)
    for r in rows:
        assert r["source_url"] and r["last_verified"], r["seat_id"]
        assert r["vacant"] == (r["name"] is None), r["seat_id"]
        assert r["vacant"] or r["contact_url"], r["seat_id"]
        assert r["cross_check"] is None or r["cross_check"]["agrees"], r["seat_id"]
        # Affiliation only on MLA and MP rows (docs/SPEC_data_schema.md §7 point 1)
        if r["body"] not in ("legislative_assembly_of_alberta", "house_of_commons"):
            assert r["affiliation"] is None, r["seat_id"]
