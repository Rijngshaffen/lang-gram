"""Colours and style sheets of the light and the dark theme."""
from __future__ import annotations

LIGHT = {
    "bg": "#fbfaf7", "panel": "#ffffff", "text": "#1f2328", "muted": "#6b7280", "rule": "#d9d6ce",
    "accent": "#b4541a", "link": "#1d5fa8",
    "sel": "#ffd76a", "head": "#bcd9ff", "child": "#cdeecb", "sentence": "#f3efe4",
    "hit": "#ffd76a", "same": "#fff1c4", "th": "#f1eee6", "ending": "#b4541a", "note": "#f6f3ea",
    "warn": "#8a5a00",
}
DARK = {
    "bg": "#1e1f22", "panel": "#26282c", "text": "#e6e6e6", "muted": "#9aa0a6", "rule": "#3c3f45",
    "accent": "#f0a060", "link": "#7db7ff",
    "sel": "#7a5c00", "head": "#1f4b7a", "child": "#2c5a33", "sentence": "#2a2b30",
    "hit": "#7a5c00", "same": "#4a4020", "th": "#303338", "ending": "#f0a060", "note": "#2c2e33",
    "warn": "#e0b060",
}

# Colours of the ordinary widgets (menus, lists, tabs ...) as QPalette roles; used
# when Qt's own palette does not already match the wanted theme.
WIDGETS_LIGHT = {
    "Window": "#f0efec", "WindowText": "#1f2328", "Base": "#ffffff", "AlternateBase": "#f5f4f0",
    "Text": "#1f2328", "Button": "#eceae6", "ButtonText": "#1f2328", "BrightText": "#ffffff",
    "ToolTipBase": "#fffbe6", "ToolTipText": "#1f2328", "PlaceholderText": "#8a8f98",
    "Highlight": "#2f7fd6", "HighlightedText": "#ffffff", "Link": "#1d5fa8", "LinkVisited": "#6a3fb5",
    "Light": "#ffffff", "Midlight": "#f6f5f2", "Mid": "#c2c0ba", "Dark": "#a3a19b", "Shadow": "#6f6d68",
    "Accent": "#2f7fd6",
    "DisabledText": "#9aa0a6", "DisabledWindowText": "#9aa0a6", "DisabledButtonText": "#9aa0a6",
    "DisabledHighlight": "#c9c7c1", "DisabledHighlightedText": "#6b7280",
}
WIDGETS_DARK = {
    "Window": "#2b2d31", "WindowText": "#e6e6e6", "Base": "#1e1f22", "AlternateBase": "#26282c",
    "Text": "#e6e6e6", "Button": "#35383d", "ButtonText": "#e6e6e6", "BrightText": "#ffffff",
    "ToolTipBase": "#35383d", "ToolTipText": "#e6e6e6", "PlaceholderText": "#8b9098",
    "Highlight": "#2f65ca", "HighlightedText": "#ffffff", "Link": "#7db7ff", "LinkVisited": "#b9a0f5",
    "Light": "#4a4e55", "Midlight": "#3c3f45", "Mid": "#2f3136", "Dark": "#1b1c1f", "Shadow": "#0e0f10",
    "Accent": "#2f65ca",
    "DisabledText": "#7a7f87", "DisabledWindowText": "#7a7f87", "DisabledButtonText": "#7a7f87",
    "DisabledHighlight": "#3c3f45", "DisabledHighlightedText": "#9aa0a6",
}

# Text colours for the "colour by ..." reading modes.
POS_COLOURS = {
    "light": {"NOUN": "#1d5fa8", "PROPN": "#1d5fa8", "VERB": "#b3261e", "AUX": "#b3261e", "ADJ": "#1b7f3b",
              "ADV": "#8a5a00", "PRON": "#6a3fb5", "DET": "#6a3fb5", "ADP": "#00707a", "NUM": "#1b7f3b",
              "CCONJ": "#6b7280", "SCONJ": "#a0307a", "PART": "#6b7280", "INTJ": "#6b7280"},
    "dark": {"NOUN": "#7db7ff", "PROPN": "#7db7ff", "VERB": "#ff8a80", "AUX": "#ff8a80", "ADJ": "#7fd69a",
             "ADV": "#e0b060", "PRON": "#b9a0f5", "DET": "#b9a0f5", "ADP": "#5fd0da", "NUM": "#7fd69a",
             "CCONJ": "#9aa0a6", "SCONJ": "#f08ac8", "PART": "#9aa0a6", "INTJ": "#9aa0a6"},
}
CASE_COLOURS = {
    "light": {"nominative": "#1d5fa8", "accusative": "#b3261e", "genitive": "#1b7f3b", "dative": "#8a5a00",
              "ablative": "#6a3fb5", "vocative": "#a0307a", "locative": "#00707a", "instrumental": "#6a3fb5"},
    "dark": {"nominative": "#7db7ff", "accusative": "#ff8a80", "genitive": "#7fd69a", "dative": "#e0b060",
             "ablative": "#b9a0f5", "vocative": "#f08ac8", "locative": "#5fd0da", "instrumental": "#b9a0f5"},
}
POS_LEGEND = [("noun", "NOUN"), ("verb", "VERB"), ("adjective / numeral", "ADJ"), ("adverb", "ADV"),
              ("pronoun / determiner", "PRON"), ("preposition", "ADP"), ("subordinator", "SCONJ")]


def is_dark(palette) -> bool:
    return palette.window().color().lightness() < 128


def colours(dark: bool) -> dict:
    return DARK if dark else LIGHT


def html_css(c: dict, base_pt: int = 11) -> str:
    """Style sheet for the rich-text panels (Qt's HTML subset)."""
    return f"""
    body {{ color: {c['text']}; font-size: {base_pt}pt; }}
    h1 {{ font-size: {base_pt + 9}pt; font-weight: 600; margin: 0 0 2px 0; }}
    h2 {{ font-size: {base_pt + 2}pt; color: {c['accent']}; margin: 14px 0 4px 0; }}
    h3 {{ font-size: {base_pt + 1}pt; margin: 10px 0 2px 0; }}
    p {{ margin: 4px 0; }}
    a {{ color: {c['link']}; text-decoration: none; }}
    .muted {{ color: {c['muted']}; }}
    .small {{ font-size: {base_pt - 1}pt; }}
    .lemma {{ font-size: {base_pt + 3}pt; font-weight: 600; }}
    .gloss {{ font-style: italic; }}
    .tag {{ color: {c['accent']}; font-weight: 600; }}
    .warn {{ color: {c['warn']}; }}
    .end {{ color: {c['ending']}; font-weight: 600; }}
    .sep {{ color: {c['rule']}; }}
    table.grid {{ border-collapse: collapse; margin: 4px 0 8px 0; }}
    table.grid td, table.grid th {{ border: 1px solid {c['rule']}; padding: 2px 7px; white-space: nowrap; }}
    table.grid td.wrap {{ white-space: normal; }}
    table.grid th {{ background-color: {c['th']}; font-weight: 600; text-align: left; }}
    td.hit {{ background-color: {c['hit']}; font-weight: 700; }}
    td.same {{ background-color: {c['same']}; }}
    td.model {{ background-color: {c['note']}; }}
    td.note {{ background-color: {c['note']}; padding: 6px 9px; }}
    """
