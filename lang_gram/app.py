"""The desktop application: a reader in the middle, the library on the left and
the grammar of the clicked word on the right."""
from __future__ import annotations

import bisect
import sys
from html import escape

from PyQt6.QtCore import QSettings, Qt, QUrl, pyqtSignal
from PyQt6.QtGui import (QAction, QActionGroup, QColor, QDesktopServices, QFont, QKeySequence,
                         QTextBlockFormat, QTextCharFormat, QTextCursor)
from PyQt6.QtWidgets import (QApplication, QComboBox, QDockWidget, QLabel, QMainWindow, QMessageBox,
                             QSizePolicy, QSplitter, QTabWidget, QTextBrowser, QTextEdit, QToolBar,
                             QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget)

from . import __version__, lang_la, theme
from .appearance import MODES as THEME_MODES
from .appearance import ThemeManager
from .analysis import analyse
from .library import Library, Token
from .morph import LANGS

READER_FONTS = ["Gentium Plus", "Charis SIL", "Noto Serif", "Source Serif 4", "DejaVu Serif", "Cambria",
                "Georgia", "Times New Roman", "serif"]
COLOUR_MODES = [("plain", "Plain text"), ("pos", "Colour by part of speech"), ("case", "Colour by case")]


class Reader(QTextEdit):
    """Shows one section of a text; every word can be clicked."""

    tokenClicked = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setMouseTracking(True)
        self.viewport().setMouseTracking(True)
        self.setFrameShape(QTextEdit.Shape.NoFrame)
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.section = None
        self.mode = "plain"
        self.colours = theme.LIGHT
        self.dark = False
        self._starts: list[int] = []          # document position where each paragraph begins
        self._paragraphs = []
        self._press = None
        self.current: Token | None = None

    # -- building the page ----------------------------------------------------
    def show_section(self, section, mode: str | None = None):
        self.section = section
        if mode:
            self.mode = mode
        self.current = None
        self._starts, self._paragraphs = [], []
        doc = self.document()
        doc.clear()
        doc.setDocumentMargin(28)
        cursor = QTextCursor(doc)
        base = QTextCharFormat()
        base.setForeground(QColor(self.colours["text"]))

        title_block = QTextBlockFormat()
        title_block.setBottomMargin(4)
        title_fmt = QTextCharFormat(base)
        title_fmt.setFontPointSize(self.font().pointSizeF() * 1.35)
        title_fmt.setFontWeight(QFont.Weight.DemiBold)
        title_fmt.setForeground(QColor(self.colours["accent"]))
        cursor.setBlockFormat(title_block)
        cursor.insertText(section.label, title_fmt)
        if section.subtitle:
            sub_block = QTextBlockFormat()
            sub_block.setBottomMargin(6)
            sub_fmt = QTextCharFormat(base)
            sub_fmt.setFontItalic(True)
            sub_fmt.setForeground(QColor(self.colours["muted"]))
            cursor.insertBlock(sub_block)
            cursor.insertText(section.subtitle, sub_fmt)

        body = QTextBlockFormat()
        body.setLineHeight(150, 1)                      # proportional
        body.setTopMargin(10)
        verse = QTextBlockFormat(body)
        verse.setLeftMargin(36)
        for para in section.paragraphs:
            is_verse = "\n" in para.text
            cursor.insertBlock(verse if is_verse else body)
            self._starts.append(cursor.position())
            self._paragraphs.append(para)
            cursor.insertText(para.text.replace("\n", " "), base)
        self._colourise()
        self.setExtraSelections([])
        self.moveCursor(QTextCursor.MoveOperation.Start)

    def _colourise(self):
        if self.mode == "plain":
            return
        palette = (theme.POS_COLOURS if self.mode == "pos" else theme.CASE_COLOURS)["dark" if self.dark else "light"]
        cursor = QTextCursor(self.document())
        cursor.beginEditBlock()
        for start, para in zip(self._starts, self._paragraphs):
            for sent in para.sentences:
                for tok in sent.tokens:
                    if not tok.is_word:
                        continue
                    key = tok.upos if self.mode == "pos" else tok.cats.get("case")
                    if self.mode == "pos" and key == "DET":
                        key = "PRON"
                    colour = palette.get(key)
                    if not colour:
                        continue
                    fmt = QTextCharFormat()
                    fmt.setForeground(QColor(colour))
                    cursor.setPosition(start + tok.start)
                    cursor.setPosition(start + tok.end, QTextCursor.MoveMode.KeepAnchor)
                    cursor.mergeCharFormat(fmt)
        cursor.endEditBlock()

    # -- positions --------------------------------------------------------------
    def _paragraph_at(self, position: int):
        i = bisect.bisect_right(self._starts, position) - 1
        if i < 0:
            return None, 0
        para = self._paragraphs[i]
        offset = position - self._starts[i]
        if offset > len(para.text):
            return None, 0
        return para, offset

    def shows(self, token: Token) -> bool:
        return any(p is token.sentence.paragraph for p in self._paragraphs)

    def _position_of(self, token: Token) -> int:
        i = next(n for n, p in enumerate(self._paragraphs) if p is token.sentence.paragraph)
        return self._starts[i]

    def token_at(self, point) -> Token | None:
        cursor = self.cursorForPosition(point)
        position = cursor.position()
        for candidate in (position, position - 1):
            para, offset = self._paragraph_at(candidate)
            if para is None:
                continue
            token = para.token_at(offset)
            if token is None:
                continue
            # cursorForPosition snaps to the nearest character: make sure the pointer
            # really is over the word.
            start = self._position_of(token)
            c = QTextCursor(self.document())
            c.setPosition(start + token.start)
            left = self.cursorRect(c)
            c.setPosition(start + token.end)
            right = self.cursorRect(c)
            if left.top() - 2 <= point.y() <= left.bottom() + 2 and left.left() - 3 <= point.x() <= (
                    right.right() + 3 if right.top() == left.top() else self.viewport().width()):
                return token
        return None

    # -- interaction -----------------------------------------------------------
    def mousePressEvent(self, event):
        self._press = event.position().toPoint()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        point = event.position().toPoint()
        if event.button() != Qt.MouseButton.LeftButton or self._press is None:
            return
        if (point - self._press).manhattanLength() > 8:
            return                                   # a drag: the user is selecting text
        token = self.token_at(point) or self.token_at(self._press)
        if token is not None:
            cursor = self.textCursor()
            if cursor.hasSelection():                # the pointer slipped over a letter or two
                cursor.clearSelection()
                self.setTextCursor(cursor)
            self.tokenClicked.emit(token)

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        if event.buttons() == Qt.MouseButton.NoButton:
            over = self.token_at(event.position().toPoint()) is not None
            self.viewport().setCursor(Qt.CursorShape.PointingHandCursor if over else Qt.CursorShape.IBeamCursor)

    def select(self, token: Token, head: Token | None = None, children=()):
        """Highlight a word, the word it depends on and the words depending on it."""
        self.current = token
        selections = []

        def mark(tok, colour, whole_sentence=False):
            start = self._position_of(tok)
            sel = QTextEdit.ExtraSelection()
            sel.cursor = QTextCursor(self.document())
            a, b = tok.sentence.span if whole_sentence else (tok.start, tok.end)
            sel.cursor.setPosition(start + a)
            sel.cursor.setPosition(start + b, QTextCursor.MoveMode.KeepAnchor)
            sel.format.setBackground(QColor(colour))
            selections.append(sel)

        mark(token, self.colours["sentence"], whole_sentence=True)
        for child in children:
            if child.sentence is token.sentence and (child.start, child.end) != (token.start, token.end):
                mark(child, self.colours["child"])
        if head is not None and (head.start, head.end) != (token.start, token.end):
            mark(head, self.colours["head"])
        mark(token, self.colours["sel"])
        self.setExtraSelections(selections)
        # keep the word in view without jumping when it already is
        cursor = QTextCursor(self.document())
        cursor.setPosition(self._position_of(token) + token.start)
        rect = self.cursorRect(cursor)
        if rect.top() < 0 or rect.bottom() > self.viewport().height():
            self.setTextCursor(cursor)
            self.ensureCursorVisible()

    def neighbour(self, step: int) -> Token | None:
        words = [t for p in self._paragraphs for s in p.sentences for t in s.tokens if t.is_word]
        seen, unique = set(), []
        for t in words:                               # one stop per written word
            key = (id(t.sentence.paragraph), t.start, t.end)
            if key not in seen:
                seen.add(key)
                unique.append(t)
        if not unique:
            return None
        if self.current is None:
            return unique[0]
        cur = (id(self.current.sentence.paragraph), self.current.start, self.current.end)
        index = next((i for i, t in enumerate(unique)
                      if (id(t.sentence.paragraph), t.start, t.end) == cur), 0)
        return unique[max(0, min(len(unique) - 1, index + step))]


class Panel(QTextBrowser):
    """A rich-text pane whose links are handled by the main window."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setOpenLinks(False)
        self.setFrameShape(QTextBrowser.Shape.NoFrame)

    def show_html(self, body: str, css: str):
        self.setHtml(f"<html><head><style>{css}</style></head><body>{body}</body></html>")


class ReferenceWindow(QMainWindow):
    """Grammar tables of one language to browse on their own."""

    def __init__(self, library: Library, parent=None):
        super().__init__(parent)
        self.library = library
        self.lang = None
        self.css = ""
        self.resize(1100, 800)
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.currentItemChanged.connect(self._open)
        self.browser = Panel()
        self.browser.anchorClicked.connect(self._link)
        splitter = QSplitter()
        splitter.addWidget(self.tree)
        splitter.addWidget(self.browser)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([300, 800])
        self.setCentralWidget(splitter)

    def load(self, lang: str, css: str):
        self.css = css
        if lang == self.lang:
            return
        self.lang = lang
        self.setWindowTitle(f"{LANGS[lang]} grammar reference")
        self.tree.clear()
        if lang == "la":
            typed = QTreeWidgetItem(self.tree, ["Paradigms"])
            for title, html in lang_la.paradigm_reference():
                item = QTreeWidgetItem(typed, [title])
                item.setData(0, Qt.ItemDataRole.UserRole, ("html", html))
            ag = QTreeWidgetItem(self.tree, ["Allen & Greenough: topics"])
            for key, (title, numbers) in lang_la.TOPICS.items():
                item = QTreeWidgetItem(ag, [f"{title}  (§ {', '.join(map(str, numbers))})"])
                item.setData(0, Qt.ItemDataRole.UserRole, ("ag", numbers))
            sections = self.library.grammar("la", "allen_greenough").get("sections", {})
            every = QTreeWidgetItem(self.tree, ["Allen & Greenough: all sections"])
            numbers = sorted(int(n) for n in sections)
            for lo in range(1, 651, 25):
                chunk = [n for n in numbers if lo <= n < lo + 25]
                if not chunk:
                    continue
                node = QTreeWidgetItem(every, [f"§ {chunk[0]} – {chunk[-1]}"])
                for n in chunk:
                    first = sections[str(n)][0]
                    item = QTreeWidgetItem(node, [f"§ {n}  {first[:60]}"])
                    item.setData(0, Qt.ItemDataRole.UserRole, ("ag", [n]))
            typed.setExpanded(True)
        else:
            reference = self.library.grammar(lang, "reference")
            pages: dict[str, QTreeWidgetItem] = {}
            for chapter in reference.get("chapters", []):
                node = pages.get(chapter["page"])
                if node is None:
                    node = pages[chapter["page"]] = QTreeWidgetItem(self.tree, [chapter["page"]])
                item = QTreeWidgetItem(node, [chapter["path"]])
                item.setData(0, Qt.ItemDataRole.UserRole, ("chapter", chapter))
            for node in pages.values():
                node.setExpanded(True)
        first = self.tree.topLevelItem(0)
        if first is not None and first.childCount():
            self.tree.setCurrentItem(first.child(0))

    def restyle(self, css: str):
        self.css = css
        self._open(self.tree.currentItem())

    def _open(self, item, _previous=None):
        if item is None:
            return
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data:
            return
        kind, payload = data
        if kind == "html":
            body = payload
        elif kind == "ag":
            body = "".join(self._ag(n) for n in payload) + (
                '<p class="muted small">Allen and Greenough’s New Latin Grammar (1903). The text comes '
                'from a scan that lost most macrons and garbles some letters and tables.</p>')
        else:
            body = (f'<h2>{escape(payload["page"])} — {escape(payload["path"])}</h2>{payload["html"]}'
                    f'<p class="muted small">Source: <a href="{payload["url"]}">Wikipedia, '
                    f'{escape(payload["page"])}</a> (CC BY-SA 4.0).</p>')
        self.browser.show_html(body, self.css)

    def _ag(self, number: int) -> str:
        sections = self.library.grammar("la", "allen_greenough").get("sections", {})
        n = number
        while n > 0 and str(n) not in sections:
            n -= 1
        if n <= 0:
            return ""
        note = "" if n == number else f' <span class="muted small">(§ {number} runs on from § {n})</span>'
        return f"<h2>§ {number}{note}</h2>" + "".join(f"<p>{escape(p)}</p>" for p in sections[str(n)])

    def _link(self, url: QUrl):
        if url.scheme() in ("http", "https"):
            QDesktopServices.openUrl(url)

    def show_ag(self, numbers: list[int]):
        body = "".join(self._ag(n) for n in numbers)
        self.browser.show_html(body, self.css)

    def show_chapter(self, chapter_id: str):
        for chapter in self.library.grammar(self.lang, "reference").get("chapters", []):
            if chapter["id"] == chapter_id:
                self._open_chapter(chapter)
                return

    def _open_chapter(self, chapter):
        body = (f'<h2>{escape(chapter["page"])} — {escape(chapter["path"])}</h2>{chapter["html"]}'
                f'<p class="muted small">Source: <a href="{chapter["url"]}">Wikipedia, '
                f'{escape(chapter["page"])}</a> (CC BY-SA 4.0).</p>')
        self.browser.show_html(body, self.css)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.library = Library()
        self.settings = QSettings("lang-gram", "lang-gram")
        self.themes = ThemeManager(QApplication.instance(), self.settings.value("theme", "system"))
        self.themes.changed.connect(self._theme_changed)
        self.dark = self.themes.dark
        self.colours = theme.colours(self.dark)
        self.point_size = int(self.settings.value("point_size", 13))
        self.lang = None
        self.work = None
        self.section = None
        self.reference: ReferenceWindow | None = None
        self.setWindowTitle("Lang-Gram")
        self.resize(1500, 900)

        self.reader = Reader()
        self.reader.tokenClicked.connect(self.show_token)
        self.setCentralWidget(self.reader)

        # library dock -----------------------------------------------------------
        self.language_box = QComboBox()
        for code in self.library.languages:
            self.language_box.addItem(LANGS[code], code)
        self.language_box.currentIndexChanged.connect(self._language_chosen)
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.currentItemChanged.connect(self._tree_chosen)
        left = QWidget()
        layout = QVBoxLayout(left)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.addWidget(self.language_box)
        layout.addWidget(self.tree)
        docked = (QDockWidget.DockWidgetFeature.DockWidgetClosable
                  | QDockWidget.DockWidgetFeature.DockWidgetMovable)
        self.library_dock = QDockWidget("Library", self)
        self.library_dock.setObjectName("library")
        self.library_dock.setFeatures(docked)
        self.library_dock.setWidget(left)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.library_dock)

        # analysis dock ------------------------------------------------------------
        self.tabs = QTabWidget()
        self.word_panel, self.paradigm_panel, self.grammar_panel = Panel(), Panel(), Panel()
        for panel, name in ((self.word_panel, "Word"), (self.paradigm_panel, "Paradigm"),
                            (self.grammar_panel, "Grammar")):
            panel.anchorClicked.connect(self._panel_link)
            self.tabs.addTab(panel, name)
        self.tabs.setMinimumWidth(340)
        self.analysis_dock = QDockWidget("Grammar of the selected word", self)
        self.analysis_dock.setObjectName("analysis")
        self.analysis_dock.setFeatures(docked)
        self.analysis_dock.setWidget(self.tabs)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.analysis_dock)
        self.resizeDocks([self.library_dock, self.analysis_dock], [270, 520], Qt.Orientation.Horizontal)

        self._build_actions()
        self.source_label = QLabel()
        self.source_label.setOpenExternalLinks(True)
        self.statusBar().addPermanentWidget(self.source_label, 1)
        self._apply_fonts()

        geometry = self.settings.value("geometry")
        if geometry is not None:
            self.restoreGeometry(geometry)
        state = self.settings.value("state")
        if state is not None:
            self.restoreState(state)
        self.current_token: Token | None = None
        self._ensure_panel()
        self._restore_position()

    # -- menus and toolbar ---------------------------------------------------------
    def _build_actions(self):
        bar = QToolBar("Navigation")
        bar.setObjectName("navigation")
        bar.setMovable(False)
        self.addToolBar(bar)

        def action(text, slot, shortcut=None, tip=None):
            act = QAction(text, self)
            act.triggered.connect(slot)
            if shortcut:
                act.setShortcut(QKeySequence(shortcut))
            if tip:
                act.setToolTip(tip)
                act.setStatusTip(tip)
            return act

        self.prev_action = action("◀  Previous", lambda: self._step_section(-1), "Alt+Left", "Previous section")
        self.next_action = action("Next  ▶", lambda: self._step_section(1), "Alt+Right", "Next section")
        prev_word = action("Previous word", lambda: self._step_word(-1), "Left")
        next_word = action("Next word", lambda: self._step_word(1), "Right")
        head_word = action("Go to the word it depends on", self._go_head, "Up")
        zoom_in = action("Larger text", lambda: self._zoom(1), "Ctrl++")
        zoom_in.setShortcuts([QKeySequence("Ctrl++"), QKeySequence("Ctrl+=")])
        zoom_out = action("Smaller text", lambda: self._zoom(-1), "Ctrl+-")
        reference = action("Grammar reference", self.open_reference, "F2",
                           "Browse the grammar tables of this language")
        about = action("About and sources", self._about)
        quit_action = action("Quit", self.close, "Ctrl+Q")

        bar.addAction(self.prev_action)
        bar.addAction(self.next_action)
        bar.addSeparator()
        self.mode_box = QComboBox()
        for key, label in COLOUR_MODES:
            self.mode_box.addItem(label, key)
        self.mode_box.setCurrentIndex(max(0, self.mode_box.findData(self.settings.value("mode", "plain"))))
        self.mode_box.currentIndexChanged.connect(self._mode_chosen)
        bar.addWidget(self.mode_box)
        self.legend = QLabel()
        self.legend.setTextFormat(Qt.TextFormat.RichText)
        bar.addWidget(self.legend)
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        bar.addWidget(spacer)
        self.theme_box = QComboBox()
        self.theme_box.setToolTip("Light or dark appearance; “System theme” follows the desktop setting")
        for key, label in THEME_MODES:
            self.theme_box.addItem(label, key)
        self.theme_box.setCurrentIndex(max(0, self.theme_box.findData(self.themes.mode)))
        self.theme_box.currentIndexChanged.connect(self._theme_chosen)
        bar.addWidget(self.theme_box)
        bar.addSeparator()
        bar.addAction(zoom_out)
        bar.addAction(zoom_in)
        bar.addSeparator()
        bar.addAction(reference)

        menu = self.menuBar()
        file_menu = menu.addMenu("&File")
        file_menu.addAction(quit_action)
        go = menu.addMenu("&Go")
        for act in (self.prev_action, self.next_action, prev_word, next_word, head_word):
            go.addAction(act)
        view = menu.addMenu("&View")
        view.addAction(zoom_in)
        view.addAction(zoom_out)
        view.addSeparator()
        group = QActionGroup(self)
        for i, (key, label) in enumerate(COLOUR_MODES):
            act = QAction(label, self, checkable=True)
            act.setChecked(i == self.mode_box.currentIndex())
            act.triggered.connect(lambda _checked, n=i: self.mode_box.setCurrentIndex(n))
            group.addAction(act)
            view.addAction(act)
        self._mode_actions = group
        view.addSeparator()
        theme_menu = view.addMenu("Theme")
        self._theme_actions = QActionGroup(self)
        for i, (key, label) in enumerate(THEME_MODES):
            act = QAction(label, self, checkable=True)
            act.setChecked(i == self.theme_box.currentIndex())
            act.triggered.connect(lambda _checked, n=i: self.theme_box.setCurrentIndex(n))
            self._theme_actions.addAction(act)
            theme_menu.addAction(act)
        view.addSeparator()
        view.addAction(self.library_dock.toggleViewAction())
        view.addAction(self.analysis_dock.toggleViewAction())
        grammar = menu.addMenu("G&rammar")
        grammar.addAction(reference)
        help_menu = menu.addMenu("&Help")
        help_menu.addAction(about)
        # Word navigation keys must work while the reader has the focus.
        for act in (prev_word, next_word, head_word):
            act.setShortcutContext(Qt.ShortcutContext.WindowShortcut)
            self.addAction(act)

    def _apply_fonts(self):
        font = QFont()
        font.setFamilies(READER_FONTS)
        font.setPointSize(self.point_size)
        self.reader.setFont(font)
        self.reader.colours, self.reader.dark = self.colours, self.dark
        self.reader.setStyleSheet(f"QTextEdit {{ background: {self.colours['bg']}; }}")
        self.css = theme.html_css(self.colours, max(9, self.point_size - 2))
        for panel in (self.word_panel, self.paradigm_panel, self.grammar_panel):
            panel.setStyleSheet(f"QTextBrowser {{ background: {self.colours['panel']}; }}")
        self._update_legend()
        self._update_theme_label()

    def _update_theme_label(self):
        """Say in the switcher which look "System theme" currently resolves to."""
        box = getattr(self, "theme_box", None)
        if box is not None:
            box.setItemText(0, f"System theme ({'dark' if self.themes.system_dark() else 'light'})")

    def _update_legend(self):
        mode = self.mode_box.currentData()
        key = "dark" if self.dark else "light"
        if mode == "pos":
            items = [(label, theme.POS_COLOURS[key][tag]) for label, tag in theme.POS_LEGEND]
        elif mode == "case":
            names = {"la": ["nominative", "accusative", "genitive", "dative", "ablative", "vocative"],
                     "de": ["nominative", "accusative", "dative", "genitive"]}.get(
                self.lang, ["nominative", "genitive", "dative", "accusative", "vocative", "locative",
                            "instrumental"])
            items = [(n, theme.CASE_COLOURS[key][n]) for n in names]
        else:
            items = []
        self.legend.setText("&nbsp;&nbsp;" + " &nbsp;".join(
            f'<span style="color:{colour}">■ {escape(label)}</span>' for label, colour in items))

    # -- library ---------------------------------------------------------------------
    def _restore_position(self):
        lang = self.settings.value("lang", "la")
        index = self.language_box.findData(lang)
        self.language_box.blockSignals(True)
        self.language_box.setCurrentIndex(max(0, index))
        self.language_box.blockSignals(False)
        self._load_language(self.language_box.currentData(),
                            self.settings.value("work"), int(self.settings.value("section", 0)))

    def _language_chosen(self, _index):
        self._load_language(self.language_box.currentData())

    def _load_language(self, lang, work_id=None, section_index=0):
        if lang is None:
            self._welcome("No texts are installed. Run the tools in the tools folder to build the data.")
            return
        self.lang = lang
        self.tree.blockSignals(True)
        self.tree.clear()
        target = None
        for work in self.library.works(lang):
            top = QTreeWidgetItem(self.tree, [work.title])
            top.setToolTip(0, f"{work.author} ({work.year})\n{work.blurb}")
            top.setData(0, Qt.ItemDataRole.UserRole, work.sections[0])
            groups: dict[str, QTreeWidgetItem] = {}
            for section in work.sections:
                parent = top
                if section.group:
                    parent = groups.get(section.group)
                    if parent is None:
                        parent = groups[section.group] = QTreeWidgetItem(top, [section.group])
                        parent.setData(0, Qt.ItemDataRole.UserRole, section)
                label = section.title if not section.subtitle else f"{section.title}. {section.subtitle}"
                item = QTreeWidgetItem(parent, [label])
                item.setData(0, Qt.ItemDataRole.UserRole, section)
                item.setToolTip(0, label)
                if work.id == work_id and section.index == section_index:
                    target = item
            top.setExpanded(True)
            if target is None and (work_id is None or work.id == work_id):
                first = top.child(0)
                target = first.child(0) if first is not None and first.childCount() else first
        self.tree.blockSignals(False)
        self._update_legend()
        if target is not None:
            self.tree.setCurrentItem(target)
        if self.reference is not None and self.reference.isVisible():
            self.reference.load(lang, self.css)

    def _tree_chosen(self, item, _previous=None):
        if item is None:
            return
        section = item.data(0, Qt.ItemDataRole.UserRole)
        if section is not None:
            self.open_section(section)

    def open_section(self, section):
        self.section = section
        self.work = section.work
        self.current_token = None
        self.reader.show_section(section, self.mode_box.currentData())
        self.setWindowTitle(f"{self.work.title} — {section.label} — Lang-Gram")
        self._update_source_label()
        sections = self.work.sections
        self.prev_action.setEnabled(section.index > 0)
        self.next_action.setEnabled(section.index < len(sections) - 1)
        self._ensure_panel()
        self._welcome()
        self.settings.setValue("lang", self.lang)
        self.settings.setValue("work", self.work.id)
        self.settings.setValue("section", section.index)

    def _update_source_label(self):
        page = self.work.source_page(self.section) if self.section is not None else None
        if page:
            self.source_label.setText(
                f'{escape(self.work.author)}, <i>{escape(self.work.title)}</i> — text from '
                f'<a href="{page["url"]}" style="color:{self.colours["link"]}">'
                f'{escape(self.work.source.get("site", "Wikisource"))}</a>')

    def _welcome(self, message: str | None = None):
        work = self.work
        intro = message or "Click any word of the text."
        body = f"<h2>{escape(intro)}</h2>"
        if work is not None:
            body += (f"<p><b>{escape(work.title)}</b><br>{escape(work.author)} · {escape(work.year)}</p>"
                     f"<p>{escape(work.blurb)}</p>")
        c = self.colours
        body += (
            "<p>The panel then shows the dictionary form and meaning of the word, every grammatical "
            "category of the form, and what the word does in its sentence.</p>"
            '<table cellspacing="6"><tr>'
            f'<td style="background:{c["sel"]}">&nbsp;word&nbsp;</td><td>the word you clicked</td></tr><tr>'
            f'<td style="background:{c["head"]}">&nbsp;word&nbsp;</td><td>the word it depends on</td></tr><tr>'
            f'<td style="background:{c["child"]}">&nbsp;word&nbsp;</td><td>words that depend on it</td></tr><tr>'
            f'<td style="background:{c["sentence"]}">&nbsp;word&nbsp;</td><td>the rest of its sentence</td></tr>'
            "</table>"
            "<p class=\"muted\">← → move from word to word · ↑ jumps to the governing word · "
            "Alt+← / Alt+→ change section · F2 opens the grammar reference.</p>"
            "<p class=\"muted small\">The analysis is produced automatically (parser and dictionary); "
            "it is right most of the time, not always.</p>")
        self.word_panel.show_html(body, self.css)
        self.paradigm_panel.show_html('<p class="muted">The paradigm of the selected word appears here.</p>',
                                      self.css)
        self.grammar_panel.show_html('<p class="muted">Grammar sections on the selected word appear here.</p>',
                                     self.css)

    def _step_section(self, step: int):
        if self.section is None:
            return
        sections = self.work.sections
        index = self.section.index + step
        if 0 <= index < len(sections):
            self._select_tree_section(sections[index])

    def _select_tree_section(self, section):
        def walk(item):
            for i in range(item.childCount()):
                child = item.child(i)
                if child.childCount() == 0 and child.data(0, Qt.ItemDataRole.UserRole) is section:
                    return child
                found = walk(child)
                if found is not None:
                    return found
            return None

        found = walk(self.tree.invisibleRootItem())
        if found is not None:
            self.tree.setCurrentItem(found)
        else:
            self.open_section(section)

    # -- the selected word -------------------------------------------------------------
    def _ensure_panel(self):
        """Bring the grammar panel back if it was closed, undocked or squeezed away."""
        dock = self.analysis_dock
        if dock.isFloating():
            dock.setFloating(False)
        if self.dockWidgetArea(dock) == Qt.DockWidgetArea.NoDockWidgetArea:
            self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)
        if not dock.isVisible():
            dock.show()
        dock.raise_()                                 # in front, should it share a tabbed area
        if self.isVisible() and dock.width() < 300:
            self.resizeDocks([dock], [min(520, max(340, self.width() // 3))], Qt.Orientation.Horizontal)

    def show_token(self, token: Token):
        if not self.reader.shows(token):              # a word of a text that is no longer open
            return
        result = analyse(self.library, token)
        self.current_token = token
        self.current_analysis = result
        self._ensure_panel()
        self.reader.select(token, result.head, result.children)
        self.word_panel.show_html(result.word, self.css)
        self.paradigm_panel.show_html(result.paradigm, self.css)
        self.grammar_panel.show_html(result.grammar, self.css)

    def _step_word(self, step: int):
        token = self.reader.neighbour(step)
        if token is not None:
            self.show_token(token)

    def _go_head(self):
        token = getattr(self, "current_token", None)
        if token is not None and token.head_token is not None:
            self.show_token(token.head_token)

    def _panel_link(self, url: QUrl):
        scheme = url.scheme()
        target = url.toString()[len(scheme) + 1:]
        token = getattr(self, "current_token", None)
        if scheme == "tok" and token is not None:
            index = int(target)
            tokens = token.sentence.tokens
            if 0 <= index < len(tokens):
                self.show_token(tokens[index])
        elif scheme == "ag":
            self.tabs.setCurrentWidget(self.grammar_panel)
            self.grammar_panel.scrollToAnchor(target)
        elif scheme == "agfull":
            self.open_reference()
            self.reference.show_ag([int(target)])
        elif scheme == "ref":
            self.tabs.setCurrentWidget(self.grammar_panel)
            self.grammar_panel.scrollToAnchor(QUrl.fromPercentEncoding(target.encode()))
        elif scheme in ("http", "https"):
            QDesktopServices.openUrl(url)
        elif url.hasFragment() and not scheme:
            self.sender().scrollToAnchor(url.fragment())

    # -- view ----------------------------------------------------------------------------
    def _mode_chosen(self, index):
        self.settings.setValue("mode", self.mode_box.currentData())
        actions = self._mode_actions.actions()
        if 0 <= index < len(actions):
            actions[index].setChecked(True)
        self._update_legend()
        self._reload_reader()

    def _reload_reader(self):
        if self.section is None:
            return
        token = getattr(self, "current_token", None)
        self.reader.show_section(self.section, self.mode_box.currentData())
        if token is not None and token.sentence.paragraph.section is self.section:
            self.show_token(token)

    def _theme_chosen(self, index):
        mode = self.theme_box.itemData(index)
        self.settings.setValue("theme", mode)
        actions = self._theme_actions.actions()
        if 0 <= index < len(actions):
            actions[index].setChecked(True)
        self.themes.set_mode(mode)
        self._update_theme_label()

    def _theme_changed(self, dark: bool):
        """Light <-> dark: recolour the reader, the panels and the reference window."""
        self.dark = dark
        self.colours = theme.colours(dark)
        self._apply_fonts()
        self._update_source_label()
        self._reload_reader()
        if self.current_token is None and self.section is not None:
            self._welcome()
        if self.reference is not None:
            self.reference.restyle(self.css)

    def _zoom(self, step: int):
        self.point_size = max(8, min(30, self.point_size + step))
        self.settings.setValue("point_size", self.point_size)
        self._apply_fonts()
        self._reload_reader()
        if getattr(self, "current_token", None) is None:
            self._welcome()

    def open_reference(self):
        if self.reference is None:
            self.reference = ReferenceWindow(self.library, self)
        self.reference.load(self.lang, self.css)
        self.reference.show()
        self.reference.raise_()
        self.reference.activateWindow()

    def _about(self):
        works = "".join(
            f"<li><i>{escape(w.title)}</i>, {escape(w.author)} — {escape(w.source.get('site', ''))}</li>"
            for lang in self.library.languages for w in self.library.works(lang))
        QMessageBox.about(self, "About Lang-Gram", f"""
            <h3>Lang-Gram {__version__}</h3>
            <p>Read a classical text; click a word to see its grammar.</p>
            <p><b>Texts</b> (public domain, from Wikisource):</p><ul>{works}</ul>
            <p><b>Latin grammar</b>: Allen and Greenough’s New Latin Grammar, 1903.</p>
            <p><b>German, Czech and Polish grammar tables</b>: English Wikipedia, CC BY-SA 4.0.</p>
            <p><b>Dictionary forms and glosses</b>: English Wiktionary, CC BY-SA 4.0, via the kaikki.org
            extract.</p>
            <p><b>Analysis</b>: UDPipe 2 / LatinPipe models (Charles University, CC BY-NC-SA 4.0), checked
            against the Wiktionary inflection tables. It is automatic and can be wrong.</p>""")

    def closeEvent(self, event):
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("state", self.saveState())
        super().closeEvent(event)


def _report_error(kind, value, trace):
    """PyQt aborts the program on an uncaught exception; print it and carry on instead."""
    import traceback
    traceback.print_exception(kind, value, trace)


def main(argv=None) -> int:
    sys.excepthook = _report_error
    app = QApplication(sys.argv if argv is None else argv)
    app.setApplicationName("Lang-Gram")
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
