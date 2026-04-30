import os
import tempfile

import ee
import requests

from .dem_registry import DEMRegistry


class DEMService:
    """Service for downloading DEM data from Google Earth Engine."""

    @staticmethod
    def download_dem(aoi_feature_collection, dataset_name, output_folder=None):
        """
        Download a DEM clipped to the given AOI and save it as a GeoTIFF.

        Args:
            aoi_feature_collection: Earth Engine FeatureCollection defining the
                area of interest.
            dataset_name: Name of the DEM dataset as registered in the catalog.
            output_folder: Optional path to the destination folder.  When
                ``None`` (or empty), the file is saved to the system's default
                temporary directory.

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

        response = requests.get(url, timeout=300)
        if not response.ok:
            raise RuntimeError(
                f"DEM download failed (HTTP {response.status_code}): {response.reason}"
            )

        safe_name = dataset_name.replace(" ", "_").replace("/", "-")
        filename = f"EasyDEM_{safe_name}.tif"

        base_dir = output_folder if (output_folder and os.path.isdir(output_folder)) else tempfile.gettempdir()
        output_path = DEMService._resolve_path(base_dir, filename)

        with open(output_path, "wb") as f:
            f.write(response.content)

        return output_path

    @staticmethod
    def _resolve_path(folder: str, filename: str) -> str:
        """
        Return a path that does not overwrite an existing file.

        If ``<folder>/<filename>`` already exists, appends an incrementing
        integer suffix before the extension until a free name is found:
        ``dem.tif`` → ``dem_1.tif`` → ``dem_2.tif`` → …

        Args:
            folder: Destination directory.
            filename: Desired filename (e.g. ``EasyDEM_SRTM.tif``).

        Returns:
            Absolute path to a file that does not yet exist.
        """
        candidate = os.path.join(folder, filename)
        if not os.path.exists(candidate):
            return candidate

        name, ext = os.path.splitext(filename)
        counter = 1
        while True:
            candidate = os.path.join(folder, f"{name}_{counter}{ext}")
            if not os.path.exists(candidate):
                return candidate
            counter += 1