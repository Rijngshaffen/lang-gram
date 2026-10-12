"""Polish: usage notes and the matching sections of the grammar reference."""
from __future__ import annotations

from . import lang_slavic

M, G = "Polish morphology#", "Polish grammar#"
REF = {
    "prepositions": [G + "Prepositions", M + "Prepositions and prefixes"],
    "numerals": [G + "Numbers and quantifiers"],
    "agreement": [G + "Verbs"],
    "noun_syntax": [G + "Syntax › Noun syntax"],
    "adjectives": [M + "Adjectives", G + "Adjectives"],
    "short": [G + "Adjectives"],
    "comparison": [G + "Adjectives"],
    "possessive": [M + "Pronouns › Possessive pronouns"],
    "personal": [M + "Pronouns › Personal pronouns", M + "Pronouns › Reflexive pronouns"],
    "relative": [M + "Pronouns › Interrogative pronouns", G + "Pronouns"],
    "past": [M + "Verbs"],
    "conditional": [M + "Verbs"],
    "future": [M + "Verbs"],
    "aspect": [G + "Verbs"],
    "negation": [G + "Syntax › Noun syntax"],
    "reflexive": [M + "Pronouns › Reflexive pronouns", G + "Verbs"],
    "imperative": [M + "Verbs"],
    "infinitive": [M + "Verbs"],
    "passive": [G + "Verbs"],
    "transgressive": [G + "Verbs"],
    "verbs": [M + "Verbs", G + "Verbs"],
}


def notes(token, entry):
    return lang_slavic.notes("pl", token, entry, REF)


def chapters(token, entry) -> list[str]:
    upos, feats, cats = token.upos, token.feats, token.cats
    out = []
    if upos in ("NOUN", "PROPN"):
        gender = cats.get("gender")
        section = {"masculine": "Masculine nouns", "feminine": "Feminine nouns", "neuter": "Neuter nouns"}.get(gender)
        if section:
            out.append(M + "Nouns › " + section)
        out += [G + "Nouns › Declension", G + "Nouns › Gender › Inflection"]
    elif upos == "ADJ":
        out += REF["adjectives"]
    elif upos in ("PRON", "DET"):
        pt = feats.get("PronType", "")
        out.append(M + "Pronouns › " + (
            "Possessive pronouns" if feats.get("Poss") == "Yes" else
            "Reflexive pronouns" if feats.get("Reflex") == "Yes" else
            "Personal pronouns" if pt == "Prs" else
            "Demonstrative pronouns" if pt == "Dem" else "Interrogative pronouns"))
        out.append(G + "Pronouns")
    elif upos == "NUM":
        out += REF["numerals"] + [M + "Numbers and quantifiers"]
    elif upos in ("VERB", "AUX"):
        out += REF["verbs"]
    elif upos == "ADP":
        out += REF["prepositions"]
    return out
