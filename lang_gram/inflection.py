"""Which declension or conjugation a word belongs to, in words.

Shown at the top of the Paradigm tab: the class of the word (third declension
i-stem, weak masculine noun, hard-stem adjective, verb class IV ...), its key
forms and, where there is one, the model word it is declined like.
"""
from __future__ import annotations

import re
from html import escape

from . import lang_cs, lang_de, lang_la
from .morph import norm_form
from .paradigm import entry_cells

GENDER_ABBR = {"masculine": "m.", "feminine": "f.", "neuter": "n."}
NOMINAL = ("NOUN", "PROPN", "ADJ", "DET", "PRON", "NUM")


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def table_form(entry, *tags: str, phrase: bool = False) -> str | None:
    """First form of the entry's table that carries all *tags* (one word unless *phrase*)."""
    wanted = set(tags)
    for form, form_tags in (entry or {}).get("f", []):
        have = set(form_tags.split())
        if wanted <= have and form and form != "-" and (phrase and "multiword-construction" not in have
                                                        or " " not in form):
            return form
    return None


def gender_of(token, entry) -> str | None:
    tags = (entry or {}).get("t", [])
    found = [g for g in GENDER_ABBR if g in tags]
    if len(found) == 1:
        return found[0]
    return token.cats.get("gender")


def is_indeclinable(entry) -> bool:
    return "indeclinable" in (entry or {}).get("t", []) and not (entry or {}).get("f")


def line(kind: str, detail: str = "") -> str:
    return f"<p><b>{escape(kind)}</b>" + (f" — {detail}" if detail else "") + "</p>"


def key_forms(*parts: str) -> str:
    shown = [p for p in parts if p]
    return f'<p class="muted">{" · ".join(shown)}</p>' if shown else ""


def result(heading: str, *html: str) -> tuple[str, str]:
    return heading, "".join(h for h in html if h)


# --------------------------------------------------------------------------- #
# Latin
# --------------------------------------------------------------------------- #
LA_NOUN = {
    "hora": ("First declension", "ā-stems: nominative -a, genitive -ae"),
    "servus": ("Second declension", "o-stems, masculine in -us: genitive -ī"),
    "liber": ("Second declension", "o-stems, masculine in -er: genitive -ī"),
    "verbum": ("Second declension", "o-stems, neuter in -um: genitive -ī, plural -a"),
    "sol": ("Third declension", "consonant stem: genitive -is, genitive plural -um"),
    "leo": ("Third declension", "consonant stem (-ō, -ōnis / -inis): genitive plural -um"),
    "vox": ("Third declension", "consonant stem, nominative in -s / -x: genitive -is, genitive plural -um"),
    "nomen": ("Third declension", "consonant stem, neuter: genitive -is, nominative and accusative plural -a"),
    "navis": ("Third declension", "i-stem with nominative in -is / -ēs: genitive plural -ium"),
    "urbs": ("Third declension", "mixed i-stem (stem in two consonants): genitive plural -ium"),
    "mons": ("Third declension", "mixed i-stem (-ns / -rs, genitive -ntis / -rtis): genitive plural -ium"),
    "mare": ("Third declension", "i-stem, neuter in -e / -al / -ar: ablative -ī, plural -ia, -ium"),
    "casus": ("Fourth declension", "u-stems in -us: genitive -ūs"),
    "cornu": ("Fourth declension", "u-stems, neuter in -ū: genitive -ūs, plural -ua"),
    "dies": ("Fifth declension", "ē-stems: nominative -ēs, genitive -ēī (after i)"),
    "res": ("Fifth declension", "ē-stems: nominative -ēs, genitive -eī (after a consonant)"),
}
LA_MODEL_NAME = {"hora": "hōra", "servus": "servus", "liber": "liber", "verbum": "verbum", "sol": "sōl",
                 "leo": "leō", "vox": "vōx", "nomen": "nōmen", "navis": "nāvis", "urbs": "urbs", "mons": "mōns",
                 "mare": "mare", "casus": "cāsus", "cornu": "cornū", "dies": "diēs", "res": "rēs"}
LA_VERB = {
    "amare": ("First conjugation", "ā-stems: present infinitive -āre", "amāre"),
    "monere": ("Second conjugation", "ē-stems: present infinitive -ēre", "monēre"),
    "legere": ("Third conjugation", "consonant stems: present infinitive -ere", "legere"),
    "audire": ("Fourth conjugation", "ī-stems: present infinitive -īre", "audīre"),
}


def _la_adjective(token, entry, as_participle: bool = False) -> str:
    got = lang_la.adjective_model(token, entry)
    if not got:
        return ""
    kind, key = got
    tags = (entry or {}).get("t", [])
    lemma = norm_form("la", (entry or {}).get("w") or token.lemma)
    if kind == "personal":
        if key in ("sui", "se"):
            return line("Reflexive pronoun", "no nominative; the same forms for singular and plural: "
                                             "<i>suī, sibi, sē, sē</i>")
        return line("Personal pronoun", "a declension of its own (<i>ego, meī, mihi, mē, mē</i>; "
                                        "<i>tū, tuī, tibi, tē, tē</i>)")
    if kind == "pron":
        model = {"is": "is, ea, id", "hic": "hic, haec, hoc", "ille": "ille, illa, illud",
                 "qui": "quī / quis, quae, quod / quid"}[key]
        return line("Pronominal declension", f"genitive singular in -ius, dative in -ī for all genders; "
                                             f"declined like <i>{model}</i>")
    if key == "nullus":
        return line("First and second declension, pronominal type",
                    "like <i>magnus</i>, but genitive singular -īus and dative -ī in all genders "
                    "(<i>ūnus, sōlus, tōtus, ūllus, nūllus, alius, alter, uter, neuter</i>); "
                    "declined like <i>nūllus</i>")
    if key == "magnus":
        if as_participle:
            return line("First and second declension", "as every perfect participle, future participle and "
                                                       "gerundive: -us, -a, -um; declined like <i>magnus</i>")
        endings = "-er, -a, -um" if lemma.endswith("er") else "-us, -a, -um"
        return line("First and second declension", f"three endings {endings}: masculine and neuter follow the "
                                                   f"second declension, the feminine the first; declined like "
                                                   f"<i>magnus</i>")
    if key == "ingens":
        if as_participle:
            return line("Third declension", "as every present participle: -ns, genitive -ntis, one nominative "
                                            "form for all genders; declined like <i>ingēns</i>")
        return line("Third declension, one ending", "the same nominative singular for all three genders; "
                                                    "i-stem (ablative -ī, genitive plural -ium); declined like "
                                                    "<i>ingēns</i>")
    if key == "melior":
        return line("Third declension, comparative", "-ior (masculine and feminine), -ius (neuter); consonant "
                                                     "stem: ablative -e, genitive plural -um; declined like "
                                                     "<i>melior</i>")
    if key == "gravis":
        if "three-termination" in tags or lemma.endswith("er"):
            return line("Third declension, three endings", "-er, -ris, -re; i-stem (ablative -ī, genitive plural "
                                                           "-ium); otherwise declined like <i>gravis</i>")
        return line("Third declension, two endings", "-is (masculine and feminine), -e (neuter); i-stem: "
                                                     "ablative -ī, genitive plural -ium; declined like "
                                                     "<i>gravis</i>")
    return ""


def latin(token, entry, verb) -> tuple[str, str] | None:
    cats, upos = token.cats, token.upos
    if upos in ("VERB", "AUX"):
        ventry = verb or entry
        got = lang_la.verb_model(token, ventry)
        head = (ventry or {}).get("h", "")
        parts = re.search(r"\(([^)]*)\)", head)
        principal = ""
        if ventry and parts:
            principal = f"<i>{escape(ventry['w'])}</i>, " + escape(
                parts.group(1).replace("present infinitive ", "").replace("perfect active ", "").replace(
                    "supine ", ""))
        if got is None:
            html = line("Irregular verb", "its forms do not follow one of the four conjugations")
        else:
            model, note = got
            if model == "esse":
                html = line("Irregular verb", "<i>esse</i> and its compounds")
            else:
                name, detail, word = LA_VERB[model]
                if note:
                    name, detail = "Third conjugation, -iō type", ("present infinitive -ere, but -i- before a, o, "
                                                                  "u and e as in the fourth conjugation "
                                                                  "(<i>capiō, capiunt, capiam, capiēns</i>)")
                html = line(name, f"{detail}; conjugated like <i>{word}</i>")
        if lang_la.is_deponent(ventry):
            html += line("Deponent", "passive forms with active meaning; no active forms except the present and "
                                     "future participles, the future infinitive, gerund and supine")
        html += key_forms(principal)
        if cats.get("verbform") in ("participle", "gerundive") and "case" in cats:
            html += "<h3>Declension of this form</h3>" + _la_adjective(token, entry, as_participle=True)
        return result("Conjugation type", html)
    tags = (entry or {}).get("t", [])
    declined = any(t.startswith("declension-") for t in tags)
    if upos in NOMINAL and "indeclinable" in tags and not declined:
        return result("Declension type", line("Indeclinable", "the same form in every case"))
    if upos in ("NOUN", "PROPN"):
        if not entry or entry["p"] not in ("noun", "name"):
            if "case" not in cats:
                return None
        key = lang_la.noun_model(token, entry)
        if key is None:
            return None
        name, detail = LA_NOUN[key]
        gender = gender_of(token, entry)
        plural_only = "plural-only" in (entry or {}).get("t", []) or not table_form(entry, "nominative", "singular")
        genitive = table_form(entry, "genitive", "plural" if plural_only and entry else "singular")
        forms = ""
        if entry:
            forms = f"<i>{escape(entry['w'])}</i>" + (f", <i>{escape(genitive)}</i>" if genitive else "")
            if gender:
                forms += f" {GENDER_ABBR[gender]}"
        irregular = "irregular" in (entry or {}).get("h", "") or "variously declined" in (entry or {}).get("h", "")
        html = line(name if entry else f"Probably {name[0].lower()}{name[1:]}", detail)
        if irregular:
            html += line("With irregular forms", "see the forms of the word below")
        if "indeclinable" in tags:
            html += line("Often left undeclined", "a foreign name that may keep one form for all cases")
        html += key_forms(forms, f"declined like <i>{LA_MODEL_NAME[key]}</i>")
        return result("Declension type", html)
    if "case" not in cats:
        return None
    html = _la_adjective(token, entry)
    if not html:
        return None
    if cats.get("degree") == "superlative":
        html += line("Superlative", "formed with -issimus (-errimus, -illimus), declined like <i>magnus</i>")
    return result("Declension type", html)


# --------------------------------------------------------------------------- #
# German
# --------------------------------------------------------------------------- #
DE_DER_WORDS = {"der", "dieser", "jener", "jeder", "welcher", "mancher", "solcher", "aller", "all", "derselbe",
                "derjenige"}
DE_EIN_WORDS = {"ein", "kein", "mein", "dein", "sein", "ihr", "unser", "euer"}
_UMLAUT = str.maketrans("äöüÄÖÜ", "aouAOU")


def _de_plural(lemma: str, plural: str | None) -> str:
    if not plural:
        return ""
    plain = plural.translate(_UMLAUT)
    umlaut = plain != plural and lemma.translate(_UMLAUT) == lemma
    stem = lemma.translate(_UMLAUT)
    if plain == stem:
        ending = "no ending"
    elif plain.startswith(stem):
        ending = "-" + plain[len(stem):]
    elif stem.endswith("e") and plain.startswith(stem[:-1]):
        ending = "-" + plain[len(stem) - 1:]
    else:
        return f"plural <i>{escape(plural)}</i>"
    return f"plural <i>{escape(plural)}</i> ({ending}{' with umlaut' if umlaut else ''})"


def german(token, entry, verb) -> tuple[str, str] | None:
    cats, upos, feats = token.cats, token.upos, token.feats
    tags = (entry or {}).get("t", [])
    lemma = token.lemma
    if upos in ("VERB", "AUX"):
        if not entry or entry["p"] != "verb":
            return None
        head = entry["h"]
        strong_class = next((t for t in tags if t.startswith("class-")), None)
        if "preterite-present" in head or "preterite-present" in tags:
            html = line("Preterite-present verb", "present tense formed like a strong preterite: no ending in the "
                                                  "1st and 3rd person singular (<i>ich kann, er kann</i>); "
                                                  "the modal verbs and <i>wissen</i>")
        elif "irregular weak" in head:
            html = line("Mixed verb (irregular weak)", "vowel change as in a strong verb, but the endings -te and "
                                                       "-t of a weak one (<i>bringen, brachte, gebracht</i>)")
        elif "irregular strong" in head:
            html = line("Strong verb with irregular forms", "vowel change in the preterite and a past participle "
                                                            "in -en, with further changes in the stem")
        elif "irregular" in head:
            html = line("Irregular verb", "stem changes that follow no regular pattern")
        elif "strong" in tags or strong_class:
            number = f" (ablaut class {strong_class.split('-')[1]})" if strong_class else ""
            html = line("Strong verb" + number, "the stem vowel changes in the preterite, which has no ending in "
                                                "the 1st and 3rd person singular; past participle in -en")
        elif "mixed" in tags or "mixed" in head:
            html = line("Mixed verb", "vowel change as in a strong verb, endings -te and -t as in a weak one "
                                      "(<i>bringen, brachte, gebracht</i>)")
        elif "weak" in tags or "weak" in head:
            html = line("Weak verb", "regular: preterite in -te, past participle in -t, no vowel change")
        else:
            return None
        aux = re.search(r"auxiliary ([^,)]+)", head)
        parts = [table_form(entry, "third-person", "singular", "present", "indicative", phrase=True),
                 table_form(entry, "third-person", "singular", "preterite", "indicative", phrase=True),
                 table_form(entry, "participle", "past")]
        forms = f"<i>{escape(entry['w'])}</i>" + "".join(f" – {escape(p)}" for p in parts if p)
        return result("Conjugation type", html, key_forms(
            forms, f"perfect with <i>{escape(aux.group(1))}</i>" if aux else ""))
    if upos in ("NOUN", "PROPN"):
        if entry and entry["p"] not in ("noun", "name"):
            return None
        if not entry:
            # Mostly compounds: they decline like their last part, which the gender shows.
            gender = cats.get("gender")
            if upos != "NOUN" or gender is None:
                return None
            if gender == "feminine":
                return result("Declension type", line("Feminine declension", "no case endings in the singular; "
                                                                             "only the article shows the case"))
            return result("Declension type", line("Probably strong declension", "most masculine and all but one "
                                                                                "neuter nouns: genitive singular "
                                                                                "in -(e)s"))
        gender = gender_of(token, entry)
        genitive = table_form(entry, "genitive", "singular")
        plural = table_form(entry, "nominative", "plural")
        stated = re.match(r"[^(]*\((?:proper noun, )?(strong|weak|mixed|irregular)\b", entry["h"])
        tags = list(tags) + ([stated.group(1)] if stated else [])
        if "irregular" in tags and gender in ("masculine", "neuter"):
            html = line("Irregular declension", "forms that follow neither the strong nor the weak pattern")
        elif "weak" in tags and (genitive or "").endswith("ns"):
            html = line("Weak declension with genitive in -ns", "-(e)n in the other cases, but genitive singular "
                                                                "-(e)ns (<i>das Herz, des Herzens</i>; "
                                                                "<i>der Name, des Namens</i>)")
        elif "weak" in tags:
            html = line("Weak declension (n-declension)", "masculine nouns that take -(e)n in every form except "
                                                          "the nominative singular")
        elif "mixed" in tags:
            html = line("Mixed declension", "strong in the singular (genitive -(e)s), weak in the plural (-(e)n)")
        elif "strong" in tags and gender in ("masculine", "neuter"):
            html = line("Strong declension", "masculine and neuter nouns with genitive singular in -(e)s; the "
                                             "dative singular may add -e in older texts")
        elif gender == "feminine":
            html = line("Feminine declension", "no case endings in the singular; only the article shows the case")
        elif "strong" in tags:
            html = line("Strong declension", "genitive singular in -(e)s")
        else:
            return None
        forms = f"<i>{escape(entry['w'])}</i>" + (f" {GENDER_ABBR[gender]}" if gender else "")
        return result("Declension type", html, key_forms(
            forms, f"genitive <i>{escape(genitive)}</i>" if genitive else "", _de_plural(entry["w"], plural)))
    if upos == "ADJ":
        kind = lang_de.adjective_inflection(token)
        if kind is None and "case" in cats:
            # An adjective standing alone as a noun ("der erste"): its own article decides.
            dets = [c for c in token.children if c.upos == "DET" and c.index < token.index]
            if dets:
                last = dets[-1]
                kind = "mixed" if (last.lemma.lower() in lang_de.MIXED_DETERMINERS
                                   or last.feats.get("Poss") == "Yes") else "weak"
        if kind is None:
            if "case" in cats:
                return None
            if cats.get("degree") == "superlative" and token.text.lower().endswith("sten"):
                return result("Declension type", line("Superlative with am", "the fixed form <i>am …-sten</i>, "
                                                                             "used in the predicate and as an "
                                                                             "adverb"))
            return result("Declension type", line("Not declined here", "an adjective used in the predicate or as "
                                                                       "an adverb has no ending"))
        why = {"strong": "no article before it: the adjective takes the endings of <i>der, die, das</i> itself "
                         "(-er, -e, -es …), except genitive masculine and neuter -en",
               "weak": "after <i>der, dieser, jeder …</i>: only -e (nominative singular, and accusative feminine "
                       "and neuter) or -en",
               "mixed": "after <i>ein, kein</i> and the possessives: -er, -e, -es where that word has no ending, "
                        "otherwise -en"}[kind]
        return result("Declension type", line(f"{kind.capitalize()} adjective declension", why),
                      '<p class="muted">Every adjective has all three declensions; which one is used depends on '
                      'the word before it.</p>')
    if upos in ("DET", "PRON") and "case" in cats:
        low = lemma.lower()
        if low in DE_DER_WORDS or feats.get("PronType") == "Art" and feats.get("Definite") == "Def":
            return result("Declension type", line("der-word", "declined like the definite article: -er, -e, -es in "
                                                              "the nominative, with the full set of case endings"))
        if low in DE_EIN_WORDS or feats.get("Poss") == "Yes" or feats.get("PronType") == "Art":
            return result("Declension type", line("ein-word", "declined like the indefinite article: no ending in "
                                                              "the nominative masculine and the nominative and "
                                                              "accusative neuter, otherwise the endings of "
                                                              "<i>der</i>"))
        if feats.get("Reflex") == "Yes":
            return result("Declension type", line("Reflexive pronoun", "<i>sich</i> for the accusative and dative "
                                                                       "of the 3rd person; otherwise the forms of "
                                                                       "the personal pronoun (<i>mich, dir …</i>)"))
        if feats.get("PronType") == "Prs":
            return result("Declension type", line("Personal pronoun", "separate forms for each case "
                                                                      "(<i>ich, mich, mir</i>)"))
    return None


# --------------------------------------------------------------------------- #
# Czech
# --------------------------------------------------------------------------- #
CS_MODELS = {
    "pán": ("Masculine animate, hard type", "genitive -a, dative and locative -ovi / -u, nominative plural -i / -ové"),
    "muž": ("Masculine animate, soft type", "genitive -e, dative and locative -i / -ovi, nominative plural -i / -ové"),
    "předseda": ("Masculine animate in -a", "singular like the feminine <i>žena</i> except dative and locative "
                                            "-ovi; plural -ové / -é"),
    "soudce": ("Masculine animate in -e", "genitive -e, dative and locative -i / -ovi, nominative plural -i / -ové"),
    "hrad": ("Masculine inanimate, hard type", "genitive -u (or -a), locative -u / -ě, nominative plural -y"),
    "stroj": ("Masculine inanimate, soft type", "genitive -e, locative -i, nominative plural -e"),
    "žena": ("Feminine in -a", "genitive -y, dative and locative -ě / -e, accusative -u, instrumental -ou"),
    "růže": ("Feminine in -e", "genitive -e, dative, accusative and locative -i, instrumental -í"),
    "píseň": ("Feminine in a consonant, type píseň", "genitive -e / -ě, dative and locative -i"),
    "kost": ("Feminine in a consonant, type kost", "genitive, dative and locative -i, nominative plural -i"),
    "město": ("Neuter in -o", "genitive -a, dative -u, locative -ě / -u, plural -a"),
    "moře": ("Neuter in -e", "genitive -e, dative and locative -i, plural -e"),
    "kuře": ("Neuter in -e with stem in -et-", "genitive -ete, plural -ata (names of young animals)"),
    "stavení": ("Neuter in -í", "-í in almost all cases; instrumental singular -ím"),
}
CS_SOFT = "žščřcjďťň"
CS_VERB = {
    "I": ("Class I", "present in -u, -eš, -e (<i>nést – nesu, nese</i>; <i>brát – beru</i>)"),
    "II": ("Class II", "present in -nu, -neš, -ne; infinitive in -nout (<i>tisknout – tisknu</i>)"),
    "III": ("Class III", "present in -ji / -ju, -ješ, -je (<i>krýt – kryji</i>; <i>kupovat – kupuji</i>)"),
    "IV": ("Class IV", "present in -ím, -íš, -í (<i>prosit, trpět, sázet</i>)"),
    "V": ("Class V", "present in -ám, -áš, -á; infinitive in -at (<i>dělat – dělám</i>)"),
}


def _cs_noun_model(lemma: str, gender: str | None, animate: bool, genitive: str | None) -> str | None:
    low = lemma.lower()
    gen = (genitive or "").lower()
    soft_gen = gen.endswith(("e", "ě"))
    soft_stem = low[-1:] in CS_SOFT
    if gender == "masculine":
        if animate:
            if low.endswith("a"):
                return "předseda"
            if low.endswith("e"):
                return "soudce"
            return "muž" if (soft_gen if gen else soft_stem) else "pán"
        return "stroj" if (soft_gen if gen else soft_stem) else "hrad"
    if gender == "feminine":
        if low.endswith("a"):
            return "žena"
        if low.endswith(("e", "ě")):
            return "růže"
        if gen:
            return "píseň" if soft_gen else "kost"
        return "kost" if low.endswith(("st", "c")) else "píseň"
    if gender == "neuter":
        if low.endswith("o"):
            return "město"
        if low.endswith("í"):
            return "stavení"
        if low.endswith(("e", "ě")):
            return "kuře" if gen.endswith("te") else "moře"
    return None


def _slavic_adjective(lang: str, token, entry) -> str:
    feats = token.feats
    low = ((entry or {}).get("w") or token.lemma).lower()
    if lang == "cs":
        if feats.get("Variant") == "Short" and token.upos == "ADJ":
            return line("Short (nominal) form", "noun-like endings (-, -a, -o); used only in the predicate")
        if low.endswith(("ův", "in")) and feats.get("Poss") == "Yes":
            return line("Possessive adjective", "-ův (from a masculine owner) / -in (from a feminine owner): "
                                                "noun-like endings in most singular cases, adjective endings "
                                                "elsewhere; like <i>otcův, matčin</i>")
        if low.endswith("ý"):
            return line("Hard adjective declension", "nominative -ý, -á, -é; declined like <i>mladý</i>")
        if low.endswith("í"):
            return line("Soft adjective declension", "nominative -í for all genders; declined like <i>jarní</i>")
        return ""
    if low.endswith(("ki", "gi")):
        return line("Adjectival declension, stem in k / g", "nominative -i, -a, -ie; like <i>wysoki, drogi</i>")
    if low.endswith("i"):
        return line("Adjectival declension, soft stem", "nominative -i, -ia, -ie; like <i>tani, głupi</i>")
    if low.endswith("y"):
        return line("Adjectival declension, hard stem", "nominative -y, -a, -e; like <i>dobry, nowy</i>")
    return ""


def czech(token, entry, verb) -> tuple[str, str] | None:
    cats, upos, feats = token.cats, token.upos, token.feats
    tags = (entry or {}).get("t", [])
    if upos in ("VERB", "AUX"):
        if not entry or entry["p"] != "verb":
            return None
        aspect = "perfective" if "perfective" in tags else "imperfective" if "imperfective" in tags else ""
        if entry["k"] in ("být", "mít", "jít", "jíst", "vědět", "chtít", "moci", "moct"):
            html = line("Irregular verb", "one of the few verbs with forms of its own")
        else:
            cls = lang_cs.verb_class(entry)
            if cls is None:
                low = entry["k"]
                cls = ("II" if low.endswith("nout") else "III" if low.endswith("ovat") else
                       "V" if low.endswith(("at", "át")) else "IV" if low.endswith(("it", "et", "ět")) else
                       "I" if low.endswith(("ci", "ct", "st", "zt")) else None)
                if cls is None:
                    return None
            html = line(*CS_VERB[cls])
        third = table_form(entry, "third-person", "singular", "present", "indicative")
        past = table_form(entry, "participle", "past", "masculine", "singular")
        forms = f"<i>{escape(entry['w'])}</i>" + (f" – {escape(third)}" if third else "") + (
            f" – {escape(past)}" if past else "")
        html += key_forms(forms, aspect)
        if feats.get("VerbForm") == "Part" and "case" in cats:
            html += "<h3>Declension of this form</h3>" + line("Hard adjective declension",
                                                              "a participle used as an adjective: -ý, -á, -é")
        return result("Conjugation type", html)
    if upos in ("NOUN", "PROPN"):
        if is_indeclinable(entry):
            return result("Declension type", line("Indeclinable", "the same form in every case"))
        gender = gender_of(token, entry)
        animate = "animate" in tags and "inanimate" not in tags if entry else cats.get("animacy") == "animate"
        genitive = table_form(entry, "genitive", "singular")
        lemma = (entry or {}).get("w") or token.lemma
        low, gen = lemma.lower(), (genitive or "").lower()
        if gen.endswith(("ého", "ího")) or (gender == "feminine" and low.endswith("á") and gen.endswith("é")) \
                or (not gen and low.endswith(("ý", "í")) and gender == "masculine"):
            soft = low.endswith("í")
            return result("Declension type", line(
                "Noun declined like an adjective",
                ("soft adjective declension (-í), like <i>jarní</i>" if soft
                 else "hard adjective declension (-ý, -á, -é), like <i>mladý</i>")),
                key_forms(f"<i>{escape(lemma)}</i>" + (f", <i>{escape(genitive)}</i>" if genitive else "")))
        model = _cs_noun_model(lemma, gender, animate, genitive)
        if model is None:
            return None
        name, detail = CS_MODELS[model]
        forms = f"<i>{escape(lemma)}</i>" + (f", <i>{escape(genitive)}</i>" if genitive else "")
        if gender:
            forms += f" {GENDER_ABBR[gender]}" + (" anim." if gender == "masculine" and animate else
                                                 " inan." if gender == "masculine" else "")
        html = line(name if entry else f"Probably: {name[0].lower()}{name[1:]}", detail)
        return result("Declension type", html, key_forms(forms, f"declined like <i>{model}</i>"))
    if upos in ("ADJ", "DET", "PRON", "NUM") and ("case" in cats or upos == "ADJ" and (
            feats.get("Variant") == "Short" or not token.lemma.lower().endswith(("ý", "í")))):
        html = _slavic_adjective("cs", token, entry)
        if upos == "ADJ" and not html and "case" not in cats:
            html = line("Short (nominal) form", "noun-like endings (-, -a, -o); used only in the predicate")
        elif upos == "ADJ" and not html:
            html = line("Adjective declension", "declined like <i>mladý</i> (hard) or <i>jarní</i> (soft)")
        if feats.get("Reflex") == "Yes" and feats.get("Poss") != "Yes":
            html = line("Reflexive pronoun", "no nominative; <i>sebe, sobě, sebe, sobě, sebou</i> with the short "
                                             "forms <i>se</i> (accusative) and <i>si</i> (dative)")
        elif not html and feats.get("PronType") == "Prs" and feats.get("Poss") != "Yes":
            html = line("Personal pronoun", "forms of its own; many cases have a long and a short (clitic) form")
        elif not html and upos in ("DET", "PRON"):
            html = line("Pronominal declension", "endings of <i>ten, ta, to</i>: genitive -oho, dative -omu, "
                                                 "locative -om, instrumental -ím")
        if not html:
            return None
        if cats.get("degree") in ("comparative", "superlative"):
            html += line(cats["degree"].capitalize(), "in -ší / -ejší: always the soft declension")
        return result("Declension type", html)
    return None


# --------------------------------------------------------------------------- #
# Polish
# --------------------------------------------------------------------------- #
def _pl_stem(lemma: str) -> str:
    low = lemma.lower()
    stem = low.rstrip("aeouyąęió") if low[-1:] in "aeoąę" else low
    soft_i = low[-2:-1] == "i" and low[-1:] in "aeo"
    for ending, label in ((("ć", "ś", "ź", "ń", "dź", "j", "l"), "soft"),
                          (("cz", "dz", "dż", "sz", "rz", "ż", "c"), "hardened"),
                          (("k", "g", "ch"), "velar")):
        if stem.endswith(ending):
            return label
    return "soft" if soft_i else "hard"


PL_STEM_TEXT = {
    "hard": "stem in a hard consonant",
    "soft": "stem in a soft consonant (ć, ś, ź, ń, l, j, or a consonant + i)",
    "hardened": "stem in a hardened consonant (c, cz, dz, dż, rz, sz, ż), declined mostly like a soft stem",
    "velar": "stem in k, g or ch: -i instead of -y after k and g",
}


def _pl_conjugation(entry) -> tuple[str, str] | None:
    first = second = None
    for cell in entry_cells("pl", entry):
        if not cell.word or cell.cats.get("number") != {"singular"} or "past" in cell.tags \
                or "conditional" in cell.tags or "imperative" in cell.tags:
            continue
        if not ({"present", "future"} & cell.tags):
            continue
        if cell.cats.get("person") == {"first-person"} and first is None:
            first = cell.word
        elif cell.cats.get("person") == {"second-person"} and second is None:
            second = cell.word
    if not first or not second:
        return None
    if first.endswith("am") and second.endswith("asz"):
        return "Conjugation III (-am, -asz)", "like <i>czytać – czytam, czytasz</i>"
    if first.endswith("em") and second.endswith("esz"):
        return "Conjugation IV (-em, -esz)", "like <i>umieć – umiem, umiesz</i>"
    if second.endswith(("isz", "ysz")):
        return "Conjugation II (-ę, -isz / -ysz)", "like <i>robić – robię, robisz</i>"
    if second.endswith("esz"):
        return "Conjugation I (-ę, -esz)", "like <i>pisać – piszę, piszesz</i>"
    return None


def polish(token, entry, verb, lexicon=None) -> tuple[str, str] | None:
    cats, upos, feats = token.cats, token.upos, token.feats
    tags = (entry or {}).get("t", [])
    if upos in ("VERB", "AUX"):
        if not entry or entry["p"] != "verb":
            return None
        aspect = "perfective" if "perfective" in tags else "imperfective" if "imperfective" in tags else ""
        if not entry["f"] and lexicon is not None:    # the table sits in a sister entry
            entry = next((e for e in lexicon.find(entry["w"], "verb") if e["f"]), entry)
        if entry["k"] == "być":
            html = line("Irregular verb", "<i>być</i> has forms of its own")
            forms = "<i>być</i> – jestem, jesteś – był"
        elif "defective" in tags or feats.get("VerbType") == "Quasi":
            return result("Conjugation type", line("Defective (impersonal) verb", "it has no personal forms: one "
                                                                                  "form for the present, used "
                                                                                  "with an infinitive"))
        else:
            got = _pl_conjugation(entry)
            if got is None:
                return None
            html = line(*got)
            cells = entry_cells("pl", entry)
            first = next((c.word for c in cells if c.word and c.cats.get("person") == {"first-person"}
                          and c.cats.get("number") == {"singular"} and {"present", "future"} & c.tags), None)
            past = table_form(entry, "past", "masculine", "singular", "third-person")
            forms = f"<i>{escape(entry['w'])}</i>" + (f" – {escape(first)}" if first else "") + (
                f" – {escape(past)}" if past else "")
        html += key_forms(forms, aspect)
        if feats.get("VerbForm") == "Part" and "case" in cats:
            html += "<h3>Declension of this form</h3>" + line("Adjectival declension",
                                                              "a participle is declined like an adjective")
        return result("Conjugation type", html)
    if upos in ("NOUN", "PROPN"):
        if is_indeclinable(entry):
            return result("Declension type", line("Indeclinable", "the same form in every case"))
        gender = gender_of(token, entry)
        if gender is None:
            return None
        lemma = (entry or {}).get("w") or token.lemma
        low = lemma.lower()
        genitive = table_form(entry, "genitive", "singular")
        stem = PL_STEM_TEXT[_pl_stem(lemma)]
        sub = ""
        if gender == "masculine":
            if "person" in tags or (not entry and cats.get("animacy") == "personal"):
                sub, rule = "masculine personal", ("accusative = genitive in both numbers; nominative plural "
                                                   "-owie / -i / -y with softening")
            elif "animal-not-person" in tags or (not entry and cats.get("animacy") == "animate"):
                sub, rule = "masculine animate", "accusative singular = genitive (-a); plural as for things"
            else:
                sub, rule = "masculine inanimate", "accusative = nominative; genitive singular -u or -a"
            if low.endswith("a"):
                name, rule = "Masculine in -a", "singular declined like a feminine noun in -a; plural masculine"
            else:
                name = "Masculine declension"
        elif gender == "feminine":
            if low.endswith("i"):
                name, rule = "Feminine in -i", "like <i>pani</i>: accusative -ą, other singular cases -i"
            elif low.endswith("a"):
                name, rule = "Feminine in -a", "genitive -y / -i, accusative -ę, instrumental -ą"
            else:
                name, rule = "Feminine in a consonant", "genitive, dative and locative -i / -y; accusative = nominative"
        else:
            if low.endswith("ę"):
                name, rule = "Neuter in -ę", "stem extended in the other cases: -ęcia / -enia, plural -ęta / -ona"
            elif low.endswith("um"):
                name, rule = "Neuter in -um", "not declined in the singular; plural -a, genitive -ów"
            else:
                name, rule = f"Neuter in -{low[-1:]}", "genitive -a, nominative and accusative plural -a"
        forms = f"<i>{escape(lemma)}</i>" + (f", <i>{escape(genitive)}</i>" if genitive else "")
        forms += f" {GENDER_ABBR[gender]}"
        if not entry:
            name = f"Probably: {name[0].lower()}{name[1:]}"
        html = line(name + (f" ({sub})" if sub else ""), rule) + line("Stem", stem)
        return result("Declension type", html, key_forms(forms))
    if upos in ("ADJ", "DET", "PRON", "NUM") and "case" in cats:
        html = _slavic_adjective("pl", token, entry) if upos != "NUM" else ""
        if feats.get("Reflex") == "Yes" and feats.get("Poss") != "Yes":
            html = line("Reflexive pronoun", "no nominative; <i>siebie, sobie, siebie / się, sobą, sobie</i>")
        elif feats.get("PronType") == "Prs" and feats.get("Poss") != "Yes":
            html = line("Personal pronoun", "forms of its own; several cases have a long and a short form")
        elif not html and upos in ("DET", "PRON"):
            html = line("Pronominal declension", "adjective-like endings: genitive -ego, dative -emu, instrumental "
                                                 "and locative -ym / -im (<i>ten, tego, temu, tym</i>)")
        elif not html and upos == "ADJ":
            html = line("Adjectival declension", "the endings of <i>dobry</i>: genitive -ego, -ej; dative -emu, -ej")
        if not html:
            return None
        if cats.get("degree") in ("comparative", "superlative") and upos == "ADJ":
            html += line(cats["degree"].capitalize(), "in -szy / -ejszy: hardened stem (nominative -y, -a, -e)")
        return result("Declension type", html)
    return None


def describe(token, entry, verb=None, lexicon=None) -> tuple[str, str] | None:
    """(heading, html) naming the declension or conjugation of the word, or None.

    *verb* is the verb's own dictionary entry when *entry* is that of a participle;
    *lexicon* lets a language look at sister entries of the same word.
    """
    if token.lang == "pl":
        got = polish(token, entry, verb, lexicon)
    else:
        handler = {"la": latin, "de": german, "cs": czech}.get(token.lang)
        if handler is None:
            return None
        got = handler(token, entry, verb)
    return got if got and got[1] else None
