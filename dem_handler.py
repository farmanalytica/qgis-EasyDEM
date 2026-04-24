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
)

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

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

    def handle_get_aoi(self):
        """Load the AOI from the selected layer and store it for downstream use."""
        try:
            layer = self.dlg.layer_combo.currentLayer()

            if not layer:
                self.dlg.pop_message("Select a layer.", "warning")
                return

            self.current_aoi, self.current_aoi_bbox = AOIService.get_aoi_from_layer(layer)

            self.load_available_datasets()

        except Exception as e:
            self.dlg.pop_message(str(e), "warning")

    def handle_dem_service(self, interface):
        """
        Given a DEM, load it in QGIS.

        Args:
            interface: The QGIS interface instance for message bar.
        """
        dataset_name = self.dlg.dem_combo.currentData()

        QApplication.setOverrideCursor(Qt.WaitCursor)
        QApplication.processEvents()

        try:
            dem_path = DEMService.download_dem(self.current_aoi, dataset_name)
            self._load_dem_to_qgis(dem_path, dataset_name)
            interface.messageBar().pushMessage("DEM loaded.")
        finally:
            QApplication.restoreOverrideCursor()

    def handle_layer_changed(self, layer):
        """
        Handle layer selection changes.

        Zooms the map canvas to the selected layer, then uploads the current
        AOI and loads the available datasets of that region.

        Args:
            layer: The newly selected layer.
        """
        if layer:
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

        try:
            self.current_aoi, self.current_aoi_bbox = AOIService.get_aoi_from_layer(layer)

            self.load_available_datasets()

        except Exception as e:
            self.dlg.pop_message(str(e), "warning")

    def load_available_datasets(self):
        """Load available datasets in the combobox based on current AOI."""
        registry = DEMRegistry()

        self.dlg.dem_combo.clear()

        if not self.current_aoi:
            return

        QApplication.setOverrideCursor(Qt.WaitCursor)
        QApplication.processEvents()

        try:
            geometry = self.current_aoi.geometry()

            for dataset in registry.list_datasets():
                QApplication.processEvents()
                if registry.is_available(dataset.name, geometry, aoi_bbox=self.current_aoi_bbox):
                    self.dlg.dem_combo.addItem(dataset.name, dataset.name)
        finally:
            QApplication.restoreOverrideCursor()

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

    def _load_dem_to_qgis(self, path: str, dataset_name: str) -> QgsRasterLayer:
        """
        Load a DEM GeoTIFF into QGIS with a Magma color ramp renderer.

        Args:
            path: Absolute path to the GeoTIFF file.

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
