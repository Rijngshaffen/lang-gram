"""Turn a dictionary entry's inflected forms into paradigm tables (HTML) and
mark the cells that the clicked word occupies."""
from __future__ import annotations

from html import escape

from .morph import CASE_ORDER, norm_form, spelling_variants, tags_to_cats

ARTICLES = {"der", "die", "das", "des", "dem", "den", "ein", "eine", "eines", "einem", "einen", "einer",
            "kein", "keine", "keines", "keinem", "keinen", "keiner", "am"}
PERSON_ROWS = [("1 sg", {"person": "first-person", "number": "singular"}),
               ("2 sg", {"person": "second-person", "number": "singular"}),
               ("3 sg", {"person": "third-person", "number": "singular"}),
               ("1 pl", {"person": "first-person", "number": "plural"}),
               ("2 pl", {"person": "second-person", "number": "plural"}),
               ("3 pl", {"person": "third-person", "number": "plural"})]
PRONOUN_ROWS = {
    "de": ["ich", "du", "er/sie/es", "wir", "ihr", "sie"],
    "cs": ["já", "ty", "on/ona/ono", "my", "vy", "oni"],
    "pl": ["ja", "ty", "on/ona/ono", "my", "wy", "oni/one"],
    "la": ["1 sg", "2 sg", "3 sg", "1 pl", "2 pl", "3 pl"],
}
MATCH_CATS = ("case", "number", "gender", "person", "tense", "mood", "voice", "degree", "inflection")


class Cell:
    __slots__ = ("form", "tags", "cats", "word", "used")

    def __init__(self, lang, form, tags):
        self.form = form
        self.tags = set(tags.split())
        self.cats = tags_to_cats(lang, self.tags)
        parts = form.split()
        if len(parts) > 1 and lang == "de" and all(p.lower() in ARTICLES for p in parts[:-1]):
            self.word = parts[-1]
        else:
            self.word = form if len(parts) == 1 else None
        self.used = False


def entry_cells(lang: str, entry: dict) -> list[Cell]:
    """The entry's table forms with a few known gaps in the tagging repaired."""
    cells = [Cell(lang, f, t) for f, t in entry["f"] if f and f != "-" and not f.startswith("-")]
    pos = entry["p"]
    if lang == "pl":
        if pos in ("adj", "pron", "det", "num") or (pos == "verb" and any("case" in c.cats for c in cells)):
            for c in cells:
                if "case" not in c.cats and "error-unrecognized-form" in c.tags:
                    c.cats["case"] = {"nominative", "vocative"}
                if c.cats.get("number") == {"plural"} and "animacy" not in c.cats:
                    c.cats["animacy"] = {"nonpersonal"}
        if pos == "verb":
            # 1st and 2nd person carry no person tag: they come first and second.
            seen: dict[tuple, int] = {}
            for c in cells:
                if "multiword-construction" in c.tags or " " in c.form:
                    continue
                if "person" in c.cats or "impersonal" in c.tags or "participle" in c.tags \
                        or c.cats.get("verbform", {"finite"}) != {"finite"} and "verbform" in c.cats:
                    continue
                if not ({"present", "past", "future", "imperative", "conditional"} & c.tags):
                    continue
                key = (tuple(sorted(c.tags)),)
                n = seen.get(key, 0)
                seen[key] = n + 1
                if "imperative" in c.tags:
                    c.cats["person"] = {"first-person"} if "plural" in c.tags and n == 0 else {"second-person"}
                else:
                    c.cats["person"] = {"first-person"} if n == 0 else {"second-person"}
                c.cats["verbform"] = {"finite"}
    if lang == "de" and pos == "adj":
        # Positive, comparative and superlative tables follow one another untagged;
        # each begins with the predicative forms.
        block, last_pred = -1, False
        for c in cells:
            pred = "predicative" in c.tags
            if pred and not last_pred:
                block += 1
            last_pred = pred
            degree = ("positive", "comparative", "superlative")[min(max(block, 0), 2)]
            c.cats["degree"] = {degree}
            c.tags.add(degree)
    if lang == "cs" and pos != "verb" and any("gender" in c.cats for c in cells):
        extra = []
        for c in cells:
            if "case" not in c.cats:
                continue
            if "number" not in c.cats:
                c.cats["number"] = {"plural"}
            if "gender" not in c.cats and c.cats.get("animacy"):
                c.cats["gender"] = {"masculine"}
        plural = [c for c in cells if c.cats.get("number") == {"plural"} and "case" in c.cats]
        for case in ("nominative", "accusative", "vocative"):
            row = [c for c in plural if case in c.cats["case"]]
            fem = [c for c in row if c.cats.get("gender") == {"feminine"}]
            for anim in ("inanimate", "animate"):
                have = any("masculine" in c.cats.get("gender", ()) and
                           anim in c.cats.get("animacy", {anim}) for c in row)
                if not have and fem and not (anim == "animate" and case != "accusative"):
                    for f in fem:
                        twin = Cell(lang, f.form, " ".join(f.tags))
                        twin.cats = dict(f.cats, gender={"masculine"}, animacy={anim})
                        extra.append(twin)
        cells += extra
    if lang == "cs" and pos == "verb":
        for c in cells:
            if "error-unrecognized-form" in c.tags and c.word:
                if c.word.startswith("bud"):
                    c.cats["tense"], c.cats["mood"] = {"future"}, {"indicative"}
                elif c.word.startswith("by"):
                    c.cats["mood"] = {"conditional"}
                    c.cats.pop("tense", None)
                c.cats["verbform"] = {"finite"}
    return cells


def _fits(cell: Cell, want: dict) -> bool:
    for name, value in want.items():
        have = cell.cats.get(name)
        if value is None:
            if have:
                return False
        elif isinstance(value, (set, frozenset, tuple, list)):
            if not have or not (have & set(value)):
                return False
        elif not have or value not in have:
            return False
    return True


class Highlighter:
    """Decides which cells show the clicked word."""

    def __init__(self, lang, token=None, extra=None):
        self.lang = lang
        self.keys = set()
        self.cats = {}
        if token is not None:
            keys = [norm_form(lang, token.form)]
            if token.norm and not token.is_mwt_part:
                keys.append(norm_form(lang, token.norm))
            for k in list(keys):
                keys += spelling_variants(lang, k)
            self.keys = set(keys)
            self.cats = dict(token.cats, **(extra or {}))
        self.strong_found = False

    def match(self, cell: Cell) -> str:
        if not self.keys or not cell.word or norm_form(self.lang, cell.word) not in self.keys:
            return ""
        for name in MATCH_CATS:
            want, have = self.cats.get(name), cell.cats.get(name)
            if want and have and want not in have:
                # "superlative" in a comparative table etc. never matches; gender of a
                # noun table is not marked, so only compare what both sides state.
                return "same"
        self.strong_found = True
        return "hit"


def _cell_html(cells: list[Cell], hl: Highlighter) -> tuple[str, str]:
    if not cells:
        return "", ""
    seen, parts, cls = [], [], ""
    for c in cells:
        c.used = True
        if c.form in seen:
            m = hl.match(c)
        else:
            seen.append(c.form)
            m = hl.match(c)
            parts.append(escape(c.form))
        if m == "hit" or (m == "same" and cls != "hit"):
            cls = m
    return "<br>".join(parts[:4]), cls


def grid(title: str, columns: list[tuple[str, dict]], rows: list[tuple[str, dict]], cells: list[Cell],
         hl: Highlighter, base: dict | None = None, corner: str = "") -> str:
    """A table whose cell (row, column) lists the forms fitting row + column + base."""
    base = base or {}
    pool = [c for c in cells if _fits(c, base)]
    body, any_form = [], False
    for label, want_row in rows:
        tds, row_has = [], False
        for _, want_col in columns:
            found = [c for c in pool if _fits(c, want_row) and _fits(c, want_col)]
            text, cls = _cell_html(found, hl)
            row_has = row_has or bool(text)
            tds.append(f'<td class="{cls}">{text or "&nbsp;"}</td>' if cls else f"<td>{text or '&nbsp;'}</td>")
        if row_has:
            any_form = True
            body.append(f"<tr><th>{escape(label)}</th>{''.join(tds)}</tr>")
    if not any_form:
        return ""
    head = "".join(f"<th>{escape(lbl)}</th>" for lbl, _ in columns)
    cap = f"<h3>{escape(title)}</h3>" if title else ""
    return f'{cap}<table class="grid" cellspacing="0"><tr><th>{escape(corner)}</th>{head}</tr>{"".join(body)}</table>'


def listing(title: str, items: list[tuple[str, list[Cell]]], hl: Highlighter) -> str:
    rows = []
    for label, found in items:
        text, cls = _cell_html(found, hl)
        if text:
            rows.append(f'<tr><th>{escape(label)}</th><td class="{cls}">{text}</td></tr>')
    if not rows:
        return ""
    cap = f"<h3>{escape(title)}</h3>" if title else ""
    return f'{cap}<table class="grid" cellspacing="0">{"".join(rows)}</table>'


# --------------------------------------------------------------------------- #
# Layouts
# --------------------------------------------------------------------------- #
def _case_rows(lang, cells):
    present = {c for cell in cells for c in cell.cats.get("case", ())}
    return [(case, {"case": case}) for case in CASE_ORDER[lang] if case in present]


def noun_tables(lang, cells, hl):
    numbers = [n for n in ("singular", "dual", "plural") if any(n in c.cats.get("number", ()) for c in cells)]
    cols = [(n, {"number": n}) for n in numbers] or [("", {})]
    return [grid("", cols, _case_rows(lang, cells), cells, hl)]


def gendered_tables(lang, cells, hl, title=""):
    """Adjectives, participles, pronouns and determiners that distinguish gender."""
    out = []
    rows = _case_rows(lang, cells)
    if lang == "de":
        cols = [("masculine", {"gender": "masculine", "number": "singular"}),
                ("feminine", {"gender": "feminine", "number": "singular"}),
                ("neuter", {"gender": "neuter", "number": "singular"}), ("plural", {"number": "plural"})]
        kinds = [k for k in ("strong", "weak", "mixed") if any(k in c.cats.get("inflection", ()) for c in cells)]
        names = {"strong": "Strong declension (no article)", "weak": "Weak declension (after der, dieser …)",
                 "mixed": "Mixed declension (after ein, kein, mein …)"}
        if kinds:
            for k in kinds:
                out.append(grid(names[k], cols, rows, cells, hl, {"inflection": k}))
        else:
            out.append(grid(title, cols, rows, cells, hl))
        return out
    if lang == "la":
        for number in ("singular", "plural"):
            cols = [(g, {"gender": g}) for g in ("masculine", "feminine", "neuter")]
            out.append(grid(number, cols, rows, cells, hl, {"number": number}))
        return out
    if lang == "cs":
        sg = [("masc. animate", {"gender": "masculine", "_anim": "animate"}),
              ("masc. inanimate", {"gender": "masculine", "_anim": "inanimate"}),
              ("feminine", {"gender": "feminine"}), ("neuter", {"gender": "neuter"})]
        return [_cs_grid(number, sg, rows, cells, hl, number) for number in ("singular", "plural")]
    if lang == "pl":
        cols = [("masculine", {"gender": "masculine", "number": "singular"}),
                ("feminine", {"gender": "feminine", "number": "singular"}),
                ("neuter", {"gender": "neuter", "number": "singular"}),
                ("pl. masc. personal", {"number": "plural", "animacy": "personal"}),
                ("pl. other", {"number": "plural", "animacy": "nonpersonal"})]
        return [grid(title, cols, rows, cells, hl)]
    return []


def _cs_grid(title, cols, rows, cells, hl, number):
    """Czech: a form without an animacy tag serves both masculine columns."""
    pool = [c for c in cells if number in c.cats.get("number", ())]
    body = []
    for label, want_row in rows:
        tds, has = [], False
        for _, want in cols:
            anim = want.get("_anim")
            plain = {k: v for k, v in want.items() if k != "_anim"}
            found = [c for c in pool if _fits(c, want_row)
                     and (not c.cats.get("gender") or _fits(c, plain))
                     and (anim is None or not c.cats.get("animacy") or anim in c.cats["animacy"])]
            text, cls = _cell_html(found, hl)
            has = has or bool(text)
            tds.append(f'<td class="{cls}">{text or "&nbsp;"}</td>')
        if has:
            body.append(f"<tr><th>{escape(label)}</th>{''.join(tds)}</tr>")
    if not body:
        return ""
    head = "".join(f"<th>{escape(lbl)}</th>" for lbl, _ in cols)
    return (f'<h3>{escape(title)}</h3><table class="grid" cellspacing="0"><tr><th></th>{head}</tr>'
            f'{"".join(body)}</table>')


def verb_tables(lang, cells, hl):
    out = []
    rows = [(PRONOUN_ROWS[lang][i], want) for i, (_, want) in enumerate(PERSON_ROWS)]
    simple = [c for c in cells if "multiword-construction" not in c.tags and c.word]
    if lang == "la":
        fin = [c for c in cells if "finite" in c.cats.get("verbform", ()) or "person" in c.cats]
        ind = [("present", "present"), ("imperfect", "imperfect"), ("future", "future"), ("perfect", "perfect"),
               ("pluperfect", "pluperfect"), ("future perfect", "future perfect")]
        sub = [t for t in ind if t[0] not in ("future", "future perfect")]
        voices = [v for v in ("active", "passive") if any(v in c.cats.get("voice", ()) for c in fin)]
        for voice in voices:
            out.append(grid(f"Indicative {voice}", [(lbl, {"tense": t}) for lbl, t in ind], rows, fin, hl,
                            {"mood": "indicative", "voice": voice}))
            out.append(grid(f"Subjunctive {voice}", [(lbl, {"tense": t}) for lbl, t in sub], rows, fin, hl,
                            {"mood": "subjunctive", "voice": voice}))
        out.append(grid("Imperative", [(f"{t} {v}", {"tense": t, "voice": v}) for t in ("present", "future")
                                       for v in voices], rows, fin, hl, {"mood": "imperative"}))
        nonfin = [c for c in cells if "person" not in c.cats]
        items = []
        for label, want in [
            ("infinitive, present active", {"verbform": "infinitive", "tense": "present", "voice": "active"}),
            ("infinitive, present passive", {"verbform": "infinitive", "tense": "present", "voice": "passive"}),
            ("infinitive, perfect active", {"verbform": "infinitive", "tense": "perfect", "voice": "active"}),
            ("infinitive, perfect passive", {"verbform": "infinitive", "tense": "perfect", "voice": "passive"}),
            ("infinitive, future active", {"verbform": "infinitive", "tense": "future", "voice": "active"}),
            ("infinitive, future passive", {"verbform": "infinitive", "tense": "future", "voice": "passive"}),
            ("participle, present active", {"verbform": "participle", "tense": "present", "voice": "active"}),
            ("participle, perfect passive", {"verbform": "participle", "tense": "perfect", "voice": "passive"}),
            ("participle, perfect (deponent)", {"verbform": "participle", "tense": "perfect", "voice": "active"}),
            ("participle, future active", {"verbform": "participle", "tense": "future", "voice": "active"}),
            ("gerundive", {"verbform": "participle", "tense": "future", "voice": "passive"}),
        ]:
            items.append((label, [c for c in nonfin if _fits(c, want)]))
        for case in ("genitive", "dative", "accusative", "ablative"):
            items.append((f"gerund, {case}", [c for c in nonfin if "gerund" in c.tags and case in c.tags]))
        for case in ("accusative", "ablative"):
            items.append((f"supine, {case}", [c for c in nonfin if "supine" in c.tags and case in c.tags]))
        out.append(listing("Infinitives, participles, gerund, supine", items, hl))
    elif lang == "de":
        fin = [c for c in simple if "person" in c.cats]
        cols = [("present", {"tense": "present", "mood": "indicative"}),
                ("preterite", {"tense": "past", "mood": "indicative"}),
                ("subjunctive I", {"tense": "present", "mood": "subjunctive"}),
                ("subjunctive II", {"tense": "past", "mood": "subjunctive"})]
        out.append(grid("Simple tenses", cols, rows, fin, hl))
        out.append(listing("Other forms", [
            ("infinitive", [c for c in simple if c.tags == {"infinitive"}]),
            ("zu-infinitive", [c for c in cells if "infinitive-zu" in c.tags]),
            ("present participle", [c for c in simple if {"participle", "present"} <= c.tags]),
            ("past participle", [c for c in simple if {"participle", "past"} <= c.tags]),
            ("imperative (du)", [c for c in simple if {"imperative", "singular"} <= c.tags]),
            ("imperative (ihr)", [c for c in simple if {"imperative", "plural"} <= c.tags]),
        ], hl))
        aux = [c.form for c in cells if "multiword-construction" in c.tags and "perfect" in c.tags
               and "indicative" in c.tags and {"third-person", "singular"} <= c.tags]
        if aux:
            out.append(f'<p class="muted small">Perfect: {escape(aux[0])} · the other compound tenses are '
                       f'built with haben/sein and werden.</p>')
    elif lang == "cs":
        fin = [c for c in simple if "person" in c.cats]
        cols = [("present", {"tense": "present", "mood": "indicative"}), ("future", {"tense": "future"}),
                ("imperative", {"mood": "imperative"}), ("conditional auxiliary", {"mood": "conditional"})]
        out.append(grid("Finite forms", cols, rows, fin, hl))
        part = [c for c in simple if "participle" in c.tags and "adjectival" not in c.tags]
        pcols = [("masc. animate", {"gender": "masculine", "animacy": "animate"}),
                 ("masc. inanimate", {"gender": "masculine", "animacy": "inanimate"}),
                 ("feminine", {"gender": "feminine"}), ("neuter", {"gender": "neuter"})]
        prow = [("singular", {"number": "singular"}), ("plural", {"number": "plural"})]
        out.append(grid("Past participle (l-form): with jsem, jsi … it makes the past tense", pcols, prow,
                        [c for c in part if "past" in c.tags], hl))
        out.append(grid("Passive participle", pcols, prow, [c for c in part if "passive" in c.tags], hl))
        out.append(listing("Other forms", [
            ("infinitive", [c for c in simple if "infinitive" in c.tags]),
            ("verbal noun", [c for c in simple if "noun-from-verb" in c.tags]),
            ("active participle (adj.)", [c for c in simple if {"adjectival", "active"} <= c.tags]),
            ("passive participle (adj.)", [c for c in simple if {"adjectival", "passive"} <= c.tags]),
            ("present transgressive", [c for c in simple if {"transgressive", "present"} <= c.tags]),
            ("past transgressive", [c for c in simple if {"transgressive", "past"} <= c.tags]),
        ], hl))
    elif lang == "pl":
        fin = [c for c in simple if "person" in c.cats]
        cols = [("present", {"tense": "present"}), ("future (simple)", {"tense": "future"}),
                ("imperative", {"mood": "imperative"})]
        out.append(grid("Present / future and imperative", cols, rows,
                        [c for c in fin if "past" not in c.tags and "conditional" not in c.tags], hl))
        gcols = [("masculine", {"gender": "masculine"}), ("feminine", {"gender": "feminine"}),
                 ("neuter", {"gender": "neuter"}), ("pl. masc. personal", {"animacy": "personal"}),
                 ("pl. other", {"animacy": "nonpersonal"})]
        persons = [("1st person", {"person": "first-person"}), ("2nd person", {"person": "second-person"}),
                   ("3rd person", {"person": "third-person"})]
        past = [c for c in fin if "past" in c.tags and "conditional" not in c.tags]
        for c in past + [c for c in fin if "conditional" in c.tags]:
            if c.cats.get("number") == {"plural"} and "animacy" not in c.cats:
                c.cats["animacy"] = {"nonpersonal"}
        out.append(grid("Past tense", gcols, persons, past, hl))
        out.append(grid("Conditional", gcols, persons, [c for c in fin if "conditional" in c.tags], hl))
        out.append(listing("Other forms", [
            ("infinitive", [c for c in simple if "infinitive" in c.tags]),
            ("impersonal past", [c for c in simple if {"impersonal", "past"} <= c.tags]),
            ("active participle", [c for c in simple if {"participle", "active", "masculine", "singular"} <= c.tags]),
            ("passive participle", [c for c in simple if {"participle", "passive", "masculine", "singular"} <= c.tags]),
            ("adverbial participle", [c for c in simple if "contemporary" in c.tags or "anterior" in c.tags]),
            ("verbal noun", [c for c in simple if "noun-from-verb" in c.tags]),
        ], hl))
    return out


def leftovers(cells, hl, limit=60) -> str:
    rest = [c for c in cells if not c.used and c.word and "multiword-construction" not in c.tags]
    if not rest:
        return ""
    rows, seen = [], set()
    for c in rest:
        key = (c.form, tuple(sorted(c.tags)))
        if key in seen:
            continue
        seen.add(key)
        cls = hl.match(c)
        tags = " ".join(t for t in sorted(c.tags) if not t.startswith("error"))
        rows.append(f'<tr><td class="{cls}">{escape(c.form)}</td><td class="muted">{escape(tags)}</td></tr>')
        if len(rows) >= limit:
            break
    return f'<h3>Other forms</h3><table class="grid" cellspacing="0">{"".join(rows)}</table>'


def entry_paradigm(lang: str, entry: dict, token=None, extra=None) -> tuple[str, bool]:
    """HTML tables for an entry; the flag tells whether the word was found in them.

    *extra* adds categories the token's own features lack (German adjective declension type).
    """
    cells = entry_cells(lang, entry)
    if not cells:
        return "", False
    hl = Highlighter(lang, token, extra)
    pos = entry["p"]
    has_case = any("case" in c.cats for c in cells)
    has_gender = any("gender" in c.cats or "animacy" in c.cats for c in cells if "case" in c.cats)
    has_person = any("person" in c.cats for c in cells)
    if lang == "de" and has_case and pos == "adj":
        degree = (token.cats.get("degree") if token is not None else None) or "positive"
        cells = [c for c in cells if degree in c.tags] or cells
    if pos == "verb" and has_person:
        tables = verb_tables(lang, cells, hl)
    elif has_case and has_gender and pos not in ("noun", "name"):
        tables = gendered_tables(lang, cells, hl)
    elif has_case:
        tables = noun_tables(lang, cells, hl)
    else:
        tables = []
    html = "".join(t for t in tables if t)
    html += leftovers(cells, hl) if html else leftovers(cells, hl, limit=120)
    found = hl.strong_found or any(hl.match(c) for c in cells)
    return html, found
