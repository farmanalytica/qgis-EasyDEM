# -*- coding: utf-8 -*-
"""
DEM rendering and styling module.

Handles color ramp creation and raster layer rendering with Magma color scheme.
"""

from qgis.core import (
    QgsRasterLayer,
    QgsColorRampShader,
    QgsProject,
    QgsRasterShader,
    QgsSingleBandPseudoColorRenderer,
    QgsStyle,
    QgsLayerTreeLayer,
)


class DEMRenderer:
    """Handles DEM rendering and layer styling with color ramps."""

    @staticmethod
    def build_color_renderer(
        provider, min_val, max_val
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

    @staticmethod
    def load_dem_to_qgis(path: str, dataset_name: str) -> QgsRasterLayer:
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

        renderer = DEMRenderer.build_color_renderer(provider, min_val, max_val)
        raster_layer.setRenderer(renderer)

        QgsProject.instance().addMapLayer(raster_layer, False)
        QgsProject.instance().layerTreeRoot().insertChildNode(
            0, QgsLayerTreeLayer(raster_layer)
        )
        raster_layer.triggerRepaint()

        return raster_layer
