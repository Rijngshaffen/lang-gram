"""Morphological vocabulary shared by the app and the build tools.

Two tag worlds meet here:

* Universal Dependencies features produced by the parser ("Case=Abl|Number=Plur"),
* the plain-English tags of Wiktionary inflection tables ("ablative", "plural").

Both are reduced to the same small dictionary of *categories*
({"case": "ablative", "number": "plural", ...}) so that a word in a text can be
located in a paradigm and described in words.
"""
from __future__ import annotations

import unicodedata

LANGS = {"la": "Latin", "de": "German", "cs": "Czech", "pl": "Polish"}


# --------------------------------------------------------------------------- #
# Spelling normalisation for look-ups
# --------------------------------------------------------------------------- #
def norm_form(lang: str, s: str) -> str:
    """Key under which a written form is looked up (case- and macron-insensitive)."""
    s = unicodedata.normalize("NFC", s).lower()
    if lang == "la":
        s = "".join(c for c in unicodedata.normalize("NFD", s) if not unicodedata.combining(c))
        s = s.replace("æ", "ae").replace("œ", "oe").replace("j", "i")
    return s


def spelling_variants(lang: str, key: str) -> list[str]:
    """Modern spellings to try when an old-fashioned form is not in the dictionary."""
    out: list[str] = []
    if lang == "de":
        if "ß" in key:
            out.append(key.replace("ß", "ss"))
    elif lang == "pl":
        if key.endswith("iemi"):
            out.append(key[:-4] + "imi")
        elif key.endswith("emi"):
            out.append(key[:-3] + "ymi")
        if key.endswith("iem"):
            out.append(key[:-3] + "im")
        elif key.endswith("em"):
            out.append(key[:-2] + "ym")
        if "ó" in key:
            out.append(key.replace("ó", "u"))
        if "j" in key:
            out.append(key.replace("j", "i"))
        if key.startswith("nie") and len(key) > 5:
            out.append(key[3:])                     # negated verbs / adjectives written together
    elif lang == "cs":
        if key.endswith("ti") and len(key) > 3:
            out.append(key[:-1])                    # old infinitive: býti -> být
        if key.startswith("ne") and len(key) > 4:
            out.append(key[2:])                     # negation prefix
        if key.startswith("nej") and len(key) > 5:
            out.append(key[3:])
    elif lang == "la":
        if key.endswith("que") and len(key) > 4:
            out.append(key[:-3])
    return [v for v in out if v and v != key]


# --------------------------------------------------------------------------- #
# Categories
# --------------------------------------------------------------------------- #
CATEGORY_ORDER = ["verbform", "mood", "tense", "voice", "person", "number", "case", "gender", "animacy",
                  "degree", "inflection", "aspect"]

CASES = {"Nom": "nominative", "Gen": "genitive", "Dat": "dative", "Acc": "accusative", "Abl": "ablative",
         "Voc": "vocative", "Loc": "locative", "Ins": "instrumental"}
NUMBERS = {"Sing": "singular", "Plur": "plural", "Dual": "dual", "Ptan": "plural"}
GENDERS = {"Masc": "masculine", "Fem": "feminine", "Neut": "neuter"}
PERSONS = {"1": "first-person", "2": "second-person", "3": "third-person"}
MOODS = {"Ind": "indicative", "Sub": "subjunctive", "Imp": "imperative", "Cnd": "conditional"}
VOICES = {"Act": "active", "Pass": "passive"}
DEGREES = {"Pos": "positive", "Cmp": "comparative", "Sup": "superlative", "Abs": "superlative"}
ANIMACY = {"Anim": "animate", "Inan": "inanimate", "Hum": "personal", "Nhum": "animate"}

CASE_ORDER = {
    "la": ["nominative", "accusative", "genitive", "dative", "ablative", "vocative", "locative"],
    "de": ["nominative", "accusative", "dative", "genitive"],
    "cs": ["nominative", "genitive", "dative", "accusative", "vocative", "locative", "instrumental"],
    "pl": ["nominative", "genitive", "dative", "accusative", "instrumental", "locative", "vocative"],
}

_TAG_CATEGORY: dict[str, tuple[str, str]] = {}
for _v in CASES.values():
    _TAG_CATEGORY[_v] = ("case", _v)
for _v in ("singular", "plural", "dual"):
    _TAG_CATEGORY[_v] = ("number", _v)
for _v in GENDERS.values():
    _TAG_CATEGORY[_v] = ("gender", _v)
for _v in PERSONS.values():
    _TAG_CATEGORY[_v] = ("person", _v)
for _v in ("indicative", "subjunctive", "imperative", "conditional"):
    _TAG_CATEGORY[_v] = ("mood", _v)
for _v in ("active", "passive"):
    _TAG_CATEGORY[_v] = ("voice", _v)
for _v in ("infinitive", "participle", "gerund", "supine", "transgressive"):
    _TAG_CATEGORY[_v] = ("verbform", _v)
for _v in ("comparative", "superlative"):
    _TAG_CATEGORY[_v] = ("degree", _v)
for _v in ("strong", "weak", "mixed"):
    _TAG_CATEGORY[_v] = ("inflection", _v)
_TAG_CATEGORY.update({
    "virile": ("animacy", "personal"), "nonvirile": ("animacy", "nonpersonal"),
    "animate": ("animacy", "animate"), "inanimate": ("animacy", "inanimate"),
    "personal": ("animacy", "personal"),
    "subjunctive-i": ("mood", "subjunctive"), "subjunctive-ii": ("mood", "subjunctive"),
    "adjectival": ("verbform", "participle"), "adverbial": ("verbform", "transgressive"),
    "noun-from-verb": ("verbform", "verbal noun"),
})


def tags_to_cats(lang: str, tags) -> dict[str, set[str]]:
    """Categories named by a set of Wiktionary table tags (a cell may span several genders)."""
    tags = set(tags)
    cats: dict[str, set[str]] = {}
    for t in tags:
        hit = _TAG_CATEGORY.get(t)
        if hit:
            cats.setdefault(hit[0], set()).add(hit[1])
    # Tense is spread over several tags.
    tense = None
    if lang == "la":
        if "pluperfect" in tags:
            tense = "pluperfect"
        elif "future" in tags and "perfect" in tags:
            tense = "future perfect"
        elif "perfect" in tags:
            tense = "perfect"
        elif "imperfect" in tags:
            tense = "imperfect"
        elif "future" in tags:
            tense = "future"
        elif "present" in tags:
            tense = "present"
    else:
        if "multiword-construction" in tags:
            tense = "compound"
        elif "subjunctive-i" in tags or "present" in tags:
            tense = "present"
        elif "subjunctive-ii" in tags or "preterite" in tags or "past" in tags:
            tense = "past"
        elif "future" in tags:
            tense = "future"
    if tense:
        cats["tense"] = {tense}
    if "verbform" not in cats and ("person" in cats or cats.get("mood", set()) & {"indicative", "subjunctive",
                                                                                 "imperative", "conditional"}):
        cats["verbform"] = {"finite"}
    return cats


def parse_feats(feats: str) -> dict[str, str]:
    return dict(kv.split("=", 1) for kv in feats.split("|") if "=" in kv) if feats else {}


def format_feats(feats: dict[str, str]) -> str:
    return "|".join(f"{k}={v}" for k, v in sorted(feats.items(), key=lambda kv: kv[0].lower()))


def ud_to_cats(lang: str, upos: str, feats: dict[str, str]) -> dict[str, str]:
    """Describe a parsed word with the category vocabulary used for paradigm cells."""
    cats: dict[str, str] = {}

    def first(name, table):
        value = feats.get(name)
        if value:
            value = value.split(",")[0]
            if value in table:
                return table[value]
        return None

    for cat, name, table in (("case", "Case", CASES), ("number", "Number", NUMBERS), ("gender", "Gender", GENDERS),
                             ("person", "Person", PERSONS), ("mood", "Mood", MOODS), ("voice", "Voice", VOICES),
                             ("degree", "Degree", DEGREES), ("animacy", "Animacy", ANIMACY)):
        value = first(name, table)
        if value:
            cats[cat] = value
    if cats.get("degree") == "positive":
        del cats["degree"]

    vf, tense, aspect = feats.get("VerbForm"), feats.get("Tense"), feats.get("Aspect")
    is_verb = upos in ("VERB", "AUX")
    if vf == "Fin":
        cats["verbform"] = "finite"
    elif vf == "Inf":
        cats["verbform"] = "infinitive"
    elif vf == "Part":
        cats["verbform"] = "participle"
    elif vf == "Conv":
        cats["verbform"] = "supine" if lang == "la" else "transgressive"
    elif vf == "Ger":
        cats["verbform"] = "gerund"
    elif vf == "Gdv":
        cats["verbform"] = "gerundive"
    elif vf == "Sup":
        cats["verbform"] = "supine"
    elif vf == "Vnoun":
        cats["verbform"] = "verbal noun"

    if lang == "la":
        if vf == "Part" and aspect == "Prosp" and feats.get("Voice") == "Pass":
            cats["verbform"] = "gerundive"
        if vf in ("Part", "Inf") or (vf is None and is_verb and aspect):
            t = {"Perf": "perfect", "Imp": "present", "Prosp": "future"}.get(aspect or "")
            if t and cats.get("verbform") not in ("gerundive", "supine"):
                cats["tense"] = t
        elif vf == "Fin" or (is_verb and tense):
            if tense == "Pqp":
                cats["tense"] = "pluperfect"
            elif tense == "Fut":
                cats["tense"] = "future perfect" if aspect == "Perf" else "future"
            elif tense == "Past":
                cats["tense"] = "perfect" if aspect == "Perf" else "imperfect"
            elif tense == "Pres":
                cats["tense"] = "present"
        if cats.get("verbform") in ("gerundive", "supine"):
            cats.pop("voice", None)
    else:
        if tense:
            cats["tense"] = {"Pres": "present", "Past": "past", "Fut": "future", "Pqp": "pluperfect",
                             "Imp": "imperfect"}.get(tense.split(",")[0], tense.lower())
        if aspect and lang in ("cs", "pl"):
            cats["aspect"] = {"Imp": "imperfective", "Perf": "perfective"}.get(aspect.split(",")[0], aspect)
        if lang in ("cs", "pl") and vf == "Part" and tense == "Past":
            cats["verbform"] = "past participle (l-form)"
        if lang == "pl" and vf == "Fin" and tense == "Past":
            cats["verbform"] = "finite"
    return cats


# For writing a table cell's analysis back into UD features (build-time corrections).
_INV = {
    "case": ("Case", {v: k for k, v in CASES.items()}),
    "number": ("Number", {"singular": "Sing", "plural": "Plur", "dual": "Dual"}),
    "gender": ("Gender", {v: k for k, v in GENDERS.items()}),
    "person": ("Person", {v: k for k, v in PERSONS.items()}),
    "mood": ("Mood", {v: k for k, v in MOODS.items()}),
    "voice": ("Voice", {v: k for k, v in VOICES.items()}),
}
_LA_TENSE = {"present": ("Pres", "Imp"), "imperfect": ("Past", "Imp"), "future": ("Fut", "Imp"),
             "perfect": ("Past", "Perf"), "pluperfect": ("Pqp", "Perf"), "future perfect": ("Fut", "Perf")}


def apply_cats(lang: str, feats: dict[str, str], cats: dict[str, str], names) -> dict[str, str]:
    """Return a copy of *feats* with the categories listed in *names* taken from *cats*."""
    out = dict(feats)
    for name in names:
        value = cats.get(name)
        if value is None:
            continue
        if name == "tense":
            if lang == "la" and value in _LA_TENSE and out.get("VerbForm", "Fin") == "Fin":
                out["Tense"], out["Aspect"] = _LA_TENSE[value]
            elif lang != "la" and value in ("present", "past", "future"):
                out["Tense"] = value[:4].capitalize() if value != "future" else "Fut"
            continue
        if name in _INV:
            feat, table = _INV[name]
            if value in table:
                out[feat] = table[value]
    return out


# Which Wiktionary parts of speech can stand behind which UD tags.
POS_COMPAT = {
    "noun": {"NOUN", "PROPN"},
    "name": {"PROPN", "NOUN"},
    "verb": {"VERB", "AUX", "ADJ"},
    "participle": {"VERB", "AUX", "ADJ"},
    "adj": {"ADJ", "DET", "NUM", "VERB", "PRON"},
    "adv": {"ADV", "PART", "SCONJ", "CCONJ", "ADP"},
    "pron": {"PRON", "DET"},
    "det": {"DET", "PRON", "NUM"},
    "article": {"DET", "PRON"},
    "num": {"NUM", "DET", "ADJ"},
    "prep": {"ADP", "ADV"},
    "postp": {"ADP"},
    "conj": {"CCONJ", "SCONJ", "ADV", "PART"},
    "particle": {"PART", "ADV", "INTJ", "CCONJ", "SCONJ"},
    "intj": {"INTJ", "PART"},
    "contraction": {"ADP", "PRON", "DET", "AUX", "VERB", "SCONJ"},
}
