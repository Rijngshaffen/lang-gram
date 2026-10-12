"""Everything the side panel says about a clicked word."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from html import escape

from . import lang_cs, lang_de, lang_la, lang_pl
from .library import Library, Token
from .morph import CATEGORY_ORDER, LANGS, norm_form
from .paradigm import entry_paradigm

POS_NAMES = {
    "NOUN": "noun", "PROPN": "proper noun", "VERB": "verb", "AUX": "auxiliary verb", "ADJ": "adjective",
    "ADV": "adverb", "PRON": "pronoun", "DET": "determiner", "ADP": "preposition", "NUM": "numeral",
    "CCONJ": "coordinating conjunction", "SCONJ": "subordinating conjunction", "PART": "particle",
    "INTJ": "interjection", "X": "other", "SYM": "symbol", "PUNCT": "punctuation",
}
PRON_TYPES = {"Prs": "personal", "Dem": "demonstrative", "Rel": "relative", "Int": "interrogative",
              "Ind": "indefinite", "Tot": "collective (“all, every”)", "Neg": "negative", "Art": "article",
              "Con": "contrastive (“other”)", "Emp": "emphatic", "Rcp": "reciprocal"}
CATEGORY_LABELS = {"verbform": "Form", "mood": "Mood", "tense": "Tense", "voice": "Voice", "person": "Person",
                   "number": "Number", "case": "Case", "gender": "Gender", "animacy": "Animacy",
                   "degree": "Degree", "aspect": "Aspect", "inflection": "Declension"}
VALUE_NAMES = {"first-person": "1st person", "second-person": "2nd person", "third-person": "3rd person",
               "personal": "masculine personal", "nonpersonal": "not masculine personal"}

HINTS = {
    "case": {
        "*": {
            "nominative": "the subject, and what is said to be the subject",
            "accusative": "the direct object; also the goal of motion and extent of time or space",
            "genitive": "“of”: possession, belonging, the whole of which something is a part",
            "dative": "“to, for”: the indirect object, the person concerned",
            "vocative": "the form of address",
        },
        "la": {"ablative": "“by, with, from, in”: means, manner, cause, separation, place and time",
               "locative": "the place where (towns, domī, humī, rūrī)"},
        "cs": {"locative": "only after a preposition: place where, topic (“about”)",
               "instrumental": "“with, by”: means, accompaniment (with s), predicate after být"},
        "pl": {"locative": "only after a preposition: place where, topic (“about”)",
               "instrumental": "“with, by”: means, accompaniment (with z), predicate after być"},
        "de": {"accusative": "the direct object; after some prepositions; direction with an, auf, in …",
               "dative": "the indirect object; after many prepositions; position with an, auf, in …"},
    },
    "tense": {
        "la": {"present": "action going on now; in lively narrative also for the past (historical present)",
               "imperfect": "continuing, repeated or attempted action in the past: “was …ing, used to …”",
               "perfect": "completed action: “did …” or “has done …”", "pluperfect": "“had …”",
               "future": "“will …”", "future perfect": "“will have …”"},
        "de": {"present": "present (also used for the future)", "past": "preterite: the tense of narration"},
        "cs": {"present": "present (of perfective verbs: future meaning)", "past": "past", "future": "future"},
        "pl": {"present": "present (of perfective verbs: future meaning)", "past": "past", "future": "future"},
    },
    "mood": {
        "*": {"indicative": "states a fact or asks about one", "imperative": "a command or request",
              "conditional": "“would …”"},
        "la": {"subjunctive": "will, wish, possibility — and the mood of most dependent clauses"},
        "de": {"subjunctive": "reported speech (I) or unreal conditions and wishes (II)"},
    },
    "voice": {"*": {"active": "the subject acts", "passive": "the subject undergoes the action"}},
    "verbform": {
        "*": {"finite": "has person and number, can be the predicate of a clause",
              "infinitive": "the verb's name form: “to …”",
              "participle": "a verbal adjective: “…ing, …ed”",
              "gerundive": "verbal adjective in -ndus: “to be …ed, that must be …ed”",
              "gerund": "verbal noun in -ndum: “…ing”",
              "supine": "verbal noun in -um / -ū",
              "transgressive": "verbal adverb: “(while) …ing, having …ed”",
              "verbal noun": "noun made from the verb: “the …ing”",
              "past participle (l-form)": "the form in -l that builds the past tense and the conditional"},
    },
    "degree": {"*": {"comparative": "“more …, …er”", "superlative": "“most …, …est”, or “very …”"}},
    "aspect": {"*": {"imperfective": "the action as a process, a habit or a general fact",
                     "perfective": "the action as one completed whole"}},
    "animacy": {
        "cs": {"animate": "living beings: accusative singular = genitive, special nominative plural",
               "inanimate": "things: accusative = nominative"},
        "pl": {"personal": "men: special plural forms (“virile”), accusative = genitive",
               "animate": "living beings: accusative singular = genitive",
               "inanimate": "things: accusative = nominative"},
    },
}

RELATIONS = {
    "root": "<b>Main predicate</b> of the sentence.",
    "nsubj": "<b>Subject</b> of {h}.",
    "nsubj:pass": "<b>Subject</b> of the passive {h}.",
    "nsubj:outer": "<b>Subject</b> of the clause whose predicate is {h}.",
    "csubj": "Predicate of a clause that is the <b>subject</b> of {h}.",
    "csubj:pass": "Predicate of a clause that is the <b>subject</b> of the passive {h}.",
    "obj": "<b>Direct object</b> of {h}.",
    "iobj": "<b>Indirect object</b> of {h}.",
    "obl": "<b>Adverbial</b> of {h}: place, time, manner, means or circumstance.",
    "obl:arg": "<b>Object</b> of {h} in an oblique case (not the plain accusative) or with a preposition.",
    "obl:agent": "<b>Agent</b> of the passive {h}: by whom it is done.",
    "obl:cmpr": "<b>Standard of comparison</b> for {h}: “than …, as …”.",
    "obl:lmod": "<b>Adverbial of place</b> with {h}.",
    "obl:tmod": "<b>Adverbial of time</b> with {h}.",
    "vocative": "<b>Address</b>: the person spoken to.",
    "nmod": "<b>Attribute</b> of the noun {h}.",
    "nmod:poss": "<b>Possessor</b> of {h}.",
    "nmod:arg": "<b>Complement</b> of the noun {h}.",
    "appos": "<b>Apposition</b> to {h}: another name for the same person or thing.",
    "amod": "<b>Adjective</b> describing {h}.",
    "amod:flat": "<b>Adjective</b> forming a fixed name with {h}.",
    "det": "<b>Determiner</b> of {h}.",
    "det:poss": "<b>Possessive</b> determiner of {h}.",
    "det:numgov": "<b>Quantity word</b> with {h}; it decides the case of the noun.",
    "det:nummod": "<b>Quantity word</b> agreeing with {h}.",
    "nummod": "<b>Numeral</b> counting {h}.",
    "nummod:gov": "<b>Numeral</b> counting {h}; it decides the case of the noun (genitive plural).",
    "case": "<b>Preposition</b> governing {h}.",
    "mark": "<b>Subordinator</b>: introduces the clause whose predicate is {h}.",
    "cc": "<b>Conjunction</b> joining {h} to what precedes.",
    "cc:preconj": "First part of a <b>paired conjunction</b> (“both … and”, “either … or”) with {h}.",
    "conj": "<b>Coordinated</b> with {h}: it has the same function in the sentence.",
    "conj:expl": "Explains or restates {h}.",
    "advmod": "<b>Adverb</b> modifying {h}.",
    "advmod:neg": "<b>Negation</b> of {h}.",
    "advmod:emph": "<b>Emphasising particle</b> on {h}.",
    "advmod:tmod": "<b>Adverb of time</b> with {h}.",
    "advmod:lmod": "<b>Adverb of place</b> with {h}.",
    "advcl": "Predicate of an <b>adverbial clause</b> (when, because, if, although, in order to …) attached to {h}.",
    "advcl:abs": "Predicate of an <b>absolute construction</b> attached to {h}.",
    "advcl:pred": "<b>Predicative attribute</b>: describes the subject or object while {h} takes place.",
    "advcl:cmp": "Predicate of a <b>comparative clause</b> (“as …, than …”) attached to {h}.",
    "advcl:cmpr": "Predicate of a <b>comparative clause</b> (“as …, than …”) attached to {h}.",
    "advcl:relcl": "Predicate of a relative clause loosely attached to {h}.",
    "acl": "Predicate of a clause or participle phrase <b>describing</b> {h}.",
    "acl:relcl": "Predicate of a <b>relative clause</b> describing {h}.",
    "ccomp": "Predicate of a <b>content clause</b> (“that …”, reported statement or question) depending on {h}.",
    "ccomp:obj": "Predicate of an <b>object clause</b> depending on {h}.",
    "ccomp:cleft": "Predicate of the clause that completes {h}.",
    "ccomp:relcl": "Predicate of a relative clause used as a content clause with {h}.",
    "ccomp:reported": "Predicate of <b>reported speech</b> depending on {h}.",
    "csubj:relcl": "Predicate of a relative clause that is the subject of {h}.",
    "xcomp": "<b>Complement</b> of {h}: an infinitive or predicate without a subject of its own.",
    "xcomp:pred": "<b>Predicative complement</b> of {h}.",
    "xcomp:subj": "<b>Predicative complement</b> of {h}, said of its subject.",
    "cop": "<b>Copula</b> (“to be”) linking the subject with the predicate {h}.",
    "cop:locat": "<b>Verb “to be”</b> with a place expression {h}.",
    "aux": "<b>Auxiliary</b> of {h}.",
    "aux:pass": "<b>Passive auxiliary</b> of {h}.",
    "aux:clitic": "<b>Personal ending</b> (movable) of {h}.",
    "aux:cnd": "<b>Conditional particle</b> of {h}.",
    "aux:imp": "<b>Imperative particle</b> with {h}.",
    "expl": "<b>Dummy pronoun</b> filling a position in the clause of {h}.",
    "expl:pv": "<b>Reflexive particle</b> belonging to the verb {h}.",
    "expl:pass": "<b>Reflexive particle</b> giving {h} a passive or impersonal sense.",
    "compound": "Part of a <b>compound</b> with {h}.",
    "compound:prt": "<b>Separable prefix</b> of the verb {h}.",
    "flat": "Part of a multi-word <b>name or expression</b> with {h}.",
    "flat:name": "Part of the <b>name</b> {h}.",
    "fixed": "Part of a <b>fixed expression</b> with {h}.",
    "parataxis": "A clause set <b>side by side</b> with {h} — direct speech, an aside, or a loosely added clause.",
    "parataxis:obj": "<b>Direct speech</b> that is the object of {h}.",
    "parataxis:insert": "An <b>inserted</b> clause (“said he”) in {h}.",
    "parataxis:reporting": "The reporting clause (“said he”) inserted in {h}.",
    "discourse": "<b>Discourse word</b> (connective, interjection) in the clause of {h}.",
    "discourse:intj": "<b>Interjection</b> in the clause of {h}.",
    "orphan": "Belongs to a clause whose verb is left out; attached to {h}.",
    "dep": "Loosely attached to {h}.",
}
SHORT = {
    "nsubj": "subject", "csubj": "subject clause", "obj": "object", "iobj": "indirect object", "obl": "adverbial",
    "vocative": "address", "nmod": "attribute", "appos": "apposition", "amod": "adjective", "det": "determiner",
    "nummod": "numeral", "case": "preposition", "mark": "subordinator", "cc": "conjunction", "conj": "coordinated",
    "advmod": "adverb", "advcl": "adverbial clause", "acl": "describing clause", "ccomp": "content clause",
    "xcomp": "complement", "cop": "copula", "aux": "auxiliary", "expl": "reflexive/dummy", "compound": "prefix",
    "flat": "name part", "fixed": "fixed", "parataxis": "parataxis", "discourse": "discourse word",
    "orphan": "orphan", "dep": "dependent",
}
LANG_MODULES = {"la": lang_la, "de": lang_de, "cs": lang_cs, "pl": lang_pl}


@dataclass
class Analysis:
    word: str = ""
    paradigm: str = ""
    grammar: str = ""
    head: Token | None = None
    children: list = field(default_factory=list)


def link(token: Token) -> str:
    if token is None:
        return "the clause"
    return f'<a href="tok:{token.index}"><i>{escape(token.text)}</i></a>'


def hint(lang: str, category: str, value: str) -> str:
    table = HINTS.get(category, {})
    return table.get(lang, {}).get(value) or table.get("*", {}).get(value, "")


def pos_name(token: Token) -> str:
    feats = token.feats
    name = POS_NAMES.get(token.upos, token.upos.lower())
    if token.upos in ("PRON", "DET"):
        kinds = []
        if feats.get("Poss") == "Yes":
            kinds.append("possessive")
        if feats.get("Reflex") == "Yes":
            kinds.append("reflexive")
        for pt in feats.get("PronType", "").split(","):
            if pt in PRON_TYPES and not (pt == "Prs" and kinds):
                kinds.append(PRON_TYPES[pt])
        if "article" in kinds:
            return ("definite " if feats.get("Definite") == "Def" else "indefinite ") + "article"
        if kinds:
            name = " / ".join(kinds) + " " + name
    if token.upos == "NUM":
        name = {"Card": "cardinal ", "Ord": "ordinal ", "Dist": "distributive ", "Mult": "multiplicative "}.get(
            feats.get("NumType", ""), "") + name
    if token.upos == "ADJ" and feats.get("NumType") == "Ord":
        name = "ordinal numeral (adjective)"
    return name


def entry_for(lib: Library, token: Token):
    return lib.lexicon(token.lang).get(token.lex)


def display_cats(token: Token, entry) -> dict:
    cats = dict(token.cats)
    if token.lang == "la":
        if cats.get("verbform") == "gerundive" and not lang_la._is_gerundive_agreeing(token):
            cats["verbform"] = "gerund"
            cats.pop("gender", None)
        if lang_la.is_deponent(entry) and cats.get("voice") == "passive":
            cats["voice"] = "passive in form (deponent: active meaning)"
        if cats.get("verbform") in ("gerund", "gerundive", "supine"):
            cats.pop("tense", None)
    if token.lang == "de" and token.upos == "ADJ":
        kind = lang_de.adjective_inflection(token)
        if kind:
            cats["inflection"] = kind
    return cats


def form_table(token: Token, entry) -> str:
    cats = display_cats(token, entry)
    rows = []
    for cat in CATEGORY_ORDER:
        value = cats.get(cat)
        if not value:
            continue
        shown = VALUE_NAMES.get(value, value)
        h = hint(token.lang, cat, value)
        if cat == "tense" and token.lang == "la" and cats.get("verbform") in ("participle", "infinitive"):
            h = {"present": "at the same time as the governing verb", "perfect": "before the governing verb",
                 "future": "after the governing verb"}.get(value, h)
        rows.append(f'<tr><th>{CATEGORY_LABELS[cat]}</th><td><b>{escape(shown)}</b></td>'
                    f'<td class="muted wrap">{escape(h)}</td></tr>')
    if not rows:
        return '<p class="muted">This word does not inflect.</p>'
    return f'<table class="grid" cellspacing="0">{"".join(rows)}</table>'


def summary_line(token: Token, entry) -> str:
    """ablative plural feminine · perfect passive participle"""
    cats = display_cats(token, entry)
    order = ["person", "number", "tense", "mood", "voice", "verbform", "degree", "case", "gender"]
    if token.upos not in ("VERB", "AUX"):
        order = ["degree", "case", "number", "gender", "animacy"]
    elif cats.get("verbform") not in ("finite", None):
        order = ["tense", "voice", "verbform", "case", "number", "gender"]
    if cats.get("verbform") == "past participle (l-form)":
        return " ".join(["past tense form (l-participle)"] + [cats[c] for c in ("gender", "number") if cats.get(c)])
    if token.lang in ("cs", "pl") and cats.get("voice") == "active":
        cats.pop("voice")
    parts = [VALUE_NAMES.get(cats[c], cats[c]) for c in order if cats.get(c) and cats[c] != "finite"]
    return " ".join(parts)


def relation_html(token: Token) -> str:
    rel = token.deprel
    template = RELATIONS.get(rel) or RELATIONS.get(rel.split(":")[0]) or "Attached to {h}."
    h = token.head_token
    if h is None:
        return RELATIONS["root"] if rel == "root" else template.replace(" of {h}", "").replace("{h}", "the clause")
    return template.format(h=link(h))


def dependents_html(token: Token) -> str:
    kids = [c for c in token.children if c.is_word]
    if not kids:
        return ""
    parts = []
    for c in kids:
        label = SHORT.get(c.deprel.split(":")[0], c.deprel)
        if c.deprel == "nsubj:pass":
            label = "subject (passive)"
        parts.append(f"{link(c)} <span class=\"muted\">({label})</span>")
    return "<p><b>Words depending on it:</b> " + ", ".join(parts) + "</p>"


def refs_html(lang: str, refs: list[str], lib: Library) -> str:
    if not refs:
        return ""
    links = []
    if lang == "la":
        for topic in refs:
            title, sections = lang_la.TOPICS[topic]
            nums = ", ".join(str(n) for n in sections)
            links.append(f'<a href="ag:{topic}">A&amp;G §&nbsp;{nums} {escape(title)}</a>')
    else:
        known = {c["id"] for c in lib.grammar(lang, "reference").get("chapters", [])}
        for ref in refs:
            if ref in known:
                links.append(f'<a href="ref:{escape(ref)}">{escape(ref.replace("#", " › "))}</a>')
    return ' <span class="small">[' + "; ".join(links) + "]</span>" if links else ""


def word_block(lib: Library, token: Token, heading: bool = True):
    """HTML for one syntactic word plus the grammar references it wants."""
    lang = token.lang
    entry = entry_for(lib, token)
    module = LANG_MODULES[lang]
    html = []
    if heading:
        html.append(f"<h1>{escape(token.text)}</h1>")
    # dictionary line
    lemma = entry["w"] if entry and norm_form(lang, entry["w"]) == norm_form(lang, token.lemma) else token.lemma
    line = f'<span class="lemma">{escape(lemma)}</span> &nbsp;<span class="tag">{escape(pos_name(token))}</span>'
    summary = summary_line(token, entry)
    if summary:
        line += f" &nbsp;·&nbsp; {escape(summary)}"
    html.append(f"<p>{line}</p>")
    if entry:
        bases = lib.lexicon(lang).bases(entry)
        verb = next((b for b, kind in bases if kind in ("participle", "form") and b["p"] == "verb"), None)
        if verb is not None and token.upos in ("VERB", "AUX"):
            # A participle with an entry of its own: the verb is the real dictionary word.
            if verb["g"]:
                html.append('<p class="gloss">' + escape("; ".join(verb["g"][:4])) + "</p>")
            html.append(f'<p class="muted small">{escape(verb["h"])}</p>')
            own = f" — <span class=\"gloss\">{escape('; '.join(entry['g'][:3]))}</span>" if entry["g"] else ""
            html.append(f'<p>participle <b>{escape(entry["w"])}</b>{own}</p>')
        else:
            if entry["g"]:
                html.append('<p class="gloss">' + escape("; ".join(entry["g"][:4])) + "</p>")
            if entry["h"] and norm_form(lang, entry["h"]) != norm_form(lang, entry["w"]):
                html.append(f'<p class="muted small">{escape(entry["h"])}</p>')
            for base, kind in bases[:2]:
                label = {"participle": "participle of", "comparative": "comparative of",
                         "superlative": "superlative of", "adverb": "adverb from", "form": "form of"}[kind]
                gloss = f" — <span class=\"gloss\">{escape('; '.join(base['g'][:3]))}</span>" if base["g"] else ""
                html.append(f'<p>{label} <b>{escape(base["w"])}</b>{gloss}<br>'
                            f'<span class="muted small">{escape(base["h"])}</span></p>')
    else:
        html.append('<p class="muted small">Not found in the dictionary; the analysis below comes from the '
                    'parser alone.</p>')
    # form
    html.append("<h2>Form</h2>")
    html.append(form_table(token, entry))
    # role
    html.append("<h2>Role in the sentence</h2>")
    html.append(f"<p>{relation_html(token)}</p>")
    refs: list[str] = []
    notes = module.syntax_notes(token, entry) if lang == "la" else module.notes(token, entry)
    if notes:
        items = []
        for text, note_refs in notes:
            items.append(f"<li>{text}{refs_html(lang, note_refs, lib)}</li>")
            refs += [r for r in note_refs if r not in refs]
        html.append("<ul>" + "".join(items) + "</ul>")
    html.append(dependents_html(token))
    # remarks about the analysis itself
    remarks = []
    if token.norm and not token.is_mwt_part:
        remarks.append(f"Older spelling; in today's dictionaries: <b>{escape(token.norm)}</b>.")
    if "F" in token.flags:
        remarks.append("The parser's features were adjusted to fit this word's inflection table.")
    if "i" in token.flags:
        remarks.append("The case is not marked on the word itself; it is read off its article, preposition or "
                       "function.")
    if remarks:
        html.append('<p class="muted small">' + " ".join(remarks) + "</p>")
    return "".join(html), entry, refs


def paradigm_html(lib: Library, token: Token, entry) -> str:
    lang = token.lang
    parts = []
    if lang == "la":
        model = lang_la.model_paradigm(token, entry)
        if model:
            parts.append("<h2>Model paradigm</h2>" + model)
    if entry:
        lexicon = lib.lexicon(lang)
        shown = [entry] + [b for b, kind in lexicon.bases(entry) if kind in ("participle", "form")]
        extra = {}
        if lang == "de" and token.upos == "ADJ":
            kind = lang_de.adjective_inflection(token)
            if kind:
                extra["inflection"] = kind
        for i, e in enumerate(shown):
            table, _found = entry_paradigm(lang, e, token, extra)
            if table:
                parts.append(f"<h2>Forms of <i>{escape(e['w'])}</i></h2>")
                if i == 0:
                    parts.append('<p class="muted small">The form in the text is marked; a paler mark shows '
                                 'other cells with the same spelling.</p>')
                parts.append(table)
        if len(parts) > (1 if lang == "la" else 0):
            parts.append(f'<p class="muted small">Forms from {escape(lexicon.source)}.</p>')
    if not parts:
        parts.append('<p class="muted">No paradigm: this word does not inflect, or it is not in the '
                     'dictionary.</p>')
    return "".join(parts)


def ag_section_html(lib: Library, number: int, limit: int = 14) -> str:
    sections = lib.grammar("la", "allen_greenough").get("sections", {})
    n = number
    while n > 0 and str(n) not in sections:
        n -= 1
    if n <= 0:
        return ""
    paras = sections[str(n)]
    note = "" if n == number else (f' <span class="muted small">(in the scanned text § {number} runs on from '
                                   f'§ {n}; look further down)</span>')
    body = "".join(f"<p>{escape(p)}</p>" for p in paras[:limit if n == number else limit * 3])
    more = len(paras) - (limit if n == number else limit * 3)
    if more > 0:
        body += f'<p class="muted small">… {more} more paragraphs: <a href="agfull:{n}">show all of § {n}</a></p>'
    return f'<h3 id="s{number}">§ {number}{note}</h3>{body}'


def grammar_html(lib: Library, token: Token, entry, refs: list[str]) -> str:
    lang = token.lang
    module = LANG_MODULES[lang]
    parts = []
    if lang == "la":
        topics = list(refs)
        for t in lang_la.morphology_topics(token, entry):
            if t not in topics:
                topics.append(t)
        if not topics:
            return '<p class="muted">No grammar section is linked to this word.</p>'
        toc = " · ".join(f'<a href="#{t}">{escape(lang_la.TOPICS[t][0])}</a>' for t in topics)
        parts.append(f'<p class="small">{toc}</p>')
        for t in topics:
            title, numbers = lang_la.TOPICS[t]
            parts.append(f'<h2 id="{t}">{escape(title)}</h2>')
            shown = set()
            for n in numbers:
                html = ag_section_html(lib, n)
                if html and html not in shown:
                    shown.add(html)
                    parts.append(html)
        parts.append('<p class="muted small">Allen and Greenough’s New Latin Grammar (1903). The text comes '
                     'from a scan that lost most macrons and garbles some letters and tables.</p>')
        return "".join(parts)
    chapters = {c["id"]: c for c in lib.grammar(lang, "reference").get("chapters", [])}
    wanted = [r for r in module.chapters(token, entry) + refs if r in chapters]
    wanted = list(dict.fromkeys(wanted))
    if not wanted:
        return '<p class="muted">No grammar section is linked to this word.</p>'
    for ref in wanted[:6]:
        c = chapters[ref]
        parts.append(f'<h2 id="{escape(ref)}">{escape(c["page"])} — {escape(c["path"])}</h2>{c["html"]}')
    pages = sorted({(chapters[r]["page"], chapters[r]["url"]) for r in wanted[:6]})
    src = "; ".join(f'<a href="{u}">{escape(p)}</a>' for p, u in pages)
    parts.append(f'<p class="muted small">Source: Wikipedia — {src} (CC BY-SA 4.0).</p>')
    return "".join(parts)


def analyse(lib: Library, token: Token) -> Analysis:
    """Build the three panels for a clicked word (all parts of a contraction together)."""
    group = token.siblings_in_token() if token.is_mwt_part else [token]
    result = Analysis(head=token.head_token, children=[c for c in token.children if c.is_word])
    word_parts, paradigm_parts, grammar_parts = [], [], []
    if len(group) > 1:
        surface = token.text
        pieces = " + ".join(f"<b>{escape(t.form)}</b>" for t in group)
        word_parts.append(f"<h1>{escape(surface)}</h1><p>One written word, {len(group)} grammatical words: "
                          f"{pieces}.</p>")
    for i, t in enumerate(group):
        block, entry, refs = word_block(lib, t, heading=len(group) == 1)
        if len(group) > 1:
            word_parts.append(f'<h1>{escape(t.form)}</h1>')
        word_parts.append(block)
        para = paradigm_html(lib, t, entry)
        if len(group) > 1:
            paradigm_parts.append(f"<h1>{escape(t.form)}</h1>")
            grammar_parts.append(f"<h1>{escape(t.form)}</h1>")
        paradigm_parts.append(para)
        grammar_parts.append(grammar_html(lib, t, entry, refs))
    sentence = token.sentence
    a, b = sentence.span
    text = sentence.paragraph.text
    marked = (escape(text[a:token.start]) + "<b>" + escape(text[token.start:token.end]) + "</b>"
              + escape(text[token.end:b]))
    word_parts.append(f'<h2>Sentence</h2><p class="small">{marked}</p>')
    result.word = "".join(word_parts)
    result.paradigm = "".join(paradigm_parts)
    result.grammar = "".join(grammar_parts)
    return result


def language_name(code: str) -> str:
    return LANGS.get(code, code)


def strip_tags(html: str) -> str:
    return re.sub(r"<[^>]+>", "", html)
