# -*- coding: utf-8 -*-
"""
AOI service layer.

Extract and convert uploaded AOI geometries to EE objects.
"""

import json
import ee

from qgis.core import (
    QgsProject,
    QgsMapLayer,
    QgsWkbTypes,
    QgsGeometry,
    QgsCoordinateTransform,
    QgsCoordinateReferenceSystem,
)


def _strip_z(coords):
    """
    Remove Z dimension from GeoJSON coordinates recursively.
    Ensures compatibility with Earth Engine, which expects 2D coordinates.

    Args:
        coords: A coordinate or nested list of coordinates.

    Returns:
        Coordinate or nested list with only X and Y values.
    """
    if isinstance(coords[0], (int, float)):
        return coords[:2]
    return [_strip_z(c) for c in coords]


class AOIService:
    """Service for extracting and converting AOI geometries to Earth Engine objects."""

    @staticmethod
    def _validate_layer(layer):
        """
        Validate that a layer is a polygon vector layer.

        Args:
            layer: QgsMapLayer to validate.

        Raises:
            ValueError: If the layer is not a valid polygon vector layer.
        """
        if not layer or layer.type() != QgsMapLayer.VectorLayer:
            raise ValueError("Layer must be a valid vector layer.")

        if layer.geometryType() != QgsWkbTypes.PolygonGeometry:
            raise ValueError("Layer must be polygon or multipolygon.")

    @staticmethod
    def _get_layer_by_id(layer_id):
        """
        Retrieve and validate a layer from the current QGIS project by ID.

        Args:
            layer_id: String ID of the map layer.

        Returns:
            Validated QgsVectorLayer instance.

        Raises:
            ValueError: If the layer does not exist or is not a valid polygon vector layer.
        """
        layer = QgsProject.instance().mapLayer(layer_id)
        AOIService._validate_layer(layer)
        return layer

    @staticmethod
    def _get_geometry(layer):
        """
        Get the dissolved geometry from a layer's selected or all features.

        Uses selected features when a selection exists, otherwise uses all features.

        Args:
            layer: QgsVectorLayer to extract geometry from.

        Returns:
            QgsGeometry: Dissolved geometry of selected or all features.

        Raises:
            ValueError: If the layer contains no geometries.
        """

        features = layer.selectedFeatures() or list(layer.getFeatures())
        geometries = [f.geometry() for f in features]

        if not geometries:
            raise ValueError("Layer has no geometries.")

        return QgsGeometry.unaryUnion(geometries)

    @staticmethod
    def _to_ee_feature_collection(layer):
        """
        Convert a QGIS layer's geometry to an Earth Engine FeatureCollection.
        Ensures geometry is valid and compatible with Earth Engine requirements.
        Reprojects to EPSG:4326 if necessary, strips Z coordinates, and wraps
        the geometry in an ee.FeatureCollection.

        Args:
            layer: QgsVectorLayer to convert.

        Returns:
            Tuple of (ee.FeatureCollection, (min_x, min_y, max_x, max_y)) where
            bbox is in EPSG:4326, computed locally from the QGIS geometry.

        Raises:
            ValueError: If the geometry is empty or cannot be exported to GeoJSON.
        """
        geometry = AOIService._get_geometry(layer)

        if geometry.isEmpty():
            raise ValueError("Empty geometry.")

        if not geometry.isGeosValid():
            geometry = geometry.makeValid()

        if layer.crs().authid() != "EPSG:4326":
            transform = QgsCoordinateTransform(
                layer.crs(),
                QgsCoordinateReferenceSystem("EPSG:4326"),
                QgsProject.instance(),
            )
            geometry.transform(transform)

        rect = geometry.boundingBox()
        bbox = (rect.xMinimum(), rect.yMinimum(), rect.xMaximum(), rect.yMaximum())

        geojson_str = geometry.asJson()
        if not geojson_str:
            raise ValueError(
                f"Could not export geometry to GeoJSON. "
                f"Geometry type: {geometry.type()}, WKB type: {geometry.wkbType()}"
            )

        geojson = json.loads(geojson_str)
        geojson["coordinates"] = _strip_z(geojson["coordinates"])

        ee_geometry = ee.Geometry(geojson)
        return ee.FeatureCollection([ee.Feature(ee_geometry)]), bbox

    @staticmethod
    def get_aoi_from_layer(layer):
        """
        Get an Earth Engine FeatureCollection AOI from a QGIS layer object.

        Args:
            layer: QgsVectorLayer to use as AOI source.

        Returns:
            Tuple of (ee.FeatureCollection, (min_x, min_y, max_x, max_y)).

        Raises:
            ValueError: If the layer or its geometry is invalid.
        """
        AOIService._validate_layer(layer)
        return AOIService._to_ee_feature_collection(layer)

    @staticmethod
    def get_aoi_from_layer_id(layer_id):
        """
        Get an Earth Engine FeatureCollection AOI from a QGIS layer ID.

        Args:
            layer_id: String ID of the map layer in the current QGIS project.

        Returns:
            Tuple of (ee.FeatureCollection, (min_x, min_y, max_x, max_y)).

        Raises:
            ValueError: If the layer does not exist or its geometry is invalid.
        """
        layer = AOIService._get_layer_by_id(layer_id)
        return AOIService._to_ee_feature_collection(layer)
