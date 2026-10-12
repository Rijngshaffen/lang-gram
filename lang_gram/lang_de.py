"""German: notes on how a word is used in its sentence, and the sections of the
grammar reference (Wikipedia tables) that show its paradigm."""
from __future__ import annotations

from html import escape

PREPOSITIONS = {
    "acc": {"durch": "through", "für": "for", "gegen": "against; towards", "ohne": "without", "um": "around; at (time)",
            "bis": "until, as far as", "wider": "against", "entlang": "along"},
    "dat": {"aus": "out of, from", "außer": "except; out of", "bei": "at, near, with", "mit": "with",
            "nach": "after; to (places)", "seit": "since, for (time)", "von": "from, of, by", "zu": "to",
            "gegenüber": "opposite", "samt": "together with", "nebst": "together with", "ab": "from"},
    "both": {"an": "at, on (vertical); to", "auf": "on (top of); onto", "hinter": "behind", "in": "in; into",
             "neben": "next to", "über": "over, above; about", "unter": "under; among", "vor": "in front of; before",
             "zwischen": "between"},
    "gen": {"während": "during", "wegen": "because of", "trotz": "in spite of", "statt": "instead of",
            "anstatt": "instead of", "innerhalb": "within", "außerhalb": "outside", "unweit": "not far from",
            "um": "(um … willen) for the sake of"},
}
DATIVE_VERBS = {"helfen", "danken", "folgen", "gefallen", "gehören", "glauben", "antworten", "begegnen", "dienen",
                "gehorchen", "schaden", "vertrauen", "fehlen", "passen", "schmecken", "geschehen", "gelingen",
                "nahen", "erscheinen", "drohen", "raten", "zuhören", "zusehen", "nachgehen", "entgegnen",
                "gleichen", "nützen", "widersprechen", "zureden", "bekommen", "wehtun", "leidtun", "einfallen",
                "ausweichen", "entkommen", "nachlaufen", "zustoßen", "widerfahren"}
WEAK_DETERMINERS = {"der", "dieser", "jener", "jeder", "welcher", "mancher", "solcher", "aller", "alle",
                    "derselbe", "derjenige", "beide"}
MIXED_DETERMINERS = {"ein", "kein", "mein", "dein", "sein", "ihr", "unser", "euer", "eine"}
SUBORDINATORS = {
    "dass": "that", "daß": "that", "weil": "because", "wenn": "if; whenever", "als": "when (single past event); than; as",
    "ob": "whether", "da": "since, as", "obwohl": "although", "bis": "until", "damit": "so that",
    "während": "while", "nachdem": "after", "bevor": "before", "ehe": "before", "wie": "as, how; when (narrative)",
    "sobald": "as soon as", "indem": "by …ing, while", "falls": "in case", "seit": "since", "wo": "where; when",
    "so": "as (so … als)", "um": "(um … zu) in order to", "ohne": "(ohne … zu) without …ing",
}


def link(token) -> str:
    if token is None:
        return "the clause"
    return f'<a href="tok:{token.index}"><i>{escape(token.text)}</i></a>'


def lemma(token) -> str:
    return token.lemma.lower()


def phrase_base(token):
    t, n = token, 0
    while t.head_token is not None and n < 5:
        h = t.head_token
        if t.deprel in ("amod", "det", "nummod", "det:poss") and h.upos in ("NOUN", "PROPN", "ADJ", "PRON"):
            t = h
        elif t.deprel in ("conj", "appos", "flat", "flat:name") and h.cats.get("case") == t.cats.get("case"):
            t = h
        else:
            break
        n += 1
    return t


def adjective_inflection(token) -> str | None:
    """strong / weak / mixed, read off the determiner of the noun phrase."""
    h = token.head_token
    if token.deprel != "amod" or h is None:
        return None
    dets = [c for c in h.children if c.upos == "DET" and c.index < token.index]
    if not dets:
        return "strong"
    d = lemma(dets[-1])
    if d in MIXED_DETERMINERS or dets[-1].feats.get("Poss") == "Yes":
        return "mixed"
    return "weak"


def case_notes(token, add):
    b = phrase_base(token)
    case = b.cats.get("case")
    if not case:
        return
    who = "" if b is token else f"The phrase round {link(b)}: "
    h = b.head_token
    rel = b.deprel.split(":")[0]
    prep = b.child("case", upos="ADP")
    if prep is not None:
        p = lemma(prep)
        group = next((g for g in ("acc", "dat", "both", "gen") if p in PREPOSITIONS[g]), None)
        meaning = PREPOSITIONS[group][p] if group else ""
        text = f"{who}governed by the preposition {link(prep)}" + (f" (“{meaning}”)" if meaning else "") + "."
        if group == "both":
            text += (" This is a <b>two-way preposition</b>: accusative for movement towards a place "
                     "(<i>wohin?</i>), dative for position (<i>wo?</i>). Here: <b>" + case + "</b>.")
        elif group:
            text += f" It always takes the <b>{ {'acc': 'accusative', 'dat': 'dative', 'gen': 'genitive'}[group] }</b>."
        add(text, "German grammar#Introduction")
        return
    if case == "nominative":
        if rel == "nsubj":
            add(f"{who}<b>subject</b> of {link(h)}: the verb agrees with it in person and number.")
        elif b.child("cop") is not None or rel in ("xcomp", "root"):
            add(f"{who}<b>predicate nominative</b>: after <i>sein, werden, bleiben, heißen</i> the noun stays in "
                f"the nominative.")
        else:
            add(f"{who}nominative: the case of the subject (and of forms of address).")
    elif case == "accusative":
        if rel == "obj":
            add(f"{who}<b>direct object</b> (accusative) of {link(h)}.")
        else:
            add(f"{who}accusative without a preposition: direct object, or an expression of time or measure "
                f"(<i>den ganzen Tag</i>, <i>einen Schritt</i>).")
    elif case == "dative":
        if h is not None and lemma(h) in DATIVE_VERBS:
            add(f"{who}object of {link(h)}: this verb takes its object in the <b>dative</b>.",
                "German verbs#Conjugation › Dative verbs")
        else:
            add(f"{who}<b>dative</b>: the indirect object — the person to or for whom something is done; some "
                f"verbs (<i>helfen, danken, folgen, gefallen</i>) take only a dative.",
                "German verbs#Conjugation › Dative verbs")
        if b.upos == "NOUN" and b.text.lower().endswith("e") and b.cats.get("number") == "singular" \
                and not b.lemma.lower().endswith("e"):
            add("The ending <b>-e</b> is the old dative singular of strong masculine and neuter nouns "
                "(<i>dem Kinde, im Walde, zu Hause</i>); today it survives in set phrases.",
                "German nouns#Declension for case › For singular nouns")
    elif case == "genitive":
        if h is not None and h.upos in ("NOUN", "PROPN"):
            add(f"{who}<b>genitive</b> attribute of {link(h)}: possession or belonging (“of”, “’s”).")
        else:
            add(f"{who}genitive: possession; a few verbs, adjectives and prepositions also require it.")


def verb_notes(token, entry, add):
    cats, feats = token.cats, token.feats
    vf = cats.get("verbform")
    h = token.head_token
    rel = token.deprel.split(":")[0]
    prt = token.child("compound")
    if prt is not None:
        add(f"<b>Separable verb</b>: {link(prt)} + <i>{escape(token.lemma)}</i> = "
            f"<b>{escape(prt.text.lower() + token.lemma.lower())}</b>. In a main clause the prefix goes to the "
            f"end; in the infinitive, the participle and in subordinate clauses it is attached.",
            "German verbs#Prefixes › Separable prefixes", "German conjugation#Separable and inseparable verbs")
    if token.deprel == "aux:pass" and h is not None:
        add(f"<i>werden</i> + past participle {link(h)} forms the <b>passive</b>: “is/was …ed”.",
            "German verbs#Complex infinitives › Compound infinitives › Passive infinitive", "German verbs#Tenses")
        return
    if rel == "aux" and h is not None:
        hv = h.cats.get("verbform")
        if feats.get("VerbType") == "Mod":
            add(f"<b>Modal verb</b> with the infinitive {link(h)}, which stands at the end of the clause.",
                "German verbs#Conjugation › Modal verbs", "German conjugation#Modal verbs (dürfen, may)")
        elif lemma(token) == "werden" and hv == "infinitive":
            add(f"<i>werden</i> + infinitive {link(h)}: the <b>future</b> tense.", "German verbs#Tenses")
        elif lemma(token) in ("haben", "sein") and hv == "participle":
            tense = "pluperfect" if cats.get("tense") == "past" else "perfect"
            add(f"Auxiliary of the <b>{tense}</b> tense with the past participle {link(h)}. Most verbs take "
                f"<i>haben</i>; verbs of motion or change of state (and <i>sein, bleiben, werden</i>) take "
                f"<i>sein</i>.", "German verbs#Conjugation › Auxiliary verbs", "German verbs#Tenses")
        else:
            add(f"<b>Auxiliary</b> used with {link(h)}.", "German verbs#Conjugation › Auxiliary verbs")
        return
    if rel == "cop" and h is not None:
        add(f"<b>Copula</b>: links the subject with the predicate {link(h)}.")
        return
    if vf == "finite":
        mark = token.child("mark")
        relative = token.deprel.startswith("acl") or any(
            "Rel" in c.feats.get("PronType", "") and c.index < token.index and c.upos == "PRON"
            for c in token.children)
        if mark is not None and mark.upos == "SCONJ":
            add(f"Verb of a <b>subordinate clause</b> introduced by {link(mark)}: the finite verb stands at the "
                f"<b>end</b> of the clause.", "German grammar#Sentence structure")
        elif relative and token.deprel.startswith("acl"):
            add("Verb of a <b>relative clause</b>: like every subordinate clause it has the finite verb at the "
                "end.", "Pronouns in German#Classification and usage › Relative pronouns")
        elif token.deprel in ("root", "parataxis", "conj"):
            add("Finite verb of a main clause: it stands in <b>second position</b> (verb-second); anything "
                "placed first — subject, adverb or a whole clause — is followed directly by the verb.",
                "German grammar#Sentence structure")
        if cats.get("mood") == "imperative":
            add("<b>Imperative</b>: a command to <i>du</i> (verb stem, sometimes + e) or <i>ihr</i> (-t).",
                "German verbs#Conjugation › Imperative conjugation")
        if cats.get("mood") == "subjunctive":
            if cats.get("tense") == "past":
                add("<b>Subjunctive II</b> (Konjunktiv II): unreal conditions and wishes (“would …, were to …”), "
                    "also polite requests.", "German conjugation#German tenses and moods")
            else:
                add("<b>Subjunctive I</b> (Konjunktiv I): reported speech — the narrator repeats what someone "
                    "said without vouching for it.", "German conjugation#German tenses and moods")
        if cats.get("tense") == "past" and cats.get("mood", "indicative") == "indicative":
            add("<b>Preterite</b> (simple past): the normal tense of written narrative. Weak verbs add -te, "
                "strong verbs change the stem vowel (<i>geben – gab</i>).", "German verbs#Tenses")
        refl = token.child("expl")
        if refl is not None:
            add(f"<b>Reflexive verb</b> with {link(refl)}.", "German verbs#Conjugation › Reflexive verbs")
    elif vf == "participle":
        aux = token.child("aux")
        if aux is not None and token.child("aux:pass") is None and lemma(aux) in ("haben", "sein"):
            tense = "pluperfect" if aux.cats.get("tense") == "past" else "perfect"
            add(f"<b>Past participle</b>; with {link(aux)} it forms the <b>{tense}</b> tense and stands at the "
                f"end of the clause.", "German verbs#Participles and verbal nouns › Past participle",
                "German verbs#Tenses")
        elif any(c.deprel == "aux:pass" for c in token.children):
            add("<b>Past participle</b> in the <b>passive</b> (with <i>werden</i>).",
                "German verbs#Participles and verbal nouns › Past participle")
        else:
            add("<b>Past participle</b> (ge-…-t for weak, ge-…-en for strong verbs), used here like an adjective "
                "or with an auxiliary understood.", "German verbs#Participles and verbal nouns › Past participle")
    elif vf == "infinitive":
        zu = next((c for c in token.children if c.feats.get("PartType") == "Inf" or c.text.lower() == "zu"
                   and c.upos == "PART"), None)
        if zu is not None:
            add(f"<b>Infinitive with zu</b> ({link(zu)}): depends on a verb, noun or adjective; with "
                f"<i>um … zu</i> it expresses purpose.", "German verbs#Complex infinitives › The zu-infinitive")
        elif h is not None and (rel in ("xcomp", "ccomp") or any(c.feats.get("VerbType") == "Mod"
                                                                  for c in token.children)):
            add("<b>Infinitive</b> without <i>zu</i>, depending on a modal verb or on <i>lassen, sehen, hören, "
                "gehen, werden</i>; it stands at the end of the clause.", "German verbs#Bare infinitives",
                "German verbs#Conjugation › Modal verbs")
        else:
            add("<b>Infinitive</b>.", "German verbs#Bare infinitives")


def notes(token, entry) -> list[tuple[str, list[str]]]:
    out: list[tuple[str, list[str]]] = []

    def add(text, *refs):
        if text not in [n[0] for n in out]:
            out.append((text, list(refs)))

    upos, cats, feats = token.upos, token.cats, token.feats
    h = token.head_token
    if upos in ("VERB", "AUX"):
        verb_notes(token, entry, add)
    elif upos in ("NOUN", "PROPN", "ADJ", "DET", "PRON", "NUM"):
        if upos == "ADJ":
            kind = adjective_inflection(token)
            if token.deprel == "amod" and h is not None:
                why = {"strong": "no article precedes, so the adjective itself shows gender and case "
                                 "(endings like those of <i>der, die, das</i>)",
                       "weak": "a definite article or <i>dieser, jeder …</i> precedes and already shows the "
                               "case, so the adjective only takes -e or -en",
                       "mixed": "<i>ein, kein</i> or a possessive precedes: -er/-es/-e where that word has no "
                                "ending, otherwise -en"}[kind]
                add(f"Attributive adjective of {link(h)}, <b>{kind} declension</b>: {why}.",
                    f"German adjectives#Adjective inflection › {kind.capitalize()} inflection")
            elif feats.get("Variant") == "Short" or "case" not in cats:
                add("Adjective without an ending: used <b>predicatively</b> (after <i>sein, werden</i> …) or as "
                    "an adverb.", "German adjectives#Adjective inflection › No inflection")
            if cats.get("degree") == "comparative":
                add("<b>Comparative</b> (-er, often with umlaut): “more …, …er”; “than” is <i>als</i>.",
                    "German adjectives#Adjective comparison › Comparative form")
            elif cats.get("degree") == "superlative":
                add("<b>Superlative</b> (-st-): <i>der kleinste</i>, predicatively <i>am kleinsten</i>.",
                    "German adjectives#Adjective comparison › Superlative form")
        if upos == "DET" and feats.get("PronType") == "Art" and h is not None:
            add(f"<b>Article</b> of {link(h)}: its form shows the gender, number and case of the noun — German "
                f"nouns themselves rarely change.", "German articles#Declension › Definite article")
        if upos == "PRON":
            pt = feats.get("PronType", "")
            clause = h
            if "Rel" in pt and clause is not None and clause.deprel.startswith("acl") \
                    and clause.head_token is not None:
                add(f"<b>Relative pronoun</b>: gender and number come from its antecedent "
                    f"{link(clause.head_token)}, the case from its role in the relative clause.",
                    "Pronouns in German#Classification and usage › Relative pronouns")
            elif feats.get("Reflex") == "Yes":
                add("<b>Reflexive pronoun</b>: refers back to the subject of the clause.",
                    "Pronouns in German#Classification and usage › Reflexive pronouns")
            elif pt == "Prs" and token.text.lower() == "es" and token.deprel == "expl":
                add("<i>es</i> as a dummy subject (“there”, “it”) holding the first position.",
                    "Pronouns in German#Classification and usage › Personal pronouns")
            elif pt == "Prs" and cats.get("gender") == "neuter" and cats.get("person") == "third-person":
                add("A neuter pronoun refers to a neuter noun whatever the natural sex: <i>das Mädchen</i>, "
                    "<i>das Rotkäppchen</i>, <i>das Kind</i> → <i>es, ihm, sein</i>.",
                    "Pronouns in German#Classification and usage › Personal pronouns")
        if token.is_mwt_part and upos in ("ADP", "DET"):
            pass
        else:
            case_notes(token, add)
    if upos == "ADP":
        p = lemma(token)
        group = next((g for g in ("acc", "dat", "both", "gen") if p in PREPOSITIONS[g]), None)
        if token.deprel == "compound:prt" and h is not None:
            add(f"<b>Separable prefix</b> of {link(h)}: together they are the verb "
                f"<b>{escape(token.text.lower() + h.lemma.lower())}</b>. In a main clause the prefix stands at "
                f"the end.", "German verbs#Prefixes › Separable prefixes")
        elif group:
            governs = {"acc": "the accusative", "dat": "the dative", "gen": "the genitive",
                       "both": "the accusative (movement towards) or the dative (position)"}[group]
            text = f"<b>Preposition</b> “{PREPOSITIONS[group][p]}”; it takes {governs}."
            if h is not None and h.cats.get("case"):
                text += f" Here it governs {link(h)} ({h.cats['case']})."
            add(text)
    elif upos == "SCONJ":
        meaning = SUBORDINATORS.get(lemma(token)) or SUBORDINATORS.get(token.text.lower())
        text = "<b>Subordinating conjunction</b>" + (f" “{meaning}”" if meaning else "")
        if h is not None:
            text += f": it introduces a subordinate clause, whose finite verb {link(h)} goes to the end"
        add(text + ".", "German grammar#Sentence structure")
    elif upos == "CCONJ":
        add("<b>Coordinating conjunction</b>: it joins words or clauses of equal rank and does not change the "
            "word order (<i>und, aber, oder, denn, sondern</i>).")
    elif upos == "PART":
        if feats.get("PartType") == "Inf" and h is not None:
            add(f"<i>zu</i> marking the infinitive {link(h)}.", "German verbs#Complex infinitives › The zu-infinitive")
        elif feats.get("Polarity") == "Neg":
            add("Negation: <i>nicht</i> stands before the element it negates, or towards the end of the clause.")
    return out


def chapters(token, entry) -> list[str]:
    """Reference sections with the paradigm of this kind of word."""
    upos, feats = token.upos, token.feats
    tags = (entry or {}).get("t", [])
    out = []
    if upos in ("NOUN", "PROPN"):
        out += ["German nouns#Declension for case › General rules of declension",
                "German nouns#Declension for case › Declension classes", "German declension#Nouns"]
    elif upos == "DET":
        if feats.get("PronType") == "Art":
            out += ["German declension#Articles › Definite article" if feats.get("Definite") == "Def"
                    else "German declension#Articles › Indefinite article",
                    "German articles#Declension › Definite article" if feats.get("Definite") == "Def"
                    else "German articles#Declension › Indefinite article"]
        elif feats.get("Poss") == "Yes":
            out += ["Pronouns in German#Classification and usage › Possessive pronouns"]
        else:
            out += ["German declension#Adjectival pronouns"]
    elif upos == "ADJ":
        kind = adjective_inflection(token)
        if kind:
            out += [f"German declension#Adjectives › Attributive adjectives › {kind.capitalize()} inflection"]
        out += ["German adjectives#Adjective inflection"]
    elif upos == "PRON":
        pt = feats.get("PronType", "")
        section = ("Reflexive pronouns" if feats.get("Reflex") == "Yes" else
                   "Personal pronouns" if pt == "Prs" else
                   "Relative pronouns" if "Rel" in pt and "Int" not in pt else
                   "Interrogative pronouns" if "Int" in pt else
                   "Demonstrative pronouns" if "Dem" in pt else "Indefinite pronouns")
        out += [f"German declension#Pronouns › {section}",
                f"Pronouns in German#Classification and usage › {section}"]
    elif upos in ("VERB", "AUX"):
        lem = lemma(token)
        special = {"sein": "German conjugation#Irregular verbs sein (to be)", "haben": "German conjugation#haben (to have)",
                   "werden": "German conjugation#werden (to become, shall, will)", "tun": "German conjugation#tun (to do)",
                   "gehen": "German conjugation#Irregular verbs (gehen, to go, to walk)"}
        if lem in special:
            out.append(special[lem])
        elif feats.get("VerbType") == "Mod" or lem in ("können", "müssen", "sollen", "wollen", "dürfen", "mögen"):
            out += ["German conjugation#Modal verbs (dürfen, may)", "German verbs#Conjugation › Modal verbs"]
        elif "strong" in tags or any(t.startswith("class-") for t in tags):
            out.append("German conjugation#Irregular -en verbs (strong verbs) (geben, to give)")
        else:
            out.append("German conjugation#Regular -en verbs (weak verbs) (lieben, to love)")
        out += ["German verbs#Conjugation", "German conjugation#German tenses and moods"]
    return out
