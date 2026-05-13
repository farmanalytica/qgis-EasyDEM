# -*- coding: utf-8 -*-
"""
DEM handler orchestration module for EasyDEM QGIS plugin.

Orchestrates DEM operations, AOI management, and coordinates between
services for dataset loading and layer rendering.
"""

from qgis.core import (
    QgsProject,
    QgsCoordinateTransform,
)

from qgis.PyQt.QtWidgets import QApplication, QFileDialog
from qgis.PyQt.QtCore import Qt, QTimer, QCoreApplication


try:
    from qgis.PyQt.QtCore import Qt

    WAIT_CURSOR = Qt.CursorShape.WaitCursor
except AttributeError:
    from qgis.PyQt.QtCore import Qt

    WAIT_CURSOR = Qt.WaitCursor

from .services.map_utils import hybrid_function
from .services.aoi_service import AOIService
from .services.dem_service import DEMService
from .services.dem_renderer import DEMRenderer
from .services.dataset_manager import DatasetManager
from .services.settings_manager import SettingsManager
from .services.dem_registry import DEMRegistry


def _tr(text):
    return QCoreApplication.translate("EasyDem", text)


class DEMHandler:
    """
    Orchestrates DEM operations and coordinates between services.

    Manages AOI-based dataset loading, DEM service calls, and layer
    management across the plugin.
    """

    def __init__(self, dialog, gee_service, interface):
        self.dlg = dialog
        self.gee_service = gee_service
        self.interface = interface
        self.current_aoi = None
        self.current_aoi_bbox = None
        self._pending_layer = None
        self._debounce_timer = QTimer()
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.timeout.connect(self._load_aoi_for_pending_layer)

    def handle_get_aoi(self):
        """Load the AOI from the selected layer and store it for downstream use."""
        try:
            layer = self.dlg.layer_combo.currentLayer()

            if not layer:
                self.dlg.pop_message(_tr("Select a layer."), "warning")
                return

            self.current_aoi, self.current_aoi_bbox = AOIService.get_aoi_from_layer(
                layer
            )

            self.load_available_datasets()

        except Exception as e:
            self.dlg.pop_message(str(e), "warning")

    def handle_dem_service(self, interface):
        """
        Download the selected DEM and load it into QGIS.

        The file is saved to the folder chosen by the user via the Browse
        button. When no folder is selected, it falls back to the system's
        temporary directory.

        Args:
            interface: The QGIS interface instance for message bar.
        """

        if not self.gee_service.is_authenticated:
            self.dlg.pop_message(
                _tr(
                    "Authentication is required to download DEM data. "
                    "Please go to the Auth page and validate your Google Cloud project ID."
                ),
                "warning",
            )
            return

        if not self.current_aoi:
            self.dlg.pop_message(
                _tr("No AOI selected. Please select a layer first."), "warning"
            )
            return

        dataset_name = self.dlg.dem_combo.currentData()
        if not dataset_name:
            self.dlg.pop_message(_tr("No dataset selected."), "warning")
            return

        output_folder = self.dlg.folder_input.text().strip() or None
        buffer_m = self.dlg.buffer_slider.value()
        aoi = self._apply_buffer(self.current_aoi, buffer_m)

        QApplication.setOverrideCursor(WAIT_CURSOR)
        QApplication.processEvents()

        try:
            dem_path = DEMService.download_dem(
                aoi, dataset_name, output_folder=output_folder
            )
            DEMRenderer.load_dem_to_qgis(dem_path, dataset_name)
            interface.messageBar().pushMessage(
                "EasyDEM", _tr("DEM '%s' loaded successfully.") % dataset_name
            )
        except Exception as e:
            self.dlg.pop_message(str(e), "warning")
        finally:
            QApplication.restoreOverrideCursor()

    def handle_layer_changed(self, layer):
        """
        Handle layer selection changes.

        Zooms the map canvas to the selected layer, then updates the current
        AOI and loads the available datasets for that region.

        Args:
            layer: The newly selected layer.
        """
        if not layer or not layer.isValid():
            self._debounce_timer.stop()
            self.current_aoi = None
            self.current_aoi_bbox = None
            self.dlg.dem_combo.clear()
            return

        canvas = self.interface.mapCanvas()
        transform = QgsCoordinateTransform(
            layer.crs(),
            canvas.mapSettings().destinationCrs(),
            QgsProject.instance(),
        )
        extent = transform.transformBoundingBox(layer.extent())
        extent.scale(1.8)
        canvas.setExtent(extent)
        canvas.refresh()

        self._pending_layer = layer
        self._debounce_timer.start(300)

    def _load_aoi_for_pending_layer(self):
        """Load AOI and available datasets for the debounced pending layer."""
        layer = self._pending_layer
        if not layer or not layer.isValid():
            self.current_aoi = None
            self.current_aoi_bbox = None
            self.dlg.dem_combo.clear()
            return
        try:
            self.current_aoi, self.current_aoi_bbox = AOIService.get_aoi_from_layer(
                layer
            )
            self.load_available_datasets()
        except Exception as e:
            self.dlg.pop_message(str(e), "warning")

    def load_available_datasets(self):
        """Load available datasets in the combobox based on current AOI.

        When the user is not authenticated, all datasets from the catalog are
        listed without any GEE availability check.  When authenticated, only
        datasets that intersect the current AOI are shown.
        """
        registry = DEMRegistry()
        self.dlg.dem_combo.clear()

        if not self.gee_service.is_authenticated:
            for dataset in registry.list_datasets():
                self.dlg.dem_combo.addItem(dataset.name, dataset.name)
            return

        if not self.current_aoi:
            return

        try:
            WAIT_CURSOR = Qt.CursorShape.WaitCursor
        except AttributeError:
            WAIT_CURSOR = Qt.WaitCursor
        QApplication.setOverrideCursor(WAIT_CURSOR)
        QApplication.processEvents()

        try:
            geometry = self.current_aoi.geometry()

            for dataset in registry.list_datasets():
                QApplication.processEvents()
                if registry.is_available(
                    dataset.name, geometry, aoi_bbox=self.current_aoi_bbox
                ):
                    self.dlg.dem_combo.addItem(dataset.name, dataset.name)
        finally:
            QApplication.restoreOverrideCursor()

    def handle_folder_selection(self):
        """Open a folder picker, persist the choice, and update the UI."""
        current_folder = SettingsManager.load_download_folder()

        folder = QFileDialog.getExistingDirectory(
            self.dlg,
            _tr("Select DEM Download Folder"),
            current_folder,
        )

        if folder:
            self.dlg.folder_input.setText(folder)
            SettingsManager.save_download_folder(folder)

    def on_dataset_changed(self):
        """Update the dataset info panel when the selected dataset changes."""
        DatasetManager.update_dataset_info(self.dlg.dem_combo, self.dlg.dem_info)

    def handle_hybrid_layer(self):
        """Load the Google hybrid basemap layer."""
        hybrid_function()
        self.interface.messageBar().pushMessage(
            "EasyDEM", _tr("Google Hybrid Layer loaded successfully")
        )

    def _apply_buffer(self, aoi, buffer_distance: int):
        """
        Return a buffered copy of the AOI without mutating the original.

        Args:
            aoi: ee.FeatureCollection representing the current AOI.
            buffer_distance: Buffer in metres.  Zero returns the original
                object unchanged.

        Returns:
            ee.FeatureCollection — buffered when distance != 0, original otherwise.
        """
        if buffer_distance == 0:
            return aoi
        return aoi.map(lambda feature: feature.buffer(buffer_distance))
