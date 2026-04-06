# -*- coding: utf-8 -*-
"""
/***************************************************************************
 easydemDialog
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

from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QLabel,
)


class easydemDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle("EasyDEM")
        #self.resize(600, 300)

        # --- Auth row ---
        auth_layout = QHBoxLayout()

        self.btn_authenticate = QPushButton("Authenticate on GEE")
        self.btn_reset_auth = QPushButton("Reset Authentication")

        self.project_id_input = QLineEdit()
        self.project_id_input.setPlaceholderText("Project ID")

        auth_layout.addWidget(self.btn_authenticate)
        auth_layout.addWidget(self.btn_reset_auth)
        auth_layout.addWidget(QLabel("Project ID:"))
        auth_layout.addWidget(self.project_id_input)

        # --- Main layout ---
        main_layout = QVBoxLayout()
        main_layout.addLayout(auth_layout)
        main_layout.addStretch()
        self.setLayout(main_layout)

