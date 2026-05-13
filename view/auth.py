# -*- coding: utf-8 -*-
"""
Authentication page for the EasyDEM dialog.

Builds the first workflow page: Google Earth Engine project configuration
and authentication controls. Signal connections are wired externally by
``easy.py``.
"""

import os

from qgis.PyQt.QtCore import Qt, QCoreApplication
from qgis.PyQt.QtGui import QPixmap
from qgis.PyQt.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from qgis.gui import QgsPasswordLineEdit

from .styles import STYLE_BTN_PRIMARY


def _tr(text):
    return QCoreApplication.translate("EasyDem", text)


# ---------------------------------------------------------------------------
# STEP 1 — Authentication
# ---------------------------------------------------------------------------

def setup_auth_page(dialog, page):
    """
    Populate the authentication page.

    The layout is a two-column row centred vertically on the page:

    - **Left column** (220 px fixed): plugin icon + caption, title label,
      plain-text description, and an info box explaining GEE prerequisites.
    - **Right card** (260 px fixed, white rounded card): a ``project_id_input``
      field for the Google Cloud project ID, a ``btn_authenticate`` primary
      action button, and a ``btn_reset_auth`` discrete reset link.
    All interactive widgets are exposed on ``dialog`` so ``easy.py`` can wire
    signal connections without importing this module's internals.
    """
    page.setStyleSheet("background-color: #f5f5f5;")

    outer = QVBoxLayout(page)
    outer.setContentsMargins(0, 0, 0, 0)
    outer.setSpacing(0)
    outer.addStretch(2)

    row = QHBoxLayout()
    row.setContentsMargins(28, 0, 28, 0)
    row.setSpacing(34)

    # ── Left column ───────────────────────────────────────────────────────
    left = QWidget()
    left.setFixedWidth(230)
    left.setStyleSheet("background: transparent;")
    left_lay = QVBoxLayout(left)
    left_lay.setContentsMargins(0, 0, 0, 0)
    left_lay.setSpacing(8)

    left_lay.addStretch(1)

    # Page title.
    title_lbl = QLabel(_tr("GEE Authentication"))
    title_lbl.setStyleSheet("color: #1a1a1a; font-size: 18px; font-weight: bold;")
    left_lay.addWidget(title_lbl)

    # Short explanation of why authentication is required.
    desc_lbl = QLabel(
        _tr(
            "EasyDEM uses <b>Google Earth Engine</b> for processing. "
            "To continue, you will need authorized access."
        )
    )
    desc_lbl.setWordWrap(True)
    desc_lbl.setTextFormat(Qt.TextFormat.RichText)
    desc_lbl.setStyleSheet("color: #616161; font-size: 13px;")
    left_lay.addWidget(desc_lbl)

    # Info box — green left border highlights the prerequisite note.
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
    info_icon.setStyleSheet("color: #2e7d32; font-size: 14px; font-weight: bold;")
    info_lay.addWidget(info_icon)

    info_text = QLabel(
        _tr(
            "Requires an active GEE account and a Google Cloud Console project "
            "with the API enabled."
        )
    )
    info_text.setWordWrap(True)
    info_text.setStyleSheet("color: #1b5e20; font-size: 12px;")
    info_lay.addWidget(info_text, 1)

    left_lay.addWidget(info_frame)
    left_lay.addStretch(1)
    row.addStretch(1)
    row.addWidget(left)

    # ── Right card ────────────────────────────────────────────────────────
    card = QFrame()
    card.setFixedWidth(258)
    card.setFixedHeight(218)
    card.setStyleSheet("""
        QFrame {
            background-color: #ffffff;
            border: 1px solid #e0e0e0;
            border-radius: 12px;
        }
        QLabel { background: transparent; border: none; }
    """)
    card_lay = QVBoxLayout(card)
    card_lay.setContentsMargins(20, 18, 20, 14)
    card_lay.setSpacing(7)

    # Field label.
    pid_lbl = QLabel(_tr("PROJECT ID (GOOGLE CLOUD)"))
    pid_lbl.setStyleSheet(
        "color: #9e9e9e; font-size: 11px; letter-spacing: 1px; font-weight: bold;"
    )
    card_lay.addWidget(pid_lbl)
    card_lay.addSpacing(18)

    # Project ID input — underline style with password-toggle via QGIS widget.
    dialog.project_id_input = QgsPasswordLineEdit()
    dialog.project_id_input.setEchoMode(QLineEdit.EchoMode.Normal)
    dialog.project_id_input.setPlaceholderText(_tr("e.g. my-geospatial-project-42"))
    dialog.project_id_input.setFixedHeight(28)
    dialog.project_id_input.setStyleSheet("""
        QLineEdit {
            background-color: transparent;
            color: #212121;
            border: none;
            border-bottom: 1.5px solid #d0d0d0;
            border-radius: 0;
            padding: 2px 0 6px 0;
            font-size: 14px;
        }
        QLineEdit:focus {
            border-bottom: 2px solid #1b6b39;
        }
    """)
    card_lay.addWidget(dialog.project_id_input)

    card_lay.addSpacing(3)

    # Primary action — validates the ID and initiates GEE authentication.
    dialog.btn_authenticate = QPushButton(_tr("🔑   Validate ID"))
    dialog.btn_authenticate.setFixedHeight(34)
    dialog.btn_authenticate.setStyleSheet(STYLE_BTN_PRIMARY)
    card_lay.addWidget(dialog.btn_authenticate)

    card_lay.addSpacing(2)

    # Reset link — small and discrete; clears stored GEE credentials.
    dialog.btn_reset_auth = QPushButton(_tr("Reset authentication"))
    dialog.btn_reset_auth.setFixedHeight(20)
    dialog.btn_reset_auth.setStyleSheet("""
        QPushButton {
            background-color: transparent;
            color: #bdbdbd;
            border: none;
            font-size: 10px;
        }
        QPushButton:hover { color: #c62828; }
    """)
    card_lay.addWidget(dialog.btn_reset_auth, 0, Qt.AlignmentFlag.AlignHCenter)
    card_lay.addStretch(1)

    row.addWidget(card)
    row.addStretch(1)
    outer.addLayout(row)

    # Hidden navigation hook used by the sidebar and controller to load
    # datasets before showing the AOI page.
    dialog.btn_go_to_aoi = QPushButton(page)
    dialog.btn_go_to_aoi.hide()
    dialog.btn_go_to_aoi.clicked.connect(dialog.show_aoi_page)

    outer.addStretch(3)
