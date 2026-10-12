"""Merge the parser output with the dictionary and write the data the app ships with.

For every word the parser's analysis is checked against the Wiktionary inflection
tables: a lemma the dictionary does not know is replaced by the lemma whose table
contains the form, and a case/number/person the table rules out is corrected.
Corrections are flagged so the app can say that it made them.

Input : build/parsed/<lang>/*.json, build/lex/<lang>.json
Output: lang_gram/data/texts/<lang>/<work>.json.gz
        lang_gram/data/lexicon/<lang>.json.gz
"""
from __future__ import annotations

import gzip
import json
import re
import sys
from collections import Counter, defaultdict

from common import DATA, ROOT, read_json

sys.path.insert(0, str(ROOT))
from lang_gram.morph import (POS_COMPAT, apply_cats, format_feats, norm_form, parse_feats,  # noqa: E402
                             spelling_variants, tags_to_cats, ud_to_cats)

sys.path.insert(0, str(ROOT / "tools"))
from build_lexicon import single_word  # noqa: E402

PARSED = ROOT / "build" / "parsed"
LEX = ROOT / "build" / "lex"

NOMINAL = {"NOUN", "PROPN", "ADJ", "DET", "PRON", "NUM"}
CHECKED = ("case", "number", "gender", "person", "tense", "mood", "voice", "verbform", "degree")


def write_gz(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    with gzip.GzipFile(path, "wb", mtime=0) as fh:
        fh.write(raw)
    return len(raw)


# Closed-class words that the Wiktionary extract happens to lack.
SUPPLEMENT = {
    "la": [{"w": "-que", "k": "que", "p": "conj", "h": "-que (enclitic)",
            "g": ["and (enclitic: attached to the end of the second of two connected words)"]}],
    "cs": [{"w": "i", "k": "i", "p": "conj", "h": "i", "g": ["and; and also", "even, too (as a particle)"]},
           {"w": "-li", "k": "li", "p": "conj", "h": "-li (enclitic)", "g": ["if; whether (attached to the first word of its clause)"]}],
    "pl": [{"w": "i", "k": "i", "p": "conj", "h": "i", "g": ["and", "also, too; even (as a particle)"]}],
    "de": [],
}

# Forms of the personal pronouns whose lemma taggers and tables disagree about.
PRONOUN_LEMMA = {
    "de": {"mich": "ich", "mir": "ich", "dich": "du", "dir": "du", "ihn": "er", "ihm": "er", "uns": "wir",
           "euch": "ihr"},
    "la": {}, "cs": {}, "pl": {},
}

DERIVED = (("participle", "participle"), ("comparative", "comparative"), ("superlative", "superlative"),
           ("adverb", "adverb"))


def lemma_key(lang: str, s: str) -> str:
    """Key for comparing lemmas: Latin taggers write u for v."""
    key = norm_form(lang, s)
    if lang == "la":
        return key.replace("v", "u")
    if lang == "de":
        return key.replace("ß", "ss")           # the tagger writes Grossmutter, Fuss
    return key


class Lexicon:
    def __init__(self, lang: str):
        self.lang = lang
        data = read_json(LEX / f"{lang}.json")
        self.entries = data["entries"]
        for extra in SUPPLEMENT[lang]:
            self.entries.append(dict({"t": [], "f": [], "x": []}, **extra))
        self.by_key = defaultdict(list)             # lemma key -> entry ids
        self.by_form = defaultdict(list)            # form key  -> (entry id, tags or None)
        derived = defaultdict(list)                 # form key  -> (base entry id, kind)
        for i, e in enumerate(self.entries):
            self.by_key[lemma_key(lang, e["k"])].append(i)
            self.by_form[e["k"]].append((i, None))
            seen = set()
            for form, tags in e["f"]:
                word = single_word(lang, form, tags)
                if not word:
                    continue
                key = norm_form(lang, word)
                if (key, tags) in seen:
                    continue
                seen.add((key, tags))
                self.by_form[key].append((i, tags))
                if lang == "la" and e["p"] == "verb" and "participle" in tags.split() and key != e["k"]:
                    derived[key].append((i, "participle"))
            for form, tags in e.get("x", []):
                if " " in form:
                    continue
                for tag, kind in DERIVED[1:]:
                    if tag in tags.split() and e["p"] in ("adj", "adv"):
                        derived[norm_form(lang, form)].append((i, kind))
        for key, refs in data["formof"].items():
            for lemma, pos, tags in refs:
                for i in self.by_key.get(lemma_key(lang, lemma), []):
                    if self.entries[i]["p"] == pos or pos in ("verb", "participle") and self.entries[i]["p"] == "verb":
                        self.by_form[key].append((i, tags))
        # Which lemmas stand behind an entry: its own, plus the verb of a participle,
        # the positive of a comparative, the adjective of an adverb.
        self.bases = []
        for i, e in enumerate(self.entries):
            links = []
            for j, kind in derived.get(e["k"], []):
                if j == i:
                    continue
                if kind == "participle" and not (e["p"] == "verb" and any("nominative" in t for _, t in e["f"])):
                    continue
                if kind in ("comparative", "superlative") and e["p"] not in ("adj", "adv"):
                    continue
                if kind == "adverb" and e["p"] != "adv":
                    continue
                links.append((j, kind))
            if e.get("of") and not links:
                for j in self.by_key.get(lemma_key(lang, e["of"]), []):
                    links.append((j, "form"))
            self.bases.append(links)
        self._cats = {}

    def cats(self, tags: str | None):
        if tags is None:
            return {}
        if tags not in self._cats:
            self._cats[tags] = tags_to_cats(self.lang, tags.split())
        return self._cats[tags]

    def base_keys(self, i: int) -> set[str]:
        keys = {lemma_key(self.lang, self.entries[i]["k"])}
        keys.update(lemma_key(self.lang, self.entries[j]["k"]) for j, _ in self.bases[i])
        return keys


OLD_SPELLING = re.compile(r"^(obsolete|archaic|dated|alternative|nonstandard|superseded|former|formerly standard|"
                          r"pre-\d+|misspelling|eye dialect|rare) (spelling|form|typography|variant)", re.I)


def score(lex: Lexicon, i, cell_tags, upos, lemma_keys, cats, freq, lower=False):
    entry = lex.entries[i]
    if upos not in POS_COMPAT.get(entry["p"], ()):
        return None
    s = -3.0 if (lower and entry["p"] == "name" and lex.lang != "de") else 0.0
    bases = lex.base_keys(i)
    lemma_hit = bool(bases & lemma_keys)
    if lemma_hit:
        s += 6
    else:
        s += min(1.0, max(freq.get(k, 0) for k in bases) / 20)     # lemmas seen elsewhere in the texts
    # Prefer the obvious part of speech (noun entry for NOUN ...).
    if upos == {"noun": "NOUN", "name": "PROPN", "verb": "VERB", "adj": "ADJ", "adv": "ADV", "pron": "PRON",
                "det": "DET", "num": "NUM", "prep": "ADP", "conj": "CCONJ", "article": "DET",
                "intj": "INTJ", "particle": "PART"}.get(entry["p"]):
        s += 1.5
    if upos == "AUX" and entry["p"] == "verb":
        s += 1.5
    deponent = "deponent" in entry["h"]
    cell = lex.cats(cell_tags)
    for name in CHECKED:
        want = cats.get(name)
        have = cell.get(name)
        if want is None or have is None or (name == "voice" and deponent):
            continue
        s += 1 if want in have else -1
    if cell_tags is None and upos in NOMINAL | {"VERB", "AUX"}:
        s -= 0.5                                   # head-word match without a table cell
    if not entry["g"]:
        s -= 1
    elif OLD_SPELLING.match(entry["g"][0]) and not entry["f"]:
        s -= 3
    return s, lemma_hit


def reconcile(lex: Lexicon, word, surface, stats, freq):
    """Pick the dictionary entry behind *word*; return (entry id, lemma, feats, flags)."""
    lang = lex.lang
    upos, feats = word["upos"], parse_feats(word["feats"])
    flags = "m" if word.get("mwt") else ""
    lemma = word["lemma"]
    if upos in ("PUNCT", "SYM", "X") or not any(ch.isalpha() for ch in word["norm"]):
        return -1, lemma, feats, flags

    base = [norm_form(lang, word["norm"])]
    if norm_form(lang, surface) not in base and not word.get("mwt"):
        base.append(norm_form(lang, surface))
    keys = list(dict.fromkeys(base + [v for k in base for v in spelling_variants(lang, k)]))
    lemma = PRONOUN_LEMMA[lang].get(base[0], lemma)
    lemma_keys = {lemma_key(lang, lemma)}
    if "alt" in word:
        lemma_keys.add(lemma_key(lang, word["alt"][0]))
    cats = ud_to_cats(lang, upos, feats)

    scored = []
    for rank, key in enumerate(keys):
        for i, tags in lex.by_form.get(key, ()):
            got = score(lex, i, tags, upos, lemma_keys, cats, freq, surface[:1].islower())
            if got is not None:
                scored.append((got[0] - 0.75 * (rank > 0), got[1], i, tags))
    if lang == "de" and upos == "NOUN" and base[0].endswith("e") and not any(hit for _, hit, _, _ in scored):
        # Old dative singular in -e: dem Kinde, im Walde.
        for i, tags in lex.by_form.get(base[0][:-1], ()):
            got = score(lex, i, tags, upos, lemma_keys, dict(cats, case="dative", number="singular"), freq)
            if got is not None and got[1] and lex.entries[i]["p"] == "noun":
                scored.append((got[0], True, i, None))
    if not any(hit for _, hit, _, _ in scored):
        # The parser's own lemma has an entry (form missing from its table, or another
        # part of speech such as the locative "domi" tagged as an adverb): trust it.
        own = [i for i in lex.by_key.get(lemma_key(lang, lemma), [])]
        compatible = [i for i in own if upos in POS_COMPAT.get(lex.entries[i]["p"], ())]
        with_form = [(i, t) for k in keys for i, t in lex.by_form.get(k, ()) if i in own]
        if with_form:
            stats["confirmed"] += 1
            return with_form[0][0], lex.entries[with_form[0][0]]["w"], feats, flags
        if compatible and (upos in ("VERB", "AUX") or not scored):
            stats["lemma only"] += 1
            return compatible[0], lex.entries[compatible[0]]["w"], feats, flags
    if not scored:
        stats["not in dictionary"] += 1
        return -1, lemma, feats, flags

    scored.sort(key=lambda t: -t[0])
    best_score, lemma_hit, best_i, best_tags = scored[0]
    entry = lex.entries[best_i]
    if lemma_hit:
        stats["confirmed"] += 1
    else:
        flags += "L"
        stats["lemma changed"] += 1

    # "die: form of der" - go to the real entry when it has the form in its own table.
    plain = [j for j, kind in lex.bases[best_i] if kind == "form"
             and upos in POS_COMPAT.get(lex.entries[j]["p"], ()) and lex.entries[j]["p"] != "verb"]
    if plain:
        hit = [(j, t) for k in keys for j, t in lex.by_form.get(k, ()) if j in plain]
        if hit:
            best_i = hit[0][0]
            entry = lex.entries[best_i]
            scored = [(0, True, j, t) for j, t in hit]
    # The lemma shown is the dictionary's own spelling (macrons, capitals); for a
    # participle it is the verb.
    lemma = entry["w"]
    verbs = [j for j, kind in lex.bases[best_i] if kind in ("participle", "form") and lex.entries[j]["p"] == "verb"]
    if verbs and upos in ("VERB", "AUX"):
        hit = [j for j in verbs if lemma_key(lang, lex.entries[j]["k"]) in lemma_keys]
        pick = hit[0] if hit else max(verbs, key=lambda j: freq.get(lemma_key(lang, lex.entries[j]["k"]), 0))
        lemma = lex.entries[pick]["w"]

    # Do the table cells of this entry agree with the parser?
    cells = [lex.cats(t) for s, lh, i, t in scored if i == best_i and t is not None]
    verbform = cats.get("verbform")
    cells = [c for c in cells if not (verbform and c.get("verbform") and verbform not in c["verbform"]
                                      and not (verbform == "gerundive" and "participle" in c["verbform"]))]
    if cells and lang in ("la", "de"):
        if cats.get("verbform") == "finite":
            names = ["person", "number", "tense", "mood"]
        elif lang == "la" and (upos in NOMINAL or verbform in ("participle", "gerundive")):
            names = ["case", "number"]
        else:
            names = []
        names = [n for n in names if n in cats]
        if names and not any(all(cats[n] in c.get(n, {cats[n]}) for n in names) for c in cells):
            def agreement(c):
                return sum(cats[n] in c.get(n, ()) for n in names)
            def specific(c):
                return sum(len(c.get(n, ())) == 1 for n in names)
            ranked = sorted(cells, key=lambda c: (agreement(c), specific(c)), reverse=True)
            top = [c for c in ranked if agreement(c) == agreement(ranked[0])]
            choice = {n: next(iter(top[0][n])) for n in names if len(top[0].get(n, ())) == 1}
            # every equally good cell must be compatible with the chosen reading
            same = all(choice[n] in c.get(n, {choice[n]}) for c in top for n in choice)
            swap = {cats.get("case"), choice.get("case")}
            if choice and same and swap != {"dative", "ablative"} and choice.get("number") != "dual":
                feats = apply_cats(lang, feats, choice, names)
                flags += "F"
                stats["features corrected"] += 1
    # Nouns: the dictionary knows the gender.
    if upos in ("NOUN", "PROPN") and entry["p"] in ("noun", "name"):
        genders = {"masculine": "Masc", "feminine": "Fem", "neuter": "Neut"}
        have = [genders[t] for t in entry["t"] if t in genders]
        if len(have) == 1 and feats.get("Gender", have[0]).split(",")[0] != have[0]:
            feats["Gender"] = have[0]
            stats["gender from dictionary"] += 1
    return best_i, lemma, feats, flags


def fix_german_person(sent):
    """The HDT model labels second-person forms as first person; GSD gets them right."""
    second = {"du", "dich", "dir", "euch", "ihr"}
    for w in sent:
        f = parse_feats(w["feats"])
        if f.get("Person") != "1":
            continue
        alt = parse_feats(w["alt"][2]) if "alt" in w else {}
        form = w["norm"].lower()
        if alt.get("Person") == "2" or (w["upos"] == "PRON" and form in second) or \
                (w["upos"] == "DET" and form.startswith(("dein", "euer", "eur"))):
            f["Person"] = "2"
            if alt.get("Person") == "2" and "Number" in alt:
                f["Number"] = alt["Number"]
            w["feats"] = format_feats(f)


INTERJECTIONS = {"de": {"ach": "INTJ", "ei": "INTJ", "o": "INTJ", "oh": "INTJ", "nein": "PART", "ja": "PART"}}


def infer_german_case(sent):
    """HDT leaves the case of most nouns unmarked; recover it from the noun phrase."""
    by_id = {w["id"]: w for w in sent}
    kids = defaultdict(list)
    for w in sent:
        kids[w["head"]].append(w)

    def phrase_case(noun):
        for k in kids[noun["id"]]:
            f = parse_feats(k["feats"])
            if k["upos"] == "DET" and k["deprel"].startswith("det") and "Case" in f:
                return f["Case"]
        for k in kids[noun["id"]]:
            f = parse_feats(k["feats"])
            if k["upos"] == "ADP" and "Case" in f:
                return f["Case"]
        if "alt" in noun:
            f = parse_feats(noun["alt"][2])
            if "Case" in f:
                return f["Case"]
        rel = noun["deprel"]
        if rel in ("nsubj", "nsubj:pass", "vocative", "root"):
            return "Nom"
        if rel == "obj":
            return "Acc"
        if rel in ("iobj", "obl:arg"):
            return "Dat"
        if rel == "nmod" and not any(k["upos"] == "ADP" for k in kids[noun["id"]]):
            return "Gen"
        return None

    for w in sent:
        f = parse_feats(w["feats"])
        if w["upos"] in ("NOUN", "PROPN") and "Case" not in f:
            case = phrase_case(w)
            if case is None and w["deprel"] in ("conj", "appos", "flat", "flat:name") and w["head"] in by_id:
                case = parse_feats(by_id[w["head"]]["feats"]).get("Case")
            if case:
                f["Case"] = case
                w["feats"] = format_feats(f)
                w["inferred"] = True
    for w in sent:
        f = parse_feats(w["feats"])
        if w["upos"] == "ADJ" and "Case" not in f and w["deprel"] == "amod" and w["head"] in by_id:
            case = parse_feats(by_id[w["head"]]["feats"]).get("Case")
            if case:
                f["Case"] = case
                w["feats"] = format_feats(f)
                w["inferred"] = True


def build_language(lang: str):
    lex = Lexicon(lang)
    stats = Counter()
    used = set()
    docs = []
    extra_lemmas = set()
    paths = sorted((PARSED / lang).glob("*.json"))
    freq = Counter()
    for path in paths:
        for section in read_json(path)["sections"]:
            for para in section["paras"]:
                for sent in para["sents"]:
                    freq.update(lemma_key(lang, w["lemma"]) for w in sent if w["upos"] != "PUNCT")
    for path in paths:
        doc = read_json(path)
        for section in doc["sections"]:
            for para in section["paras"]:
                out_sents = []
                for sent in para["sents"]:
                    for w in sent:
                        if w["upos"] != "PUNCT" and not any(ch.isalnum() for ch in w["norm"]):
                            # dashes and stray quotes the tagger took for words
                            w["upos"], w["feats"], w["deprel"], w["lemma"] = "PUNCT", "", "punct", w["norm"]
                        fixed = INTERJECTIONS.get(lang, {}).get(w["norm"].lower())
                        if fixed and w["upos"] in ("PRON", "VERB", "DET", "X", "NOUN", "ADJ"):
                            w["upos"], w["feats"], w["lemma"] = fixed, "", w["norm"].lower()
                    if lang == "de":
                        fix_german_person(sent)
                        infer_german_case(sent)
                        by_id = {w["id"]: w for w in sent}
                        for w in sent:                    # ging ... fort -> fortgehen
                            if w["deprel"] == "compound:prt" and w["head"] in by_id:
                                extra_lemmas.add(lemma_key(lang, w["norm"] + by_id[w["head"]]["lemma"]))
                    ids = {w["id"]: n + 1 for n, w in enumerate(sent)}
                    out = []
                    for w in sent:
                        surface = para["text"][w["start"]:w["end"]]
                        i, lemma, feats, flags = reconcile(lex, w, surface, stats, freq)
                        if w.get("inferred"):
                            flags += "i"
                        if i >= 0:
                            used.add(i)
                        stats["words"] += w["upos"] != "PUNCT"
                        tok = [w["start"], w["end"], lemma, w["upos"], format_feats(feats),
                               ids.get(w["head"], 0), w["deprel"], i, flags]
                        if norm_form(lang, w["norm"]) != norm_form(lang, surface):
                            tok.append(w["norm"])       # part of a contraction, or modernised spelling
                        out.append(tok)
                    out_sents.append(out)
                para["sents"] = out_sents
        docs.append(doc)

    # Ship only the entries that are referred to, plus the verbs behind participles
    # and the full forms of separable verbs.
    for i in list(used):
        used.update(j for j, _ in lex.bases[i])
    for key in extra_lemmas:
        used.update(j for j in lex.by_key.get(key, []) if lex.entries[j]["p"] == "verb")
    remap = {old: new for new, old in enumerate(sorted(used))}
    entries = []
    for old in sorted(used):
        e = lex.entries[old]
        slim = {"w": e["w"], "k": e["k"], "p": e["p"], "h": e["h"], "g": e["g"], "t": e["t"], "f": e["f"]}
        links = [[remap[j], kind] for j, kind in lex.bases[old] if j in remap]
        if links:
            slim["of"] = links
        entries.append(slim)
    size = write_gz(DATA / "lexicon" / f"{lang}.json.gz", {
        "lang": lang,
        "source": "English Wiktionary (CC BY-SA 4.0), machine-readable extract by kaikki.org / Wiktextract",
        "entries": entries,
    })
    print(f"{lang}: lexicon {len(entries)} entries ({size / 1e6:.1f} MB raw)")
    for doc in docs:
        for section in doc["sections"]:
            for para in section["paras"]:
                for sent in para["sents"]:
                    for tok in sent:
                        tok[7] = remap.get(tok[7], -1)
        size = write_gz(DATA / "texts" / lang / f"{doc['id']}.json.gz", doc)
        print(f"  {doc['id']}: {size / 1e6:.1f} MB raw")
    total = stats["words"] or 1
    print("  " + ", ".join(f"{k}: {v} ({100 * v / total:.1f}%)" for k, v in stats.most_common()))


def main():
    for lang in (sys.argv[1:] or ["la", "de", "cs", "pl"]):
        build_language(lang)


if __name__ == "__main__":
    main()
