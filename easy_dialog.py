# -*- coding: utf-8 -*-
"""
/***************************************************************************
 EasyDemDialog
                                 A QGIS plugin
 DEM
                             -------------------
        begin                : 2026-04-22
        copyright            : (C) 2026 by FARM Analytica
        email                : leandro.eloi@farmanalytica.com.br
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os

from qgis.PyQt.QtCore import QSettings, Qt, QUrl
from qgis.PyQt.QtWidgets import (
    QDialog,
    QApplication,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLineEdit,
    QLabel,
    QMessageBox,
    QStackedWidget,
    QWidget,
    QComboBox,
    QTextBrowser,
    QFrame,
    QSizePolicy,
)
from qgis.PyQt.QtGui import QPixmap, QDesktopServices

from qgis.gui import QgsMapLayerComboBox, QgsPasswordLineEdit
from qgis.core import QgsMapLayerProxyModel


# ---------------------------------------------------------------------------
# Stylesheet constants — light theme
# ---------------------------------------------------------------------------
_STYLE_DIALOG = """
QDialog {
    background-color: #f5f5f5;
    color: #212121;
}
QWidget {
    color: #212121;
}
QLineEdit {
    background-color: #ffffff;
    color: #212121;
    border: 1px solid #e0e0e0;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 12px;
}
QLineEdit:focus {
    border-color: #1b6b39;
}
QScrollBar:vertical {
    background: #f5f5f5;
    width: 6px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #bdbdbd;
    border-radius: 3px;
    min-height: 20px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
"""

_STYLE_BTN_PRIMARY = """
QPushButton {
    background-color: #1b6b39;
    color: #ffffff;
    border: none;
    border-radius: 8px;
    font-size: 12px;
    font-weight: bold;
    padding: 0 16px;
}
QPushButton:hover  { background-color: #1e7d42; }
QPushButton:pressed { background-color: #155a2f; }
QPushButton:disabled {
    background-color: #bdbdbd;
    color: #f5f5f5;
}
"""


# ---------------------------------------------------------------------------
# Dialog class
# ---------------------------------------------------------------------------

class EasyDemDialog(QDialog):
    """Dialog window for EasyDEM plugin user interface."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.language = QSettings().value("locale/userLocale", "en")[0:2]
        self._setup_ui()

    def _setup_ui(self):
        """Set up the dialog layout and widgets."""
        self.setWindowTitle("EasyDEM")
        self.setFixedSize(600, 400)
        self.setStyleSheet(_STYLE_DIALOG)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_header())

        self.stack = QStackedWidget()
        self.stack.setFrameShape(QFrame.Shape.NoFrame)
        self.stack.setLineWidth(0)
        self.stack.setStyleSheet("background-color: #f5f5f5;")
        root.addWidget(self.stack, 1)

        self.auth_page = QWidget()
        self.aoi_page = QWidget()

        self._setup_auth_page()
        self._setup_aoi_page()

        self.stack.addWidget(self.auth_page)
        self.stack.addWidget(self.aoi_page)

        self.stack.setCurrentWidget(self.auth_page)

        root.addWidget(self._build_footer())

    # -----------------------------------------------------------------------
    # HEADER
    # -----------------------------------------------------------------------

    def _build_header(self):
        is_pt = self.language == "pt"

        header = QWidget()
        header.setFixedHeight(38)
        header.setStyleSheet("background-color: #ffffff;")

        lay = QHBoxLayout(header)
        lay.setContentsMargins(28, 0, 20, 0)
        lay.setSpacing(0)

        brand = QLabel("EasyDEM")
        brand.setStyleSheet(
            "color: #1b6b39; font-size: 13px; font-weight: bold; letter-spacing: 0.5px;"
        )
        lay.addWidget(brand)

        sep_lbl = QLabel("  |")
        sep_lbl.setStyleSheet("color: #d0d0d0; font-size: 16px;")
        lay.addWidget(sep_lbl)

        self._header_title = QLabel(
            "Configuração GEE" if is_pt else "GEE Configuration"
        )
        self._header_title.setStyleSheet(
            "color: #616161; font-size: 13px; margin-left: 4px;"
        )
        lay.addWidget(self._header_title)

        lay.addStretch()

        self.browser = QPushButton("?")
        self.browser.setFixedSize(28, 28)
        self.browser.setToolTip("Saiba mais" if is_pt else "Learn more")
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
            lambda: QDesktopServices.openUrl(QUrl("https://caioarantes.github.io/EasyDEM/"))
        )
        lay.addWidget(self.browser)

        return header

    # -----------------------------------------------------------------------
    # STEP 1 — Authentication
    # -----------------------------------------------------------------------

    def _setup_auth_page(self):
        is_pt = self.language == "pt"

        page = self.auth_page
        page.setStyleSheet("background-color: #f5f5f5;")

        outer = QVBoxLayout(page)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addStretch(2)

        row = QHBoxLayout()
        row.setContentsMargins(24, 0, 24, 0)
        row.setSpacing(20)

        # ── Left column ───────────────────────────────────────────────────
        left = QWidget()
        left.setFixedWidth(200)
        left.setStyleSheet("background: transparent;")
        left_lay = QVBoxLayout(left)
        left_lay.setContentsMargins(0, 0, 0, 0)
        left_lay.setSpacing(10)

        # Plugin icon + caption
        logo_col = QVBoxLayout()
        logo_col.setSpacing(4)
        logo_col.setAlignment(Qt.AlignmentFlag.AlignLeft)

        icon_lbl = QLabel()
        icon_lbl.setFixedSize(50, 40)
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.png")
        if os.path.exists(icon_path):
            raw = QPixmap(icon_path)
            crop_top = int(raw.height() * 0.11)
            cropped = raw.copy(0, crop_top, raw.width(), raw.height() - crop_top)
            pix = cropped.scaled(
                40, 40,
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            icon_lbl.setPixmap(pix)
        else:
            icon_lbl.setText("🗺")
            icon_lbl.setStyleSheet("font-size: 28px;")
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setStyleSheet("background: transparent; border: none;")
        logo_col.addWidget(icon_lbl)

        icon_caption = QLabel("EasyDEM")
        icon_caption.setFixedWidth(50)
        icon_caption.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_caption.setStyleSheet(
            "color: #9e9e9e; font-size: 9px; letter-spacing: 0.5px;"
        )
        logo_col.addWidget(icon_caption)
        left_lay.addLayout(logo_col)

        # Title
        title_lbl = QLabel(
            "Autenticação GEE" if is_pt else "GEE Authentication"
        )
        title_lbl.setStyleSheet(
            "color: #1a1a1a; font-size: 16px; font-weight: bold;"
        )
        left_lay.addWidget(title_lbl)

        # Description
        desc_lbl = QLabel(
            'O EasyDEM utiliza o <b>Google Earth Engine</b> para processamento. '
            'Para prosseguir, você precisará de acesso autorizado.'
            if is_pt else
            'EasyDEM uses <b>Google Earth Engine</b> for processing. '
            'To continue, you will need authorized access.'
        )
        desc_lbl.setWordWrap(True)
        desc_lbl.setTextFormat(Qt.TextFormat.RichText)
        desc_lbl.setStyleSheet("color: #616161; font-size: 11px;")
        left_lay.addWidget(desc_lbl)

        # Info box — green left border, light green background
        info_frame = QFrame()
        info_frame.setStyleSheet("""
            QFrame {
                background-color: #e8f5e9;
                border-left: 3px solid #43a047;
                border-radius: 4px;
            }
            QLabel { background: transparent; border: none; }
        """)
        info_lay = QHBoxLayout(info_frame)
        info_lay.setContentsMargins(12, 10, 12, 10)
        info_lay.setSpacing(8)

        info_icon = QLabel("ⓘ")
        info_icon.setFixedWidth(18)
        info_icon.setAlignment(Qt.AlignmentFlag.AlignTop)
        info_icon.setStyleSheet(
            "color: #2e7d32; font-size: 14px; font-weight: bold;"
        )
        info_lay.addWidget(info_icon)

        info_text = QLabel(
            'Requer uma conta GEE ativa e um projeto no Google Cloud Console com a API ativada.'
            if is_pt else
            'Requires an active GEE account and a Google Cloud Console project with the API enabled.'
        )
        info_text.setWordWrap(True)
        info_text.setStyleSheet("color: #1b5e20; font-size: 10px;")
        info_lay.addWidget(info_text, 1)

        left_lay.addWidget(info_frame)
        left_lay.addStretch()
        row.addWidget(left)

        # ── Right card ────────────────────────────────────────────────────
        card = QFrame()
        card.setFixedWidth(260)
        card.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 12px;
            }
            QLabel { background: transparent; border: none; }
        """)
        card_lay = QVBoxLayout(card)
        card_lay.setContentsMargins(20, 20, 20, 20)
        card_lay.setSpacing(7)

        # Label
        pid_lbl = QLabel(
            "ID DO PROJETO (GOOGLE CLOUD)" if is_pt else "PROJECT ID (GOOGLE CLOUD)"
        )
        pid_lbl.setStyleSheet(
            "color: #9e9e9e; font-size: 10px; letter-spacing: 1px; font-weight: bold;"
        )
        card_lay.addWidget(pid_lbl)

        # Project ID input — underline style, show password toggle
        self.project_id_input = QgsPasswordLineEdit()
        self.project_id_input.setEchoMode(QLineEdit.EchoMode.Normal)
        self.project_id_input.setPlaceholderText(
            "ex: meu-projeto-geoespacial-42" if is_pt else "e.g. my-geospatial-project-42"
        )
        self.project_id_input.setFixedHeight(30)
        self.project_id_input.setStyleSheet("""
            QLineEdit {
                background-color: transparent;
                color: #212121;
                border: none;
                border-bottom: 1.5px solid #d0d0d0;
                border-radius: 0;
                padding: 2px 0 6px 0;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-bottom: 2px solid #1b6b39;
            }
        """)
        card_lay.addWidget(self.project_id_input)

        card_lay.addSpacing(3)

        # Authenticate button
        self.btn_authenticate = QPushButton(
            "🔑   Validar ID" if is_pt else "🔑   Validate ID"
        )
        self.btn_authenticate.setFixedHeight(34)
        self.btn_authenticate.setStyleSheet(_STYLE_BTN_PRIMARY)
        card_lay.addWidget(self.btn_authenticate)

        card_lay.addSpacing(2)

        # Reset button — small, discrete
        self.btn_reset_auth = QPushButton(
            "Resetar autenticação" if is_pt else "Reset authentication"
        )
        self.btn_reset_auth.setFixedHeight(20)
        self.btn_reset_auth.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #bdbdbd;
                border: none;
                font-size: 10px;
            }
            QPushButton:hover { color: #c62828; }
        """)
        card_lay.addWidget(self.btn_reset_auth, 0, Qt.AlignmentFlag.AlignHCenter)

        row.addWidget(card)

        outer.addLayout(row)
        outer.addStretch(3)

    # -----------------------------------------------------------------------
    # STEP 2 — AOI (unchanged)
    # -----------------------------------------------------------------------

    def _setup_aoi_page(self):
        """Set up the AOI page with a polygon layer selector and load button."""
        layout = QVBoxLayout(self.aoi_page)

        layout.addWidget(QLabel("Select AOI Layer"))

        self.layer_combo = QgsMapLayerComboBox()
        self.layer_combo.setFilters(QgsMapLayerProxyModel.PolygonLayer)

        self.btn_download_dem = QPushButton("Download DEM")
        self.dem_combo = QComboBox()

        self.dem_info = QTextBrowser()
        self.dem_info.setOpenExternalLinks(True)
        self.dem_info.setMinimumHeight(120)

        layout.addWidget(self.layer_combo)
        layout.addWidget(self.dem_combo)
        layout.addWidget(self.dem_info)
        layout.addWidget(self.btn_download_dem)

    # -----------------------------------------------------------------------
    # FOOTER
    # -----------------------------------------------------------------------

    def _build_footer(self):
        is_pt = self.language == "pt"

        footer = QWidget()
        footer.setFixedHeight(52)
        footer.setStyleSheet(
            "background-color: #ffffff;"
            "QLabel { border: none; background: transparent; }"
        )

        lay = QHBoxLayout(footer)
        lay.setContentsMargins(28, 6, 28, 6)
        lay.setSpacing(8)

        # FARM Analytica attribution
        farm_icon = QLabel()
        farm_icon.setFixedHeight(24)
        farm_icon.setStyleSheet("background: transparent;")
        _logo_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "medias", "farm_analytica_logo.svg"
        )
        if os.path.exists(_logo_path):
            _pix = QPixmap(_logo_path).scaledToHeight(
                24, Qt.TransformationMode.SmoothTransformation
            )
            farm_icon.setPixmap(_pix)
            farm_icon.setFixedWidth(_pix.width())
        else:
            farm_icon.setText("FARM ANALYTICA")
            farm_icon.setStyleSheet(
                "color: #1b6b39; font-size: 10px; font-weight: bold;"
            )
        farm_icon.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        lay.addWidget(farm_icon)

        farm_text = QLabel()
        farm_text.setTextFormat(Qt.TextFormat.RichText)
        farm_text.setOpenExternalLinks(True)
        farm_text.setWordWrap(True)
        if is_pt:
            farm_text.setText(
                'Este é um projeto gratuito e aberto, desenvolvido pela '
                '<a href="https://farmanalytica.com.br" style="color:#1b6b39;'
                'text-decoration:none;font-weight:bold;">FARM Analytica</a>. '
                'Fale conosco sobre soluções comerciais exclusivas e personalizadas.'
            )
        else:
            farm_text.setText(
                'This is a free and open project, developed by '
                '<a href="https://farmanalytica.com.br" style="color:#1b6b39;'
                'text-decoration:none;font-weight:bold;">FARM Analytica</a>. '
                'Contact us for exclusive and personalized commercial solutions.'
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
        self.stack.setCurrentWidget(self.aoi_page)

    def pop_message(self, message, kind):
        """
        Display a modal message box to the user.

        Args:
            message: Text content to display.
            kind: Message type — "info" for informational, "warning" for warnings.
        """
        QApplication.restoreOverrideCursor()

        config = {
            "info": (
                "Informação" if self.language == "pt" else "Information",
                QMessageBox.Icon.Information,
            ),
            "warning": (
                "Aviso" if self.language == "pt" else "Warning",
                QMessageBox.Icon.Warning,
            ),
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
