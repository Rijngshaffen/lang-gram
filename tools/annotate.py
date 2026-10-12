"""Tag, lemmatise and parse the raw texts with UDPipe 2 (LINDAT web service).

The texts are sent paragraph by paragraph (in batches) to the public UDPipe REST
service of Charles University; the CoNLL-U replies are cached under
build/cache/udpipe, so the service is contacted once per distinct batch.

Before parsing, a copy of each paragraph is normalised for the parser (macrons
removed, enclitic -que detached, 19th-century German spellings modernised ...).
Every character of the normalised copy remembers where it came from, so the
analysis is mapped back onto the untouched Wikisource text that the reader shows.

Output: build/parsed/<lang>/<work>.json
"""
from __future__ import annotations

import difflib
import hashlib
import re
import sys
import unicodedata

from common import CACHE, ROOT, get, read_json, write_json

RAW = ROOT / "build" / "raw"
PARSED = ROOT / "build" / "parsed"
UDPIPE = "https://lindat.mff.cuni.cz/services/udpipe/api/process"

MODELS = {
    "la": "latin-evalatin24-240520",
    "de": "german-hdt-ud-2.17-251125",
    "cs": "czech-pdtc-ud-2.17-251125",
    "pl": "polish-pdb-ud-2.17-251125",
}
# A second opinion, used only to fill in features the main model leaves out.
SECOND = {"de": "german-gsd-ud-2.17-251125"}

BATCH_CHARS = 12000


# --------------------------------------------------------------------------- #
# Normalisation with provenance
# --------------------------------------------------------------------------- #
class Mapped:
    """A string whose characters each know the offset they came from."""

    def __init__(self, text: str, src: list[int] | None = None):
        self.text = text
        self.src = list(range(len(text))) if src is None else src

    def sub(self, pattern: str, repl, flags=0) -> "Mapped":
        """Regex replace; characters of the replacement are aligned with the match."""
        out, src, pos = [], [], 0
        for m in re.finditer(pattern, self.text, flags):
            out.append(self.text[pos:m.start()])
            src.extend(self.src[pos:m.start()])
            old = m.group(0)
            new = repl(m) if callable(repl) else m.expand(repl)
            span = self.src[m.start():m.end()]
            out.append(new)
            if new == old:
                src.extend(span)
            else:
                last = span[0]
                for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, old, new, autojunk=False).get_opcodes():
                    if tag == "equal":
                        src.extend(span[i1:i2])
                        last = span[i2 - 1]
                    elif tag == "replace":
                        src.extend(span[min(i1 + k, i2 - 1)] for k in range(j2 - j1))
                        last = span[i2 - 1]
                    elif tag == "insert":
                        src.extend([last] * (j2 - j1))
            pos = m.end()
        out.append(self.text[pos:])
        src.extend(self.src[pos:])
        return Mapped("".join(out), src)

    def translate_chars(self, fn) -> "Mapped":
        out, src = [], []
        for ch, s in zip(self.text, self.src):
            new = fn(ch)
            out.append(new)
            src.extend([s] * len(new))
        return Mapped("".join(out), src)


def strip_marks(ch: str) -> str:
    """Remove macrons, breves, accents - Latin only."""
    base = "".join(c for c in unicodedata.normalize("NFD", ch) if not unicodedata.combining(c))
    return {"æ": "ae", "Æ": "Ae", "œ": "oe", "Œ": "Oe"}.get(base, base)


# Words in -que that are not "X + and".
QUE_WORDS = set("""
atque neque quoque itaque usque denique undique utique ubique namque quinque absque quandoque
plerumque plerique pleraeque pleraque plerosque plerasque plerisque plerorumque plerarumque pleramque
plerusque quisque quaeque quidque quodque cuiusque cuique quemque quamque quaque quique quosque quasque
quorumque quarumque quibusque uterque utraque utrumque utriusque utrique utroque utramque utrosque
utrasque utrorumque utrarumque utrisque utrimque utrobique undecumque ubicumque utcumque quotienscumque
quotiescumque usquequaque quousque adusque hucusque antique inique oblique aeque adaeque peraeque
simulatque torque relinque coque unusquisque uniuscuiusque unicuique unumquemque unaquaeque
unumquodque unumquidque unamquamque unoquoque susque deque abusque cumque
""".split())

PRAENOMINA = r"(?:A|Ap|App|C|Cn|D|K|L|M|Mam|N|P|Q|Ser|Sex|Sp|T|Ti|Tib)"


def split_que(m: re.Match) -> str:
    word = m.group(0)
    low = word.lower()
    if low in QUE_WORDS or low.endswith(("cumque", "cunque")) or len(low) < 5:
        return word
    return word[:-3] + " " + word[-3:]


# Spellings of older school editions (Lhomond) -> the classical ones of dictionaries.
LA_SPELLING = [
    (r"\bquum\b", "cum"), (r"coel", "cael"), (r"caeter", "ceter"), (r"nunci", "nunti"),
    (r"lacrym", "lacrim"), (r"sylv", "silv"), (r"foemin", "femin"), (r"foecund", "fecund"),
    (r"quatuor", "quattuor"), (r"moer", "maer"), (r"moest", "maest"), (r"poenit", "paenit"),
    (r"solemn", "sollemn"), (r"quotidi", "cotidi"), (r"\bimo\b", "immo"), (r"intellig", "intelleg"),
    (r"neglig", "negleg"), (r"\bliter", "litter"), (r"\bmillia", "milia"), (r"\bpene\b", "paene"),
    (r"obedi", "oboedi"), (r"\bhyem", "hiem"), (r"inclyt", "inclit"), (r"conditio", "condicio"),
    (r"\bconcio", "contio"), (r"\bcharit", "carit"), (r"\bnunquam\b", "numquam"),
    (r"\bquanquam\b", "quamquam"), (r"\btanquam\b", "tamquam"), (r"\bunquam\b", "umquam"),
    (r"\bquidquid\b", "quidquid"), (r"\bquandiu\b", "quamdiu"), (r"\bnequidquam\b", "nequiquam"),
    (r"\bseculum", "saeculum"), (r"\bsecul", "saecul"), (r"\bpraelium", "proelium"),
    (r"\bpraeli", "proeli"), (r"\bhaered", "hered"), (r"\bcoen", "cen"), (r"\bfoed(?=us|er)", "foed"),
    (r"\bmoen", "moen"), (r"\blethal", "letal"), (r"\bauctorit", "auctorit"),
]


def keep_case(new: str):
    def repl(m: re.Match) -> str:
        return new.capitalize() if m.group(0)[:1].isupper() else new
    return repl


def prepare_la(text: str) -> Mapped:
    t = Mapped(text).translate_chars(strip_marks)
    t = t.translate_chars(lambda c: {"j": "i", "J": "I"}.get(c, c))
    for pattern, new in LA_SPELLING:
        t = t.sub("(?i)" + pattern, keep_case(new))
    # "M. Messala", "legione XII." - the full stop is not a sentence end.
    t = t.sub(rf"\b({PRAENOMINA})\.(?=\s+[A-Z])", r"\1")
    t = t.sub(r"\b([IVXLCDM]{2,})\.(?=\s+[a-z])", r"\1")
    t = t.sub(r"\b[A-Za-z]+que\b", split_que)
    # Editorial brackets and quotation marks glued to a word confuse the tokeniser.
    t = t.sub(r"([\[(“„‘\"])(?=\w)", r"\1 ")
    t = t.sub(r"(?<=\w)([\])”’\"])", r" \1")
    return t


# Pre-1901 spellings in the Grimm text -> modern ones the tagger knows.
DE_KEEP_TH = re.compile(r"^(thron|theat|them|theo|apothek|kathol|method|sympath|biblioth|panther|äther|thermo|"
                        r"elisabeth|goethe|thomas|martha|bertha|ruth|judith|kathe)", re.I)


def de_th(m: re.Match) -> str:
    word = m.group(0)
    if DE_KEEP_TH.search(word):
        return word
    return re.sub(r"th", "t", re.sub(r"Th", "T", word))


DE_WORDS = {
    "gieng": "ging", "giengen": "gingen", "giengst": "gingst", "gienge": "ginge",
    "fieng": "fing", "fiengen": "fingen", "hieng": "hing", "hiengen": "hingen",
    "giebt": "gibt", "giebst": "gibst", "gieb": "gib", "seyn": "sein", "bey": "bei",
    "todt": "tot", "todte": "tote", "todten": "toten", "todter": "toter", "todtes": "totes",
    "brod": "Brot", "brot": "Brot", "wol": "wohl", "kömmt": "kommt", "kömmst": "kommst",
    "hülfe": "Hilfe", "ergötzen": "ergötzen",
}


def de_word(m: re.Match) -> str:
    word = m.group(0)
    low = word.lower()
    for old, new in DE_WORDS.items():
        if low == old or (low.endswith(old) and old in ("gieng", "giengen", "fieng", "fiengen", "hieng", "hiengen")):
            fixed = low[: len(low) - len(old)] + new.lower()
            return fixed.capitalize() if word[0].isupper() else fixed
    return word


def prepare_de(text: str) -> Mapped:
    # The HDT tokeniser only knows straight quotes; "stärken.“" would stay one token.
    t = Mapped(text).translate_chars(lambda c: {"„": '"', "“": '"', "”": '"', "»": '"', "«": '"',
                                                "‚": "'", "‘": "'", "’": "'"}.get(c, c))
    t = t.sub(r"\b\w*[Tt]h\w*\b", de_th)
    t = t.sub(r"\b\w+\b", de_word)
    return t


def prepare(lang: str, text: str) -> Mapped:
    text_for_parser = text.replace("\n", " ")
    if lang == "la":
        return prepare_la(text_for_parser)
    if lang == "de":
        return prepare_de(text_for_parser)
    if lang == "cs":
        return Mapped(text_for_parser).translate_chars(lambda c: "–" if c == "—" else c)
    return Mapped(text_for_parser)


# --------------------------------------------------------------------------- #
# UDPipe
# --------------------------------------------------------------------------- #
def udpipe(model: str, text: str) -> str:
    key = hashlib.sha1((model + "\0" + text).encode("utf-8")).hexdigest()
    cache = CACHE / "udpipe" / model / f"{key}.conllu"
    if cache.exists():
        return cache.read_text(encoding="utf-8")
    reply = get(UDPIPE, data={"model": model, "tokenizer": "ranges", "tagger": "", "parser": "", "data": text},
                pause=0.5)
    result = reply.json()["result"]
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(result, encoding="utf-8")
    return result


def read_conllu(conllu: str):
    """Yield sentences: lists of dicts with id, form, lemma, upos, feats, head, deprel, range."""
    sent, pending = [], None      # pending = (last_id, range) of an open multi-word token
    for line in conllu.splitlines():
        if not line.strip():
            if sent:
                yield sent
            sent, pending = [], None
            continue
        if line.startswith("#"):
            continue
        cols = line.split("\t")
        if len(cols) != 10 or "." in cols[0]:
            continue
        misc = dict(kv.split("=", 1) for kv in cols[9].split("|") if "=" in kv)
        rng = tuple(int(x) for x in misc["TokenRange"].split(":")) if "TokenRange" in misc else None
        if "-" in cols[0]:
            pending = (int(cols[0].split("-")[1]), rng)
            continue
        wid = int(cols[0])
        mwt = False
        if rng is None and pending and wid <= pending[0]:
            rng, mwt = pending[1], True
        sent.append({
            "id": wid, "form": cols[1], "lemma": cols[2], "upos": cols[3],
            "feats": "" if cols[5] == "_" else cols[5],
            "head": int(cols[6]) if cols[6].isdigit() else 0, "deprel": cols[7],
            "range": rng, "mwt": mwt,
        })
    if sent:
        yield sent


def annotate_paragraphs(lang: str, model: str, paragraphs: list[str]):
    """Return, for each paragraph, its sentences with offsets into the original text."""
    prepared = [prepare(lang, p) for p in paragraphs]
    results: list[list] = [[] for _ in paragraphs]
    start = 0
    while start < len(prepared):
        end, size = start, 0
        while end < len(prepared) and (end == start or size + len(prepared[end].text) < BATCH_CHARS):
            size += len(prepared[end].text) + 2
            end += 1
        offsets, pos = [], 0
        for p in prepared[start:end]:
            offsets.append(pos)
            pos += len(p.text) + 2
        batch = "\n\n".join(p.text for p in prepared[start:end])
        for sent in read_conllu(udpipe(model, batch)):
            first = next((w["range"] for w in sent if w["range"]), None)
            if first is None:
                continue
            k = max(i for i, off in enumerate(offsets) if off <= first[0])
            para = prepared[start + k]
            words = []
            for w in sent:
                if w["range"] is None:
                    continue
                a, b = w["range"][0] - offsets[k], w["range"][1] - offsets[k]
                if a < 0 or b > len(para.src) or a >= b:
                    continue
                w = dict(w, start=para.src[a], end=para.src[b - 1] + 1,
                         norm=w["form"] if w["mwt"] else para.text[a:b])
                del w["range"]
                words.append(w)
            if words:
                results[start + k].append(words)
        start = end
    return results


def main():
    only = set(sys.argv[1:])
    for path in sorted(RAW.glob("*/*.json")):
        doc = read_json(path)
        if only and doc["id"] not in only and doc["lang"] not in only:
            continue
        lang = doc["lang"]
        paragraphs = [p for s in doc["sections"] for p in s["paras"]]
        print(f"{doc['id']}: {len(paragraphs)} paragraphs with {MODELS[lang]}", flush=True)
        main_parse = annotate_paragraphs(lang, MODELS[lang], paragraphs)
        second = annotate_paragraphs(lang, SECOND[lang], paragraphs) if lang in SECOND else None
        it = iter(range(len(paragraphs)))
        n_words = 0
        for section in doc["sections"]:
            paras = []
            for text in section["paras"]:
                i = next(it)
                sents = main_parse[i]
                if second:
                    alt = {(w["start"], w["end"]): w for s in second[i] for w in s if not w["mwt"]}
                    for s in sents:
                        for w in s:
                            other = alt.get((w["start"], w["end"]))
                            if other and not w["mwt"]:
                                w["alt"] = [other["lemma"], other["upos"], other["feats"]]
                n_words += sum(len(s) for s in sents)
                paras.append({"text": text, "sents": sents})
            section["paras"] = paras
        write_json(PARSED / lang / f"{doc['id']}.json", doc)
        print(f"  {n_words} words", flush=True)


if __name__ == "__main__":
    main()
