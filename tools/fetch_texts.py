"""Download the reading texts from Wikisource and reduce them to plain paragraphs.

Every text in the app comes from a Wikisource page listed in WORKS below; nothing
else is used as a text source.  Rendered HTML is cached under build/cache/html so
that re-running the tool does not hit the network again.

Output: build/raw/<lang>/<work>.json
"""
from __future__ import annotations

import re
import sys
import unicodedata

from bs4 import BeautifulSoup, Comment, NavigableString, Tag

from common import CACHE, ROOT, mediawiki, write_json

RAW = ROOT / "build" / "raw"

ROMAN = "I II III IV V VI VII VIII".split()

WORKS = [
    {
        "id": "bello_gallico",
        "lang": "la",
        "title": "Commentarii de Bello Gallico",
        "author": "C. Iulius Caesar",
        "year": "58–50 BC",
        "blurb": "Caesar's own account of the Gallic War (book VIII is by Aulus Hirtius). "
                 "Plain, regular prose - the traditional first real author for students of Latin.",
        "pages": [(f"Commentarii de bello Gallico/Liber {r}", f"Liber {r}") for r in ROMAN],
        "mode": "headings",
    },
    {
        "id": "epitome_historiae_sacrae",
        "lang": "la",
        "title": "Epitome Historiae Sacrae",
        "author": "C. F. Lhomond",
        "year": "1784",
        "blurb": "Bible stories retold in very simple Latin for beginners (text of the 1856 "
                 "Philadelphia school edition, with its English chapter summaries).",
        "pages": [("Epitome historiæ sacræ", None)],
        "mode": "numbered",
    },
    {
        "id": "grimm_maerchen",
        "lang": "de",
        "title": "Kinder- und Hausmärchen",
        "author": "Jacob und Wilhelm Grimm",
        "year": "1857",
        "blurb": "Twelve of the best-known Grimm fairy tales in the text of the final 1857 edition. "
                 "Short sentences and everyday vocabulary; the spelling is pre-1901 (Thür, roth, gieng).",
        "pages": [
            ("Rothkäppchen (1857)", "Rothkäppchen"),
            ("Der Froschkönig oder der eiserne Heinrich (1857)", "Der Froschkönig oder der eiserne Heinrich"),
            ("Hänsel und Grethel (1857)", "Hänsel und Grethel"),
            ("Die Bremer Stadtmusikanten (1857)", "Die Bremer Stadtmusikanten"),
            ("Aschenputtel (1857)", "Aschenputtel"),
            ("Sneewittchen (1857)", "Sneewittchen"),
            ("Dornröschen (1857)", "Dornröschen"),
            ("Rumpelstilzchen (1857)", "Rumpelstilzchen"),
            ("Der Wolf und die sieben jungen Geislein (1857)", "Der Wolf und die sieben jungen Geislein"),
            ("Frau Holle (1857)", "Frau Holle"),
            ("Hans im Glück (1857)", "Hans im Glück"),
            ("Die Sternthaler (1857)", "Die Sternthaler"),
        ],
        "mode": "tale",
    },
    {
        "id": "erben_pohadky",
        "lang": "cs",
        "title": "Pohádky",
        "author": "Karel Jaromír Erben",
        "year": "1858–1860",
        "blurb": "Three classic Czech fairy tales as Erben first printed them in the almanac Máj. "
                 "Lively, spoken-style narration.",
        "pages": [
            ("Máj (almanach 1859)/Zlatovláska", "Zlatovláska"),
            ("Máj (almanach 1860)/Tři zlaté vlasy Děda-Vševěda", "Tři zlaté vlasy Děda-Vševěda"),
            ("Máj (almanach 1858)/Pták Ohnivák a liška Ryška", "Pták Ohnivák a liška Ryška"),
        ],
        "mode": "tale",
    },
    {
        "id": "nowele_i_bajki",
        "lang": "pl",
        "title": "Nowele i bajki",
        "author": "Sienkiewicz, Kraszewski, Prus",
        "year": "1879–1880",
        "blurb": "Four short classics of Polish school reading: Sienkiewicz's \"Bajka\" and "
                 "\"Janko Muzykant\", Kraszewski's \"Kwiat paproci\" and Prus's \"Katarynka\".",
        "pages": [
            ("Bajka (Sienkiewicz, 1931)", "Bajka (H. Sienkiewicz)"),
            ("Kwiat paproci (Kraszewski)", "Kwiat paproci (J. I. Kraszewski)"),
            ("Janko muzykant (1931)", "Janko Muzykant (H. Sienkiewicz)"),
            ("Katarynka", "Katarynka (B. Prus)"),
        ],
        "mode": "tale",
        "br_paragraphs": True,
    },
]

# Elements that never belong to the running text.
DROP = (
    "table, style, script, sup.reference, .reference, .mw-references-wrap, ol.references, "
    ".ws-noexport, .noprint, .PageNumber, .pagenum, .ws-pagenum, .titulusHeaderBox, "
    ".interwiki-extra, .toccolours, .AndereVersion, figure, .mw-file-description, img, "
    ".sz--dane-tekstu--nastepny, .mw-editsection, .mw-empty-elt, .catlinks"
)
BLOCKS = {"p", "div", "h1", "h2", "h3", "h4", "h5", "blockquote", "dd", "li", "center"}


def page_html(lang: str, title: str) -> str:
    cache = CACHE / "html" / lang / (re.sub(r"[^\w]+", "_", title).strip("_") + ".html")
    if cache.exists():
        return cache.read_text(encoding="utf-8")
    print(f"  fetching {lang}.wikisource.org: {title}")
    reply = mediawiki(lang, action="parse", page=title, prop="text", redirects=1,
                      disableeditsection=1, disabletoc=1)
    html = reply["parse"]["text"]["*"]
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(html, encoding="utf-8")
    return html


def clean_text(s: str) -> str:
    s = unicodedata.normalize("NFC", s)
    s = s.replace(" ", " ").replace(" ", " ").replace("​", "").replace("­", "")
    lines = [re.sub(r"[ \t\r\f\v]+", " ", ln).strip() for ln in s.split("\n")]
    return "\n".join(ln for ln in lines if ln)


def blocks(html: str, br_paragraphs: bool):
    """Yield (kind, text) for every leaf block in reading order.

    kind is 'h' for headings, 'c' for centred lines, 'v' for verse and 'p' for prose.
    In prose, source line breaks are just wrapping and become spaces; <br> either
    separates paragraphs (Polish pages) or is kept as a line break (verse).
    """
    soup = BeautifulSoup(html, "lxml")
    root = soup.select_one(".mw-parser-output") or soup
    for el in root.select(DROP):
        el.decompose()
    for comment in root.find_all(string=lambda t: isinstance(t, Comment)):
        comment.extract()
    for br in root.find_all("br"):
        br.replace_with(NavigableString(""))

    def leaf_blocks(node: Tag, verse: bool, centred: bool):
        cls = node.get("class") or []
        style = (node.get("style") or "").replace(" ", "")
        verse = verse or "poem" in cls
        centred = centred or "centertext" in cls or "center" in cls or "text-align:center" in style
        if "oddelovac" in cls:                  # cs.wikisource: rule between a text and its notes
            yield "h", "***"
            return
        kids = [c for c in node.children if isinstance(c, Tag) and c.name in BLOCKS]
        if not kids:
            raw = node.get_text()
            raw = re.sub(r"\s*\n\s*", " ", raw)           # soft wraps in the source
            raw = raw.replace("", "\n")
            text = clean_text(raw)
            if not text:
                return
            if node.name in ("h1", "h2", "h3", "h4", "h5"):
                yield "h", text.replace("\n", " ")
            elif centred:
                yield "c", text.replace("\n", " ")
            elif verse:
                yield "v", text
            elif br_paragraphs:
                for part in text.split("\n"):
                    yield "p", part
            else:
                yield "p", text.replace("\n", " ")
            return
        # Mixed content: emit stray text between child blocks as its own paragraph.
        buf = []

        def flush():
            raw = re.sub(r"\s*\n\s*", " ", "".join(buf)).replace("", "\n")
            buf.clear()
            text = clean_text(raw)
            if text:
                for part in (text.split("\n") if br_paragraphs else [text.replace("\n", " ")]):
                    yield ("c" if centred else "p"), part

        for child in node.children:
            if isinstance(child, Tag) and child.name in BLOCKS:
                yield from flush()
                yield from leaf_blocks(child, verse, centred)
            elif isinstance(child, Tag):
                buf.append(child.get_text())
            elif isinstance(child, NavigableString):
                buf.append(str(child))
        yield from flush()

    yield from leaf_blocks(root, False, False)


def extract_headings(work, title, group):
    """Caesar: every <h3> is a chapter number."""
    sections, current = [], None
    for kind, text in blocks(page_html(work["lang"], title), False):
        if kind == "h" and re.fullmatch(r"\d+", text):
            current = {"group": group, "title": text, "paras": []}
            sections.append(current)
        elif kind == "p" and current is not None:
            current["paras"].append(text)
    return sections


def extract_numbered(work, title, group):
    """Lhomond: centred lines "12. English summary" open each chapter.

    A few of the printed numbers are mis-transcribed on Wikisource (84 for 34 ...),
    so a number is only trusted when it continues the sequence.
    """
    sections, current, n = [], None, 0
    for kind, text in blocks(page_html(work["lang"], title), False):
        m = re.match(r"\W*(\d{1,3})\s*[.,]\s*(\S.*)", text) if kind == "c" else None
        if m and (n or m.group(1) == "1"):
            n = int(m.group(1)) if int(m.group(1)) in (n + 1, n + 2) else n + 1
            current = {"group": group, "title": str(n), "subtitle": m.group(2).strip(), "paras": []}
            sections.append(current)
        elif kind == "p" and current is not None:
            if re.match(r"Finis\b", text):
                break
            current["paras"].append(text)
    return sections


def extract_tale(work, title, label):
    """A whole page is one tale; drop the header lines and trailing apparatus."""
    paras = []
    for kind, text in blocks(page_html(work["lang"], title), work.get("br_paragraphs", False)):
        if kind == "h":
            if paras:
                break               # "See also", notes, ... after the text
            continue
        if kind == "c":
            continue                # title lines
        if kind in ("p", "v") and len(text) > 1 and not re.fullmatch(r"\d+\.?", text):
            paras.append(text)
    # Leading boiler-plate that is not marked up as a table on some pages.
    while paras and len(paras[0]) < 60 and not re.search(r"[.!?…“”\"—:,]", paras[0]):
        paras.pop(0)
    return [{"group": None, "title": label, "paras": paras}]


def build(work):
    extractor = {"headings": extract_headings, "numbered": extract_numbered, "tale": extract_tale}[work["mode"]]
    sections = []
    for title, label in work["pages"]:
        got = extractor(work, title, label)
        if not got or not any(s["paras"] for s in got):
            raise SystemExit(f"nothing extracted from {title!r}")
        sections.extend(got)
    lang = work["lang"]
    return {
        "id": work["id"], "lang": lang, "title": work["title"], "author": work["author"],
        "year": work["year"], "blurb": work["blurb"],
        "source": {
            "site": f"{lang}.wikisource.org",
            "pages": [{"title": t, "url": f"https://{lang}.wikisource.org/wiki/" + t.replace(" ", "_")}
                      for t, _ in work["pages"]],
        },
        "sections": sections,
    }


def main():
    only = set(sys.argv[1:])
    for work in WORKS:
        if only and work["id"] not in only:
            continue
        doc = build(work)
        out = RAW / work["lang"] / f"{work['id']}.json"
        write_json(out, doc, indent=1)
        words = sum(len(p.split()) for s in doc["sections"] for p in s["paras"])
        print(f"{work['id']}: {len(doc['sections'])} sections, ~{words} words -> {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
