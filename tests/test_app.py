"""Smoke tests: the bundled data loads, every kind of word can be analysed and
the window reacts to clicks and keys.  Run with:  python -m pytest  (or python tests/test_app.py)
"""
import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lang_gram import lang_la, latin_paradigms              # noqa: E402
from lang_gram.analysis import analyse                      # noqa: E402
from lang_gram.library import Library                       # noqa: E402
from lang_gram.paradigm import entry_paradigm               # noqa: E402

LIB = Library()


def find(lang, work, section, word, nth=0):
    sec = LIB.works(lang)[work].sections[section]
    hits = [t for p in sec.paragraphs for s in p.sentences for t in s.tokens if t.text == word]
    return hits[nth]


def test_all_languages_have_texts_and_lexicon():
    assert LIB.languages == ["la", "de", "cs", "pl"]
    titles = {w.title for lang in LIB.languages for w in LIB.works(lang)}
    assert {"Commentarii de Bello Gallico", "Epitome Historiae Sacrae"} <= titles
    for lang in LIB.languages:
        assert LIB.works(lang) and len(LIB.lexicon(lang).entries) > 500
        for work in LIB.works(lang):
            assert work.source["site"].endswith("wikisource.org")


def test_token_offsets_point_at_words():
    for lang in LIB.languages:
        section = LIB.works(lang)[0].sections[0]
        for para in section.paragraphs:
            for sent in para.sentences:
                for tok in sent.tokens:
                    assert 0 <= tok.start < tok.end <= len(para.text)
                    assert 0 <= tok.head <= len(sent.tokens)
                    assert para.token_at(tok.start) is not None or not tok.is_word


def test_latin_model_paradigms():
    plain = latin_paradigms.plain
    assert [plain(latin_paradigms.NOUNS["res"][2][("singular", c)]) for c in latin_paradigms.CASES] == \
        ["rēs", "rem", "reī", "reī", "rē"]
    assert plain(latin_paradigms.T[("active", "subjunctive", "imperfect")]["legere"][5]) == "legerent"
    assert plain(latin_paradigms.T[("passive", "indicative", "future")]["audire"][1]) == "audiēris"
    assert latin_paradigms.T[("passive", "indicative", "perfect")]["amare"][3] == "amāt|ī sumus"
    assert len(lang_la.paradigm_reference()) == 6


def test_latin_ablative_absolute_and_grammar_references():
    tok = find("la", 0, 2, "occupātō")                # ... et regno occupato ...
    result = analyse(LIB, tok)
    assert "ablative absolute" in result.word
    assert "419" in result.grammar                    # Allen & Greenough § 419
    assert "Model paradigm" in result.paradigm
    assert "scan" not in result.paradigm.lower()


def test_latin_subjunctive_after_persuadere():
    tok = find("la", 0, 1, "exīrent")
    assert tok.cats["mood"] == "subjunctive" and tok.cats["tense"] == "imperfect"
    html = analyse(LIB, tok).word
    assert "object clause" in html and "563" in html


def test_latin_paradigm_marks_the_clicked_form():
    tok = find("la", 0, 0, "partēs")
    entry = LIB.lexicon("la").get(tok.lex)
    assert entry["w"] == "pars"
    html, found = entry_paradigm("la", entry, tok)
    assert found and 'class="hit">partēs' in html
    model = lang_la.model_paradigm(tok, entry)
    assert "Dēclīnātiō III" in model and 'class="hit"' in model


def test_paradigm_tab_names_the_declension_or_conjugation():
    def top(lang, work, section, word):
        html = analyse(LIB, find(lang, work, section, word)).paradigm
        assert html.startswith(("<h2>Declension type</h2>", "<h2>Conjugation type</h2>")), html[:80]
        return html.split("<h2>")[1]

    assert "Third declension" in top("la", 0, 0, "partēs") and "mōns" in top("la", 0, 0, "partēs")
    assert "Fifth declension" in top("la", 0, 2, "rēbus")
    assert "Fourth declension" in top("la", 0, 2, "senātū") and "senātūs" in top("la", 0, 2, "senātū")
    assert "Second conjugation" in top("la", 0, 2, "persuādet")
    assert "-iō type" in top("la", 0, 2, "suscipit")
    # a participle: the conjugation of its verb, and how the participle itself declines
    occupato = top("la", 0, 2, "occupātō")
    assert "First conjugation" in occupato and "occupāre" in occupato and "magnus" in occupato
    assert "Deponent" in top("la", 0, 2, "proficīscendum")
    assert "Mixed adjective declension" in top("de", 0, 0, "kleine")
    assert "Strong declension" in top("de", 0, 0, "Kinde") and "Kinder" in top("de", 0, 0, "Kinde")
    assert "Strong verb" in top("de", 0, 0, "ansah") and "sieht an" in top("de", 0, 0, "ansah")
    assert "soft type" in top("cs", 0, 0, "králi") and "muž" in top("cs", 0, 0, "králi")
    assert "Class IV" in top("cs", 0, 0, "naučil")
    assert "Feminine in -a" in top("pl", 0, 2, "głowami") and "hard consonant" in top("pl", 0, 2, "głowami")
    assert "Conjugation II" in top("pl", 0, 2, "kręciły")
    # words that do not inflect get no such heading
    assert "type</h2>" not in analyse(LIB, find("la", 0, 0, "in")).paradigm


def test_latin_participle_uses_the_conjugation_of_its_verb():
    tok = find("la", 0, 2, "occupātō")
    paradigm = analyse(LIB, tok).paradigm
    model = paradigm.split("<h2>Model paradigm</h2>")[1].split("<h2>")[0]
    assert 'class="hit">amāt' in model                 # occupāre is first conjugation, like amāre
    grammar = analyse(LIB, tok).grammar
    assert "First conjugation" in grammar


def test_german_contraction_and_adjective_declension():
    am = find("de", 0, 0, "am")
    assert [t.form for t in am.siblings_in_token()] == ["an", "dem"]
    assert "2 grammatical words" in analyse(LIB, am).word
    kleine = find("de", 0, 0, "kleine")
    assert "mixed declension" in analyse(LIB, kleine).word


def test_czech_and_polish_words():
    krali = find("cs", 0, 0, "králi")
    assert krali.cats["case"] == "dative" and krali.lemma == "král"
    assert "dative" in analyse(LIB, krali).word
    glowami = find("pl", 0, 2, "głowami")
    assert glowami.cats["case"] == "instrumental"
    assert "Instrumental" in analyse(LIB, glowami).word


def test_every_word_of_a_sample_can_be_analysed():
    for lang in LIB.languages:
        for work in LIB.works(lang):
            for section in work.sections[:2]:
                for para in section.paragraphs[:4]:
                    for sent in para.sentences:
                        for tok in sent.tokens:
                            if tok.is_word:
                                assert analyse(LIB, tok).word


def test_window_click_and_keyboard():
    from PyQt6.QtCore import QPoint, Qt
    from PyQt6.QtGui import QTextCursor
    from PyQt6.QtTest import QTest
    from PyQt6.QtWidgets import QApplication

    from lang_gram import app as appmod

    qapp = QApplication.instance() or QApplication([])
    real = appmod.QSettings
    appmod.QSettings = lambda *a: real("lang-gram-test", "pytest")
    real("lang-gram-test", "pytest").clear()
    try:
        window = appmod.MainWindow()
        window.resize(1400, 850)
        window.show()
        qapp.processEvents()
        reader = window.reader
        assert reader.section is not None and window.lang == "la"
        # click in the middle of the first word of the first paragraph
        first = reader._paragraphs[0].sentences[0].tokens[0]
        cursor = QTextCursor(reader.document())
        cursor.setPosition(reader._starts[0] + first.start + 1)
        rect = reader.cursorRect(cursor)
        QTest.mouseClick(reader.viewport(), Qt.MouseButton.LeftButton, pos=rect.center())
        qapp.processEvents()
        assert window.current_token is first
        assert first.text in window.word_panel.toPlainText()
        # a click on empty margin selects nothing new
        QTest.mouseClick(reader.viewport(), Qt.MouseButton.LeftButton, pos=QPoint(3, 3))
        assert window.current_token is first
        # arrow keys walk through the words
        QTest.keyClick(reader, Qt.Key.Key_Right)
        qapp.processEvents()
        assert window.current_token is not first
        QTest.keyClick(reader, Qt.Key.Key_Left)
        qapp.processEvents()
        assert window.current_token is first
        # a click still counts when the pointer slips a few pixels between press and release
        target = reader._paragraphs[0].sentences[0].tokens[5]
        cursor.setPosition(reader._starts[0] + target.start + 2)
        point = reader.cursorRect(cursor).center()
        QTest.mousePress(reader.viewport(), Qt.MouseButton.LeftButton, pos=point)
        QTest.mouseMove(reader.viewport(), point + QPoint(5, 1))
        QTest.mouseRelease(reader.viewport(), Qt.MouseButton.LeftButton, pos=point + QPoint(5, 1))
        qapp.processEvents()
        assert window.current_token is target
        # the grammar panel comes back on the next click if it was closed ...
        window.analysis_dock.close()
        qapp.processEvents()
        assert not window.analysis_dock.isVisible()
        QTest.mouseClick(reader.viewport(), Qt.MouseButton.LeftButton, pos=rect.center())
        qapp.processEvents()
        assert window.analysis_dock.isVisible() and window.current_token is first
        # ... and also after changing text several times
        for index in (3, 60, 1, 0):
            window.analysis_dock.close()
            window._select_tree_section(window.work.sections[index])
            qapp.processEvents()
            assert window.current_token is None
            window._go_head()                          # no selected word: must do nothing
            word = reader._paragraphs[0].sentences[0].tokens[1]
            cursor.setPosition(reader._starts[0] + word.start + 1)
            window.analysis_dock.close()
            QTest.mouseClick(reader.viewport(), Qt.MouseButton.LeftButton, pos=reader.cursorRect(cursor).center())
            qapp.processEvents()
            assert window.current_token is word
            assert window.analysis_dock.isVisible() and not window.analysis_dock.isFloating()
            assert window.analysis_dock.width() >= 300
            assert word.text in window.word_panel.toPlainText()
        # switching language and colour mode keeps working
        for lang in ("de", "cs", "pl"):
            window.language_box.setCurrentIndex(window.language_box.findData(lang))
            qapp.processEvents()
            assert window.lang == lang and reader.section.work.lang == lang
            window.mode_box.setCurrentIndex(2)
            window._step_word(1)
            window._step_section(1)
            qapp.processEvents()
            window.open_reference()
            qapp.processEvents()
            assert window.reference.tree.topLevelItemCount() > 0
        window.language_box.setCurrentIndex(window.language_box.findData("la"))
        window.open_reference()
        qapp.processEvents()
        tree = window.reference.tree
        tops = [tree.topLevelItem(i).text(0) for i in range(tree.topLevelItemCount())]
        assert tops[0] == "Paradigms" and not any("scan" in t.lower() for t in tops)
        assert "hōr" in window.reference.browser.toPlainText()
        window.close()
    finally:
        appmod.QSettings = real


def test_themes_switch_and_follow_the_system():
    from PyQt6.QtWidgets import QApplication

    from lang_gram import app as appmod
    from lang_gram import theme

    qapp = QApplication.instance() or QApplication([])
    real = appmod.QSettings
    appmod.QSettings = lambda *a: real("lang-gram-test", "pytest-theme")
    real("lang-gram-test", "pytest-theme").clear()
    try:
        window = appmod.MainWindow()
        window.show()
        qapp.processEvents()
        box, themes = window.theme_box, window.themes
        assert [box.itemData(i) for i in range(box.count())] == ["system", "light", "dark"]
        assert themes.mode == "system" and window.dark == themes.system_dark()

        def looks(dark):
            colours = theme.DARK if dark else theme.LIGHT
            return (window.dark is dark and theme.is_dark(qapp.palette()) is dark
                    and colours["bg"] in window.reader.styleSheet()
                    and colours["accent"] in window.css)

        box.setCurrentIndex(box.findData("dark"))
        qapp.processEvents()
        assert looks(True) and real("lang-gram-test", "pytest-theme").value("theme") == "dark"
        token = window.reader._paragraphs[0].sentences[0].tokens[0]
        window.show_token(token)
        box.setCurrentIndex(box.findData("light"))
        qapp.processEvents()
        assert looks(False)
        assert window.current_token is token          # the selected word survives a theme change
        assert theme.LIGHT["hit"] in window.paradigm_panel.toHtml() or "hit" not in window.current_analysis.paradigm

        # "System theme": pretend the desktop switches between light and dark
        setting = {"dark": False}
        themes._portal_scheme = lambda: setting["dark"]
        box.setCurrentIndex(box.findData("system"))
        qapp.processEvents()
        assert looks(False) and "light" in box.itemText(0)
        setting["dark"] = True
        themes._system_changed()                      # what the periodic check does
        qapp.processEvents()
        assert looks(True) and "dark" in box.itemText(0)
        setting["dark"] = False
        themes._system_changed()
        qapp.processEvents()
        assert looks(False)
        # light -> back to the (dark) system theme gives exactly the look of the dark theme,
        # including menus, tool tips and drop-down lists
        from PyQt6.QtGui import QPalette
        from PyQt6.QtTest import QTest

        from lang_gram.appearance import build_palette

        def colours_of(name=None):
            pal = QApplication.palette(name) if name else qapp.palette()
            return [pal.color(g, r).name() for g in (QPalette.ColorGroup.Active, QPalette.ColorGroup.Disabled)
                    for r in (QPalette.ColorRole.Window, QPalette.ColorRole.Base, QPalette.ColorRole.Text,
                              QPalette.ColorRole.Button, QPalette.ColorRole.Highlight)]

        box.setCurrentIndex(box.findData("dark"))
        qapp.processEvents()
        pinned = {name: colours_of(name) for name in (None, "QMenu", "QToolTip", "QComboBox", "QAbstractItemView")}
        setting["dark"] = True
        box.setCurrentIndex(box.findData("light"))
        qapp.processEvents()
        assert looks(False) and themes.consistent()
        box.setCurrentIndex(box.findData("system"))
        qapp.processEvents()
        assert looks(True) and themes.consistent()
        assert {name: colours_of(name) for name in pinned} == pinned
        assert qapp.style().objectName().lower() == "fusion"
        # the desktop's own theme code may push foreign colours at any moment: they do not stick
        qapp.setPalette(build_palette(False))
        QApplication.setPalette(build_palette(False), "QMenu")
        assert not themes.consistent()
        QTest.qWait(50)
        assert themes.consistent() and looks(True)
        assert {name: colours_of(name) for name in pinned} == pinned
        # a pinned theme ignores the desktop
        box.setCurrentIndex(box.findData("dark"))
        setting["dark"] = False
        themes._system_changed()
        qapp.processEvents()
        assert looks(True)
        window.close()
    finally:
        appmod.QSettings = real


if __name__ == "__main__":
    failed = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print("ok  ", name)
            except Exception as exc:                  # noqa: BLE001
                failed += 1
                import traceback
                traceback.print_exc()
                print("FAIL", name, exc)
    raise SystemExit(1 if failed else 0)
