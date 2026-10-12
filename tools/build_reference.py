"""Grammar tables for German, Czech and Polish, taken from English Wikipedia.

Each listed article is fetched through the MediaWiki API (cached under
build/cache/wikipedia), cut into its sections and reduced to plain headings,
paragraphs, lists and tables that Qt's rich-text widget can show.

Output: lang_gram/data/grammar/<lang>/reference.json
"""
from __future__ import annotations

import json
import re
import sys

from bs4 import BeautifulSoup, Comment, NavigableString, Tag

from common import CACHE, DATA, mediawiki, write_json

PAGES = {
    "de": ["German grammar", "German nouns", "German articles", "German declension", "German adjectives",
           "Pronouns in German", "German verbs", "German conjugation"],
    "cs": ["Czech declension", "Czech conjugation"],
    "pl": ["Polish grammar", "Polish morphology"],
}
SKIP_SECTIONS = {"see also", "references", "notes", "external links", "further reading", "sources", "bibliography",
                 "citations", "explanatory notes", "footnotes", "literature"}
DROP = ("style, script, sup.reference, .reference, .mw-editsection, .navbox, .infobox, .sidebar, .metadata, "
        ".ambox, .hatnote, .noprint, figure, img, .mw-references-wrap, ol.references, .reflist, .thumb, "
        ".shortdescription, .mw-empty-elt, .navigation-not-searchable, .toc, .portalbox, .sistersitebox, "
        "link, meta, .IPA-label, .nowrap.noexcerpt, .side-box")
KEEP = {"p", "table", "tr", "th", "td", "ul", "ol", "li", "b", "i", "em", "strong", "br", "sup", "sub",
        "caption", "dl", "dt", "dd", "blockquote"}


def fetch(title: str) -> dict:
    cache = CACHE / "wikipedia" / (re.sub(r"[^\w]+", "_", title) + ".json")
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))
    print(f"  fetching en.wikipedia.org: {title}")
    reply = mediawiki("en", site="wikipedia", action="parse", page=title, prop="text|sections|revid",
                      redirects=1, disableeditsection=1)
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(reply["parse"], ensure_ascii=False), encoding="utf-8")
    return reply["parse"]


def sanitize(node: Tag) -> str:
    """Serialise *node* keeping only simple structure."""
    out = []

    def walk(el):
        if isinstance(el, Comment):
            return
        if isinstance(el, NavigableString):
            text = str(el)
            out.append(text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
            return
        name = el.name
        if name in ("tbody", "thead", "tfoot", "a", "span", "div", "abbr", "small", "big", "font", "code",
                    "center", "cite", "u", "s", "var", "kbd", "samp", "bdi", "q", "time", "mark", "ins", "del"):
            for child in el.children:
                walk(child)
            if name == "div":
                out.append(" ")
            return
        if name not in KEEP:
            return
        attrs = ""
        if name in ("td", "th"):
            for a in ("colspan", "rowspan"):
                value = el.get(a)
                if value and str(value).isdigit() and int(value) > 1:
                    attrs += f' {a}="{int(value)}"'
        if name == "table":
            attrs = ' class="grid" cellspacing="0"'
        if name == "caption":
            out.append("<tr><th colspan=\"20\">")
            for child in el.children:
                walk(child)
            out.append("</th></tr>")
            return
        if name == "br":
            out.append("<br>")
            return
        out.append(f"<{name}{attrs}>")
        for child in el.children:
            walk(child)
        out.append(f"</{name}>")

    walk(node)
    html = "".join(out)
    html = re.sub(r"[ \t\r\n]+", " ", html)
    html = re.sub(r"<p>\s*</p>", "", html)
    return html.strip()


def sections_of(parsed: dict):
    soup = BeautifulSoup(parsed["text"]["*"], "lxml")
    root = soup.select_one(".mw-parser-output") or soup
    for el in root.select(DROP):
        el.decompose()
    for comment in root.find_all(string=lambda t: isinstance(t, Comment)):
        comment.extract()
    current = {"level": 1, "title": "Introduction", "parts": []}
    result = [current]
    skipping = 0                                    # level of a skipped section, 0 = none

    def blocks(node):
        for child in node.children:
            if isinstance(child, Tag):
                heading = child if child.name in ("h2", "h3", "h4") else None
                if heading is None and child.name == "div" and "mw-heading" in (child.get("class") or []):
                    heading = child.find(["h2", "h3", "h4"])
                if heading is not None:
                    yield "h", heading
                elif child.name in ("section",):
                    yield from blocks(child)
                elif child.name == "div" and child.find(["table", "p", "ul"]) is not None \
                        and child.find(["h2", "h3", "h4"]) is None:
                    yield "b", child
                elif child.name == "div":
                    yield from blocks(child)
                else:
                    yield "b", child

    for kind, el in blocks(root):
        if kind == "h":
            level = int(el.name[1])
            title = re.sub(r"\s+", " ", el.get_text()).strip()
            if skipping and level > skipping:
                continue
            skipping = level if title.lower() in SKIP_SECTIONS else 0
            if skipping:
                continue
            current = {"level": level, "title": title, "parts": []}
            result.append(current)
        elif not skipping:
            html = sanitize(el)
            if html:
                current["parts"].append(html)
    return result


def main():
    for lang in ([a for a in sys.argv[1:] if a in PAGES] or list(PAGES)):
        chapters = []
        for title in PAGES[lang]:
            parsed = fetch(title)
            page = parsed["title"]
            url = "https://en.wikipedia.org/wiki/" + page.replace(" ", "_")
            trail: list[str] = []
            for sec in sections_of(parsed):
                html = "".join(sec["parts"])
                trail = trail[: max(sec["level"] - 2, 0)] + ([sec["title"]] if sec["level"] > 1 else [])
                if len(re.sub(r"<[^>]+>", "", html)) < 40:
                    continue
                path = " › ".join(trail) if trail else "Introduction"
                chapters.append({
                    "id": f"{page}#{path}", "page": page, "path": path, "level": sec["level"],
                    "url": url, "revid": parsed.get("revid"), "html": html,
                })
        out = DATA / "grammar" / lang / "reference.json"
        write_json(out, {
            "source": "English Wikipedia",
            "licence": "Text and tables from Wikipedia, licensed CC BY-SA 4.0; reformatted for this app.",
            "chapters": chapters,
        })
        tables = sum(c["html"].count("<table") for c in chapters)
        print(f"{lang}: {len(chapters)} sections, {tables} tables, {out.stat().st_size // 1024} KiB")
        if "-v" in sys.argv:
            for c in chapters:
                print("   ", c["id"], len(c["html"]), c["html"].count("<table"))


if __name__ == "__main__":
    main()
