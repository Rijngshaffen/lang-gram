"""Czech: usage notes and the matching sections of the grammar reference."""
from __future__ import annotations

from . import lang_slavic

D, C = "Czech declension#", "Czech conjugation#"
REF = {
    "prepositions": [D + "Prepositions with certain cases"],
    "numerals": [D + "Plural forms"],
    "agreement": [C + "Participles › Agreement between subject and predicate"],
    "noun_syntax": [D + "Introduction"],
    "adjectives": [D + "Adjective › Hard declension", D + "Adjective › Soft declension"],
    "short": [D + "Adjective › Short forms"],
    "comparison": [D + "Adjective › Comparisons"],
    "possessive": [D + "Pronouns › Possessive pronouns"],
    "personal": [D + "Pronouns › Personal pronouns"],
    "relative": [D + "Pronouns › Interrogative and relative pronouns"],
    "past": [C + "Tenses › Past tense", C + "Participles › Past participle"],
    "conditional": [C + "Conditionals"],
    "future": [C + "Tenses › Future tense"],
    "aspect": [C + "Aspect"],
    "negation": [C + "Negation"],
    "reflexive": [C + "Reflexive verbs"],
    "imperative": [C + "Imperative"],
    "infinitive": [C + "Infinitive"],
    "passive": [C + "Passive voice", C + "Participles › Passive participle"],
    "transgressive": [C + "Transgressives"],
    "verbs": [C + "Tenses › Present tense"],
}


def notes(token, entry):
    return lang_slavic.notes("cs", token, entry, REF)


def verb_class(entry) -> str | None:
    third = next((f for f, tags in (entry or {}).get("f", []) if "third-person" in tags and "singular" in tags
                  and "present" in tags and "indicative" in tags), None)
    if not third:
        return None
    for ending, cls in (("ne", "II"), ("je", "III"), ("á", "V"), ("í", "IV"), ("e", "I")):
        if third.endswith(ending):
            return cls
    return None


def chapters(token, entry) -> list[str]:
    upos, feats, cats = token.upos, token.feats, token.cats
    out = []
    if upos in ("NOUN", "PROPN"):
        gender = cats.get("gender")
        if gender == "masculine":
            out.append(D + ("Nouns › Masculine animate" if cats.get("animacy") == "animate"
                            else "Nouns › Masculine inanimate"))
        elif gender == "feminine":
            out.append(D + "Nouns › Feminine")
        elif gender == "neuter":
            out.append(D + "Nouns › Neuter")
        out.append(D + "Nouns")
    elif upos == "ADJ":
        if feats.get("Poss") == "Yes":
            out.append(D + "Adjective › Possessive adjectives")
        soft = token.lemma.lower().endswith("í")
        out.append(D + ("Adjective › Soft declension" if soft else "Adjective › Hard declension"))
    elif upos in ("PRON", "DET"):
        pt = feats.get("PronType", "")
        out.append(D + "Pronouns › " + (
            "Possessive pronouns" if feats.get("Poss") == "Yes" else
            "Personal pronouns" if pt == "Prs" else
            "Demonstrative pronouns" if pt == "Dem" else
            "Interrogative and relative pronouns" if "Int" in pt or "Rel" in pt else
            "Indefinite and negative pronouns"))
    elif upos == "NUM":
        out.append(D + "Plural forms")
    elif upos in ("VERB", "AUX"):
        if token.lemma.lower() in ("být", "mít", "jít", "jíst", "vědět", "chtít", "moci", "moct"):
            out.append(C + "Irregular verbs")
        else:
            cls = verb_class(entry)
            if cls:
                out.append(C + f"Verb classes › Class {cls}")
        vf, tense = feats.get("VerbForm"), feats.get("Tense")
        if vf == "Part" and tense == "Past":
            out += REF["past"]
        elif vf == "Part":
            out += REF["passive"]
        elif feats.get("Mood") == "Imp":
            out += REF["imperative"]
        elif feats.get("Mood") == "Cnd":
            out += REF["conditional"]
        elif tense == "Fut":
            out += REF["future"]
        elif vf == "Conv":
            out += REF["transgressive"]
        else:
            out += REF["verbs"]
    elif upos == "ADP":
        out += REF["prepositions"]
    return out
