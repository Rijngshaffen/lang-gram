"""Rebuild every bundled data file from scratch (needs the network on first run).

    python tools/build_all.py            # all languages
    python tools/build_all.py la         # one language

Steps: texts from Wikisource -> UDPipe analysis -> Wiktionary entries ->
final texts and lexicons -> Allen & Greenough sections -> Wikipedia grammar tables.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
LANGS = [a for a in sys.argv[1:] if a in ("la", "de", "cs", "pl")]


def run(script: str, *args: str) -> None:
    print(f"\n== {script} {' '.join(args)}", flush=True)
    subprocess.run([sys.executable, str(TOOLS / script), *args], check=True)


def main() -> None:
    run("fetch_texts.py")
    run("annotate.py", *LANGS)
    run("build_lexicon.py", *LANGS)
    run("build_data.py", *LANGS)
    if not LANGS or "la" in LANGS:
        run("build_grammar.py")
    run("build_reference.py", *[lang for lang in LANGS if lang != "la"])


if __name__ == "__main__":
    main()
