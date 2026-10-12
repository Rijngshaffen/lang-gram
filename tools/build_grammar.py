"""Cut Allen and Greenough's New Latin Grammar (fts.txt, an OCR scan) into its
numbered sections so the app can quote the paragraph that explains a form.

Output: lang_gram/data/grammar/la/allen_greenough.json   {"sections": {"419": "...", ...}}
"""
from __future__ import annotations

import re
import sys

from common import DATA, ROOT, write_json

SOURCE = ROOT / "fts.txt"
LAST_SECTION = 642

# Running heads: "240 SYNTAX: CONSTRUCTION OF CASES [§§ 386, 387" / "§§ 387, 388] ACCUSATIVE ... 241"
PAGE_HEAD = re.compile(
    r"^\s*(?:\d{1,3}\s+[“\"']?[A-Z][A-Z :;,.’'\-]+\s*\[\s*[§$S]{1,2}\s*[\d ,.\-—]+"
    r"|[§$]{1,2}\s*[\d ,.\-—]+\]\s*[A-Z][A-Z :;,.’'\-]+\s*\d{0,3})\s*$"
)


def clean(text: str) -> str:
    text = re.sub(r"(\w)- (?=[a-z])", r"\1", text)        # re-join words hyphenated at line ends
    text = text.replace(" : —", ":").replace(": —", ":").replace(":—", ":")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" ([,;.])", r"\1", text)
    # The OCR read macrons as accents or digits: é = ē, "6" inside a word = ō, "4" = ā.
    text = text.replace("é", "ē").replace("É", "Ē")
    text = re.sub(r"(?<=[a-z])6(?=[a-z]|\b)", "ō", text)
    text = re.sub(r"(?<=[a-z])4(?=[a-z])", "ā", text)
    return text.strip()


def split_sections(lines: list[str]) -> dict[int, str]:
    body = [ln for ln in lines if not PAGE_HEAD.match(ln)]
    start = next(i for i, ln in enumerate(body) if ln.startswith("1. The Latin Alphabet"))
    text = "\n".join(body[start:])
    # Stop before the indexes that follow the last section.
    end = re.search(r"\nINDEX OF VERBS\b", text)
    if end:
        text = text[: end.start()]

    positions = {1: 0}
    cursor = 0
    for n in range(2, LAST_SECTION + 1):
        # A section number opens a line, or follows a run-in heading / the end of a sentence.
        at_line = re.compile(rf"(?m)^(?:[A-Z][A-Za-z,’' \-]{{2,60}} )?{n}\. ?(?=[A-Z“\[(])")
        mid_line = re.compile(rf"(?<=[.:;!?\]] ){n}\. (?=[A-Z])")
        window = text[cursor: cursor + 60000]
        found = None
        for m in at_line.finditer(window):
            # In-section lists ("1. ... 2. ...") never get as far as the next section number.
            found = m
            break
        mid = mid_line.search(window)
        if mid and (found is None or mid.start() + 2500 < found.start()):
            found = mid
        if found is None:
            continue
        num_at = found.group(0).rfind(f"{n}.")
        cursor = cursor + found.start() + max(num_at, 0)
        positions[n] = cursor

    order = sorted(positions.items(), key=lambda kv: kv[1])
    sections = {}
    for (n, pos), nxt in zip(order, order[1:] + [(None, len(text))]):
        chunk = text[pos: nxt[1]]
        chunk = re.sub(rf"^{n}\.\s*", "", chunk)
        sections[n] = chunk
    return sections


def to_paragraphs(chunk: str) -> list[str]:
    """Keep the original paragraphing, dropping footnote debris and stray headings."""
    paras = []
    for raw in chunk.split("\n"):
        line = clean(raw)
        if not line or len(line) < 3:
            continue
        if re.fullmatch(r"[\W\d_]+", line):
            continue
        if re.match(r"^\d \S", line) and len(line) < 400 and not re.match(r"^\d\. ", line):
            continue                                   # footnote ("1 Such are aequalis, ...")
        paras.append(line)
    # A trailing all-caps line is the heading of the *next* group of sections.
    while paras and (paras[-1].isupper() or len(paras[-1]) < 40 and paras[-1].istitle()):
        paras.pop()
    return paras


def main():
    lines = SOURCE.read_text(encoding="utf-8", errors="replace").splitlines()
    sections = split_sections(lines)
    missing = [n for n in range(1, LAST_SECTION + 1) if n not in sections]
    out = {str(n): to_paragraphs(chunk) for n, chunk in sorted(sections.items())}
    out = {n: p for n, p in out.items() if p}
    write_json(DATA / "grammar" / "la" / "allen_greenough.json", {
        "title": "Allen and Greenough's New Latin Grammar",
        "edition": "Ginn & Company, Boston 1903 (public domain; OCR text of the Internet Archive scan)",
        "sections": out,
    })
    size = sum(len(x) for p in out.values() for x in p)
    print(f"{len(out)} sections, {size // 1024} KiB; not found: {missing}")
    if "-v" in sys.argv:
        for n, p in out.items():
            print(f"§{n} [{len(p)} par, {sum(map(len, p))} ch] {p[0][:110]}")


if __name__ == "__main__":
    main()
