"""Read-only access to the bundled texts, lexicons and grammar data."""
from __future__ import annotations

import gzip
import json
from functools import cached_property
from pathlib import Path

from .morph import LANGS, norm_form, parse_feats, spelling_variants, ud_to_cats

PACKAGE = Path(__file__).resolve().parent
DATA = PACKAGE / "data"


def _load(path: Path):
    if path.suffix == ".gz":
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            return json.load(fh)
    return json.loads(path.read_text(encoding="utf-8"))


class Token:
    """One syntactic word of a sentence, with its place in the paragraph text."""

    __slots__ = ("sentence", "index", "start", "end", "lemma", "upos", "feats_str", "head", "deprel",
                 "lex", "flags", "norm", "_feats", "_cats")

    def __init__(self, sentence, index, raw):
        self.sentence = sentence
        self.index = index                      # 0-based position in the sentence
        (self.start, self.end, self.lemma, self.upos, self.feats_str, self.head, self.deprel,
         self.lex, self.flags) = raw[:9]
        # Form the analysis was made on when it is not the written one: the part of a
        # contraction (im -> in, dem) or a modernised spelling (Thür -> Tür).
        self.norm = raw[9] if len(raw) > 9 else None
        self._feats = None
        self._cats = None

    # -- text ---------------------------------------------------------------
    @property
    def text(self) -> str:
        return self.sentence.paragraph.text[self.start:self.end]

    @property
    def lang(self) -> str:
        return self.sentence.paragraph.section.work.lang

    @property
    def form(self) -> str:
        """The word as analysed: the written form, or its part of a contraction."""
        return self.norm if (self.norm and "m" in self.flags) else self.text

    @property
    def key(self) -> str:
        return norm_form(self.lang, self.norm or self.text)

    @property
    def is_word(self) -> bool:
        return self.upos != "PUNCT" and any(ch.isalnum() for ch in self.text)

    # -- grammar ------------------------------------------------------------
    @property
    def feats(self) -> dict:
        if self._feats is None:
            self._feats = parse_feats(self.feats_str)
        return self._feats

    @property
    def cats(self) -> dict:
        if self._cats is None:
            self._cats = ud_to_cats(self.lang, self.upos, self.feats)
        return self._cats

    @property
    def head_token(self):
        return self.sentence.tokens[self.head - 1] if self.head else None

    @property
    def children(self) -> list:
        return [t for t in self.sentence.tokens if t.head == self.index + 1]

    def child(self, *deprels, upos=None):
        for t in self.children:
            if t.deprel in deprels or t.deprel.split(":")[0] in deprels:
                if upos is None or t.upos == upos:
                    return t
        return None

    @property
    def is_mwt_part(self) -> bool:
        return "m" in self.flags

    def siblings_in_token(self) -> list:
        """All words written together as one token (im = in + dem)."""
        return [t for t in self.sentence.tokens if (t.start, t.end) == (self.start, self.end)]

    def __repr__(self):
        return f"<Token {self.text!r} {self.lemma} {self.upos} {self.feats_str} {self.deprel}>"


class Sentence:
    __slots__ = ("paragraph", "tokens")

    def __init__(self, paragraph, raw):
        self.paragraph = paragraph
        self.tokens = [Token(self, i, r) for i, r in enumerate(raw)]

    @property
    def span(self):
        return (self.tokens[0].start, self.tokens[-1].end) if self.tokens else (0, 0)

    @property
    def text(self) -> str:
        a, b = self.span
        return self.paragraph.text[a:b]


class Paragraph:
    __slots__ = ("section", "text", "sentences")

    def __init__(self, section, raw):
        self.section = section
        self.text = raw["text"]
        self.sentences = [Sentence(self, s) for s in raw["sents"]]

    def token_at(self, offset: int):
        """The word covering a character offset of the paragraph, if any."""
        for sent in self.sentences:
            a, b = sent.span
            if a <= offset < b:
                hit = [t for t in sent.tokens if t.start <= offset < t.end and t.is_word]
                return hit[0] if hit else None
        return None


class Section:
    def __init__(self, work, index, raw):
        self.work = work
        self.index = index
        self.group = raw.get("group")
        self.title = raw["title"]
        self.subtitle = raw.get("subtitle")
        self._raw = raw["paras"]

    @cached_property
    def paragraphs(self) -> list[Paragraph]:
        return [Paragraph(self, p) for p in self._raw]

    @property
    def label(self) -> str:
        return f"{self.group} · {self.title}" if self.group else self.title


class Work:
    def __init__(self, path: Path):
        self.path = path
        raw = _load(path)
        self.id = raw["id"]
        self.lang = raw["lang"]
        self.title = raw["title"]
        self.author = raw["author"]
        self.year = raw.get("year", "")
        self.blurb = raw.get("blurb", "")
        self.source = raw.get("source", {})
        self.sections = [Section(self, i, s) for i, s in enumerate(raw["sections"])]

    def source_page(self, section: Section) -> dict | None:
        pages = self.source.get("pages") or []
        if not pages:
            return None
        if section.group:
            for p in pages:
                if p["title"].endswith(section.group):
                    return p
        if len(pages) == len(self.sections):
            return pages[section.index]
        return pages[0]


class Lexicon:
    """Dictionary entries (from Wiktionary) for the words of one language."""

    def __init__(self, lang: str):
        self.lang = lang
        path = DATA / "lexicon" / f"{lang}.json.gz"
        raw = _load(path) if path.exists() else {"entries": [], "source": ""}
        self.entries = raw["entries"]
        self.source = raw.get("source", "")
        self._by_key = None

    def get(self, i: int):
        return self.entries[i] if 0 <= i < len(self.entries) else None

    def find(self, word: str, pos: str | None = None) -> list[dict]:
        if self._by_key is None:
            self._by_key = {}
            for e in self.entries:
                self._by_key.setdefault(e["k"], []).append(e)
        hits = self._by_key.get(norm_form(self.lang, word), [])
        return [e for e in hits if pos is None or e["p"] == pos]

    def bases(self, entry: dict) -> list[tuple[dict, str]]:
        return [(self.entries[j], kind) for j, kind in entry.get("of", [])]


class Library:
    def __init__(self):
        self._works: dict[str, list[Work]] = {}
        self._lexicons: dict[str, Lexicon] = {}
        self._grammar: dict[tuple[str, str], dict] = {}

    @property
    def languages(self) -> list[str]:
        return [code for code in LANGS if (DATA / "texts" / code).is_dir()]

    def works(self, lang: str) -> list[Work]:
        if lang not in self._works:
            folder = DATA / "texts" / lang
            self._works[lang] = [Work(p) for p in sorted(folder.glob("*.json.gz"))] if folder.is_dir() else []
        return self._works[lang]

    def lexicon(self, lang: str) -> Lexicon:
        if lang not in self._lexicons:
            self._lexicons[lang] = Lexicon(lang)
        return self._lexicons[lang]

    def grammar(self, lang: str, name: str) -> dict:
        """A JSON document from data/grammar/<lang>/<name>.json ({} when absent)."""
        key = (lang, name)
        if key not in self._grammar:
            path = DATA / "grammar" / lang / f"{name}.json"
            self._grammar[key] = _load(path) if path.exists() else {}
        return self._grammar[key]


def form_keys(lang: str, text: str) -> list[str]:
    """Look-up keys for a written form: itself, then modernised spellings."""
    key = norm_form(lang, text)
    return [key] + spelling_variants(lang, key)
