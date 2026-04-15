import tempfile

import ee
import requests


class DEMService:
    """Service for downloading DEM data from Google Earth Engine."""

    @staticmethod
    def download_dem(aoi_feature_collection):
        """
        Download a Copernicus GLO-30 DEM clipped to the given AOI and save it as a GeoTIFF.

        Args:
            aoi_feature_collection: Earth Engine FeatureCollection defining the area of interest.

        Returns:
            Absolute path to the downloaded GeoTIFF file.
        """
        geometry = aoi_feature_collection.geometry()

        dem = (
            ee.ImageCollection("COPERNICUS/DEM/GLO30")
            .select("DEM")
            .mosaic()
            .clip(geometry)
        )
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
