"""Czech and Polish share most of their grammar; the differences are data."""
from __future__ import annotations

from html import escape

CASE_NAMES = {"gen": "genitive", "dat": "dative", "acc": "accusative", "loc": "locative", "ins": "instrumental"}

PREPOSITIONS = {
    "cs": {
        "bez": ("without", "gen"), "do": ("into, to; until", "gen"), "od": ("from; since", "gen"),
        "u": ("at, near, by", "gen"), "z": ("out of, from", "gen"), "kolem": ("around, past", "gen"),
        "okolo": ("around", "gen"), "podle": ("according to; along", "gen"), "podlé": ("beside; according to", "gen"),
        "vedle": ("next to", "gen"), "během": ("during", "gen"), "kromě": ("except", "gen"),
        "místo": ("instead of", "gen"), "uprostřed": ("in the middle of", "gen"), "prostřed": ("in the middle of", "gen"),
        "blízko": ("near", "gen"), "nedaleko": ("not far from", "gen"), "podél": ("along", "gen"),
        "k": ("to, towards", "dat"), "proti": ("against, opposite", "dat"), "naproti": ("opposite", "dat"),
        "kvůli": ("because of", "dat"), "díky": ("thanks to", "dat"),
        "pro": ("for", "acc"), "přes": ("across, over; despite", "acc"), "skrz": ("through", "acc"),
        "skrze": ("through", "acc"), "mimo": ("past; except", "acc"),
        "při": ("at, by, during", "loc"),
        "na": ("on, at (loc.); onto, to, for (acc.)", "acc/loc"), "o": ("about (loc.); against, by (acc.)", "acc/loc"),
        "po": ("after, along, over (loc.); up to, for (acc.)", "acc/loc"), "v": ("in (loc.); on a day, into (acc.)", "acc/loc"),
        "nad": ("above", "acc/ins"), "pod": ("under", "acc/ins"), "před": ("in front of, before; ago", "acc/ins"),
        "mezi": ("between, among", "acc/ins"), "za": ("behind, beyond; for; during (gen.)", "acc/ins/gen"),
        "s": ("with (ins.); down from (gen.)", "ins/gen"),
    },
    "pl": {
        "bez": ("without", "gen"), "dla": ("for", "gen"), "do": ("to, into; until", "gen"), "od": ("from; since", "gen"),
        "u": ("at, by, with", "gen"), "z": ("out of, from (gen.); with (ins.)", "gen/ins"),
        "koło": ("near, around", "gen"), "obok": ("beside", "gen"), "wśród": ("among", "gen"),
        "podczas": ("during", "gen"), "według": ("according to", "gen"), "oprócz": ("except", "gen"),
        "prócz": ("except", "gen"), "zamiast": ("instead of", "gen"), "naprzeciw": ("opposite", "gen"),
        "około": ("about, around", "gen"), "spod": ("from under", "gen"), "znad": ("from above", "gen"),
        "zza": ("from behind", "gen"), "sprzed": ("from in front of", "gen"), "wzdłuż": ("along", "gen"),
        "mimo": ("despite", "gen"), "wedle": ("according to", "gen"), "wpośród": ("amid", "gen"),
        "ku": ("towards", "dat"), "dzięki": ("thanks to", "dat"), "przeciw": ("against", "dat"),
        "przeciwko": ("against", "dat"), "wbrew": ("contrary to", "dat"),
        "przez": ("through, across; by", "acc"),
        "przy": ("at, by, near", "loc"),
        "na": ("on, at (loc.); onto, to, for (acc.)", "acc/loc"), "w": ("in (loc.); into, on a day (acc.)", "acc/loc"),
        "o": ("about (loc.); against, for (acc.)", "acc/loc"), "po": ("after, along, over (loc.); up to, to fetch (acc.)", "acc/loc"),
        "nad": ("above, over", "acc/ins"), "pod": ("under", "acc/ins"), "przed": ("in front of, before", "acc/ins"),
        "między": ("between, among", "acc/ins"), "za": ("behind, beyond; for; too", "acc/ins/gen"),
        "poza": ("beyond, outside", "acc/ins"), "pomiędzy": ("between", "acc/ins"),
    },
}
VARIANTS = {"cs": {"ve": "v", "ke": "k", "ku": "k", "ze": "z", "se": "s", "nade": "nad", "pode": "pod",
                   "přede": "před", "ode": "od", "beze": "bez", "přese": "přes"},
            "pl": {"we": "w", "ze": "z", "nade": "nad", "pode": "pod", "przede": "przed", "ode": "od",
                   "beze": "bez", "przeze": "przez"}}

DATIVE_VERBS = {
    "cs": {"pomoci", "pomoct", "pomáhat", "věřit", "rozumět", "děkovat", "říci", "říct", "povídat", "dát",
           "dávat", "sloužit", "radit", "škodit", "líbit", "patřit", "podobat", "vyhovět", "odpovědět",
           "poručit", "kázat", "slíbit", "ukázat", "divit"},
    "pl": {"pomóc", "pomagać", "wierzyć", "dziękować", "powiedzieć", "mówić", "dać", "dawać", "służyć",
           "radzić", "szkodzić", "podobać", "odpowiedzieć", "kazać", "obiecać", "pokazać", "przyglądać",
           "dziwić", "ufać", "towarzyszyć", "przypatrywać", "przysłuchiwać"},
}
BE = {"cs": {"být", "stát", "stávat", "zůstat"}, "pl": {"być", "zostać", "stać", "stawać", "bywać", "okazać"}}

TEXT = {
    "cs": {
        "loc": "The <b>locative</b> occurs only after a preposition (<i>v, na, o, po, při</i>): where something "
               "is, or what one talks about.",
        "ins": "<b>Instrumental</b> without a preposition: the means or tool (“with, by”), the way taken "
               "(<i>lesem</i> “through the forest”), or the predicate after <i>být, stát se</i>.",
        "past": "<b>Past tense</b>: the l-participle (ending shows gender and number of the subject) plus the "
                "present of <i>být</i> in the 1st and 2nd person (<i>dělal jsem, dělal jsi</i>); the 3rd person "
                "has no auxiliary (<i>dělal</i>).",
        "cond": "<b>Conditional</b>: l-participle + <i>bych, bys, by, bychom, byste, by</i> — “would …”. "
                "<i>aby</i> (“in order that, that … should”) and <i>kdyby</i> (“if … would”) contain this "
                "auxiliary and are conjugated with it (<i>abych, abys …</i>).",
        "fut": "<b>Future</b>: imperfective verbs use <i>budu, budeš …</i> + infinitive; perfective verbs have no "
               "present, their present-tense forms mean the future.",
        "refl": "<b>Reflexive</b> <i>se</i> (accusative) / <i>si</i> (dative): part of a reflexive verb, or “oneself”, "
                "“each other”; <i>si</i> often means “for oneself”. It is a clitic and stands in second position.",
        "trans": "<b>Transgressive</b> (přechodník): a bookish verbal adverb — “(while) …ing” (present) or "
                 "“having …ed” (past); it agrees with the subject in gender and number.",
        "aux_past": "Present of <i>být</i> used as the <b>past-tense auxiliary</b> (1st and 2nd person only).",
    },
    "pl": {
        "loc": "The <b>locative</b> occurs only after a preposition (<i>w, na, o, po, przy</i>): where something "
               "is, or what one talks about.",
        "ins": "<b>Instrumental</b> without a preposition: the means or tool (“with, by”), the way taken "
               "(<i>lasem</i> “through the forest”), or the predicate noun after <i>być, zostać, stać się</i> "
               "(<i>był muzykantem</i>).",
        "past": "<b>Past tense</b>: the l-form (ending shows gender and number of the subject) + personal endings "
                "<i>-m, -ś, -śmy, -ście</i>; the 3rd person has none (<i>robił</i>). The endings are movable and "
                "may attach to another word of the clause (<i>gdzieś był?</i>).",
        "cond": "<b>Conditional</b>: l-form + <i>by</i> + personal ending (<i>robiłbym</i> “I would do”); "
                "<i>by</i> may also attach to a conjunction: <i>żeby, aby, gdyby</i>.",
        "fut": "<b>Future</b>: imperfective verbs use <i>będę, będziesz …</i> + infinitive or l-form; perfective "
               "verbs have no present, their present-tense forms mean the future.",
        "refl": "<b>Reflexive</b> <i>się</i>: part of a reflexive verb, or “oneself”, “each other”; with a "
                "3rd-person verb also impersonal (<i>mówi się</i> “people say”).",
        "trans": "<b>Adverbial participle</b>: <i>-ąc</i> “(while) …ing”, <i>-wszy/-łszy</i> “having …ed”; it "
                 "does not change and refers to the subject of the clause.",
        "aux_past": "Movable <b>personal ending</b> of the past tense (historically a form of <i>być</i>).",
    },
}


def link(token) -> str:
    if token is None:
        return "the clause"
    return f'<a href="tok:{token.index}"><i>{escape(token.text)}</i></a>'


def prep_info(lang: str, word: str):
    key = word.lower()
    key = VARIANTS[lang].get(key, key)
    return PREPOSITIONS[lang].get(key)


def phrase_base(token):
    t, n = token, 0
    while t.head_token is not None and n < 5:
        h = t.head_token
        same = h.cats.get("case") == t.cats.get("case")
        if t.deprel.split(":")[0] in ("amod", "det", "nummod") and t.deprel not in ("nummod:gov", "det:numgov") \
                and h.upos in ("NOUN", "PROPN", "ADJ", "PRON", "NUM", "DET") and same:
            t = h
        elif t.deprel in ("conj", "appos", "flat") and same:
            t = h
        else:
            break
        n += 1
    return t


def case_notes(lang, token, add, ref):
    b = phrase_base(token)
    case = b.cats.get("case")
    if not case:
        return
    who = "" if b is token else f"The phrase round {link(b)}: "
    h = b.head_token
    rel = b.deprel
    base_rel = rel.split(":")[0]
    prep = b.child("case", upos="ADP")
    counted = any(c.deprel in ("nummod:gov", "det:numgov") for c in b.children)
    if counted and case == "genitive":
        q = next(c for c in b.children if c.deprel in ("nummod:gov", "det:numgov"))
        add(f"{who}<b>genitive after a quantity word</b>: {link(q)} (numerals from five up, <i>"
            + ("mnoho, málo, kolik, několik" if lang == "cs" else "dużo, mało, ile, kilka")
            + "</i>) puts the counted noun in the genitive plural, and the verb in the neuter singular.",
            ref["numerals"])
        return
    if prep is not None:
        info = prep_info(lang, prep.lemma) or prep_info(lang, prep.text)
        text = f"{who}governed by the preposition {link(prep)}"
        if info:
            meaning, cases = info
            names = [CASE_NAMES[c] for c in cases.split("/")]
            text += f" (“{meaning}”), which takes the " + " or ".join(names) + "."
            if "acc" in cases and "/" in cases and case in ("accusative", "locative", "instrumental"):
                text += (" With this preposition the accusative means movement <b>towards</b> a place "
                         "(<i>" + ("kam?" if lang == "cs" else "dokąd?") + "</i>), the other case rest "
                         "<b>in</b> a place (<i>" + ("kde?" if lang == "cs" else "gdzie?") + "</i>).")
            text += f" Here: <b>{case}</b>."
        else:
            text += f"; here it takes the <b>{case}</b>."
        add(text, ref["prepositions"])
        return
    if case == "nominative":
        if base_rel == "nsubj":
            add(f"{who}<b>subject</b> of {link(h)}; in the past tense the verb agrees with it in gender and "
                f"number as well.", ref["agreement"])
        elif b.child("cop") is not None or base_rel in ("xcomp", "root"):
            add(f"{who}<b>predicate nominative</b>: what the subject is.")
        else:
            add(f"{who}nominative: the case of the subject.")
    elif case == "vocative":
        add(f"{who}<b>vocative</b>: the form used to address someone.")
    elif case == "accusative":
        if base_rel == "obj":
            text = f"{who}<b>direct object</b> (accusative) of {link(h)}."
            if b.cats.get("gender") == "masculine" and b.cats.get("animacy") in ("animate", "personal") \
                    and b.cats.get("number") == "singular":
                text += (" For masculine nouns denoting living beings the accusative singular has the same form "
                         "as the genitive.")
            add(text)
        else:
            add(f"{who}accusative without a preposition: direct object, or an expression of time or measure "
                f"(how long, how far).")
    elif case == "genitive":
        negated = h is not None and (h.feats.get("Polarity") == "Neg" or any(
            c.deprel == "advmod:neg" or c.feats.get("Polarity") == "Neg" and c.upos == "PART" for c in h.children))
        if base_rel in ("obj", "nsubj") and negated and lang == "pl":
            add(f"{who}<b>genitive of negation</b>: the direct object of a negated verb ({link(h)}) stands in the "
                f"genitive instead of the accusative.", ref["noun_syntax"])
        elif h is not None and h.upos in ("NOUN", "PROPN", "PRON", "NUM", "DET", "ADJ") and base_rel in (
                "nmod", "obl", "det", "nummod"):
            add(f"{who}<b>genitive</b> depending on {link(h)}: possession or belonging (“of”), or the whole of "
                f"which a part or quantity is taken.")
        elif base_rel in ("obj", "obl", "iobj"):
            add(f"{who}genitive object of {link(h)}: some verbs take the genitive (to fear, ask, need, reach, "
                f"be full of …)" + (", and so often does a negated verb in older Czech." if lang == "cs" else "."))
        else:
            add(f"{who}genitive: “of”.")
    elif case == "dative":
        lemma = h.lemma.lower() if h is not None else ""
        if lemma in DATIVE_VERBS[lang]:
            add(f"{who}<b>dative</b> with {link(h)}: the person to whom something is said, given, done; this "
                f"verb regularly takes a dative.")
        else:
            add(f"{who}<b>dative</b>: the indirect object — to or for whom; also the person who feels or "
                f"experiences something (<i>" + ("je mi zima" if lang == "cs" else "jest mi zimno") + "</i>).")
    elif case == "locative":
        add(who + TEXT[lang]["loc"], ref["prepositions"])
    elif case == "instrumental":
        if h is not None and (h.lemma.lower() in BE[lang] or h.child("cop") is not None
                              and base_rel in ("xcomp", "obl", "nsubj")) and base_rel in ("xcomp", "obl", "iobj"):
            add(f"{who}<b>predicate instrumental</b> with {link(h)}: what someone is or becomes.",
                ref["noun_syntax"])
        else:
            add(who + TEXT[lang]["ins"], ref["noun_syntax"])


def verb_notes(lang, token, entry, add, ref):
    feats = token.feats
    vf = feats.get("VerbForm")
    rel = token.deprel
    base_rel = rel.split(":")[0]
    h = token.head_token
    aspect = feats.get("Aspect", "").split(",")[0]
    kids = token.children
    if rel == "aux:clitic" or (base_rel == "aux" and feats.get("Mood") != "Cnd" and h is not None
                               and h.feats.get("VerbForm") == "Part" and h.feats.get("Tense") == "Past"
                               and feats.get("Tense") == "Pres"):
        add(TEXT[lang]["aux_past"] + (f" It belongs to {link(h)}." if h is not None else ""), ref["past"])
        return
    if rel == "aux:cnd" or feats.get("Mood") == "Cnd" and base_rel == "aux":
        add(TEXT[lang]["cond"] + (f" It belongs to {link(h)}." if h is not None else ""), ref["conditional"])
        return
    if rel == "aux:imp":
        add("<i>niech</i> + 3rd person = “let him/her/them …”: the imperative of the third person.", ref["verbs"])
        return
    if rel == "aux:pass" and h is not None:
        add(f"With the passive participle {link(h)} it forms the <b>passive</b>.", ref["passive"])
        return
    if base_rel == "aux" and h is not None and h.feats.get("VerbForm") in ("Inf", "Part") \
            and feats.get("Tense") == "Fut":
        add(TEXT[lang]["fut"] + f" Here with {link(h)}.", ref["future"])
        return
    if base_rel == "cop" and h is not None:
        add(f"<b>Copula</b> linking the subject with the predicate {link(h)}.")
        return
    # aspect -------------------------------------------------------------------
    if aspect == "Perf":
        add("<b>Perfective</b> verb: the action is seen as a single completed whole"
            + (" — so this present-tense form refers to the <b>future</b>." if feats.get("Tense") == "Pres"
               and vf == "Fin" else "."), ref["aspect"])
    elif aspect == "Imp" and token.upos == "VERB":
        add("<b>Imperfective</b> verb: the action is seen as going on, repeated or in general.", ref["aspect"])
    if feats.get("Polarity") == "Neg" and lang == "cs":
        add("Negated with the prefix <b>ne-</b>, written together with the verb.", ref["negation"])
    refl = next((c for c in kids if c.deprel.startswith("expl")), None)
    if refl is not None:
        add(TEXT[lang]["refl"] + f" Here: {link(refl)}.", ref["reflexive"])
    cond = next((c for c in kids if c.deprel == "aux:cnd" or c.feats.get("Mood") == "Cnd"), None)
    mark = next((c for c in kids if c.deprel == "mark"), None)
    if vf == "Part" and feats.get("Tense") == "Past" or (lang == "pl" and vf == "Fin" and feats.get("Tense") == "Past"):
        if cond is not None:
            add(TEXT[lang]["cond"] + f" Here with {link(cond)}.", ref["conditional"])
        elif mark is not None and mark.text.lower().startswith(("aby", "kdyby", "żeby", "gdyby", "by", "iżby")):
            add(TEXT[lang]["cond"] + f" Here after {link(mark)}.", ref["conditional"])
        else:
            aux = next((c for c in kids if c.deprel.split(":")[0] == "aux"), None)
            add(TEXT[lang]["past"] + (f" Auxiliary here: {link(aux)}." if aux is not None else ""), ref["past"])
    elif vf == "Fin":
        mood = feats.get("Mood")
        if mood == "Imp":
            add("<b>Imperative</b>: a command or request.", ref["imperative"])
        elif feats.get("Tense") == "Fut":
            add(TEXT[lang]["fut"], ref["future"])
        elif feats.get("Person") == "0":
            add("<b>Impersonal</b> form (-no / -to): the action is stated without naming who did it — "
                "“people …ed, it was …ed”.", ref["verbs"])
        elif feats.get("VerbType") == "Quasi":
            add("An <b>impersonal predicative</b> word (<i>można, trzeba, wolno, warto</i>): used with an "
                "infinitive and without a subject.", ref["verbs"])
    elif vf == "Inf":
        if h is not None and base_rel in ("xcomp", "ccomp", "csubj"):
            add(f"<b>Infinitive</b> depending on {link(h)}.", ref["infinitive"])
        else:
            add("<b>Infinitive</b>.", ref["infinitive"])
        if lang == "cs" and token.text.lower().endswith("ti"):
            add("The ending <b>-ti</b> is the older, bookish form of the infinitive (today <i>-t</i>).",
                ref["infinitive"])
    elif vf == "Part" and feats.get("Voice") == "Pass":
        add("<b>Passive participle</b> (-n-, -t-): “…ed”; with <i>" + ("být" if lang == "cs" else "być / zostać")
            + "</i> it forms the passive, or it is used as an adjective.", ref["passive"])
    elif vf == "Conv":
        add(TEXT[lang]["trans"], ref["transgressive"])
    elif vf == "Vnoun":
        add("<b>Verbal noun</b> (-ní / -tí, Polish -nie / -cie): “the …ing”, declined as a neuter noun.",
            ref["verbs"])
    if mark is not None and vf in ("Fin", "Part"):
        add(f"Verb of a subordinate clause introduced by {link(mark)}.")


def notes(lang, token, entry, ref) -> list[tuple[str, list[str]]]:
    out: list[tuple[str, list[str]]] = []

    def add(text, *refs):
        if text not in [n[0] for n in out]:
            out.append((text, [r for group in refs for r in (group if isinstance(group, list) else [group])]))

    upos, cats, feats = token.upos, token.cats, token.feats
    h = token.head_token
    rel = token.deprel
    if upos in ("VERB", "AUX"):
        verb_notes(lang, token, entry, add, ref)
        if feats.get("VerbForm") == "Part" and "Case" in feats:
            case_notes(lang, token, add, ref)
    elif upos in ("NOUN", "PROPN", "ADJ", "DET", "PRON", "NUM"):
        base = phrase_base(token)
        if base is not token and rel.split(":")[0] in ("amod", "det", "nummod") and h is not None:
            add(f"It <b>agrees</b> with {link(h)} in gender, number and case.", ref["adjectives"])
        if rel in ("nummod:gov", "det:numgov") and h is not None:
            add(f"<b>Quantity word governing the genitive</b>: {link(h)} stands in the genitive plural "
                f"(“five of …”).", ref["numerals"])
        if feats.get("Variant") == "Short" and upos == "ADJ":
            add("<b>Short (nominal) form</b> of the adjective, used only in the predicate (<i>"
                + ("rád, zdráv, živ, hotov" if lang == "cs" else "rad, zdrów, gotów, wesół") + "</i>).",
                ref["short"])
        if feats.get("Reflex") == "Yes":
            if feats.get("Poss") == "Yes":
                add("<b>Reflexive possessive</b> (<i>" + ("svůj" if lang == "cs" else "swój") + "</i>): “one's "
                    "own” — it refers to the subject of the clause, whatever its person.", ref["possessive"])
            elif not rel.startswith("expl"):
                add("<b>Reflexive pronoun</b>: refers back to the subject of the clause.", ref["personal"])
            else:
                add(TEXT[lang]["refl"] + (f" It belongs to {link(h)}." if h is not None else ""), ref["reflexive"])
                return out
        pt = feats.get("PronType", "")
        if "Rel" in pt and h is not None:
            clause = h if h.upos in ("VERB", "AUX") else h.head_token
            ant = clause.head_token if clause is not None and clause.deprel.startswith("acl") else None
            if ant is not None:
                add(f"<b>Relative pronoun</b>: gender and number come from its antecedent {link(ant)}, the case "
                    f"from its role in its own clause.", ref["relative"])
        if cats.get("degree") == "comparative":
            add("<b>Comparative</b> (" + ("-ší, -ejší" if lang == "cs" else "-szy, -ejszy; or <i>bardziej</i>")
                + "): “more …, …er”; “than” is " + ("<i>než</i>." if lang == "cs" else "<i>niż</i> or <i>od</i> "
                                                    "+ genitive."), ref["comparison"])
        elif cats.get("degree") == "superlative":
            add("<b>Superlative</b>: prefix " + ("<i>nej-</i>" if lang == "cs" else "<i>naj-</i>")
                + " + comparative.", ref["comparison"])
        if lang == "pl" and upos in ("ADJ", "DET", "PRON") and token.text.lower().endswith(("emi", "em")) \
                and cats.get("case") in ("instrumental", "locative") and not token.text.lower().endswith("iem") \
                or lang == "pl" and upos in ("ADJ", "DET", "PRON") and token.text.lower().endswith("emi"):
            add("Spelling of before 1936: the endings <b>-em</b> (neuter instr./loc. singular) and <b>-emi</b> "
                "(non-masculine-personal instr. plural) are written <b>-ym/-im</b> and <b>-ymi/-imi</b> today.",
                ref["adjectives"])
        case_notes(lang, token, add, ref)
    elif upos == "ADP":
        info = prep_info(lang, token.lemma) or prep_info(lang, token.text)
        text = "<b>Preposition</b>"
        if info:
            meaning, cases = info
            text += f" “{meaning}”; it takes the " + " or ".join(CASE_NAMES[c] for c in cases.split("/"))
        if h is not None and h.cats.get("case"):
            text += f". Here it governs {link(h)} ({h.cats['case']})"
        add(text + ".", ref["prepositions"])
        if token.text.lower() in VARIANTS[lang]:
            add("The extra vowel (<i>" + escape(token.text.lower()) + "</i>) eases pronunciation before a "
                "consonant cluster or a similar sound.")
    elif upos == "SCONJ":
        if h is not None:
            add(f"<b>Subordinating conjunction</b>: it introduces the clause whose verb is {link(h)}.")
        low = token.text.lower()
        if low.startswith(("aby", "kdyby", "żeby", "gdyby", "ażeby", "iżby")):
            add(TEXT[lang]["cond"], ref["conditional"])
    elif upos == "CCONJ":
        add("<b>Coordinating conjunction</b>: joins words or clauses of equal rank.")
    elif upos == "PART" and feats.get("Polarity") == "Neg":
        add("Negation." + (" In Polish a negated verb takes its direct object in the genitive." if lang == "pl"
                           else ""), ref.get("negation", []))
    return out
