import tempfile
import ee
import requests

from .dem_registry import DEMRegistry


class DEMService:
    """Service for downloading DEM data from Google Earth Engine."""

    @staticmethod
    def download_dem(aoi_feature_collection, dataset_name):
        """
        Download a DEM clipped to the given AOI and save it as a GeoTIFF.

        Args:
            aoi_feature_collection: Earth Engine FeatureCollection defining the area of interest.
            dataset_name: Name of the DEM dataset as registered in the catalog.

        Returns:
            Absolute path to the downloaded GeoTIFF file.
        """
        geometry = aoi_feature_collection.geometry()
        registry = DEMRegistry()
        dem = registry.get_image(dataset_name)

        final_image = dem.toFloat()
        mask = ee.Image(1).clip(geometry).mask()
        final_image_masked = final_image.updateMask(mask)

        url = final_image_masked.getDownloadURL(
            {"scale": 30, "region": geometry.bounds().getInfo(), "format": "GeoTIFF"}
        )

        response = requests.get(url)
        temp_file = tempfile.NamedTemporaryFile(suffix=".tif", delete=False)
        with open(temp_file.name, "wb") as file:
            file.write(response.content)

        return temp_file.name
