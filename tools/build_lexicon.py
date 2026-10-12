"""Pull from the English Wiktionary extract (kaikki.org) every entry that could
stand behind a word of our texts: its glosses, grammatical class and the whole
inflection table.

Input : build/cache/kaikki/<Language>.jsonl.gz  (downloaded on demand)
        build/parsed/<lang>/*.json              (to know which forms occur)
Output: build/lex/<lang>.json   {"entries": [...], "formof": {form: [[lemma, pos, tags], ...]}}

The dumps are data from the network: they are only ever read as JSON.
"""
from __future__ import annotations

import gzip
import json
import re
import sys

from common import CACHE, ROOT, USER_AGENT, read_json, write_json

sys.path.insert(0, str(ROOT))
from lang_gram.morph import norm_form, spelling_variants  # noqa: E402

KAIKKI = {"la": "Latin", "de": "German", "cs": "Czech", "pl": "Polish"}
PARSED = ROOT / "build" / "parsed"
LEX = ROOT / "build" / "lex"

POS_KEEP = {"noun", "name", "verb", "adj", "adv", "pron", "det", "num", "prep", "postp", "conj", "particle",
            "intj", "article", "contraction", "participle"}
SKIP_FORM_TAGS = {"table-tags", "inflection-template", "class", "romanization", "auxiliary"}
CLASS_TAGS = {
    "masculine", "feminine", "neuter", "animate", "inanimate", "person", "personal", "virile", "nonvirile",
    "animal-not-person", "imperfective", "perfective", "strong", "weak", "mixed", "irregular", "deponent",
    "semi-deponent", "impersonal", "defective", "indeclinable", "reflexive", "transitive", "intransitive",
    "plural-only", "singular-only", "uncountable", "two-termination", "one-termination", "three-termination",
    "pluralia-tantum", "preterite-present", "separable", "auxiliary",
}
CLASS_PREFIX = ("declension-", "conjugation-", "class-")
ARTICLES = {"der", "die", "das", "des", "dem", "den", "ein", "eine", "eines", "einem", "einen", "einer",
            "kein", "keine", "keines", "keinem", "keinen", "keiner", "am"}
LOW_VALUE = {"obsolete", "archaic", "dated", "rare", "nonstandard", "dialectal", "misspelling", "Medieval-Latin",
             "New-Latin", "Ecclesiastical", "Late-Latin", "humorous", "slang", "vulgar"}


def corpus_forms(lang: str) -> tuple[set[str], set[str]]:
    """Normalised forms (with spelling variants) and parser lemmas of the parsed texts."""
    forms, lemmas = set(), set()
    for path in sorted((PARSED / lang).glob("*.json")):
        for section in read_json(path)["sections"]:
            for para in section["paras"]:
                for sent in para["sents"]:
                    for w in sent:
                        if w["upos"] == "PUNCT":
                            continue
                        for surface in (w["norm"], para["text"][w["start"]:w["end"]]):
                            key = norm_form(lang, surface)
                            forms.add(key)
                            forms.update(spelling_variants(lang, key))
                        lemmas.add(norm_form(lang, w["lemma"]))
                        if "alt" in w:
                            lemmas.add(norm_form(lang, w["alt"][0]))
    return forms, lemmas


def single_word(lang: str, form: str, tags) -> str | None:
    """The one orthographic word of a table cell, or None for periphrases."""
    form = form.strip()
    if not form or form == "-" or form.startswith("-") or "+" in form:
        return None
    parts = form.split()
    if len(parts) > 1 and lang == "de" and all(p.lower() in ARTICLES for p in parts[:-1]):
        return parts[-1]
    if len(parts) > 1 and lang == "pl" and parts[-1] == "się":
        return None
    return form if len(parts) == 1 else None


def clean_gloss(g: str) -> str:
    g = re.sub(r"\s+", " ", g).strip()
    return g[:220] + ("…" if len(g) > 220 else "")


def reduce_entry(lang: str, d: dict) -> dict | None:
    senses = d.get("senses") or []
    forms = d.get("forms") or []
    table = []
    for f in forms:
        tags = f.get("tags") or []
        if SKIP_FORM_TAGS & set(tags) or not f.get("form"):
            continue
        if f.get("source") in ("declension", "conjugation"):
            table.append([f["form"], " ".join(tags)])
    form_of = [fo.get("word") for s in senses for fo in (s.get("form_of") or []) if fo.get("word")]
    all_form_of = bool(senses) and all(s.get("form_of") for s in senses)

    canonical = next((f["form"] for f in forms if "canonical" in (f.get("tags") or [])
                      and " " not in f["form"]), None) or d["word"]
    glosses, low = [], []
    classes = set()
    for s in senses:
        tags = set(s.get("tags") or [])
        classes |= {t for t in tags if t in CLASS_TAGS or t.startswith(CLASS_PREFIX)}
        gl = s.get("glosses") or []
        if not gl:
            continue
        text = clean_gloss(gl[-1] if len(gl) == 1 else gl[0] + ": " + gl[-1] if len(gl[0]) < 40 else gl[-1])
        (low if tags & LOW_VALUE else glosses).append(text)
    glosses = list(dict.fromkeys(glosses + low))[:6]
    head = next((h.get("expansion") for h in d.get("head_templates") or [] if h.get("expansion")), "")
    head_forms = [[f["form"], " ".join(f.get("tags") or [])] for f in forms
                  if f.get("source") is None and f.get("form") and "canonical" not in (f.get("tags") or [])
                  and not SKIP_FORM_TAGS & set(f.get("tags") or [])][:12]
    entry = {"w": canonical, "k": norm_form(lang, d["word"]), "p": d.get("pos"), "h": head[:300],
             "g": glosses, "t": sorted(classes), "f": table, "x": head_forms}
    if all_form_of and form_of:
        entry["of"] = form_of[0]
    return entry


def scan(lang: str, forms: set[str], lemmas: set[str]):
    path = CACHE / "kaikki" / f"{KAIKKI[lang]}.jsonl.gz"
    if not path.exists():
        import requests
        url = f"https://kaikki.org/dictionary/{KAIKKI[lang]}/kaikki.org-dictionary-{KAIKKI[lang]}.jsonl.gz"
        print(f"  downloading {url}")
        path.parent.mkdir(parents=True, exist_ok=True)
        with requests.get(url, headers={"User-Agent": USER_AGENT}, stream=True, timeout=600) as r:
            r.raise_for_status()
            with open(path, "wb") as fh:
                for chunk in r.iter_content(1 << 20):
                    fh.write(chunk)
    entries, formof = [], {}
    n = 0
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        for line in fh:
            n += 1
            d = json.loads(line)
            if d.get("pos") not in POS_KEEP or " " in d.get("word", " "):
                continue
            key = norm_form(lang, d["word"])
            entry = reduce_entry(lang, d)
            if entry is None:
                continue
            if not entry["f"] and "of" in entry:
                # A page that only says "accusative singular of X".
                if key in forms:
                    for s in d.get("senses") or []:
                        for fo in s.get("form_of") or []:
                            tags = [t for t in s.get("tags") or [] if t != "form-of"]
                            formof.setdefault(key, []).append([fo["word"], d["pos"], " ".join(tags)])
                continue
            wanted = key in forms or key in lemmas
            if not wanted:
                for form, tags in entry["f"]:
                    word = single_word(lang, form, tags)
                    if word and norm_form(lang, word) in forms:
                        wanted = True
                        break
            if wanted:
                entries.append(entry)
    print(f"  scanned {n} dictionary entries")
    return entries, formof


def main():
    for lang in (sys.argv[1:] or list(KAIKKI)):
        forms, lemmas = corpus_forms(lang)
        print(f"{lang}: {len(forms)} distinct forms, {len(lemmas)} parser lemmas", flush=True)
        entries, formof = scan(lang, forms, lemmas)
        # Keep entries referred to by "form of" notes even when no table form matched.
        write_json(LEX / f"{lang}.json", {"entries": entries, "formof": formof})
        size = (LEX / f"{lang}.json").stat().st_size
        print(f"  kept {len(entries)} entries, {len(formof)} form-of keys, {size / 1e6:.1f} MB", flush=True)


if __name__ == "__main__":
    main()
