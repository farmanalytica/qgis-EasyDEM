# -*- coding: utf-8 -*-
"""
UI layer for the EasyDEM QGIS plugin.

Defines ``EasyDemDialog``, a two-page modal dialog that guides the user
through the full plugin workflow:

1. **Authentication page** (``auth_page``) — user supplies a Google Cloud
   project ID and validates GEE access, or browses datasets without
   authenticating.
2. **AOI page** (``aoi_page``) — user selects a polygon layer as the Area
   of Interest, picks a DEM dataset, sets an AOI buffer, chooses a download
   folder, and triggers the download.

This module owns the dialog shell only.  Page widget construction lives in
``view/auth.py`` and ``view/download_dem.py``, while signal connections are
made externally by ``easy.py`` to keep this module free of business logic
and the ``ee`` SDK.
"""

import os

from qgis.PyQt.QtCore import Qt, QUrl, QCoreApplication
from qgis.PyQt.QtGui import QDesktopServices, QPixmap
from qgis.PyQt.QtWidgets import (
    QApplication,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from .view.auth import setup_auth_page
from .view.download_dem import setup_download_dem_page
from .view.sidebar import Sidebar
from .view.styles import STYLE_DIALOG, STYLE_BTN_HELP


def _tr(text):
    return QCoreApplication.translate("EasyDem", text)


class EasyDemDialog(QDialog):
    """
    Main dialog window for the EasyDEM plugin.

    Presents a two-page ``QStackedWidget`` flow:

    - ``auth_page`` — shown on first open; collects the GCP project ID and
      validates Google Earth Engine credentials, or lets the user skip to the
      AOI page to browse available datasets.
    - ``aoi_page`` — shown after authentication; allows the user to select a
      polygon AOI layer, browse DEM datasets, adjust the AOI buffer, choose a
      download folder, and trigger the download.

    Public widget attributes created by the page modules (consumed by
    ``easy.py`` and ``dem_handler.py``):

    Auth page:
        project_id_input: GCP project ID field.
        btn_authenticate: Triggers GEE authentication.
        btn_reset_auth: Clears existing GEE credentials.
        btn_go_to_aoi: Navigates to the AOI page without authenticating.

    AOI page:
        layer_combo: Polygon layer selector.
        dem_combo: Lists DEM datasets available for the AOI.
        dem_info: Displays metadata for the selected dataset.
        buffer_slider: AOI buffer control (−300 m … +300 m).
        buffer_value_lbl: Live label showing the current buffer value.
        folder_input: Download destination path field.
        btn_browse_folder: Opens the folder picker dialog.
        btn_hybrid_layer: Adds a Google Hybrid basemap layer.
        btn_download_dem: Downloads and loads the DEM into QGIS.

    Signal connections are wired externally by ``easy.py``.
    """

    def __init__(self, parent=None):
        self._qgis_parent = parent
        super().__init__(None)
        self._setup_ui()

    def _setup_ui(self):
        """Build the root layout: fixed header, central stack, fixed footer."""
        self.setWindowTitle("EasyDEM")
        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.WindowSystemMenuHint
            | Qt.WindowType.WindowTitleHint
            | Qt.WindowType.WindowMinimizeButtonHint
            | Qt.WindowType.WindowCloseButtonHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setWindowModality(Qt.WindowModality.NonModal)
        self.setFixedSize(800, 404)
        self.setStyleSheet(STYLE_DIALOG)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_header())

        # Body row: permanent sidebar + page stack.
        body = QWidget()
        body.setStyleSheet("background-color: #f5f5f5;")
        body_lay = QHBoxLayout(body)
        body_lay.setContentsMargins(0, 0, 0, 0)
        body_lay.setSpacing(8)

        self.sidebar = Sidebar()
        self.sidebar.auth_requested.connect(self._nav_to_auth)
        self.sidebar.download_requested.connect(self._nav_to_download)
        body_lay.addWidget(self.sidebar)

        # Right column: stack + footer stacked vertically, outside the sidebar.
        right_col = QWidget()
        right_col.setStyleSheet("background-color: #f5f5f5;")
        right_lay = QVBoxLayout(right_col)
        right_lay.setContentsMargins(0, 0, 0, 0)
        right_lay.setSpacing(0)

        self.stack = QStackedWidget()
        self.stack.setFrameShape(QFrame.Shape.NoFrame)
        self.stack.setLineWidth(0)
        self.stack.setStyleSheet("background-color: #f5f5f5;")
        right_lay.addWidget(self.stack, 1)

        self.footer = self._build_footer()
        right_lay.addWidget(self.footer)

        body_lay.addWidget(right_col, 1)

        self.loading_page = self._build_loading_page()
        self.auth_page = QWidget()
        self.aoi_page = QWidget()

        setup_auth_page(self, self.auth_page)
        setup_download_dem_page(self, self.aoi_page)

        self.stack.addWidget(self.loading_page)
        self.stack.addWidget(self.auth_page)
        self.stack.addWidget(self.aoi_page)
        self.stack.currentChanged.connect(self._sync_page_state)

        self.stack.setCurrentWidget(self.auth_page)
        self._sync_page_state(self.stack.currentIndex())

        root.addWidget(body, 1)

    # -----------------------------------------------------------------------
    # LOADING PAGE
    # -----------------------------------------------------------------------

    def _build_loading_page(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(48, 0, 48, 24)
        lay.setSpacing(12)
        lay.addStretch()

        title = QLabel(_tr("Setting up EasyDEM…"))
        title.setStyleSheet(
            "color: #1b6b39; font-size: 14px; font-weight: bold;"
        )
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(title)

        sub = QLabel(_tr("Downloading dependencies. This only happens on first use."))
        sub.setStyleSheet("color: #616161; font-size: 10px;")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(sub)

        bar = QProgressBar()
        bar.setRange(0, 0)
        bar.setFixedHeight(6)
        bar.setTextVisible(False)
        bar.setStyleSheet(
            "QProgressBar { border: none; border-radius: 3px; background: #e0e0e0; }"
            "QProgressBar::chunk { background: #1b6b39; border-radius: 3px; }"
        )
        lay.addWidget(bar)
        self._loading_bar = bar

        lay.addStretch()
        return page

    # -----------------------------------------------------------------------
    # HEADER
    # -----------------------------------------------------------------------

    def _build_header(self):
        """
        Build and return the dialog header widget.

        The header is a fixed-height (38 px) white bar containing:
        - The "EasyDEM" brand label (green).
        - A vertical separator.
        - A dynamic page-title label (``_header_title``) updated by the
          controller when the active page changes.
        - A "?" help button that opens the documentation URL in the browser.
        """
        header = QWidget()
        header.setFixedHeight(38)
        header.setStyleSheet("background-color: #ffffff;")

        lay = QHBoxLayout(header)
        lay.setContentsMargins(28, 0, 20, 0)
        lay.setSpacing(0)

        # Brand name — always green, always visible.
        brand = QLabel("EasyDEM")
        brand.setStyleSheet(
            "color: #1b6b39; font-size: 13px; font-weight: bold; letter-spacing: 0.5px;"
        )
        lay.addWidget(brand)

        # Thin vertical divider between brand and page title.
        sep_lbl = QLabel("  |")
        sep_lbl.setStyleSheet("color: #d0d0d0; font-size: 16px;")
        lay.addWidget(sep_lbl)

        # Dynamic title updated by show_auth_page / show_aoi_page.
        self._header_title = QLabel(_tr("GEE Configuration"))
        self._header_title.setStyleSheet(
            "color: #616161; font-size: 13px; margin-left: 4px;"
        )
        lay.addWidget(self._header_title)

        lay.addStretch()

        # Help button — opens the plugin documentation in the default browser.
        self.browser = QPushButton("?")
        self.browser.setFixedSize(28, 28)
        self.browser.setToolTip(_tr("Learn more"))
        self.browser.setStyleSheet(STYLE_BTN_HELP)
        self.browser.clicked.connect(
            lambda: QDesktopServices.openUrl(
                QUrl("https://easydem.org")
            )
        )
        lay.addWidget(self.browser)

        return header

    # -----------------------------------------------------------------------
    # FOOTER
    # -----------------------------------------------------------------------

    def _build_footer(self):
        """
        Build and return the dialog footer widget.

        The footer is a fixed-height (52 px) white bar containing the FARM
        Analytica logo (loaded from ``assets/farm_analytica_logo.svg``) and a
        short attribution text with a clickable link to the FARM Analytica
        website.  If the SVG file is not found, the logo falls back to a
        plain-text label.
        """
        footer = QWidget()
        footer.setFixedHeight(36)
        footer.setStyleSheet(
            "background-color: transparent;"
            "QLabel { border: none; background: transparent; }"
        )

        lay = QHBoxLayout(footer)
        lay.setContentsMargins(28, 4, 28, 4)
        lay.setSpacing(8)

        # FARM Analytica logo — falls back to plain text if SVG is missing.
        farm_icon = QLabel()
        farm_icon.setFixedHeight(16)
        farm_icon.setStyleSheet("background: transparent;")
        logo_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "assets",
            "farm_analytica_logo.svg",
        )
        if os.path.exists(logo_path):
            pix = QPixmap(logo_path).scaledToHeight(
                16, Qt.TransformationMode.SmoothTransformation
            )
            farm_icon.setPixmap(pix)
            farm_icon.setFixedWidth(pix.width())
        else:
            farm_icon.setText("FARM ANALYTICA")
            farm_icon.setStyleSheet(
                "color: #1b6b39; font-size: 9px; font-weight: bold;"
            )
        farm_icon.setAlignment(
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft
        )
        lay.addWidget(farm_icon)

        # Attribution copy with an external link to the FARM Analytica website.
        farm_text = QLabel()
        farm_text.setTextFormat(Qt.TextFormat.RichText)
        farm_text.setOpenExternalLinks(True)
        farm_text.setWordWrap(False)
        farm_text.setText(
            _tr("This is a free and open project, supported by ")
            + '<a href="https://farmanalytica.com.br" style="color:#1b6b39;'
            'text-decoration:none;font-weight:bold;">FARM Analytica</a>. '
            + _tr("Get in touch for exclusive and personalized commercial solutions.")
        )
        farm_text.setStyleSheet("color: #9e9e9e; font-size: 9px;")
        farm_text.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        lay.addWidget(farm_text)

        return footer

    # -----------------------------------------------------------------------
    # PUBLIC METHODS
    # -----------------------------------------------------------------------

    def show_loading_page(self):
        """Switch the stacked widget to the loading/download page."""
        self.stack.setCurrentWidget(self.loading_page)

    def show_aoi_page(self):
        """Switch the stacked widget to the AOI selection page."""
        self.stack.setCurrentWidget(self.aoi_page)

    def show_auth_page(self):
        """Switch the stacked widget to the authentication page."""
        self.stack.setCurrentWidget(self.auth_page)

    def _nav_to_auth(self):
        """Sidebar auth button — always navigates to the auth page."""
        self.show_auth_page()

    def _nav_to_download(self):
        """Sidebar download button follows the existing dataset-loading path."""
        if hasattr(self, "btn_go_to_aoi"):
            self.btn_go_to_aoi.click()
            return
        self.show_aoi_page()

    def _sync_page_state(self, index):
        """Keep header and sidebar state aligned with the current stack page."""
        current = self.stack.widget(index)

        if current is self.loading_page:
            self._header_title.setText(_tr("Setting up…"))
            self.sidebar.set_active_page(None)
            self.footer.setVisible(True)
            return

        if current is self.auth_page:
            self._header_title.setText(_tr("GEE Configuration"))
            self.sidebar.set_active_page("auth")
            self.footer.setVisible(True)
            return

        if current is self.aoi_page:
            self._header_title.setText(_tr("Inputs & Parameters"))
            self.sidebar.set_active_page("download")
            self.footer.setVisible(False)

    def pop_message(self, message, kind):
        """
        Display a modal message box to the user.

        Args:
            message (str): Text content to display.
            kind (str): ``"info"`` or ``"warning"``.
        """
        QApplication.restoreOverrideCursor()

        # Map semantic severity to QMessageBox configuration.
        config = {
            "info": (_tr("Information"), QMessageBox.Icon.Information),
            "warning": (_tr("Warning"), QMessageBox.Icon.Warning),
        }
        title, icon = config.get(kind, config["info"])

        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setIcon(icon)
        msg.setText(message)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.button(QMessageBox.StandardButton.Ok).setText("OK")
        msg.setStyleSheet("font-size: 10pt;")
        msg.exec()
