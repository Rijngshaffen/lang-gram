"""Model paradigms of Latin nouns, adjectives, pronouns and verbs, as data, so
that a word of a text can be pointed at inside them.

A bar separates stem and ending ("serv|us"), macrons mark long vowels, and the
cases run nom - acc - gen - dat - abl.
"""
from __future__ import annotations

CASES = ["nominative", "accusative", "genitive", "dative", "ablative"]
CASE_LABELS = {"nominative": "nōm", "accusative": "acc", "genitive": "gen", "dative": "dat", "ablative": "abl"}



def _decl(sing: str, plur: str) -> dict:
    s, p = sing.split(), plur.split()
    return {("singular", c): s[i] for i, c in enumerate(CASES)} | {("plural", c): p[i] for i, c in enumerate(CASES)}


# --------------------------------------------------------------------------- #
# Nouns
# --------------------------------------------------------------------------- #
NOUNS = {
    "hora": ("Dēclīnātiō I", "hōra, -ae f", _decl("hōr|a hōr|am hōr|ae hōr|ae hōr|ā",
                                                  "hōr|ae hōr|ās hōr|ārum hōr|īs hōr|īs")),
    "servus": ("Dēclīnātiō II", "servus, -ī m", _decl("serv|us serv|um serv|ī serv|ō serv|ō",
                                                     "serv|ī serv|ōs serv|ōrum serv|īs serv|īs")),
    "liber": ("Dēclīnātiō II", "liber, -brī m", _decl("liber libr|um libr|ī libr|ō libr|ō",
                                                     "libr|ī libr|ōs libr|ōrum libr|īs libr|īs")),
    "verbum": ("Dēclīnātiō II", "verbum, -ī n", _decl("verb|um verb|um verb|ī verb|ō verb|ō",
                                                     "verb|a verb|a verb|ōrum verb|īs verb|īs")),
    "sol": ("Dēclīnātiō III", "sōl, sōlis m", _decl("sōl sōl|em sōl|is sōl|ī sōl|e",
                                                   "sōl|ēs sōl|ēs sōl|um sōl|ibus sōl|ibus")),
    "leo": ("Dēclīnātiō III", "leō, -ōnis m", _decl("leō leōn|em leōn|is leōn|ī leōn|e",
                                                   "leōn|ēs leōn|ēs leōn|um leōn|ibus leōn|ibus")),
    "vox": ("Dēclīnātiō III", "vōx, vōcis f", _decl("vōx vōc|em vōc|is vōc|ī vōc|e",
                                                   "vōc|ēs vōc|ēs vōc|um vōc|ibus vōc|ibus")),
    "nomen": ("Dēclīnātiō III", "nōmen, -inis n", _decl("nōmen nōmen nōmin|is nōmin|ī nōmin|e",
                                                       "nōmin|a nōmin|a nōmin|um nōmin|ibus nōmin|ibus")),
    "navis": ("Dēclīnātiō III", "nāvis, -is f", _decl("nāv|is nāv|em nāv|is nāv|ī nāv|e",
                                                     "nāv|ēs nāv|ēs nāv|ium nāv|ibus nāv|ibus")),
    "urbs": ("Dēclīnātiō III", "urbs, urbis f", _decl("urb|s urb|em urb|is urb|ī urb|e",
                                                     "urb|ēs urb|ēs urb|ium urb|ibus urb|ibus")),
    "mons": ("Dēclīnātiō III", "mōns, montis m", _decl("mōns mont|em mont|is mont|ī mont|e",
                                                      "mont|ēs mont|ēs mont|ium mont|ibus mont|ibus")),
    "mare": ("Dēclīnātiō III", "mare, -is n", _decl("mar|e mar|e mar|is mar|ī mar|ī",
                                                   "mar|ia mar|ia mar|ium mar|ibus mar|ibus")),
    "casus": ("Dēclīnātiō IV", "cāsus, -ūs m", _decl("cās|us cās|um cās|ūs cās|uī cās|ū",
                                                    "cās|ūs cās|ūs cās|uum cās|ibus cās|ibus")),
    "cornu": ("Dēclīnātiō IV", "cornū, -ūs n", _decl("corn|ū corn|ū corn|ūs corn|ū corn|ū",
                                                    "corn|ua corn|ua corn|uum corn|ibus corn|ibus")),
    "dies": ("Dēclīnātiō V", "diēs, -ēī m", _decl("di|ēs di|em di|ēī di|ēī di|ē",
                                                 "di|ēs di|ēs di|ērum di|ēbus di|ēbus")),
    "res": ("Dēclīnātiō V", "rēs, reī f", _decl("r|ēs r|em r|eī r|eī r|ē",
                                               "r|ēs r|ēs r|ērum r|ēbus r|ēbus")),
}
NOUN_ROWS = [["hora", "servus", "liber", "verbum"], ["sol", "leo", "vox", "nomen"],
             ["navis", "urbs", "mons", "mare"], ["casus", "cornu", "dies", "res"]]


# --------------------------------------------------------------------------- #
# Adjectives and pronouns with three genders: {(number, case): [m, f, n]}
# --------------------------------------------------------------------------- #
def _adj(rows: str) -> dict:
    """Ten lines "m f n": singular nom..abl, then plural nom..abl."""
    out = {}
    lines = [ln.split() for ln in rows.strip().splitlines()]
    for i, parts in enumerate(lines):
        if len(parts) == 2:                       # m/f share a form
            parts = [parts[0], parts[0], parts[1]]
        elif len(parts) == 1:
            parts = parts * 3
        out[("singular" if i < 5 else "plural", CASES[i % 5])] = parts
    return out


ADJECTIVES = {
    "magnus": ("Dēclīnātiō I et II: adiectīva", "magnus -a -um", _adj("""
        magn|us magn|a magn|um
        magn|um magn|am magn|um
        magn|ī magn|ae magn|ī
        magn|ō magn|ae magn|ō
        magn|ō magn|ā magn|ō
        magn|ī magn|ae magn|a
        magn|ōs magn|ās magn|a
        magn|ōrum magn|ārum magn|ōrum
        magn|īs
        magn|īs""")),
    "nullus": ("Dēclīnātiō I et II: adiectīva (gen -īus, dat -ī)", "nūllus -a -um", _adj("""
        nūll|us nūll|a nūll|um
        nūll|um nūll|am nūll|um
        nūll|īus
        nūll|ī
        nūll|ō nūll|ā nūll|ō
        nūll|ī nūll|ae nūll|a
        nūll|ōs nūll|ās nūll|a
        nūll|ōrum nūll|ārum nūll|ōrum
        nūll|īs
        nūll|īs""")),
    "gravis": ("Dēclīnātiō III: adiectīva", "gravis -e", _adj("""
        grav|is grav|e
        grav|em grav|e
        grav|is
        grav|ī
        grav|ī
        grav|ēs grav|ia
        grav|ēs grav|ia
        grav|ium
        grav|ibus
        grav|ibus""")),
    "ingens": ("Dēclīnātiō III: adiectīva", "ingēns, -entis", _adj("""
        ingēns
        ingent|em ingēns
        ingent|is
        ingent|ī
        ingent|ī
        ingent|ēs ingent|ia
        ingent|ēs ingent|ia
        ingent|ium
        ingent|ibus
        ingent|ibus""")),
    "melior": ("Dēclīnātiō III: comparātīvus", "melior, melius", _adj("""
        melior melius
        meliōr|em melius
        meliōr|is
        meliōr|ī
        meliōr|e
        meliōr|ēs meliōr|a
        meliōr|ēs meliōr|a
        meliōr|um
        meliōr|ibus
        meliōr|ibus""")),
}

PRONOUNS = {
    "is": ("Prōnōmina dēmōnstrātīva", "is ea id", _adj("""
        i|s e|a i|d
        e|um e|am i|d
        e|ius
        e|ī
        e|ō e|ā e|ō
        i|ī e|ae e|a
        e|ōs e|ās e|a
        e|ōrum e|ārum e|ōrum
        i|īs
        i|īs""")),
    "hic": ("Prōnōmina dēmōnstrātīva", "hic haec hoc", _adj("""
        hic haec hoc
        hunc hanc hoc
        huius
        huic
        hōc hāc hōc
        hī hae haec
        hōs hās haec
        hōrum hārum hōrum
        hīs
        hīs""")),
    "ille": ("Prōnōmina dēmōnstrātīva", "ille illa illud", _adj("""
        ill|e ill|a ill|ud
        ill|um ill|am ill|ud
        ill|īus
        ill|ī
        ill|ō ill|ā ill|ō
        ill|ī ill|ae ill|a
        ill|ōs ill|ās ill|a
        ill|ōrum ill|ārum ill|ōrum
        ill|īs
        ill|īs""")),
    "qui": ("Prōnōmen interrogātīvum / relātīvum", "quis/quī quae quid/quod", _adj("""
        qu|is/qu|ī qu|ae qu|id/qu|od
        qu|em qu|am qu|id/qu|od
        cu|ius
        cu|i
        qu|ō qu|ā qu|ō
        qu|ī qu|ae qu|ae
        qu|ōs qu|ās qu|ae
        qu|ōrum qu|ārum qu|ōrum
        qu|ibus
        qu|ibus""")),
}

# Personal pronouns: nom / acc / dat / abl only.
PERSONAL = {
    "columns": ["ego", "tū", "sē", "nōs", "vōs"],
    "rows": [("nominative", ["ego", "tū", "—", "nōs", "vōs"]),
             ("accusative", ["mē", "tē", "sē", "nōs", "vōs"]),
             ("dative", ["mihi", "tibi", "sibi", "nōbīs", "vōbīs"]),
             ("ablative", ["mē", "tē", "sē", "nōbīs", "vōbīs"])],
}
POSSESSIVE = ["me|us -a -um", "tu|us -a -um", "su|us -a -um", "noster -tr|a -tr|um", "vester -tr|a -tr|um"]

COMPARISON = [
    ("positīvus", ["long|us", "brev|is", "audāx -āc|is", "aeger -gr|a -gr|um"]),
    ("comparātīvus", ["long|ior -ius", "brev|ior -ius", "audāc|ior -ius", "aegr|ior -ius"]),
    ("superlātīvus", ["long|issim|us", "brev|issim|us", "audāc|issim|us", "aeger|rim|us"]),
]

CARDINALS = [
    (1, "ūn|us"), (2, "du|o -ae -o"), (3, "tr|ēs -ia"), (4, "quattuor"), (5, "quīnque"), (6, "sex"),
    (7, "septem"), (8, "octō"), (9, "novem"), (10, "decem"), (11, "ūndecim"), (12, "duodecim"),
    (13, "trēdecim"), (14, "quattuordecim"), (15, "quīndecim"), (16, "sēdecim"), (17, "septendecim"),
    (18, "duodēvīgintī"), (19, "ūndēvīgintī"), (20, "vīgintī"), (30, "trīgintā"), (40, "quadrāgintā"),
    (50, "quīnquāgintā"), (60, "sexāgintā"), (70, "septuāgintā"), (80, "octōgintā"), (90, "nōnāgintā"),
    (100, "centum"), (200, "ducent|ī"), (300, "trecent|ī"), (400, "quadringent|ī"), (500, "quīngent|ī"),
    (600, "sescent|ī"), (700, "septingent|ī"), (800, "octingent|ī"), (900, "nōngent|ī"), (1000, "mīlle"),
    (2000, "du|o mīl|ia"), (3000, "tr|ia mīl|ia"),
]
ORDINALS = [
    (1, "prīm|us"), (2, "secund|us"), (3, "terti|us"), (4, "quārt|us"), (5, "quīnt|us"), (6, "sext|us"),
    (7, "septim|us"), (8, "octāv|us"), (9, "nōn|us"), (10, "decim|us"), (11, "ūndecim|us"),
    (12, "duodecim|us"), (13, "terti|us decim|us"), (18, "duodēvīcēsim|us"), (19, "ūndēvīcēsim|us"),
    (20, "vīcēsim|us"), (30, "trīcēsim|us"), (40, "quadrāgēsim|us"), (50, "quīnquāgēsim|us"),
    (60, "sexāgēsim|us"), (70, "septuāgēsim|us"), (80, "octōgēsim|us"), (90, "nōnāgēsim|us"),
    (100, "centēsim|us"), (200, "ducentēsim|us"), (300, "trecentēsim|us"), (400, "quadringentēsim|us"),
    (500, "quīngentēsim|us"), (600, "sescentēsim|us"), (700, "septingentēsim|us"),
    (800, "octingentēsim|us"), (900, "nōngentēsim|us"), (1000, "mīllēsim|us"), (2000, "bis mīllēsim|us"),
]


# --------------------------------------------------------------------------- #
# Verbs
# --------------------------------------------------------------------------- #
VERBS = ["amare", "monere", "legere", "audire", "esse"]
VERB_TITLES = {"amare": "amāre (I)", "monere": "monēre (II)", "legere": "legere (III)", "audire": "audīre (IV)",
               "esse": "esse"}
PERSONS = [("singular", "first-person"), ("singular", "second-person"), ("singular", "third-person"),
           ("plural", "first-person"), ("plural", "second-person"), ("plural", "third-person")]
_LONG = str.maketrans("aei", "āēī")


def _lengthen(stem: str) -> str:
    return stem[:-1] + stem[-1].translate(_LONG)


def _alt(stem: str, endings: list[str], long_at: tuple[int, ...]) -> list[str]:
    """Stem + personal endings; the stem's last vowel is long before some of them."""
    return [(_lengthen(stem) if i in long_at else stem) + "|" + e for i, e in enumerate(endings)]


ACT = ["m", "s", "t", "mus", "tis", "nt"]
PAS = ["r", "ris", "tur", "mur", "minī", "ntur"]
A_LONG, P_LONG = (1, 3, 4), (1, 2, 3, 4)

PERFECT = {"amare": "amāv", "monere": "monu", "legere": "lēg", "audire": "audīv", "esse": "fu"}
SUPINE = {"amare": "amāt", "monere": "monit", "legere": "lēct", "audire": "audīt"}

T: dict[tuple[str, str, str], dict[str, list[str]]] = {}

T[("active", "indicative", "present")] = {
    "amare": ["amō", "amā|s", "ama|t", "amā|mus", "amā|tis", "ama|nt"],
    "monere": ["mone|ō", "monē|s", "mone|t", "monē|mus", "monē|tis", "mone|nt"],
    "legere": ["leg|ō", "leg|is", "leg|it", "leg|imus", "leg|itis", "leg|unt"],
    "audire": ["audi|ō", "audī|s", "audi|t", "audī|mus", "audī|tis", "audi|unt"],
    "esse": ["s|um", "es", "es|t", "s|umus", "es|tis", "s|unt"],
}
T[("active", "indicative", "imperfect")] = {
    v: _alt(s, ACT, A_LONG) for v, s in
    {"amare": "amā|ba", "monere": "monē|ba", "legere": "leg|ēba", "audire": "audi|ēba", "esse": "era"}.items()}
T[("active", "indicative", "future")] = {
    "amare": ["amā|b|" + e for e in ["ō", "is", "it", "imus", "itis", "unt"]],
    "monere": ["monē|b|" + e for e in ["ō", "is", "it", "imus", "itis", "unt"]],
    "legere": ["leg|a|m", "leg|ē|s", "leg|e|t", "leg|ē|mus", "leg|ē|tis", "leg|e|nt"],
    "audire": ["audi|a|m", "audi|ē|s", "audi|e|t", "audi|ē|mus", "audi|ē|tis", "audi|e|nt"],
    "esse": ["er|" + e for e in ["ō", "is", "it", "imus", "itis", "unt"]],
}
T[("active", "indicative", "perfect")] = {
    v: [s + "|" + e for e in ["ī", "istī", "it", "imus", "istis", "ērunt"]] for v, s in PERFECT.items()}
T[("active", "indicative", "pluperfect")] = {v: _alt(s + "|era", ACT, A_LONG) for v, s in PERFECT.items()}
T[("active", "indicative", "future perfect")] = {
    v: [s + "|er|ō"] + [s + "|eri|" + e for e in ACT[1:]] for v, s in PERFECT.items()}

T[("active", "subjunctive", "present")] = {
    v: _alt(s, ACT, A_LONG) for v, s in
    {"amare": "am|e", "monere": "mone|a", "legere": "leg|a", "audire": "audi|a", "esse": "s|i"}.items()}
T[("active", "subjunctive", "imperfect")] = {
    v: _alt(s, ACT, A_LONG) for v, s in
    {"amare": "amā|re", "monere": "monē|re", "legere": "leg|ere", "audire": "audī|re", "esse": "es|se"}.items()}
T[("active", "subjunctive", "perfect")] = {v: [s + "|eri|" + e for e in ACT] for v, s in PERFECT.items()}
T[("active", "subjunctive", "pluperfect")] = {v: _alt(s + "|isse", ACT, A_LONG) for v, s in PERFECT.items()}

T[("passive", "indicative", "present")] = {
    "amare": ["am|or", "amā|ris", "amā|tur", "amā|mur", "amā|minī", "ama|ntur"],
    "monere": ["mone|or", "monē|ris", "monē|tur", "monē|mur", "monē|minī", "mone|ntur"],
    "legere": ["leg|or", "leg|eris", "leg|itur", "leg|imur", "leg|iminī", "leg|untur"],
    "audire": ["audi|or", "audī|ris", "audī|tur", "audī|mur", "audī|minī", "audi|untur"],
}
T[("passive", "indicative", "imperfect")] = {
    v: _alt(s, PAS, P_LONG) for v, s in
    {"amare": "amā|ba", "monere": "monē|ba", "legere": "leg|ēba", "audire": "audi|ēba"}.items()}
T[("passive", "indicative", "future")] = {
    "amare": ["amā|b|" + e for e in ["or", "eris", "itur", "imur", "iminī", "untur"]],
    "monere": ["monē|b|" + e for e in ["or", "eris", "itur", "imur", "iminī", "untur"]],
    "legere": ["leg|a|r", "leg|ē|ris", "leg|ē|tur", "leg|ē|mur", "leg|ē|minī", "leg|e|ntur"],
    "audire": ["audi|a|r", "audi|ē|ris", "audi|ē|tur", "audi|ē|mur", "audi|ē|minī", "audi|e|ntur"],
}
T[("passive", "subjunctive", "present")] = {
    v: _alt(s, PAS, P_LONG) for v, s in
    {"amare": "am|e", "monere": "mone|a", "legere": "leg|a", "audire": "audi|a"}.items()}
T[("passive", "subjunctive", "imperfect")] = {
    v: _alt(s, PAS, P_LONG) for v, s in
    {"amare": "amā|re", "monere": "monē|re", "legere": "leg|ere", "audire": "audī|re"}.items()}


def _compound(aux: list[str]) -> dict[str, list[str]]:
    """Perfect passive system: participle + a form of esse."""
    return {v: [f"{s}|us {aux[0]}", f"{s}|us {aux[1]}", f"{s}|us {aux[2]}",
                f"{s}|ī {aux[3]}", f"{s}|ī {aux[4]}", f"{s}|ī {aux[5]}"] for v, s in SUPINE.items()}


T[("passive", "indicative", "perfect")] = _compound(["sum", "es", "est", "sumus", "estis", "sunt"])
T[("passive", "indicative", "pluperfect")] = _compound(["eram", "erās", "erat", "erāmus", "erātis", "erant"])
T[("passive", "indicative", "future perfect")] = _compound(["erō", "eris", "erit", "erimus", "eritis", "erunt"])
T[("passive", "subjunctive", "perfect")] = _compound(["sim", "sīs", "sit", "sīmus", "sītis", "sint"])
T[("passive", "subjunctive", "pluperfect")] = _compound(["essem", "essēs", "esset", "essēmus", "essētis", "essent"])

TENSE_LABELS = {"present": "praesēns", "imperfect": "imperfectum", "future": "futūrum", "perfect": "perfectum",
                "pluperfect": "plūsquamperfectum", "future perfect": "futūrum perfectum"}
MOOD_LABELS = {"indicative": "Indicātīvus", "subjunctive": "Coniūnctīvus", "imperative": "Imperātīvus",
               "infinitive": "Īnfīnītīvus", "participle": "Participium"}
VOICE_LABELS = {"active": "[A] Āctīvum", "passive": "[B] Passīvum"}

# Non-finite forms: (voice, kind, tense) -> one form per verb.
NONFINITE = {
    ("active", "infinitive", "present"): ["amā|re", "monē|re", "leg|ere", "audī|re", "es|se"],
    ("active", "infinitive", "perfect"): ["amāv|isse", "monu|isse", "lēg|isse", "audīv|isse", "fu|isse"],
    ("active", "infinitive", "future"): ["amāt|ūr|um esse", "monit|ūr|um esse", "lēct|ūr|um esse",
                                         "audīt|ūr|um esse", "fut|ūr|um esse"],
    ("passive", "infinitive", "present"): ["amā|rī", "monē|rī", "leg|ī", "audī|rī", "—"],
    ("passive", "infinitive", "perfect"): ["amāt|um esse", "monit|um esse", "lēct|um esse", "audīt|um esse", "—"],
    ("passive", "infinitive", "future"): ["amātum īrī", "monitum īrī", "lēctum īrī", "audītum īrī", "—"],
    ("active", "participle", "present"): ["amā|ns -ant|is", "monē|ns -ent|is", "leg|ēns -ent|is",
                                          "audi|ēns -ent|is", "—"],
    ("active", "participle", "future"): ["amāt|ūr|us", "monit|ūr|us", "lēct|ūr|us", "audīt|ūr|us", "fut|ūr|us"],
    ("passive", "participle", "perfect"): ["amāt|us", "monit|us", "lēct|us", "audīt|us", "—"],
    ("passive", "gerundive", ""): ["ama|nd|us", "mone|nd|us", "leg|end|us", "audi|end|us", "—"],
    ("active", "supine", ""): ["amāt|um -ū", "monit|um -ū", "lēct|um -ū", "audīt|um -ū", "—"],
    ("active", "imperative", "singular"): ["amā", "monē", "leg|e", "audī", "es"],
    ("active", "imperative", "plural"): ["amā|te", "monē|te", "leg|ite", "audī|te", "es|te"],
}
NONFINITE_LABELS = {
    ("active", "infinitive", "present"): "Īnfīnītīvus praes",
    ("active", "infinitive", "perfect"): "Īnfīnītīvus perf",
    ("active", "infinitive", "future"): "Īnfīnītīvus fut",
    ("passive", "infinitive", "present"): "Īnfīnītīvus praes (pass)",
    ("passive", "infinitive", "perfect"): "Īnfīnītīvus perf (pass)",
    ("passive", "infinitive", "future"): "Īnfīnītīvus fut (pass)",
    ("active", "participle", "present"): "Participium praes",
    ("active", "participle", "future"): "Participium fut",
    ("passive", "participle", "perfect"): "Participium perf",
    ("passive", "gerundive", ""): "Gerundīvum",
    ("active", "supine", ""): "Supīna",
    ("active", "imperative", "singular"): "Imperātīvus sing",
    ("active", "imperative", "plural"): "Imperātīvus plūr",
}

PRONOMINAL_ADJECTIVES = {"nullus", "ullus", "unus", "solus", "totus", "alius", "alter", "uter", "neuter",
                         "uterque", "ipse", "iste"}


def plain(form: str) -> str:
    return form.replace("|", "")
