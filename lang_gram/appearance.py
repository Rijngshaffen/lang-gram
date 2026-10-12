"""Light and dark appearance of the whole application.

Three modes: "system" follows the desktop's light/dark preference (and keeps
following it while the app runs), "light" and "dark" pin one of them.  Whichever
way a theme is reached it is painted the same way: Fusion style, own palette.
"""
from __future__ import annotations

import sys

from PyQt6.QtCore import QEvent, QObject, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QApplication

from . import theme

MODES = [("system", "System theme"), ("light", "Light theme"), ("dark", "Dark theme")]
PORTAL = ("org.freedesktop.portal.Desktop", "/org/freedesktop/portal/desktop", "org.freedesktop.portal.Settings")


# Widget classes for which a desktop's platform theme (GTK, KDE ...) may keep a
# palette of its own; they are given ours explicitly so that no part of the window
# is left in the other theme.
THEMED_CLASSES = ["QMenu", "QMenuBar", "QToolTip", "QToolButton", "QAbstractButton", "QPushButton", "QCheckBox",
                  "QRadioButton", "QHeaderView", "QComboBox", "QAbstractItemView", "QTabBar", "QLabel",
                  "QGroupBox", "QTextEdit", "QTextControl", "QLineEdit", "QMessageBoxLabel", "QToolBar",
                  "QDockWidget", "QScrollBar", "QStatusBar", "QTabWidget"]


# "ThemeChange" is not exposed by every PyQt6 version.
_PALETTE_EVENTS = {t for t in (getattr(QEvent.Type, name, None)
                               for name in ("ApplicationPaletteChange", "ThemeChange")) if t is not None}


def palette_spec(dark: bool) -> list[tuple]:
    """(colour group or None for all, role, colour) for every role the app defines."""
    spec = theme.WIDGETS_DARK if dark else theme.WIDGETS_LIGHT
    roles = QPalette.ColorRole
    out = []
    for name, colour in spec.items():
        disabled = name.startswith("Disabled")
        role = getattr(roles, name[len("Disabled"):] if disabled else name, None)   # "Accent": Qt 6.6+
        if role is not None:
            out.append((QPalette.ColorGroup.Disabled if disabled else None, role, QColor(colour)))
    return out


def build_palette(dark: bool) -> QPalette:
    """Widget palette matching theme.LIGHT / theme.DARK."""
    palette = QPalette()
    for group, role, colour in palette_spec(dark):
        if group is None:
            palette.setColor(role, colour)
        else:
            palette.setColor(group, role, colour)
    return palette


def palette_matches(palette: QPalette, dark: bool) -> bool:
    groups = (QPalette.ColorGroup.Active, QPalette.ColorGroup.Inactive)
    overridden = {role for group, role, _ in palette_spec(dark) if group is not None}
    for group, role, colour in palette_spec(dark):
        if group is not None:
            if palette.color(group, role) != colour:
                return False
        elif any(palette.color(g, role) != colour for g in groups):
            return False
        elif role not in overridden and palette.color(QPalette.ColorGroup.Disabled, role) != colour:
            return False
    return True


class ThemeManager(QObject):
    """Decides whether the app is dark and paints every widget accordingly.

    The widgets are always drawn with the Fusion style and the app's own palette.
    Qt's palette for the desktop theme is deliberately not used: on some desktops
    it does not follow the dark/light setting, or follows it only in part.
    """

    changed = pyqtSignal(bool)                      # emitted with the new "dark" flag

    def __init__(self, app: QApplication, mode: str = "system"):
        super().__init__(app)
        self.app = app
        self.mode = mode if mode in dict(MODES) else "system"
        self.dark = False
        self._startup_dark = theme.is_dark(app.palette())
        self._applying = False
        self._linux = sys.platform.startswith(("linux", "freebsd"))
        self._portal = self._open_portal()
        hints = app.styleHints()
        if hasattr(hints, "colorSchemeChanged"):    # Qt 6.5+
            hints.colorSchemeChanged.connect(self._system_changed)
        # The desktop portal has no reliable change notification through Qt on every
        # desktop, so in "system" mode its setting is simply re-read now and then.
        self._timer = QTimer(self)
        self._timer.setInterval(2500)
        self._timer.timeout.connect(self._system_changed)
        app.installEventFilter(self)
        self.apply(notify=False)

    # -- what does the desktop want? -------------------------------------------------
    def _open_portal(self):
        """XDG desktop portal (GNOME, KDE, ... on Linux): the cross-desktop dark-mode setting."""
        if not sys.platform.startswith(("linux", "freebsd")):
            return None
        try:
            from PyQt6.QtDBus import QDBusConnection, QDBusInterface
            bus = QDBusConnection.sessionBus()
            if not bus.isConnected():
                return None
            iface = QDBusInterface(*PORTAL, bus)
            if not iface.isValid():
                return None
            iface.setTimeout(400)
            return iface
        except Exception:                           # no QtDBus, no session bus ...
            return None

    def _portal_scheme(self) -> bool | None:
        if self._portal is None:
            return None
        try:
            reply = self._portal.call("Read", "org.freedesktop.appearance", "color-scheme")
            args = reply.arguments()
            value = args[0] if args else None
            while hasattr(value, "variant"):        # variant inside variant on some bindings
                value = value.variant()
            value = int(value)
        except Exception:
            return None
        return {1: True, 2: False}.get(value)       # 0 = no preference

    def _qt_scheme(self) -> bool | None:
        hints = self.app.styleHints()
        if not hasattr(hints, "colorScheme"):
            return None
        scheme = hints.colorScheme()
        if scheme == Qt.ColorScheme.Dark:
            return True
        if scheme == Qt.ColorScheme.Light:
            return False
        return None

    def system_dark(self) -> bool:
        """Is the desktop environment set to a dark appearance?"""
        for source in (self._portal_scheme, self._qt_scheme):
            answer = source()
            if answer is not None:
                return answer
        return self._startup_dark

    # -- applying --------------------------------------------------------------------
    def set_mode(self, mode: str):
        if mode not in dict(MODES):
            mode = "system"
        self.mode = mode
        self.apply()

    def apply(self, notify: bool = True):
        if self._applying:
            return
        self._applying = True
        try:
            dark = self.system_dark() if self.mode == "system" else self.mode == "dark"
            hints = self.app.styleHints()
            if not self._linux and hasattr(hints, "setColorScheme"):
                # Windows / macOS (Qt 6.8+): native title bars and dialogs follow as well.
                if self.mode == "system":
                    hints.unsetColorScheme()
                    answer = self._qt_scheme()
                    dark = answer if answer is not None else dark
                else:
                    hints.setColorScheme(Qt.ColorScheme.Dark if dark else Qt.ColorScheme.Light)
            was, self.dark = self.dark, dark
            self._paint()
            if self.mode == "system":
                self._timer.start()
            else:
                self._timer.stop()
        finally:
            self._applying = False
        if notify and was != dark:
            self.changed.emit(dark)

    def _paint(self):
        """Fusion style + our palette for the application and for every themed widget class."""
        app = self.app
        if app.style().objectName().lower() != "fusion":
            app.setStyle("Fusion")
        palette = build_palette(self.dark)
        if not palette_matches(app.palette(), self.dark):
            app.setPalette(palette)
        for name in THEMED_CLASSES:
            if not palette_matches(QApplication.palette(name), self.dark):
                QApplication.setPalette(palette, name)

    def consistent(self) -> bool:
        """True when the application and all themed widget classes show the current theme."""
        return (palette_matches(self.app.palette(), self.dark)
                and all(palette_matches(QApplication.palette(name), self.dark) for name in THEMED_CLASSES))

    def eventFilter(self, obj, event):
        # The desktop's platform theme may push its own colours at any time (for
        # instance when the system setting changes); put ours back afterwards.
        if obj is self.app and not self._applying and event.type() in _PALETTE_EVENTS:
            QTimer.singleShot(0, self._repaint_if_needed)
        return False

    def _repaint_if_needed(self):
        if self._applying or self.consistent():
            return
        self._applying = True
        try:
            self._paint()
        finally:
            self._applying = False

    def _system_changed(self, *_args):
        if self.mode == "system" and not self._applying and self.system_dark() != self.dark:
            self.apply()
