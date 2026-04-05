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

try:
    import ee
    print("Google Earth Engine API imported successfully.")
except ImportError:
    print("Google Earth Engine API not found. Please install it using 'pip install earthengine-api'.")

from qgis.PyQt.QtWidgets import QDialog, QDialogButtonBox, QVBoxLayout


class easydemDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("EasyDEM")
        self.resize(400, 300)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addStretch()
        layout.addWidget(self.button_box)
        self.setLayout(layout)
