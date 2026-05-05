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

from qgis.PyQt.QtCore import Qt, QUrl
from qgis.PyQt.QtGui import QDesktopServices, QPixmap
from qgis.PyQt.QtWidgets import (
    QApplication,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from .view.auth import setup_auth_page
from .view.download_dem import setup_download_dem_page
from .view.styles import STYLE_DIALOG


# ---------------------------------------------------------------------------
# Dialog class
# ---------------------------------------------------------------------------

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

    Signal connections are wired externally by ``easy.py``.  This class
    must not import ``ee`` or any service module directly.
    """

    def __init__(self, parent=None):
        """
        Initialise the dialog and build all widgets.

        Args:
            parent: Optional parent ``QWidget``.  Defaults to ``None``.
        """
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
        )
        self.setWindowModality(Qt.WindowModality.NonModal)
        self.setFixedSize(800, 400)
        self.setStyleSheet(STYLE_DIALOG)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_header())

        # Central stack hosts each workflow page inside the fixed-size dialog.
        self.stack = QStackedWidget()
        self.stack.setFrameShape(QFrame.Shape.NoFrame)
        self.stack.setLineWidth(0)
        self.stack.setStyleSheet("background-color: #f5f5f5;")
        root.addWidget(self.stack, 1)

        self.auth_page = QWidget()
        self.aoi_page = QWidget()

        # Delegate page construction to isolated view modules.
        setup_auth_page(self, self.auth_page)
        setup_download_dem_page(self, self.aoi_page)

        self.stack.addWidget(self.auth_page)
        self.stack.addWidget(self.aoi_page)
        self.stack.setCurrentWidget(self.auth_page)

        root.addWidget(self._build_footer())

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

        Returns:
            QWidget: The fully constructed header widget.
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
        self._header_title = QLabel("GEE Configuration")
        self._header_title.setStyleSheet(
            "color: #616161; font-size: 13px; margin-left: 4px;"
        )
        lay.addWidget(self._header_title)

        lay.addStretch()

        # Help button — opens the plugin documentation in the default browser.
        self.browser = QPushButton("?")
        self.browser.setFixedSize(28, 28)
        self.browser.setToolTip("Learn more")
        self.browser.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #9e9e9e;
                border: 1.5px solid #d0d0d0;
                border-radius: 14px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #f5f5f5;
                color: #424242;
                border-color: #bdbdbd;
            }
        """)
        self.browser.clicked.connect(
            lambda: QDesktopServices.openUrl(
                QUrl("https://farmanalytica.github.io/qgis-EasyDEM/")
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

        Returns:
            QWidget: The fully constructed footer widget.
        """
        footer = QWidget()
        footer.setFixedHeight(52)
        footer.setStyleSheet(
            "background-color: #ffffff;"
            "QLabel { border: none; background: transparent; }"
        )

        lay = QHBoxLayout(footer)
        lay.setContentsMargins(28, 6, 28, 6)
        lay.setSpacing(8)

        # FARM Analytica logo — falls back to plain text if SVG is missing.
        farm_icon = QLabel()
        farm_icon.setFixedHeight(24)
        farm_icon.setStyleSheet("background: transparent;")
        logo_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "assets",
            "farm_analytica_logo.svg",
        )
        if os.path.exists(logo_path):
            pix = QPixmap(logo_path).scaledToHeight(
                24, Qt.TransformationMode.SmoothTransformation
            )
            farm_icon.setPixmap(pix)
            farm_icon.setFixedWidth(pix.width())
        else:
            farm_icon.setText("FARM ANALYTICA")
            farm_icon.setStyleSheet(
                "color: #1b6b39; font-size: 10px; font-weight: bold;"
            )
        farm_icon.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        lay.addWidget(farm_icon)

        # Attribution copy with an external link to the FARM Analytica website.
        farm_text = QLabel()
        farm_text.setTextFormat(Qt.TextFormat.RichText)
        farm_text.setOpenExternalLinks(True)
        farm_text.setWordWrap(True)
        farm_text.setText(
            "This is a free and open project, supported by "
            '<a href="https://farmanalytica.com.br" style="color:#1b6b39;'
            'text-decoration:none;font-weight:bold;">FARM Analytica</a>. '
            "Get in touch for exclusive and personalized commercial solutions."
        )
        farm_text.setStyleSheet("color: #616161; font-size: 8px;")
        farm_text.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        lay.addWidget(farm_text)

        return footer

    # -----------------------------------------------------------------------
    # PUBLIC METHODS
    # -----------------------------------------------------------------------

    def show_aoi_page(self):
        """Switch the stacked widget to the AOI selection page."""
        self._header_title.setText("Inputs & Parameters")
        self.stack.setCurrentWidget(self.aoi_page)

    def show_auth_page(self):
        """Switch the stacked widget to the authentication page."""
        self._header_title.setText("GEE Configuration")
        self.stack.setCurrentWidget(self.auth_page)

    def pop_message(self, message, kind):
        """
        Display a modal message box to the user.

        Restores the override cursor before showing the dialog, so it is safe
        to call while a wait cursor is active.

        Args:
            message (str): Text content to display.
            kind (str): Message severity.  Accepted values:

                - ``"info"``    — informational icon, title "Information".
                - ``"warning"`` — warning icon, title "Warning".

                Any unrecognised value falls back to ``"info"``.
        """
        QApplication.restoreOverrideCursor()

        # Map semantic severity to QMessageBox configuration.
        config = {
            "info": ("Information", QMessageBox.Icon.Information),
            "warning": ("Warning", QMessageBox.Icon.Warning),
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
