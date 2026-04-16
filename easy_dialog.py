# -*- coding: utf-8 -*-
"""
/***************************************************************************
 EasyDemDialog
                                 A QGIS plugin
 DEM
                             -------------------
        begin                : 2026-04-01
        copyright            : (C) 2026 by FARM Analytica
        email                : livia.scopel@farmanalytica.com.br
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

from qgis.gui import QgsMapLayerComboBox
from qgis.core import QgsMapLayerProxyModel

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
)


class EasyDemDialog(QDialog):
    """
    Dialog window for EasyDEM plugin user interface.
    """

    def __init__(self, parent=None):
        """
        Initialize the EasyDEM dialog.

        Args:
            parent: Parent widget.
        """
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        """Set up the dialog layout and widgets."""
        self.setWindowTitle("EasyDEM")

        main_layout = QVBoxLayout(self)

        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack)

        self.auth_page = QWidget()
        self.aoi_page = QWidget()

        self._setup_auth_page()
        self._setup_aoi_page()

        self.stack.addWidget(self.auth_page)
        self.stack.addWidget(self.aoi_page)

        self.stack.setCurrentWidget(self.auth_page)

        main_layout.addStretch()

    def _setup_auth_page(self):
        """Set up the authentication page with GEE auth buttons and project ID input."""
        main_layout = QVBoxLayout(self.auth_page)

        auth_layout = QHBoxLayout()

        self.btn_authenticate = QPushButton("Authenticate on GEE")
        self.btn_reset_auth = QPushButton("Reset Authentication")

        self.project_id_input = QLineEdit()
        self.project_id_input.setPlaceholderText("Project ID")

        auth_layout.addWidget(self.btn_authenticate)
        auth_layout.addWidget(self.btn_reset_auth)
        auth_layout.addWidget(QLabel("Project ID:"))
        auth_layout.addWidget(self.project_id_input)

        main_layout.addLayout(auth_layout)
        main_layout.addStretch()

    def _setup_aoi_page(self):
        """Set up the AOI page with a polygon layer selector and load button."""
        layout = QVBoxLayout(self.aoi_page)

        layout.addWidget(QLabel("Select AOI Layer"))

        self.layer_combo = QgsMapLayerComboBox()
        self.layer_combo.setFilters(QgsMapLayerProxyModel.PolygonLayer)

        self.btn_download_dem = QPushButton("Download DEM")

        layout.addWidget(self.layer_combo)
        layout.addWidget(self.btn_download_dem)

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
