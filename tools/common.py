"""Shared helpers for the build tools (not needed at run time)."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "build" / "cache"
DATA = ROOT / "lang_gram" / "data"

USER_AGENT = "lang-gram-builder/0.1 (desktop grammar reader; python-requests)"

_session = requests.Session()
_session.headers["User-Agent"] = USER_AGENT


def get(url: str, *, params=None, data=None, pause: float = 1.0, timeout: int = 300):
    """GET/POST with polite pacing and back-off on 429/5xx."""
    last = None
    for attempt in range(8):
        try:
            if data is None:
                last = _session.get(url, params=params, timeout=timeout)
            else:
                last = _session.post(url, data=data, timeout=timeout)
        except requests.RequestException as exc:  # network hiccup
            print(f"  ! {exc!r}; retrying", file=sys.stderr)
            time.sleep(5 + 5 * attempt)
            continue
        if last.status_code == 200:
            time.sleep(pause)
            return last
        wait = float(last.headers.get("retry-after") or 5) + 3 * attempt
        print(f"  ! HTTP {last.status_code}; waiting {wait:.0f}s", file=sys.stderr)
        time.sleep(wait)
    raise RuntimeError(f"request failed: {url} ({last.status_code if last is not None else '?'})")


def mediawiki(lang: str, site: str = "wikisource", **params) -> dict:
    params.setdefault("format", "json")
    return get(f"https://{lang}.{site}.org/w/api.php", params=params).json()


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, obj, *, indent=None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=indent), encoding="utf-8")
