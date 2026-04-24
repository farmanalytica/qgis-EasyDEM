import ee
import json
from pathlib import Path


def geometry_bounds(aoi):
    """
    Extract the bounding box of an EE geometry or feature.

    Args:
        aoi: An ee.Geometry or an object with a .geometry() method
             (e.g. ee.FeatureCollection).

    Returns:
        Tuple of (ee.Geometry, (min_x, min_y, max_x, max_y)).
    """
    if isinstance(aoi, ee.Geometry):
        geom = aoi
    else:
        geom = aoi.geometry()

    bounds_info = geom.bounds().getInfo()
    coords = bounds_info["coordinates"][0]

    xs = [p[0] for p in coords]
    ys = [p[1] for p in coords]

    return geom, (min(xs), min(ys), max(xs), max(ys))


def bbox_intersects(a, b):
    """
    Check whether two axis-aligned bounding boxes overlap.

    Args:
        a: Bounding box as (min_x, min_y, max_x, max_y).
        b: Bounding box as (min_x, min_y, max_x, max_y).

    Returns:
        True if the boxes intersect, False otherwise.
    """
    return not (a[2] < b[0] or b[2] < a[0] or a[3] < b[1] or b[3] < a[1])


class DEMDataset:
    """Represents a single DEM dataset entry from the catalog."""

    def __init__(self, **kwargs):
        self.name = kwargs["name"]
        self.collection = kwargs["collection"]
        self.band = kwargs["band"]
        self.resolution = kwargs["resolution"]
        self.description = kwargs["description"]
        self.is_global = kwargs["is_global"]
        self.is_collection = kwargs["is_collection"]
        self.coverage_bbox = kwargs.get("coverage_bbox")
        self.info = kwargs["info"]

    def get_image(self) -> ee.Image:
        """
        Return the Earth Engine image for this dataset.

        Returns:
            Mosaicked ee.Image from the collection, or a single ee.Image.
        """
        if self.is_collection:
            return ee.ImageCollection(self.collection).select(self.band).mosaic()
        return ee.Image(self.collection).select(self.band)


class DEMRegistry:
    """
    Registry of available DEM datasets loaded from the catalog JSON.

    Provides lookup and availability-check operations against Google Earth Engine.
    """

    def __init__(self):
        catalog_path = Path(__file__).parent.parent / "assets" / "dem_catalog.json"

        with open(catalog_path, encoding="utf-8") as f:
            data = json.load(f)

        self._datasets = {d["name"]: DEMDataset(**d) for d in data}

    def list_datasets(self):
        """
        Return all registered DEM datasets.

        Returns:
            List of DEMDataset objects.
        """
        return list(self._datasets.values())

    def get_dataset(self, name: str) -> DEMDataset:
        """
        Retrieve a dataset by name.

        Args:
            name: Dataset name as defined in the catalog.

        Returns:
            DEMDataset instance.

        Raises:
            ValueError: If no dataset with the given name exists.
        """
        if name not in self._datasets:
            raise ValueError(f"Dataset '{name}' not found.")
        return self._datasets[name]

    def get_image(self, name: str) -> ee.Image:
        """
        Return the Earth Engine image for a named dataset.

        Args:
            name: Dataset name as defined in the catalog.

        Returns:
            ee.Image for the requested dataset.
        """
        return self.get_dataset(name).get_image()

    def is_available(self, name: str, region, aoi_bbox=None) -> bool:
        """
        Check whether a dataset has coverage over the given region in Earth Engine.

        Performs a bounding-box pre-filter, then queries EE to confirm actual data presence.

        Args:
            name: Dataset name as defined in the catalog.
            region: An ee.Geometry or object with a .geometry() method.
            aoi_bbox: Optional pre-computed (min_x, min_y, max_x, max_y) in EPSG:4326.
                      When provided, skips the remote GEE bounds call.

        Returns:
            True if the dataset covers the region, False otherwise.
        """
        dataset = self.get_dataset(name)

        if aoi_bbox is None:
            geom, aoi_bbox = geometry_bounds(region)
        else:
            geom = region if isinstance(region, ee.Geometry) else region.geometry()

        if dataset.coverage_bbox:
            if not bbox_intersects(dataset.coverage_bbox, aoi_bbox):
                return False

        try:
            if dataset.is_collection:
                return (
                    ee.ImageCollection(dataset.collection)
                    .filterBounds(geom)
                    .size()
                    .getInfo()
                    > 0
                )

            else:
                image = ee.Image(dataset.collection)

                reduced = image.reduceRegion(
                    reducer=ee.Reducer.count(),
                    geometry=geom,
                    scale=1000,
                    maxPixels=1e6,
                )

                val = reduced.get(dataset.band)
                return val.getInfo() > 0 if val else False

        except Exception:
            return False
