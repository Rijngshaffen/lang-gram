"""Latin: which model paradigm a word follows, which construction it
stands in, and which sections of Allen & Greenough explain it."""
from __future__ import annotations

from html import escape

from . import latin_paradigms as tb
from .morph import norm_form

# --------------------------------------------------------------------------- #
# Allen & Greenough: topic -> (title, section numbers)
# --------------------------------------------------------------------------- #
TOPICS = {
    # forms
    "cases": ("The cases", [35]),
    "decl1": ("First declension (ā-stems)", [40, 41, 42]),
    "decl2": ("Second declension (o-stems)", [45, 46, 47, 48]),
    "decl3": ("Third declension", [53, 54, 55, 56, 57]),
    "decl3i": ("Third declension: i-stems", [65, 66, 67, 68, 71, 73]),
    "decl4": ("Fourth declension (u-stems)", [88, 89, 90]),
    "decl5": ("Fifth declension (ē-stems)", [95, 96, 97]),
    "adj12": ("Adjectives of the first and second declensions", [109, 110, 111]),
    "adj_ius": ("Adjectives with genitive in -īus", [113]),
    "adj3": ("Adjectives of the third declension", [115, 116, 119]),
    "comparison": ("Comparison of adjectives", [123, 124, 125, 129]),
    "numerals": ("Numerals", [132, 133, 134]),
    "pers_pron": ("Personal and reflexive pronouns", [142, 143, 144]),
    "poss_pron": ("Possessive pronouns", [145]),
    "dem_pron": ("Demonstrative pronouns", [146]),
    "rel_pron": ("Relative pronoun", [147]),
    "int_pron": ("Interrogative and indefinite pronouns", [148, 149, 151]),
    "verb_general": ("The verb: voices, moods, tenses", [153, 154, 155, 156]),
    "esse": ("The verb sum", [170]),
    "conj1": ("First conjugation", [184]),
    "conj2": ("Second conjugation", [185]),
    "conj3": ("Third conjugation", [186]),
    "conj3io": ("Third conjugation verbs in -iō", [188]),
    "conj4": ("Fourth conjugation", [187]),
    "deponent": ("Deponent verbs", [190, 191]),
    "periphrastic": ("Periphrastic conjugations", [193, 196]),
    "irregular": ("Irregular verbs", [197, 198, 200, 203, 204]),
    "prepositions": ("Prepositions", [220, 221]),
    "conjunctions": ("Conjunctions", [223, 324]),
    # agreement
    "apposition": ("Apposition", [282]),
    "pred_noun": ("Predicate noun or adjective", [283, 284]),
    "adj_agreement": ("Agreement of adjectives", [286, 287]),
    "adj_as_noun": ("Adjectives used as nouns", [288, 289]),
    "reflexive": ("Reflexive pronouns (sē, suus)", [299, 300]),
    "rel_agreement": ("Agreement of the relative", [305, 306]),
    "verb_agreement": ("Agreement of the verb with its subject", [316, 317]),
    # cases
    "nominative": ("Nominative: subject", [339]),
    "vocative": ("Vocative", [340]),
    "gen_general": ("Genitive with nouns", [341, 342]),
    "gen_possessive": ("Possessive genitive", [343]),
    "gen_quality": ("Genitive of quality", [345]),
    "gen_partitive": ("Partitive genitive", [346]),
    "gen_objective": ("Objective genitive", [347, 348]),
    "gen_adj": ("Genitive with adjectives", [349]),
    "gen_verbs": ("Genitive with verbs", [350, 352, 354, 356]),
    "dat_indirect": ("Dative of the indirect object", [361, 362]),
    "dat_special": ("Dative with special verbs", [367]),
    "dat_compound": ("Dative with compound verbs", [370]),
    "dat_possession": ("Dative of possession", [373]),
    "dat_agent": ("Dative of the agent", [374, 375]),
    "dat_reference": ("Dative of reference", [376, 377]),
    "dat_purpose": ("Dative of purpose (double dative)", [382]),
    "dat_adj": ("Dative with adjectives", [383]),
    "acc_object": ("Accusative: direct object", [387]),
    "acc_two": ("Two accusatives", [391, 393, 396]),
    "acc_special": ("Special uses of the accusative", [397]),
    "acc_extent": ("Accusative of extent and duration", [423, 425]),
    "abl_general": ("The ablative and its uses", [398, 399]),
    "abl_separation": ("Ablative of separation", [400, 401, 402]),
    "abl_source": ("Ablative of source and material", [403]),
    "abl_cause": ("Ablative of cause", [404]),
    "abl_agent": ("Ablative of agent", [405]),
    "abl_comparison": ("Ablative of comparison", [406, 407]),
    "abl_means": ("Ablative of means or instrument", [408, 409]),
    "abl_utor": ("Ablative with ūtor, fruor, fungor, potior, vēscor", [410]),
    "abl_manner": ("Ablative of manner", [412]),
    "abl_accompaniment": ("Ablative of accompaniment", [413]),
    "abl_degree": ("Ablative of degree of difference", [414]),
    "abl_quality": ("Ablative of quality", [415]),
    "abl_specification": ("Ablative of specification", [418]),
    "abl_absolute": ("Ablative absolute", [419, 420]),
    "time": ("Time when and how long", [423]),
    "place": ("Relations of place", [426, 427, 428, 429]),
    "locative": ("Locative", [427]),
    # the verb
    "subj_independent": ("Subjunctive in independent sentences", [438, 439, 441, 443, 445]),
    "imperative": ("Imperative; prohibitions", [448, 450]),
    "inf_subject": ("Infinitive as subject or predicate", [452]),
    "inf_complementary": ("Complementary infinitive", [456, 457]),
    "inf_acc": ("Infinitive with subject accusative", [459]),
    "inf_historical": ("Historical infinitive", [463]),
    "sequence": ("Sequence of tenses", [482, 483, 485]),
    "inf_tenses": ("Tenses of the infinitive", [486]),
    "participles": ("Participles", [488, 489, 490, 496]),
    "fut_participle": ("Future participle", [498]),
    "gerundive": ("Gerundive", [500]),
    "gerund": ("Gerund and gerundive constructions", [501, 502, 503, 504, 506, 507]),
    "supine": ("Supine", [508, 509, 510]),
    "conditions": ("Conditional sentences", [512, 514, 515, 516, 517]),
    "concessive": ("Concessive clauses", [527]),
    "purpose": ("Clauses of purpose", [529, 530, 531]),
    "characteristic": ("Relative clauses of characteristic", [534, 535]),
    "result": ("Clauses of result", [536, 537]),
    "causal": ("Causal clauses", [539, 540]),
    "temporal": ("Temporal clauses with postquam, ubi, ut", [541, 542]),
    "cum": ("Cum-clauses", [544, 545, 546, 549]),
    "antequam": ("Antequam and priusquam", [551]),
    "dum": ("Dum, dōnec, quoad", [552, 553, 554, 555, 556]),
    "quin": ("Clauses with quīn and quōminus", [557, 558]),
    "subst_purpose": ("Substantive clauses of purpose (ut, nē)", [563, 564, 565]),
    "subst_result": ("Substantive clauses of result", [567, 568, 569]),
    "quod_fact": ("Clauses with quod: the fact that", [572]),
    "ind_question": ("Indirect questions", [573, 574, 575]),
    "ind_discourse": ("Indirect discourse", [578, 579, 580, 581]),
    "ind_discourse_sub": ("Subordinate clauses in indirect discourse", [583, 585]),
    "attraction": ("Subjunctive by attraction; informal indirect discourse", [591, 592, 593]),
    "word_order": ("Order of words", [596, 597, 598]),
}

PREP_CASE = {
    "ab": "abl", "a": "abl", "abs": "abl", "de": "abl", "ex": "abl", "e": "abl", "cum": "abl", "sine": "abl",
    "pro": "abl", "prae": "abl", "coram": "abl", "tenus": "abl",
    "ad": "acc", "ante": "acc", "apud": "acc", "circum": "acc", "circa": "acc", "circiter": "acc", "cis": "acc",
    "citra": "acc", "contra": "acc", "erga": "acc", "extra": "acc", "infra": "acc", "inter": "acc",
    "intra": "acc", "iuxta": "acc", "ob": "acc", "per": "acc", "post": "acc", "praeter": "acc", "prope": "acc",
    "propter": "acc", "secundum": "acc", "supra": "acc", "trans": "acc", "ultra": "acc", "versus": "acc",
    "adversus": "acc", "penes": "acc", "pone": "acc",
    "in": "both", "sub": "both", "super": "both", "subter": "both",
}
PREP_MEANING = {
    "ab": "from, away from; by (agent)", "a": "from, away from; by (agent)", "de": "down from; about, concerning",
    "ex": "out of, from", "e": "out of, from", "cum": "with", "sine": "without", "pro": "in front of; for, on behalf of",
    "prae": "before; because of", "ad": "to, towards; near; for (purpose)", "ante": "before", "apud": "at, among, with",
    "circum": "around", "contra": "against, opposite", "inter": "between, among", "intra": "within",
    "ob": "on account of", "per": "through; by means of", "post": "after, behind", "praeter": "past; except",
    "prope": "near", "propter": "because of", "trans": "across", "ultra": "beyond", "in": "in, on (abl.); into, onto, against (acc.)",
    "sub": "under (abl.); up to, under (acc., motion)", "super": "over, above", "supra": "above", "infra": "below",
    "extra": "outside", "citra": "on this side of", "adversus": "against, facing", "secundum": "along; according to",
    "circiter": "about", "erga": "towards (of feelings)", "versus": "towards", "iuxta": "next to",
}
SPECIAL_DATIVE = {"credo", "faveo", "ignosco", "impero", "invideo", "noceo", "parco", "pareo", "persuadeo",
                  "placeo", "resisto", "servio", "studeo", "confido", "diffido", "licet", "minor", "nubo",
                  "obtempero", "obsto", "prosum", "desum", "praesum", "praeficio", "praesto", "occurro",
                  "appropinquo", "succurro", "subvenio", "indulgeo", "suadeo", "satisfacio", "medeor",
                  "irascor", "tempero", "consulo", "obsequor", "repugno", "displiceo", "mando", "permitto",
                  "nuntio", "respondeo", "polliceor", "do", "trado", "mitto", "dico", "ostendo", "reddo"}
DATIVE_VERBS_ONLY = {"credo", "faveo", "ignosco", "impero", "invideo", "noceo", "parco", "pareo", "persuadeo",
                     "placeo", "resisto", "servio", "studeo", "confido", "diffido", "obtempero", "obsto",
                     "prosum", "desum", "praesum", "occurro", "appropinquo", "succurro", "subvenio",
                     "indulgeo", "suadeo", "satisfacio", "medeor", "irascor", "obsequor", "repugno"}
UTOR = {"utor", "fruor", "fungor", "potior", "vescor", "abutor", "perfruor", "defungor"}
PURPOSE_DATIVES = {"auxilium", "praesidium", "subsidium", "usus", "impedimentum", "cura", "salus", "munus",
                   "donum", "odium", "detrimentum", "exemplum", "dedecus", "honor", "argumentum", "cor"}
TIME_NOUNS = {"dies", "nox", "annus", "hora", "tempus", "hiems", "aestas", "ver", "mensis", "vigilia", "lux",
              "vesper", "biduum", "triduum", "aetas", "saeculum", "initium", "adventus", "occasus", "ortus"}
EXTENT_NOUNS = {"passus", "pes", "mille", "milia", "dies", "annus", "hora", "mensis", "nox", "spatium",
                "biduum", "triduum", "iter"}
VERBS_OF_ASKING = {"impero", "rogo", "peto", "postulo", "persuadeo", "hortor", "cohortor", "moneo", "admoneo",
                   "oro", "obsecro", "mando", "permitto", "concedo", "praecipio", "edico", "quaero", "contendo",
                   "curo", "video", "caveo", "volo", "censeo", "decerno", "statuo", "constituo", "impetro",
                   "laboro", "nitor", "operam", "praescribo", "denuntio", "flagito", "precor", "suadeo"}
VERBS_OF_HAPPENING = {"accido", "fio", "efficio", "facio", "perficio", "contingo", "evenio", "restat", "sequor",
                      "accedo", "mos", "ius", "relinquo"}
VERBS_OF_FEARING = {"timeo", "vereor", "metuo", "pertimesco", "periculum"}
COMPLEMENTARY = {"possum", "volo", "nolo", "malo", "debeo", "soleo", "coepi", "incipio", "conor", "audeo",
                 "desino", "desisto", "statuo", "constituo", "cupio", "studeo", "paro", "dubito", "cogito",
                 "contendo", "maturo", "propero", "videor", "scio", "nescio", "consuesco", "pergo", "instituo",
                 "intermitto", "cesso", "nequeo", "queo", "disco", "cogo"}
SAYING = {"dico", "nego", "nuntio", "respondeo", "polliceor", "confirmo", "demonstro", "ostendo", "doceo",
          "certior", "scribo", "narro", "refero", "renuntio", "praedico", "memoro", "puto", "arbitror",
          "existimo", "credo", "censeo", "iudico", "spero", "confido", "scio", "intellego", "cognosco",
          "video", "audio", "sentio", "animadverto", "comperio", "reperio", "invenio", "memini", "nescio",
          "ignoro", "suspicor", "duco", "statuo", "simulo", "queror", "glorior", "clamo", "iubeo", "veto",
          "patior", "sino", "cogo", "prohibeo", "volo", "nolo", "malo", "cupio", "constat", "apparet",
          "oportet", "necesse", "fama", "spes", "opinio"}
PRAENOMINA = {"A": "Aulus", "Ap": "Appius", "App": "Appius", "C": "Gāius", "Cn": "Gnaeus", "D": "Decimus",
              "K": "Kaesō", "L": "Lūcius", "M": "Mārcus", "Mam": "Māmercus", "N": "Numerius", "P": "Pūblius",
              "Q": "Quīntus", "Ser": "Servius", "Sex": "Sextus", "Sp": "Spurius", "T": "Titus", "Ti": "Tiberius",
              "Tib": "Tiberius"}


def lemma_key(token) -> str:
    return norm_form("la", token.lemma).replace("v", "u").lstrip("-")


def lk(word: str) -> str:
    return norm_form("la", word).replace("v", "u")


def roman_value(text: str) -> int | None:
    values = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
    s = text.upper()
    if not s or any(ch not in values for ch in s):
        return None
    total = 0
    for i, ch in enumerate(s):
        v = values[ch]
        total += -v if i + 1 < len(s) and values[s[i + 1]] > v else v
    return total


def is_deponent(entry) -> bool:
    return bool(entry) and "deponent" in entry.get("h", "")


# --------------------------------------------------------------------------- #
# Which model paradigm?
# --------------------------------------------------------------------------- #
def _class(entry, prefix: str) -> str | None:
    for t in (entry or {}).get("t", []):
        if t.startswith(prefix):
            return t[len(prefix):]
    return None


def _gen_plural_ium(entry) -> bool:
    for form, tags in (entry or {}).get("f", []):
        if "genitive" in tags and "plural" in tags:
            return norm_form("la", form).endswith("ium")
    return False


def noun_model(token, entry) -> str | None:
    lemma = norm_form("la", (entry or {}).get("w") or token.lemma)
    decl = _class(entry, "declension-")
    gender = token.cats.get("gender") or next((g for g in ("masculine", "feminine", "neuter")
                                               if g in (entry or {}).get("t", [])), None)
    if decl is None:                                    # guess from the dictionary form
        if lemma.endswith("a") or lemma.endswith("ae"):
            decl = "1"
        elif lemma.endswith(("um", "er", "ir", "i")):
            decl = "2"
        elif lemma.endswith("us"):
            decl = "4" if token.key.endswith(("ui", "uum")) else "2"
        elif lemma.endswith("es") and token.key.endswith(("ei", "erum", "ebus")):
            decl = "5"
        else:
            decl = "3"
    if decl == "1":
        return "hora"
    if decl == "2":
        if lemma.endswith(("um", "a")) or gender == "neuter":
            return "verbum"
        return "liber" if lemma.endswith(("er", "ir")) else "servus"
    if decl == "4":
        return "cornu" if lemma.endswith("u") or gender == "neuter" else "casus"
    if decl == "5":
        return "dies" if lemma.endswith("ies") else "res"
    if decl == "3":
        istem = _gen_plural_ium(entry)
        if gender == "neuter":
            return "mare" if lemma.endswith(("e", "al", "ar")) and istem else "nomen"
        if istem:
            if lemma.endswith(("is", "es")):
                return "navis"
            return "mons" if lemma.endswith(("ns", "rs")) else "urbs"
        if lemma.endswith(("o", "io")):
            return "leo"
        if lemma.endswith(("l", "r", "n")) and not lemma.endswith("er"):
            return "sol"
        if lemma.endswith(("or", "er")):
            return "sol"
        return "vox"
    return None


def adjective_model(token, entry) -> tuple[str, str] | None:
    """(table, key) for adjectives, participles and adjectival pronouns."""
    lemma = lk((entry or {}).get("w") or token.lemma)
    surface_lemma = lemma_key(token)
    cats = token.cats
    if token.upos in ("PRON", "DET"):
        for key, names in (("is", {"is", "idem"}), ("hic", {"hic"}), ("ille", {"ille"}),
                           ("qui", {"qui", "quis", "quidam", "quisque", "quisquam", "aliquis", "quicumque",
                                    "quisquis", "aliqui", "quiuis", "quilibet"})):
            if surface_lemma in names or lemma in names:
                return "pron", key
        if surface_lemma in ("ego", "tu", "nos", "uos", "sui", "se"):
            return "personal", surface_lemma
    if lemma in tb.PRONOMINAL_ADJECTIVES or surface_lemma in tb.PRONOMINAL_ADJECTIVES:
        return "adj", "nullus"
    if cats.get("verbform") in ("participle", "gerundive"):
        return ("adj", "ingens") if cats.get("tense") == "present" and cats.get("verbform") == "participle" \
            else ("adj", "magnus")
    if cats.get("degree") == "comparative" or lemma.endswith(("ior", "ius")) and _class(entry, "declension-") == "3":
        return "adj", "melior"
    decl = _class(entry, "declension-")
    tags = (entry or {}).get("t", [])
    if decl == "3" or (decl is None and lemma.endswith(("is", "ns", "x", "e"))):
        if "one-termination" in tags or lemma.endswith(("ns", "x", "ps", "rs")):
            return "adj", "ingens"
        return "adj", "gravis"
    if decl in ("1", "2") or lemma.endswith(("us", "er", "a", "um")):
        return "adj", "magnus"
    return None


def verb_model(token, entry) -> tuple[str, str] | None:
    """(model verb, note) from the conjugation of the dictionary entry."""
    lemma = lk((entry or {}).get("w") or token.lemma)
    head = (entry or {}).get("h", "")
    if lemma == "sum" or (lemma.endswith("sum") and lemma != "possum"):
        return "esse", "" if lemma == "sum" else "a compound of esse"
    conj = _class(entry, "conjugation-")
    if "irregular" in head and conj is None or lemma in ("possum", "uolo", "nolo", "malo", "eo", "fero", "fio",
                                                          "inquam", "aio", "do", "edo", "memini", "odi", "coepi"):
        if lemma not in ("do",):
            return None
    if conj is None:
        if lemma.endswith(("eo", "eor")):
            conj = "2"
        elif lemma.endswith(("io", "ior")):
            conj = "4"
        elif "first conjugation" in head:
            conj = "1"
        else:
            conj = "3"
    model = {"1": "amare", "2": "monere", "3": "legere", "4": "audire"}.get(conj)
    note = ""
    if conj == "3" and ("iō-variant" in head or "io-variant" in head or lemma.endswith(("io", "ior"))):
        note = ("a third-conjugation verb in -iō (like capiō): it follows legere, but keeps -i- before "
                "a, o, u and e, as audīre does (capiunt, capiēbat, capiam, capiēns)")
    return (model, note) if model else None


# --------------------------------------------------------------------------- #
# Rendering the model tables
# --------------------------------------------------------------------------- #
def fmt(form: str) -> str:
    """serv|us -> serv<bar>us with the ending emphasised."""
    out = []
    for word in form.split(" "):
        for alt_i, alt in enumerate(word.split("/")):
            if alt_i:
                out.append("/")
            if "|" in alt:
                stem, *rest = alt.split("|")
                out.append(escape(stem) + '<span class="sep">|</span><span class="end">' +
                           '<span class="sep">|</span>'.join(escape(r) for r in rest) + "</span>")
            else:
                out.append(escape(alt))
        out.append(" ")
    return "".join(out).strip()


def _ending(form: str) -> str:
    return form.split("|", 1)[1].replace("|", "") if "|" in form else ""


def noun_table(key: str, cats: dict | None = None, title: bool = True) -> str:
    group, name, forms = tb.NOUNS[key]
    rows = []
    for case in tb.CASES:
        tds = []
        for number in ("singular", "plural"):
            hit = cats and cats.get("case") == case and cats.get("number") == number
            tds.append(f'<td class="{"hit" if hit else ""}">{fmt(forms[(number, case)])}</td>')
        rows.append(f"<tr><th><i>{tb.CASE_LABELS[case]}</i></th>{''.join(tds)}</tr>")
    cap = f"<h3>{escape(group)}: <i>{escape(name)}</i></h3>" if title else ""
    return (f'{cap}<table class="grid" cellspacing="0"><tr><th></th><th><i>sing</i></th><th><i>plūr</i></th></tr>'
            f'{"".join(rows)}</table>')


def gender_table(group: str, name: str, forms: dict, cats: dict | None = None) -> str:
    genders = ["masculine", "feminine", "neuter"]
    rows = []
    for number, label in (("singular", "sing"), ("plural", "plūr")):
        for i, case in enumerate(tb.CASES):
            tds = []
            for g_i, g in enumerate(genders):
                hit = cats and cats.get("case") == case and cats.get("number") == number and \
                    cats.get("gender", g) == g
                tds.append(f'<td class="{"hit" if hit else ""}">{fmt(forms[(number, case)][g_i])}</td>')
            lead = f'<th rowspan="5"><i>{label}</i></th>' if i == 0 else ""
            rows.append(f"<tr>{lead}<th><i>{tb.CASE_LABELS[case]}</i></th>{''.join(tds)}</tr>")
    return (f"<h3>{escape(group)}: <i>{escape(name)}</i></h3>"
            f'<table class="grid" cellspacing="0"><tr><th></th><th></th><th><i>m</i></th><th><i>f</i></th>'
            f'<th><i>n</i></th></tr>{"".join(rows)}</table>')


def personal_table(cats: dict | None = None, lemma: str = "") -> str:
    col = {"ego": 0, "tu": 1, "sui": 2, "se": 2, "nos": 3, "uos": 4}.get(lemma, -1)
    if cats and cats.get("number") == "plural" and col in (0, 1):
        col += 3
    rows = []
    for case, forms in tb.PERSONAL["rows"]:
        tds = [f'<td class="{"hit" if cats and cats.get("case") == case and i == col else ""}">{escape(f)}</td>'
               for i, f in enumerate(forms)]
        rows.append(f"<tr><th><i>{tb.CASE_LABELS[case]}</i></th>{''.join(tds)}</tr>")
    return ('<h3>Prōnōmina persōnālia</h3><table class="grid" cellspacing="0">' + "".join(rows) + "</table>"
            '<p class="muted small">The genitives (meī, tuī, suī, nostrī/nostrum, vestrī/vestrum) are not '
            'shown; possession is expressed by meus, tuus, suus, noster, vester.</p>')


def verb_table(voice: str, mood: str, tense: str, model: str | None = None, person_row: int | None = None) -> str:
    table = tb.T.get((voice, mood, tense))
    if not table:
        return ""
    verbs = [v for v in tb.VERBS if v in table]
    head = "".join(f'<th>{escape(tb.VERB_TITLES[v])}</th>' for v in verbs)
    rows = []
    for i, (number, person) in enumerate(tb.PERSONS):
        label = f'<i>{"sing" if number == "singular" else "plūr"}</i> {i % 3 + 1}'
        tds = []
        for v in verbs:
            cls = "hit" if (v == model and i == person_row) else "model" if v == model else ""
            tds.append(f'<td class="{cls}">{fmt(table[v][i])}</td>')
        rows.append(f"<tr><th>{label}</th>{''.join(tds)}</tr>")
    title = f"{tb.VOICE_LABELS[voice]} · {tb.MOOD_LABELS[mood]} <i>{tb.TENSE_LABELS[tense]}</i>"
    return (f"<h3>{title}</h3><table class=\"grid\" cellspacing=\"0\"><tr><th></th>{head}</tr>"
            f'{"".join(rows)}</table>')


def nonfinite_table(keys: list[tuple], model: str | None = None, hit: tuple | None = None) -> str:
    head = "".join(f"<th>{escape(tb.VERB_TITLES[v])}</th>" for v in tb.VERBS)
    rows = []
    for key in keys:
        forms = tb.NONFINITE[key]
        tds = []
        for v, form in zip(tb.VERBS, forms):
            cls = "hit" if (v == model and key == hit) else "model" if v == model else ""
            tds.append(f'<td class="{cls}">{fmt(form)}</td>')
        rows.append(f"<tr><th><i>{escape(tb.NONFINITE_LABELS[key])}</i></th>{''.join(tds)}</tr>")
    return f'<table class="grid" cellspacing="0"><tr><th></th>{head}</tr>{"".join(rows)}</table>'


def model_paradigm(token, entry, verb=None) -> str:
    """HTML of the model paradigm that this word follows ("" if none).

    *verb* is the verb's own dictionary entry when *entry* is that of a participle.
    """
    cats = token.cats
    upos = token.upos
    verbform = cats.get("verbform")
    if upos in ("VERB", "AUX"):
        got = verb_model(token, verb or entry)
        if verbform == "finite" or (verbform is None and cats.get("mood")):
            if not got:
                return ('<p class="muted">This verb is irregular; the model paradigms cover only amāre, monēre, legere, '
                        'audīre and esse. See its own forms below and the grammar tab.</p>')
            model, note = got
            voice, mood, tense = cats.get("voice", "active"), cats.get("mood", "indicative"), cats.get("tense")
            if model == "esse":
                voice = "active"
            person_row = None
            for i, (number, person) in enumerate(tb.PERSONS):
                if cats.get("number") == number and cats.get("person") == person:
                    person_row = i
            html = ""
            if mood == "imperative":
                key = ("active", "imperative", cats.get("number", "singular"))
                html = "<h3>Imperātīvus</h3>" + nonfinite_table(
                    [("active", "imperative", "singular"), ("active", "imperative", "plural")], model, key)
            else:
                html = verb_table(voice, mood, tense or "present", model, person_row)
            if note:
                html += f'<p class="small">Note: this is {note}.</p>'
            return html
        if verbform == "infinitive":
            model = got[0] if got else None
            voice, tense = cats.get("voice", "active"), cats.get("tense", "present")
            keys = [(v, "infinitive", t) for v in ("active", "passive") for t in ("present", "perfect", "future")]
            return "<h3>Īnfīnītīvus</h3>" + nonfinite_table(keys, model, (voice, "infinitive", tense))
        if verbform == "supine":
            model = got[0] if got else None
            return "<h3>Supīna</h3>" + nonfinite_table([("active", "supine", "")], model, ("active", "supine", ""))
        if verbform in ("participle", "gerundive"):
            model = got[0] if got else None
            if verbform == "gerundive":
                key = ("passive", "gerundive", "")
            else:
                tense = cats.get("tense", "perfect")
                key = ("passive", "participle", "perfect") if tense == "perfect" else ("active", "participle", tense)
            keys = [("active", "participle", "present"), ("active", "participle", "future"),
                    ("passive", "participle", "perfect"), ("passive", "gerundive", "")]
            html = "<h3>Participia</h3>" + nonfinite_table(keys, model, key)
            adj = adjective_model(token, entry)
            if adj and "case" in cats:
                group, name, forms = tb.ADJECTIVES[adj[1]]
                html += ('<p class="small">A participle is declined like an adjective, here like '
                         f"<i>{escape(name)}</i>:</p>") + gender_table(group, name, forms, cats)
            return html
    if upos in ("NOUN", "PROPN") and "case" in cats:
        key = noun_model(token, entry)
        if key:
            return noun_table(key, cats)
    if upos in ("ADJ", "DET", "PRON", "NUM") and "case" in cats:
        got = adjective_model(token, entry)
        if got:
            kind, key = got
            if kind == "personal":
                return personal_table(cats, key)
            group, name, forms = (tb.PRONOUNS if kind == "pron" else tb.ADJECTIVES)[key]
            return gender_table(group, name, forms, cats)
    return ""


def morphology_topics(token, entry, verb=None) -> list[str]:
    """A&G topics on the form of the word (declension, conjugation ...)."""
    cats, upos = token.cats, token.upos
    out = []
    if upos in ("VERB", "AUX") and verb is not None:
        entry = verb                                  # the verb behind a participle
    if upos in ("NOUN", "PROPN"):
        key = noun_model(token, entry)
        out.append({"hora": "decl1", "servus": "decl2", "liber": "decl2", "verbum": "decl2", "sol": "decl3",
                    "leo": "decl3", "vox": "decl3", "nomen": "decl3", "navis": "decl3i", "urbs": "decl3i",
                    "mons": "decl3i", "mare": "decl3i", "casus": "decl4", "cornu": "decl4", "dies": "decl5",
                    "res": "decl5"}.get(key, "cases"))
    elif upos in ("VERB", "AUX"):
        got = verb_model(token, entry)
        if got:
            model, note = got
            out.append({"amare": "conj1", "monere": "conj2", "legere": "conj3", "audire": "conj4",
                        "esse": "esse"}[model])
            if note and model == "legere":
                out.append("conj3io")
        else:
            out.append("irregular")
        if is_deponent(entry):
            out.append("deponent")
    elif upos in ("ADJ", "NUM", "DET", "PRON"):
        got = adjective_model(token, entry)
        feats = token.feats
        if feats.get("PronType") == "Rel":
            out.append("rel_pron")
        elif feats.get("PronType") == "Dem":
            out.append("dem_pron")
        elif feats.get("PronType") in ("Int", "Ind"):
            out.append("int_pron")
        elif feats.get("Poss") == "Yes":
            out.append("poss_pron")
        elif feats.get("PronType") == "Prs":
            out.append("pers_pron")
        elif upos == "NUM":
            out.append("numerals")
        elif got:
            out.append({"magnus": "adj12", "nullus": "adj_ius", "gravis": "adj3", "ingens": "adj3",
                        "melior": "comparison"}.get(got[1], "adj12"))
        if cats.get("degree") in ("comparative", "superlative") and "comparison" not in out:
            out.append("comparison")
    elif upos == "ADP":
        out.append("prepositions")
    elif upos in ("CCONJ", "SCONJ"):
        out.append("conjunctions")
    return out


# --------------------------------------------------------------------------- #
# Constructions
# --------------------------------------------------------------------------- #
NOMINAL = {"NOUN", "PROPN", "PRON", "ADJ", "DET", "NUM"}
PARTITIVE_HEADS = {"pars", "nihil", "nihilum", "quis", "quid", "aliquis", "aliquid", "satis", "multum", "plus",
                   "minus", "tantum", "quantum", "mille", "milia", "nemo", "quisque", "uter", "uterque", "plerique",
                   "multi", "pauci", "nonnulli", "reliquus", "unus", "alter", "neuter", "quisquam", "quidam",
                   "numerus", "multitudo", "copia", "uis", "magnitudo", "genus", "aliquantum", "parum", "nimis",
                   "amplius", "ullus", "nullus", "complures", "medius", "summus", "pars"}
SEPARATION_VERBS = {"libero", "priuo", "careo", "egeo", "prohibeo", "abstineo", "desisto", "excedo", "cedo",
                    "pello", "expello", "intercludo", "spolio", "nudo", "uaco", "leuo", "soluo", "arceo",
                    "exuo", "decedo", "moueo", "deicio", "depello", "eicio", "exeo", "egredior", "interdico"}
DEGREE_WORDS = {"multus", "multo", "paulo", "paulum", "nihil", "nihilo", "eo", "quo", "tanto", "quanto",
                "aliquanto", "is", "qui", "tantus", "quantus", "dimidium"}
RESULT_SIGNS = {"tam", "ita", "sic", "adeo", "tantus", "talis", "tot", "eiusmodi", "tantopere", "usque"}
INTERROGATIVES = {"cur", "quare", "quomodo", "quemadmodum", "ubi", "unde", "quo", "quando", "quantus", "qualis",
                  "quot", "uter", "quis", "quid", "num", "utrum", "an", "quam", "qui", "quotiens", "necne", "ne"}
SCONJ_NOTES = {
    "ut": ("<i>ut</i> with the subjunctive: purpose (“in order that”), result (“so that”) or an object clause "
           "(“that”); with the indicative it means “as” or “when”.", ["purpose", "result", "subst_purpose"]),
    "uti": ("<i>utī</i> = <i>ut</i>.", ["purpose", "result", "subst_purpose"]),
    "ne": ("<i>nē</i> with the subjunctive: negative purpose (“in order that … not”, “lest”), a negative command, "
           "or — after verbs of fearing — “that”.", ["purpose", "subst_purpose"]),
    "cum": ("<i>cum</i> as a conjunction: with the indicative it dates an action (“when”); with the imperfect or "
            "pluperfect subjunctive it gives the circumstances (“when, as”), the cause (“since”) or a concession "
            "(“although”).", ["cum"]),
    "si": ("<i>sī</i> “if” opens the condition (protasis) of a conditional sentence.", ["conditions"]),
    "nisi": ("<i>nisi</i> “if not, unless”.", ["conditions"]),
    "quod": ("<i>quod</i> “because”; also “the fact that”. With the subjunctive the reason is quoted as "
             "someone else's.", ["causal", "quod_fact"]),
    "quia": ("<i>quia</i> “because”.", ["causal"]),
    "quoniam": ("<i>quoniam</i> “since, seeing that”.", ["causal"]),
    "dum": ("<i>dum</i> “while” (present indicative), “until” or “provided that” (subjunctive).", ["dum"]),
    "donec": ("<i>dōnec</i> “until, as long as”.", ["dum"]),
    "postquam": ("<i>postquam</i> “after”, normally with the perfect indicative.", ["temporal"]),
    "posteaquam": ("<i>posteāquam</i> “after”.", ["temporal"]),
    "ubi": ("<i>ubi</i> “when; where”.", ["temporal"]),
    "priusquam": ("<i>priusquam</i> “before”.", ["antequam"]),
    "antequam": ("<i>antequam</i> “before”.", ["antequam"]),
    "quin": ("<i>quīn</i> “but that, that … not”, after negatived verbs of doubting and hindering.", ["quin"]),
    "quominus": ("<i>quōminus</i> “so that … not”, after verbs of hindering.", ["quin"]),
    "etsi": ("<i>etsī</i> “although, even if”.", ["concessive"]),
    "tametsi": ("<i>tametsī</i> “although”.", ["concessive"]),
    "quamquam": ("<i>quamquam</i> “although” (indicative).", ["concessive"]),
    "quamuis": ("<i>quamvīs</i> “however much, although” (subjunctive).", ["concessive"]),
    "quasi": ("<i>quasi</i> “as if”.", ["conditions"]),
    "simul": ("<i>simul (atque)</i> “as soon as”.", ["temporal"]),
}


def link(token) -> str:
    """HTML link that selects another word of the sentence."""
    if token is None:
        return "the clause"
    return f'<a href="tok:{token.index}"><i>{escape(token.text)}</i></a>'


def phrase_base(token):
    """Follow agreement and coordination up to the word whose function decides the case."""
    seen = 0
    t = token
    while t.head_token is not None and seen < 6:
        rel = t.deprel
        h = t.head_token
        same_case = h.cats.get("case") == t.cats.get("case")
        if rel in ("conj", "appos", "flat", "flat:name") and same_case:
            t = h
        elif rel in ("amod", "det", "nummod") and h.upos in NOMINAL and same_case:
            t = h
        else:
            break
        seen += 1
    return t


def _is_gerundive_agreeing(token) -> bool:
    cats = token.cats
    h = token.head_token
    if token.deprel in ("amod", "acl", "det") and h is not None and h.upos in NOMINAL \
            and h.cats.get("case") == cats.get("case"):
        return True
    for c in token.children:
        if c.upos in NOMINAL and c.deprel.split(":")[0] in ("nsubj", "obj") \
                and c.cats.get("case") == cats.get("case") and c.cats.get("number") == cats.get("number"):
            return True
        if c.deprel.split(":")[0] in ("aux", "cop"):
            return True
    return cats.get("case") == "nominative" or cats.get("gender") == "feminine" or cats.get("number") == "plural"


MOTION_VERBS = {"uenio", "proficiscor", "discedo", "egredior", "exeo", "redeo", "reuertor", "fugio", "mitto",
                "peruenio", "contendo", "eo", "abeo", "decedo", "excedo", "moueo", "proficisco", "transeo",
                "duco", "educo", "reduco", "refero", "recipio", "pello", "expello"}


def _loose_absolute(b):
    """An ablative-absolute predicate next to *b* that the parser left without a subject."""
    if b.deprel.split(":")[0] not in ("obl", "nmod") or b.child("case") is not None:
        return None
    for t in b.sentence.tokens:
        if t.deprel == "advcl:abs" and t.cats.get("case") == "ablative" and t is not b \
                and abs(t.index - b.index) <= 9 and t.child("nsubj") is None \
                and (t.head == b.head or b.head_token is t) and (
                    t.cats.get("number") == b.cats.get("number") or lemma_key(t) == "consul"):
            return t
    return None


def case_notes(token, add):
    """Explain why the phrase stands in its case."""
    b = phrase_base(token)
    cats = b.cats
    case = cats.get("case")
    if not case:
        return
    h = b.head_token
    rel = b.deprel
    base_rel = rel.split(":")[0]
    hl = lemma_key(h) if h is not None else ""
    bl = lemma_key(b)
    who = "" if b is token else f"The phrase round {link(b)}: "
    prep = b.child("case", upos="ADP")
    # ---- ablative absolute -------------------------------------------------
    if case == "ablative":
        if rel == "advcl:abs":
            subj = b.child("nsubj", "obj")
            if subj is not None:
                add(f"{who}{link(b)} and {link(subj)} form an <b>ablative absolute</b>: a noun and a participle "
                    f"(or two nouns) in the ablative, loosely attached to the sentence, giving the time, cause or "
                    f"circumstances — “with … having been …”, “when/since/although …”.", "abl_absolute")
            else:
                add(f"{who}{link(b)} is the predicate of an <b>ablative absolute</b> (its subject is understood "
                    f"or expressed by a clause).", "abl_absolute")
            return
        if h is not None and h.deprel == "advcl:abs" and base_rel in ("nsubj", "obj") \
                and h.cats.get("case") == "ablative":
            add(f"{who}{link(b)} is the subject of the <b>ablative absolute</b> {link(b)} … {link(h)}: noun and "
                f"participle stand in the ablative and together work like a clause (“when/after/since …”).",
                "abl_absolute")
            return
    # ---- with a preposition --------------------------------------------------
    if prep is not None:
        pl = lemma_key(prep)
        pl = {"a": "ab", "abs": "ab", "e": "ex"}.get(pl, pl)
        meaning = PREP_MEANING.get(pl, "")
        text = (f"{who}governed by the preposition {link(prep)}"
                + (f" (“{meaning}”)" if meaning else "") + f", which here takes the <b>{case}</b>.")
        topics = ["prepositions"]
        passive_head = h is not None and (h.cats.get("voice") == "passive")
        gerund_near = b.cats.get("verbform") == "gerundive" or any(
            c.cats.get("verbform") == "gerundive" for c in b.children)
        if pl == "ab" and passive_head:
            text += (" With a passive verb, <i>ā/ab</i> + ablative of a person names the <b>agent</b> — the one "
                     "by whom the action is done.")
            topics = ["abl_agent", "abl_separation"]
        elif pl in ("ab", "ex", "de") and case == "ablative":
            text += " It expresses the place or source <b>from which</b> (separation, origin)."
            topics += ["place", "abl_separation"]
        elif pl == "cum":
            text += " <b>Accompaniment</b> (“together with”) or manner."
            topics = ["abl_accompaniment", "abl_manner"]
        elif pl in ("in", "sub", "super"):
            if case == "accusative":
                text += (" With the accusative <i>in</i>/<i>sub</i> express motion <b>into / towards</b> "
                         "(also “against”).")
            else:
                text += " With the ablative <i>in</i>/<i>sub</i> express rest: the place <b>where</b>."
            topics += ["place"]
        elif pl == "ad" and gerund_near:
            text += " <i>ad</i> with a gerund or gerundive expresses <b>purpose</b> (“in order to”)."
            topics = ["gerund", "prepositions"]
        elif pl == "ad":
            text += " The place or person <b>to which</b> the motion goes; also “near” and “for (a purpose)”."
            topics += ["place"]
        elif pl in ("causa", "gratia"):
            topics = ["gerund", "gen_possessive"]
        add(text, *topics)
        return
    # ---- no preposition --------------------------------------------------------
    if case == "nominative":
        if base_rel == "nsubj":
            if h is not None and h.cats.get("verbform") == "infinitive":
                add(f"{who}<b>subject</b> of the infinitive {link(h)}, which is used as a narrative tense "
                    f"(historical infinitive).", "inf_historical")
            else:
                passive = rel == "nsubj:pass" or (h is not None and h.cats.get("voice") == "passive")
                add(f"{who}<b>subject</b> of {link(h)}"
                    + (": the verb is passive, so the subject undergoes the action." if passive else
                       ": the verb agrees with it in person and number."), "nominative", "verb_agreement")
        elif b.child("cop") is not None or base_rel in ("xcomp", "root") and b.upos != "VERB":
            add(f"{who}<b>predicate nominative</b>: it says what the subject is, is called or becomes, and so "
                f"stands in the same case as the subject.", "pred_noun")
        elif rel == "advcl:pred" or base_rel == "acl":
            add(f"{who}in agreement with the subject it describes.", "adj_agreement")
        else:
            add(f"{who}nominative: the case of the subject and of whatever is predicated of it.", "nominative")
    elif case == "vocative":
        add(f"{who}<b>vocative</b>: the person addressed.", "vocative")
    elif case == "locative":
        add(f"{who}<b>locative</b>: the place where, used with names of towns and a few nouns "
            f"(<i>domī</i> “at home”, <i>Rōmae</i> “at Rome”).", "locative", "place")
    elif case == "accusative":
        if base_rel == "nsubj" and h is not None and h.cats.get("verbform") in ("infinitive", "participle",
                                                                                "gerundive"):
            gov = h.head_token
            extra = f" The whole clause depends on {link(gov)}." if gov is not None and h.deprel in (
                "ccomp", "xcomp", "csubj", "csubj:pass", "conj") else ""
            add(f"{who}<b>subject of the infinitive</b> {link(h)}: in the <b>accusative and infinitive</b> "
                f"construction the subject of a reported statement stands in the accusative.{extra}",
                "inf_acc", "ind_discourse")
        elif base_rel == "obj":
            other = [c for c in (h.children if h is not None else []) if c is not b and c.cats.get("case") ==
                     "accusative" and c.deprel.split(":")[0] in ("obj", "xcomp") and c.upos in NOMINAL]
            if other:
                add(f"{who}<b>direct object</b> of {link(h)}, which here takes <b>two accusatives</b> "
                    f"(the other is {link(other[0])}).", "acc_object", "acc_two")
            else:
                add(f"{who}<b>direct object</b> of {link(h)}: the person or thing the action is done to.",
                    "acc_object")
        elif base_rel == "xcomp":
            add(f"{who}<b>predicate accusative</b>: it describes the object of {link(h)} (verbs of naming, making, "
                f"considering take two accusatives).", "acc_two", "pred_noun")
        elif bl in EXTENT_NOUNS or b.child("nummod") is not None:
            add(f"{who}accusative of <b>extent</b>: how far (space) or how long (time).", "acc_extent")
        elif bl in ("domus", "rus") or b.upos == "PROPN":
            add(f"{who}accusative of the <b>place to which</b>: names of towns and <i>domum</i>, <i>rūs</i> "
                f"take no preposition.", "place")
        else:
            add(f"{who}accusative without a preposition: besides the direct object it can express extent of "
                f"space or time, or be used adverbially.", "acc_object", "acc_special", "acc_extent")
    elif case == "genitive":
        if h is not None and hl in ("causa", "gratia") and h.cats.get("case") == "ablative":
            add(f"{who}genitive with {link(h)} “for the sake of”, which follows its genitive.", "gen_possessive",
                "gerund")
        elif h is not None and h.upos in NOMINAL:
            partitive = (h.upos == "NUM" or hl in PARTITIVE_HEADS or h.cats.get("degree") == "superlative"
                         or h.feats.get("PronType") in ("Ind", "Int", "Neg", "Tot"))
            if partitive:
                add(f"{who}<b>partitive genitive</b> with {link(h)}: the whole of which a part is taken "
                    f"(“of, among”).", "gen_partitive")
            elif h.upos == "ADJ":
                add(f"{who}genitive depending on the adjective {link(h)} (adjectives of desire, knowledge, "
                    f"memory, fullness, power … take an objective genitive).", "gen_adj")
            elif b.child("nummod") is not None or (b.child("amod") is not None and bl in (
                    "pes", "passus", "dies", "annus", "genus", "modus", "magnitudo", "uirtus", "animus")):
                add(f"{who}<b>genitive of quality or measure</b> describing {link(h)} (always with an "
                    f"adjective or numeral).", "gen_quality", "gen_possessive")
            else:
                add(f"{who}genitive depending on the noun {link(h)}: possession or belonging (“of”); with nouns of "
                    f"action or feeling it may be the object of that action (objective genitive).",
                    "gen_possessive", "gen_objective", "gen_general")
        elif h is not None and h.upos in ("VERB", "AUX"):
            if hl == "sum" or h.child("cop") is not None:
                add(f"{who}<b>predicate genitive</b> with {link(h)}: “belongs to, is the mark/duty of”; or a "
                    f"genitive of quality/value.", "gen_possessive", "gen_quality")
            else:
                add(f"{who}genitive with the verb {link(h)} (verbs of remembering and forgetting, accusing, "
                    f"feeling, filling and <i>potior</i> take a genitive).", "gen_verbs")
        else:
            add(f"{who}genitive: “of”.", "gen_general")
    elif case == "dative":
        gerundive_head = h is not None and h.cats.get("verbform") == "gerundive"
        if gerundive_head:
            add(f"{who}<b>dative of the agent</b> with the gerundive {link(h)}: the person who has to do it.",
                "dat_agent", "gerundive")
        elif bl in PURPOSE_DATIVES and h is not None and (hl == "sum" or h.child("cop") is not None
                                                          or h.upos in ("VERB", "AUX")):
            add(f"{who}<b>dative of purpose</b> (“to serve as, for a …”), often together with a dative of the "
                f"person concerned — the double dative.", "dat_purpose")
        elif h is not None and hl in DATIVE_VERBS_ONLY:
            add(f"{who}object of {link(h)}: this verb takes its object in the <b>dative</b> (verbs meaning favour, "
                f"help, trust, obey, resist, persuade, command, spare, harm …).", "dat_special")
        elif h is not None and hl == "sum" and h.upos in ("VERB", "AUX") and h.child("nsubj") is not None \
                and h.child("cop") is None:
            add(f"{who}<b>dative of possession</b> with {link(h)}: <i>est mihi</i> = “I have”.", "dat_possession",
                "dat_reference")
        elif h is not None and h.upos == "ADJ":
            add(f"{who}dative with the adjective {link(h)} (near, like, friendly, suitable, pleasing … to).",
                "dat_adj")
        elif h is not None and h.upos in ("VERB", "AUX"):
            compound = hl.startswith(("ad", "ante", "con", "com", "in", "inter", "ob", "oc", "post", "prae",
                                      "pro", "sub", "suc", "super"))
            add(f"{who}<b>indirect object</b> of {link(h)}: the person to or for whom something is done, given, "
                f"said." + (" Many verbs compounded with a preposition take a dative." if compound else ""),
                "dat_indirect", *(["dat_compound"] if compound else []), "dat_reference")
        else:
            add(f"{who}dative: the person or thing concerned (“to, for”).", "dat_reference", "dat_indirect")
    elif case == "ablative":
        comparative_near = h is not None and (h.cats.get("degree") == "comparative" or any(
            c.cats.get("degree") == "comparative" for c in h.children))
        if h is not None and hl in UTOR:
            add(f"{who}object of {link(h)}: the deponents <i>ūtor, fruor, fungor, potior, vēscor</i> take the "
                f"<b>ablative</b>.", "abl_utor")
        elif h is not None and h.cats.get("degree") == "comparative" and bl not in DEGREE_WORDS \
                and b.child("nummod") is None:
            add(f"{who}<b>ablative of comparison</b> with the comparative {link(h)}: “than …”.", "abl_comparison")
        elif comparative_near and (bl in DEGREE_WORDS or b.child("nummod") is not None):
            add(f"{who}<b>ablative of degree of difference</b>: by how much (<i>multō</i> “by much”, "
                f"<i>paulō</i> “a little”).", "abl_degree")
        elif bl in TIME_NOUNS:
            add(f"{who}<b>ablative of time</b>: when, or within which time, something happens.", "time")
        elif h is not None and hl in SEPARATION_VERBS:
            add(f"{who}<b>ablative of separation</b> with {link(h)}: that from which something is kept, freed "
                f"or removed.", "abl_separation")
        elif h is not None and h.upos in ("NOUN", "PROPN") and (b.child("amod") is not None
                                                                or b.child("det") is not None):
            add(f"{who}<b>ablative of quality</b> (description) with {link(h)} — always with an adjective.",
                "abl_quality")
        elif _loose_absolute(b) is not None:
            partner = _loose_absolute(b)
            date = " — the Roman way of dating a year: “in the consulship of …”" if lemma_key(partner) == \
                "consul" else ""
            add(f"{who}probably the subject of an <b>ablative absolute</b> with {link(partner)}{date}: noun and "
                f"predicate both stand in the ablative and together work like a clause.", "abl_absolute")
        elif b.upos == "PROPN" and h is not None and hl in MOTION_VERBS and len(b.text) > 3:
            add(f"{who}ablative of a place name: the place <b>from which</b> (or, in the plural and third "
                f"declension, <b>where</b>) without a preposition.", "place", "abl_means")
        elif h is not None and h.upos == "ADJ":
            add(f"{who}ablative with the adjective {link(h)}: <b>specification</b> (in what respect) or cause; "
                f"<i>dignus</i>, <i>frētus</i>, <i>contentus</i> regularly take it.", "abl_specification",
                "abl_cause")
        else:
            add(f"{who}ablative without a preposition, depending on {link(h) if h is not None else 'the clause'}: "
                f"most often <b>means or instrument</b> (“by, with”), also cause, manner or respect.",
                "abl_means", "abl_cause", "abl_manner", "abl_specification")


def _sequence_note(token) -> str:
    tense = token.cats.get("tense")
    return {
        "present": "Present subjunctive: primary sequence — the action is contemporary with, or follows, a "
                   "present or future main verb.",
        "perfect": "Perfect subjunctive: primary sequence — the action precedes a present or future main verb.",
        "imperfect": "Imperfect subjunctive: secondary sequence — after a past main verb, for an action at the "
                     "same time or later.",
        "pluperfect": "Pluperfect subjunctive: secondary sequence — after a past main verb, for an action "
                      "already completed.",
    }.get(tense, "")


def verb_notes(token, entry, add):
    cats = token.cats
    vf = cats.get("verbform")
    rel = token.deprel
    base_rel = rel.split(":")[0]
    h = token.head_token
    hl = lemma_key(h) if h is not None else ""
    marks = [c for c in token.children if c.deprel == "mark"]
    mark = marks[0] if marks else None
    ml = lemma_key(mark) if mark is not None else ""
    deponent = is_deponent(entry)
    if deponent and cats.get("voice") == "passive" or (deponent and vf in ("finite", "infinitive")):
        add(f"<i>{escape(token.lemma)}</i> is a <b>deponent</b> verb: passive in form, active in meaning.",
            "deponent")
    # auxiliaries ---------------------------------------------------------------
    if base_rel == "aux" and h is not None:
        hv = h.cats.get("verbform")
        if hv == "gerundive":
            add(f"With the gerundive {link(h)} it forms the <b>second (passive) periphrastic</b>: necessity or "
                f"obligation — “must be …, has to be …”.", "periphrastic", "gerundive", "dat_agent")
        elif hv == "participle" and h.cats.get("tense") == "future":
            add(f"With the future participle {link(h)} it forms the <b>first (active) periphrastic</b>: “is about "
                f"to …, intends to …”.", "periphrastic", "fut_participle")
        elif hv == "participle":
            which = {"present": "perfect", "imperfect": "pluperfect", "future": "future perfect"}.get(
                cats.get("tense"), "perfect")
            add(f"Auxiliary: with the perfect participle {link(h)} it forms the <b>{which} passive</b> "
                f"(of deponents: the {which} active). The participle agrees with the subject.", "esse",
                "verb_general")
        return
    if base_rel == "cop" and h is not None:
        add(f"<b>Copula</b>: it links the subject with the predicate {link(h)}, which agrees with the subject.",
            "pred_noun", "esse")
        return
    # finite verbs ----------------------------------------------------------------
    if vf == "finite":
        mood = cats.get("mood")
        subj = token.child("nsubj")
        if subj is None and cats.get("person") == "third-person":
            pass
        if mood == "imperative":
            add("<b>Imperative</b>: a command.", "imperative")
        elif mood == "subjunctive":
            seq = _sequence_note(token)
            has_rel = any(c.feats.get("PronType") == "Rel" for c in token.children) or rel == "acl:relcl"
            interrogative = any(lemma_key(c) in INTERROGATIVES and (c.feats.get("PronType") == "Int"
                                or c.upos in ("ADV", "PART", "SCONJ")) for c in token.children)
            result_sign = h is not None and any(lemma_key(c) in RESULT_SIGNS for c in list(h.children) + [
                g for c in h.children for g in c.children])
            if ml in ("ut", "uti"):
                if hl in VERBS_OF_FEARING:
                    add(f"Subjunctive with {link(mark)} after a verb of fearing ({link(h)}): <i>ut</i> = “that … "
                        f"not”, <i>nē</i> = “that”.", "subst_purpose", "sequence")
                elif result_sign or hl in VERBS_OF_HAPPENING:
                    add(f"Subjunctive in a <b>result clause</b> with {link(mark)} (“so that”, “that”): the main "
                        f"clause has a word like <i>tam, ita, tantus</i> or a verb of happening/bringing about.",
                        "result", "subst_result", "sequence")
                elif hl in VERBS_OF_ASKING:
                    add(f"Subjunctive in an <b>object clause</b> with {link(mark)} after {link(h)} (verbs of asking, "
                        f"commanding, persuading, deciding): “that … should”, English often uses an infinitive.",
                        "subst_purpose", "sequence")
                else:
                    add(f"Subjunctive with {link(mark)}: most often a <b>purpose clause</b> (“in order that, to”); "
                        f"if the main clause contains <i>tam, ita, tantus …</i> it is a result clause (“so that”).",
                        "purpose", "result", "sequence")
            elif ml == "ne":
                if hl in VERBS_OF_FEARING:
                    add(f"Subjunctive with {link(mark)} after a verb of fearing: “(fears) that …”.",
                        "subst_purpose", "sequence")
                else:
                    add(f"Subjunctive with {link(mark)}: <b>negative purpose</b> (“in order that … not”, “lest”) "
                        f"or a negative object clause after verbs of asking and commanding.", "purpose",
                        "subst_purpose", "sequence")
            elif ml == "cum":
                add(f"Subjunctive in a <b>cum-clause</b> ({link(mark)}): with the imperfect or pluperfect "
                    f"subjunctive <i>cum</i> gives the circumstances of the main action (“when, as”), often "
                    f"shading into cause (“since”) or concession (“although”).", "cum", "sequence")
            elif ml in ("si", "nisi", "ni", "sin", "quasi"):
                kind = {"present": "a future condition put less vividly (“should … would”)",
                        "perfect": "a future condition put less vividly (“should … would”)",
                        "imperfect": "a present condition contrary to fact (“if … were”) — or, in indirect "
                                     "discourse, simply the reported form of a condition",
                        "pluperfect": "a past condition contrary to fact (“if … had”) — or, in indirect "
                                      "discourse, the reported form of a future-perfect condition"}.get(
                    cats.get("tense"), "a condition")
                add(f"Subjunctive in a <b>conditional clause</b> with {link(mark)}: {kind}.", "conditions",
                    "ind_discourse_sub")
            elif ml in ("etsi", "tametsi", "quamuis", "licet", "quamquam"):
                add(f"Subjunctive in a <b>concessive clause</b> with {link(mark)} (“although”).", "concessive")
            elif ml in ("quod", "quia", "quoniam"):
                add(f"Subjunctive in a causal clause with {link(mark)}: the reason is given as the thought or "
                    f"words of someone else (or the clause stands inside indirect discourse).", "causal",
                    "ind_discourse_sub", "attraction")
            elif ml in ("priusquam", "antequam"):
                add(f"Subjunctive with {link(mark)} “before”: the action is anticipated or prevented.",
                    "antequam", "sequence")
            elif ml in ("dum", "donec", "quoad"):
                add(f"Subjunctive with {link(mark)}: “until” (something expected or intended), or “provided "
                    f"that”.", "dum", "sequence")
            elif ml in ("quin", "quominus"):
                add(f"Subjunctive with {link(mark)} after a negatived verb of doubting or hindering.", "quin")
            elif interrogative and base_rel in ("ccomp", "csubj", "acl", "advcl", "xcomp", "obj", "conj"):
                add("Subjunctive in an <b>indirect question</b>: a question made to depend on a verb of asking, "
                    "knowing, telling.", "ind_question", "sequence")
            elif mark is not None:
                add(f"Subjunctive in a subordinate clause introduced by {link(mark)}; inside reported speech "
                    f"every subordinate verb is subjunctive.", "ind_discourse_sub", "attraction", "sequence")
            elif has_rel:
                add("Subjunctive in a <b>relative clause</b>: it expresses purpose (“who was to …”), a "
                    "characteristic (“the sort of … who”), cause — or the clause belongs to reported speech, "
                    "where all subordinate verbs are subjunctive.", "characteristic", "purpose",
                    "ind_discourse_sub", "attraction")
            elif base_rel in ("root", "parataxis") or (base_rel == "conj" and h is not None and
                                                       h.deprel == "root" and h.cats.get("mood") != "indicative"):
                add("Subjunctive in a main clause: an exhortation or command (“let …”), a wish, a deliberative "
                    "question (“what am I to …?”) or a possibility (“would, might”).", "subj_independent")
            else:
                add("Subjunctive in a dependent clause without a conjunction: an object clause (“that … "
                    "should”), or a subordinate verb inside reported speech.", "subst_purpose",
                    "ind_discourse_sub", "attraction", "sequence")
            if seq:
                add(seq, "sequence")
        elif mood == "indicative" and mark is not None and ml in SCONJ_NOTES:
            extra = {"cum": " With the indicative <i>cum</i> simply dates the action: “when”.",
                     "si": " With the indicative the condition is stated as a simple fact (nothing implied "
                           "about its fulfilment).",
                     "nisi": " With the indicative the condition is stated as a simple fact.",
                     "dum": " <i>dum</i> “while” takes the present indicative even of past time.",
                     "ut": " With the indicative <i>ut</i> means “as” or “when”."}.get(ml, "")
            add(f"Indicative in a clause introduced by {link(mark)}." + extra, *SCONJ_NOTES[ml][1])
        elif mood == "indicative" and (rel == "acl:relcl" or any(c.feats.get("PronType") == "Rel"
                                                                  for c in token.children)):
            add("Indicative in a <b>relative clause</b>: it states a fact about the antecedent.", "rel_agreement")
        if cats.get("voice") == "passive" and not deponent:
            agent = next((c for c in token.children if c.deprel == "obl:agent" or
                          (c.child("case") is not None and lemma_key(c.child("case")) in ("ab", "a"))), None)
            add("<b>Passive</b>: the subject undergoes the action" +
                (f"; the agent is expressed by <i>ā/ab</i> + ablative ({link(agent)})." if agent is not None else
                 "."), "verb_general", *(["abl_agent"] if agent is not None else []))
    # infinitives -------------------------------------------------------------------
    elif vf == "infinitive":
        subj = next((c for c in token.children if c.deprel.split(":")[0] == "nsubj"
                     and c.cats.get("case") == "accusative"), None)
        tense = cats.get("tense")
        time = {"present": "the same time as the governing verb", "perfect": "an earlier time",
                "future": "a later time"}.get(tense, "")
        if subj is not None or (base_rel in ("ccomp", "csubj") and hl in SAYING) or \
                (base_rel == "conj" and h is not None and h.cats.get("verbform") == "infinitive"
                 and any(c.deprel.split(":")[0] == "nsubj" and c.cats.get("case") == "accusative"
                         for c in h.children)):
            add("<b>Accusative and infinitive</b>" + (f" (subject: {link(subj)})" if subj is not None else "") +
                (f", depending on {link(h)}" if h is not None and base_rel in ("ccomp", "csubj", "xcomp") else "") +
                ": the regular form of a reported statement after verbs of saying, thinking, knowing and "
                "perceiving; also after <i>iubeō, vetō, patior, volō</i>." +
                (f" The {tense} infinitive marks {time}." if time else ""),
                "inf_acc", "ind_discourse", "inf_tenses")
        elif base_rel == "xcomp" and (hl in COMPLEMENTARY or h is not None and h.upos in ("VERB", "AUX")):
            add(f"<b>Complementary infinitive</b> with {link(h)}: it completes the meaning of a verb like "
                f"<i>possum, volō, dēbeō, soleō, coepī, cōnor</i>; it has the same subject as that verb.",
                "inf_complementary")
        elif base_rel == "csubj":
            add(f"Infinitive as <b>subject</b> of {link(h)} (with <i>est</i>, <i>licet</i>, <i>oportet</i>, "
                f"<i>necesse est</i> …): “to … is …”.", "inf_subject")
        elif base_rel in ("root", "parataxis") or (base_rel == "conj" and h is not None and h.deprel == "root"):
            add("<b>Historical infinitive</b>: in lively narrative the present infinitive stands for a past "
                "indicative, with its subject in the nominative.", "inf_historical")
        else:
            add("Infinitive depending on " + (link(h) if h is not None else "the clause") +
                ": either a complementary infinitive or part of an accusative-and-infinitive clause.",
                "inf_complementary", "inf_acc")
    # participles ----------------------------------------------------------------------
    elif vf == "participle":
        tense = cats.get("tense")
        aux = token.child("aux", "cop")
        if rel == "advcl:abs":
            pass                                       # explained as ablative absolute
        elif aux is not None and tense == "perfect":
            which = {"present": "perfect", "imperfect": "pluperfect", "future": "future perfect"}.get(
                aux.cats.get("tense"), "perfect")
            mood = aux.cats.get("mood", "indicative")
            add(f"With {link(aux)} it forms the <b>{which} {mood} "
                f"{'(deponent: active meaning)' if deponent else 'passive'}</b>. The participle agrees with the "
                f"subject in gender, number and case.", "verb_general", "esse")
        elif aux is not None and tense == "future":
            add(f"Future participle with {link(aux)}: the <b>first periphrastic</b> — “is about to, intends "
                f"to”; with <i>esse</i> it is the future infinitive.", "fut_participle", "periphrastic")
        elif tense == "future":
            add("<b>Future active participle</b> (-ūrus): “about to …, going to …”. In the accusative with "
                "<i>esse</i> understood it is the <b>future infinitive</b> of reported speech.",
                "fut_participle", "inf_acc", "inf_tenses")
        elif tense == "perfect" and cats.get("case") == "accusative" and base_rel in ("ccomp", "xcomp", "csubj"):
            add("Perfect participle in the accusative with <i>esse</i> understood: the <b>perfect passive "
                "infinitive</b> of an accusative-and-infinitive clause.", "inf_acc", "inf_tenses")
        elif base_rel in ("amod", "acl") and h is not None:
            add(f"Participle used <b>attributively</b>: it describes {link(h)} like an adjective and agrees with "
                f"it.", "participles", "adj_agreement")
        elif base_rel == "advcl":
            add("Participle used <b>circumstantially</b>: it agrees with a noun of the main clause and stands "
                "for a clause of time, cause, concession or condition (“when/since/although/if …”).",
                "participles")
        else:
            add({"present": "<b>Present active participle</b> (-ns, -ntis): “…ing”, action at the same time as "
                            "the main verb.",
                 "perfect": "<b>Perfect passive participle</b>: “having been …ed” (of deponents: “having …ed”), "
                            "action before the main verb."}.get(tense, "Participle."), "participles")
        if deponent and tense == "perfect":
            add("Being from a deponent verb, this perfect participle has <b>active</b> meaning (“having …”).",
                "deponent")
    # gerund, gerundive, supine -----------------------------------------------------------
    elif vf == "gerundive":
        aux = token.child("aux", "cop")
        case = cats.get("case")
        if aux is not None or (base_rel in ("root", "ccomp", "xcomp", "csubj", "conj") and case in (
                "nominative", "accusative") and token.child("case") is None):
            add("<b>Gerundive of obligation</b> (second periphrastic, with <i>esse</i> expressed or understood): "
                "“must be …ed, has to be …ed”; the person who must do it stands in the dative.",
                "gerundive", "periphrastic", "dat_agent")
        elif _is_gerundive_agreeing(token):
            noun = h if token.deprel in ("amod", "acl", "det") else token.child("nsubj", "obj")
            add("<b>Gerundive construction</b>: instead of a gerund with an object, Latin puts the noun in the "
                "required case and makes the gerundive agree with it" +
                (f" ({link(noun)} … {escape(token.text)})" if noun is not None else "") +
                {"accusative": " — with <i>ad</i> it expresses purpose (“for …ing, in order to …”).",
                 "genitive": " — the genitive depends on a noun or adjective, or on <i>causā/grātiā</i> "
                             "(“for the sake of …ing”).",
                 "ablative": " — the ablative expresses means or follows <i>in, dē, ex, ab</i>.",
                 "dative": " — the dative expresses purpose (“for …ing”)."}.get(case, "."),
                "gerund", "gerundive")
        else:
            add("<b>Gerund</b>: the verbal noun (“…ing”), neuter singular, used in the oblique cases" +
                {"accusative": " — with <i>ad</i> it expresses purpose.",
                 "genitive": " — the genitive depends on a noun or adjective, or on <i>causā/grātiā</i>.",
                 "ablative": " — the ablative expresses means (“by …ing”) or follows a preposition.",
                 "dative": "."}.get(case, "."), "gerund")
    elif vf == "supine":
        if cats.get("case") == "ablative" or token.key.endswith("u"):
            add("<b>Supine in -ū</b> with an adjective: “(easy, best, wonderful) to …”.", "supine")
        else:
            add("<b>Supine in -um</b> after a verb of motion: purpose (“to …, in order to …”).", "supine")


def syntax_notes(token, entry) -> list[tuple[str, list[str]]]:
    """Notes on how this word is used here, each with A&G topic ids."""
    notes: list[tuple[str, list[str]]] = []

    def add(text, *topics):
        if text and text not in [n[0] for n in notes]:
            notes.append((text, [t for t in topics if t in TOPICS]))

    upos, cats, feats = token.upos, token.cats, token.feats
    h = token.head_token
    rel = token.deprel
    lem = lemma_key(token)
    # abbreviations and numerals
    if upos == "PROPN" and token.text.rstrip(".") in PRAENOMINA and len(token.text) <= 3:
        add(f"Abbreviated first name (praenomen): <b>{PRAENOMINA[token.text.rstrip('.')]}</b>; it is declined "
            f"with the name it accompanies.")
    value = roman_value(token.text) if upos == "NUM" or (token.text.isupper() and len(token.text) > 1) else None
    if value and upos in ("NUM", "ADJ"):
        add(f"Roman numeral: <b>{value}</b>.", "numerals")
    if upos in ("VERB", "AUX"):
        verb_notes(token, entry, add)
        if cats.get("verbform") in ("participle", "gerundive") and "case" in cats:
            case_notes(token, add)
    elif upos in NOMINAL:
        base = phrase_base(token)
        if base is not token and rel in ("amod", "det", "nummod") and h is not None:
            add(f"It <b>agrees</b> with {link(h)} in case, number and gender.", "adj_agreement")
        elif rel == "appos" and h is not None:
            add(f"<b>Apposition</b> to {link(h)}: a noun explaining another stands in the same case.", "apposition")
        elif rel == "conj" and h is not None:
            add(f"Coordinated with {link(h)} and therefore in the same construction.")
        elif upos in ("ADJ", "DET") and rel.split(":")[0] in ("nsubj", "obj", "obl", "iobj", "nmod") \
                and feats.get("PronType") is None:
            add("An adjective used <b>as a noun</b> (masculine = persons, neuter = things).", "adj_as_noun")
        if feats.get("PronType") == "Rel":
            clause = h if h is not None else None
            if rel in ("det", "amod", "nmod") and h is not None and h.head_token is not None:
                clause = h.head_token
            antecedent = clause.head_token if clause is not None and clause.deprel.startswith(
                ("acl", "advcl")) else None
            if antecedent is not None and antecedent.upos in NOMINAL:
                add(f"<b>Relative pronoun</b>: it takes gender and number from its antecedent {link(antecedent)}, "
                    f"but its case from its role in its own clause.", "rel_agreement", "rel_pron")
            elif clause is not None and clause.deprel in ("root", "parataxis") and token.index <= 2:
                add("<b>Connecting relative</b>: at the start of a sentence <i>quī</i> refers back to the "
                    "preceding sentence and is translated “and he / this / these …”.", "rel_agreement", "rel_pron")
            else:
                add("<b>Relative pronoun</b>: gender and number come from its antecedent, the case from its own "
                    "clause.", "rel_agreement", "rel_pron")
        if feats.get("Reflex") == "Yes":
            add("<b>Reflexive</b>: <i>sē</i> and <i>suus</i> refer to the subject of their clause — and, inside "
                "reported speech or a purpose clause, to the subject of the governing verb (the speaker).",
                "reflexive")
        if cats.get("degree") == "comparative":
            add("<b>Comparative</b>: “more …, rather …, too …”; “than” is <i>quam</i> or the ablative.",
                "comparison", "abl_comparison")
        elif cats.get("degree") == "superlative":
            add("<b>Superlative</b>: “most …” or simply “very …”; with <i>quam</i> “as … as possible”.",
                "comparison")
        case_notes(token, add)
    elif upos == "ADP":
        obj = h
        pl = {"a": "ab", "abs": "ab", "e": "ex"}.get(lem, lem)
        governs = {"acc": "the accusative", "abl": "the ablative",
                   "both": "the accusative (motion towards) or the ablative (rest in a place)"}.get(
            PREP_CASE.get(pl, ""), "")
        text = "<b>Preposition</b>"
        if PREP_MEANING.get(pl):
            text += f" “{PREP_MEANING[pl]}”"
        if governs:
            text += f"; it takes {governs}"
        if obj is not None and obj.cats.get("case"):
            text += f". Here it governs {link(obj)} ({obj.cats['case']})"
        add(text + ".", "prepositions", *(["place"] if pl in ("in", "sub", "ad", "ab", "ex") else []))
    elif upos == "SCONJ":
        verb = h
        note = SCONJ_NOTES.get(lem)
        if note:
            text = note[0]
            if verb is not None and verb.cats.get("mood"):
                text += f" Here its verb is {link(verb)} ({verb.cats['mood']})."
            add(text, *note[1])
        elif verb is not None:
            add(f"<b>Subordinating conjunction</b>: it introduces the clause whose verb is {link(verb)}.",
                "conjunctions")
    elif upos == "CCONJ":
        if lem == "que":
            add("<b>-que</b> “and”: an enclitic attached to the end of the word it adds — <i>senātus populusque</i> "
                "= <i>senātus et populus</i>. It joins things that belong closely together.", "conjunctions")
        elif h is not None:
            other = h.head_token if h.deprel == "conj" else None
            add("<b>Coordinating conjunction</b>" + (f": it joins {link(other)} and {link(h)}." if other is not None
                                                      else "."), "conjunctions")
    elif upos == "ADV":
        if lem == "quam" and h is not None and h.cats.get("degree") == "superlative":
            add("<i>quam</i> with a superlative: “as … as possible”.", "comparison")
        elif cats.get("degree") in ("comparative", "superlative"):
            add(f"<b>{cats['degree'].capitalize()} adverb</b> (comparative in -ius, superlative in -issimē).",
                "comparison")
        if lem in ("non", "ne", "haud", "neque", "nec"):
            add("Negation.")
    return notes


# --------------------------------------------------------------------------- #
# All model paradigms (for the reference window)
# --------------------------------------------------------------------------- #
def _side_by_side(tables: list[str]) -> str:
    cells = "".join(f'<td valign="top" style="padding-right:14px">{t}</td>' for t in tables)
    return f'<table cellspacing="0"><tr>{cells}</tr></table>'


def _numeral_table(title: str, items) -> str:
    half = (len(items) + 2) // 3
    columns = [items[i:i + half] for i in range(0, len(items), half)]
    cells = []
    for col in columns:
        rows = "".join(f"<tr><th>{n}</th><td>{fmt(form)}</td></tr>" for n, form in col)
        cells.append(f'<td valign="top" style="padding-right:14px"><table class="grid" cellspacing="0">'
                     f"{rows}</table></td>")
    return f'<h3>{title}</h3><table cellspacing="0"><tr>{"".join(cells)}</tr></table>'


def paradigm_reference() -> list[tuple[str, str]]:
    """(title, html) for every group of model paradigms."""
    pages = []
    nouns = "".join(_side_by_side([noun_table(k) for k in row]) for row in tb.NOUN_ROWS)
    pages.append(("Nōmina — nouns", "<h2>NOMINA</h2>" + nouns))
    adj = "".join(gender_table(*tb.ADJECTIVES[k]) for k in ("magnus", "nullus", "gravis", "ingens", "melior"))
    pages.append(("Adiectīva — adjectives", "<h2>ADIECTIVA</h2>" + adj))
    comp = "".join(f"<tr><th><i>{label}</i></th>" + "".join(f"<td>{fmt(f)}</td>" for f in forms) + "</tr>"
                   for label, forms in tb.COMPARISON)
    numbers = (f'<h2>COMPARATIO</h2><table class="grid" cellspacing="0">{comp}</table><h2>NVMERI</h2>'
               + _numeral_table("Cardinālia", tb.CARDINALS) + _numeral_table("Ōrdinālia", tb.ORDINALS))
    pages.append(("Comparātiō, numerī — comparison, numerals", numbers))
    poss = "".join(f"<tr><td>{fmt(p)}</td></tr>" for p in tb.POSSESSIVE)
    pron = ("<h2>PRONOMINA</h2>" + personal_table()
            + f'<h3>Possessīva</h3><table class="grid" cellspacing="0">{poss}</table>'
            + "".join(gender_table(*tb.PRONOUNS[k]) for k in ("is", "hic", "ille", "qui")))
    pages.append(("Prōnōmina — pronouns", pron))
    for voice in ("active", "passive"):
        parts = [f"<h2>VERBA {tb.VOICE_LABELS[voice]}</h2>"]
        keys = [k for k in tb.NONFINITE if k[0] == voice and k[1] == "infinitive"]
        parts.append("<h3>Īnfīnītīvus</h3>" + nonfinite_table(keys))
        if voice == "active":
            parts.append("<h3>Imperātīvus</h3>" + nonfinite_table(
                [("active", "imperative", "singular"), ("active", "imperative", "plural")]))
        for mood in ("indicative", "subjunctive"):
            for tense in tb.TENSE_LABELS:
                parts.append(verb_table(voice, mood, tense))
        rest = [k for k in tb.NONFINITE if k[0] == voice and k[1] in ("participle", "gerundive", "supine")]
        parts.append("<h3>Participium" + (", supīna" if voice == "active" else ", gerundīvum") + "</h3>"
                     + nonfinite_table(rest))
        pages.append((f"Verba: {'āctīvum' if voice == 'active' else 'passīvum'}", "".join(parts)))
    return pages
