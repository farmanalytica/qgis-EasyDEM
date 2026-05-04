# -*- coding: utf-8 -*-
"""
DEM handling, loading, and rendering module for EasyDEM QGIS plugin.

Handles DEM service operations, AOI management, dataset loading,
and color ramp rendering for raster layers.
"""

from qgis.core import (
    QgsRasterLayer,
    QgsColorRampShader,
    QgsProject,
    QgsRasterShader,
    QgsSingleBandPseudoColorRenderer,
    QgsStyle,
    QgsLayerTreeLayer,
    QgsCoordinateTransform,
    QgsSettings,
)

from qgis.PyQt.QtWidgets import QApplication, QFileDialog
from qgis.PyQt.QtCore import Qt, QTimer

from .services.aoi_service import AOIService
from .services.dem_service import DEMService
from .services.dem_registry import DEMRegistry


class DEMHandler:
    """
    Handles DEM operations, layer management, and rendering.

    Manages AOI-based dataset loading, DEM service calls, and
    visualization of raster data with color ramps.
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
                self.dlg.pop_message("Select a layer.", "warning")
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
        button.  When no folder is selected, it falls back to the system's
        temporary directory.

        Args:
            interface: The QGIS interface instance for message bar.
        """
        if not self.current_aoi:
            self.dlg.pop_message("No AOI selected. Please select a layer first.", "warning")
            return

        dataset_name = self.dlg.dem_combo.currentData()
        if not dataset_name:
            self.dlg.pop_message("No dataset selected.", "warning")
            return

        output_folder = self.dlg.folder_input.text().strip() or None

        try:
            WAIT_CURSOR = Qt.CursorShape.WaitCursor
        except AttributeError:
            WAIT_CURSOR = Qt.WaitCursor
        QApplication.setOverrideCursor(WAIT_CURSOR)
        QApplication.processEvents()

        try:
            dem_path = DEMService.download_dem(
                self.current_aoi, dataset_name, output_folder=output_folder
            )
            self._load_dem_to_qgis(dem_path, dataset_name)
            interface.messageBar().pushMessage(
                "EasyDEM", f"DEM '{dataset_name}' loaded successfully."
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
        """Load available datasets in the combobox based on current AOI."""
        registry = DEMRegistry()

        self.dlg.dem_combo.clear()

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

        current_folder = self.load_download_folder()

        folder = QFileDialog.getExistingDirectory(
            self.dlg,
            "Select DEM Download Folder",
            current_folder,
        )

        if folder:
            self.dlg.folder_input.setText(folder)
            self.save_download_folder(folder)

    def save_download_folder(self, folder_path):
        """Persist the chosen download folder in QGIS settings."""

        settings = QgsSettings()
        settings.setValue("qgis-EasyDEM/dem_download_folder", folder_path)

    def load_download_folder(self):
        """Return the previously saved download folder, or empty string."""

        settings = QgsSettings()
        return settings.value("qgis-EasyDEM/dem_download_folder", "", type=str)

    def _build_color_renderer(
        self, provider, min_val, max_val
    ) -> QgsSingleBandPseudoColorRenderer:
        """
        Build the color ramp for the layer.

        Args:
            provider: The raster data provider.
            min_val: Minimum value for the color ramp.
            max_val: Maximum value for the color ramp.

        Returns:
            A QgsSingleBandPseudoColorRenderer with Magma color ramp.

        Raises:
            RuntimeError: If the Magma color ramp is not found.
        """
        color_ramp = QgsStyle().defaultStyle().colorRamp("Magma")
        if not color_ramp:
            raise RuntimeError("Color ramp 'Magma' not found in QGIS style library.")

        num_stops = 5
        step = (max_val - min_val) / (num_stops - 1)
        color_ramp_items = [
            QgsColorRampShader.ColorRampItem(
                min_val + i * step, color_ramp.color(i / (num_stops - 1))
            )
            for i in range(num_stops)
        ]

        color_ramp_shader = QgsColorRampShader()
        color_ramp_shader.setColorRampType(QgsColorRampShader.Interpolated)
        color_ramp_shader.setColorRampItemList(color_ramp_items)

        raster_shader = QgsRasterShader()
        raster_shader.setRasterShaderFunction(color_ramp_shader)

        renderer = QgsSingleBandPseudoColorRenderer(provider, 1, raster_shader)
        renderer.setClassificationMin(min_val)
        renderer.setClassificationMax(max_val)
        return renderer

    def on_dataset_changed(self):
        """Update the dataset info panel when the selected dataset changes."""
        dataset_name = self.dlg.dem_combo.currentData()
        if not dataset_name:
            self.dlg.dem_info.clear()
            return

        registry = DEMRegistry()
        dataset = registry.get_dataset(dataset_name)
        self.dlg.dem_info.setHtml(dataset.info)

    def _load_dem_to_qgis(self, path: str, dataset_name: str) -> QgsRasterLayer:
        """
        Load a DEM GeoTIFF into QGIS with a Magma color ramp renderer.

        Args:
            path: Absolute path to the GeoTIFF file.
            dataset_name: Name used as the layer label in QGIS.

        Returns:
            The loaded and styled QgsRasterLayer.

        Raises:
            RuntimeError: If the raster layer is invalid.
        """
        raster_layer = QgsRasterLayer(path, dataset_name)
        if not raster_layer.isValid():
            raise RuntimeError("Failed to load DEM into QGIS.")

        provider = raster_layer.dataProvider()
        stats = provider.bandStatistics(1)
        min_val, max_val = stats.minimumValue, stats.maximumValue

        renderer = self._build_color_renderer(provider, min_val, max_val)
        raster_layer.setRenderer(renderer)

        QgsProject.instance().addMapLayer(raster_layer, False)
        QgsProject.instance().layerTreeRoot().insertChildNode(
            0, QgsLayerTreeLayer(raster_layer)
        )
        raster_layer.triggerRepaint()

        return raster_layer