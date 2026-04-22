import ee


class DEMDataset:
    def __init__(
        self, key, name, collection, band, resolution, description, is_collection
    ):
        self.key = key
        self.name = name
        self.collection = collection
        self.band = band
        self.resolution = resolution
        self.description = description
        self.is_collection = is_collection

    def get_image(self) -> ee.Image:
        """Return a single ee.Image from the dataset"""
        if self.is_collection:
            return ee.ImageCollection(self.collection).select(self.band).mosaic()
        else:
            return ee.Image(self.collection).select(self.band)


class DEMRegistry:
    def __init__(self):
        self._datasets = {
            "COPERNICUS_30": DEMDataset(
                key="COPERNICUS_30",
                name="Copernicus GLO-30",
                collection="COPERNICUS/DEM/GLO30",
                band="DEM",
                resolution=30,
                description="Copernicus DEM GLO-30 at 30m resolution, derived from TanDEM-X radar data (2011-2015)",
                is_collection=True,
            ),
            "NASADEM": DEMDataset(
                key="NASADEM",
                name="NASADEM",
                collection="NASA/NASADEM_HGT/001",
                band="elevation",
                resolution=30,
                description="Reprocessed SRTM data with improved void filling and vertical accuracy (2000)",
                is_collection=False,
            ),
            "SRTM": DEMDataset(
                key="SRTM",
                name="SRTM GL1 v003",
                collection="USGS/SRTMGL1_003",
                band="elevation",
                resolution=30,
                description="Shuttle Radar Topography Mission 1 arc-second global DEM (2000)",
                is_collection=False,
            ),
            "CGIAR": DEMDataset(
                key="CGIAR",
                name="CGIAR SRTM v4",
                collection="CGIAR/SRTM90_V4",
                band="elevation",
                resolution=90,
                description="SRTM 90m DEM with void-filling applied by CGIAR (2000)",
                is_collection=False,
            ),
            "ASTER": DEMDataset(
                key="ASTER",
                name="ASTER GDEM v3",
                collection="projects/sat-io/open-datasets/ASTER/GDEM",
                band="b1",
                resolution=30,
                description="Advanced Spaceborne Thermal Emission and Reflection Radiometer Global DEM v3 (1999-2011)",
                is_collection=False,
            ),
            "ALOS": DEMDataset(
                key="ALOS",
                name="ALOS AW3D30 v4.1",
                collection="JAXA/ALOS/AW3D30/V4_1",
                band="DSM",
                resolution=30,
                description="ALOS World 3D 30m DSM derived from PRISM optical stereo imagery (2006-2011)",
                is_collection=True,
            ),
            "MERIT": DEMDataset(
                key="MERIT",
                name="MERIT DEM v1.0.3",
                collection="MERIT/DEM/v1_0_3",
                band="dem",
                resolution=90,
                description="Multi-Error-Removed Improved-Terrain DEM with noise and artifact removal (SRTM/AW3D30 base)",
                is_collection=False,
            ),
            "GMTED2010": DEMDataset(
                key="GMTED2010",
                name="GMTED2010",
                collection="USGS/GMTED2010_FULL",
                band="be75",
                resolution=250,
                description="Global Multi-resolution Terrain Elevation Data 2010 at 7.5 arc-second resolution",
                is_collection=False,
            ),
            "GTOPO30": DEMDataset(
                key="GTOPO30",
                name="GTOPO30",
                collection="USGS/GTOPO30",
                band="elevation",
                resolution=1000,
                description="Global 30 arc-second (~1km) DEM compiled from various raster and vector sources (1996)",
                is_collection=False,
            ),
            "ETOPO1": DEMDataset(
                key="ETOPO1",
                name="ETOPO1",
                collection="NOAA/NGDC/ETOPO1",
                band="bedrock",
                resolution=1800,
                description="1 arc-minute global relief model of Earth's surface including ocean bathymetry (2008)",
                is_collection=False,
            ),
            "USGS 1M": DEMDataset(
                key="USGS 1M",
                name="USGS 3DEP 1m",
                collection="USGS/3DEP/1m",
                band="elevation",
                resolution=1,
                description="3D Elevation Program LiDAR-derived 1m DTM for available areas of the United States",
                is_collection=True,
            ),
            "USGS 10M": DEMDataset(
                key="USGS 10M",
                name="USGS 3DEP 10m",
                collection="USGS/3DEP/10m_collection",
                band="elevation",
                resolution=10,
                description="3D Elevation Program 10m DEM for the contiguous US, Alaska, and Hawaii",
                is_collection=True,
            ),
            "NEON DEM": DEMDataset(
                key="NEON DEM",
                name="NEON DEM",
                collection="projects/neon-prod-earthengine/assets/DEM/001",
                band="DTM",
                resolution=1,
                description="National Ecological Observatory Network 1m LiDAR DEM for ecological field sites across the USA",
                is_collection=True,
            ),
            "CDEM": DEMDataset(
                key="CDEM",
                name="Canadian Digital Elevation Model (CDEM)",
                collection="NRCan/CDEM",
                band="elevation",
                resolution=23,
                description="Multi-resolution mosaic DEM for Canada derived from various sources (1945-2011)",
                is_collection=True,
            ),
            "5M DEM": DEMDataset(
                key="5M DEM",
                name="Australia 5m DEM",
                collection="AU/GA/AUSTRALIA_5M_DEM",
                band="elevation",
                resolution=5,
                description="High-resolution 5m DEM for Australia derived from LiDAR and photogrammetry data",
                is_collection=True,
            ),
            "DEM-S": DEMDataset(
                key="DEM-S",
                name="Australia DEM-S (Smoothed)",
                collection="AU/GA/DEM_1SEC/v10/DEM-S",
                band="elevation",
                resolution=30,
                description="1 arc-second (~30m) smoothed DEM of Australia, hydrologically conditioned surface",
                is_collection=False,
            ),
            "DEM-H": DEMDataset(
                key="DEM-H",
                name="Australia DEM-H (Hydrologically Enforced)",
                collection="AU/GA/DEM_1SEC/v10/DEM-H",
                band="elevation",
                resolution=30,
                description="1 arc-second (~30m) hydrologically enforced DEM of Australia with stream and catchment consistency",
                is_collection=False,
            ),
            "ARTICDEM V4": DEMDataset(
                key="ARTICDEM V4",
                name="ArcticDEM Mosaic V4.1 (2m)",
                collection="UMN/PGC/ArcticDEM/V4/2m_mosaic",
                band="elevation",
                resolution=2,
                description="2m resolution mosaic DEM for the Arctic from stereo satellite imagery (2012-2020)",
                is_collection=True,
            ),
            "ARTICDEM V3": DEMDataset(
                key="ARTICDEM V3",
                name="ArcticDEM Strips V3 (2m)",
                collection="UMN/PGC/ArcticDEM/V3/2m",
                band="elevation",
                resolution=2,
                description="Individual 2m strip DEMs for the Arctic from stereo satellite imagery (2009-2017)",
                is_collection=False,
            ),
            "GIMP": DEMDataset(
                key="GIMP",
                name="Greenland GIMP DEM",
                collection="OSU/GIMP/DEM",
                band="elevation",
                resolution=30,
                description="Greenland Ice Mapping Project DEM at 30m from ASTER and SPOT-5 imagery",
                is_collection=False,
            ),
            "REMA MOSAIC": DEMDataset(
                key="REMA MOSAIC",
                name="REMA Mosaic v1.1 (8m)",
                collection="UMN/PGC/REMA/V1_1/8m",
                band="elevation",
                resolution=8,
                description="Reference Elevation Model of Antarctica 8m mosaic from stereo optical imagery (2009-2018)",
                is_collection=False,
            ),
            "REMA 2M": DEMDataset(
                key="REMA 2M",
                name="REMA Strips v1 (2m)",
                collection="UMN/PGC/REMA/V1/2m",
                band="elevation",
                resolution=2,
                description="Individual 2m strip DEMs for Antarctica from stereo optical imagery (2009-2018)",
                is_collection=True,
            ),
            "REMA 8M": DEMDataset(
                key="REMA 8M",
                name="REMA Strips v1 (8m)",
                collection="UMN/PGC/REMA/V1/8m",
                band="elevation",
                resolution=8,
                description="Individual 8m strip DEMs for Antarctica from stereo optical imagery (2009-2018)",
                is_collection=True,
            ),
            "CRYOSAT-2": DEMDataset(
                key="CRYOSAT-2",
                name="CryoSat-2 Antarctica DEM",
                collection="CPOM/CryoSat2/ANTARCTICA_DEM",
                band="elevation",
                resolution=1000,
                description="1km DEM of Antarctica derived from CryoSat-2 radar altimetry (2010-2016)",
                is_collection=False,
            ),
            "DTM": DEMDataset(
                key="DTM",
                name="England 1m Terrain (DTM)",
                collection="UK/EA/ENGLAND_1M_TERRAIN/2022",
                band="dtm",
                resolution=1,
                description="1m composite DTM and DSM for England from airborne LiDAR surveys (2000-2022)",
                is_collection=False,
            ),
            "RTE ALTI": DEMDataset(
                key="RTE ALTI",
                name="France RGE ALTI 1m",
                collection="IGN/RGE_ALTI/1M/2_0",
                band="MNT",
                resolution=1,
                description="1m national DTM for Metropolitan France from airborne LiDAR and aerial surveys (2009-2021)",
                is_collection=True,
            ),
            "AHN2 INTERPOLATED": DEMDataset(
                key="AHN2 INTERPOLATED",
                name="Netherlands AHN2 0.5m (Interpolated)",
                collection="AHN/AHN2_05M_INT",
                band="elevation",
                resolution=0.5,
                description="0.5m LiDAR DEM for the Netherlands with void interpolation applied (2007-2012)",
                is_collection=False,
            ),
            "AHN2 NON-INTERPOLATED": DEMDataset(
                key="AHN2 NON-INTERPOLATED",
                name="Netherlands AHN2 0.5m (Non-interpolated)",
                collection="AHN/AHN2_05M_NON",
                band="elevation",
                resolution=0.5,
                description="0.5m LiDAR DEM for the Netherlands without void interpolation (2007-2012)",
                is_collection=False,
            ),
            "AHN2 RAW SAMPLES": DEMDataset(
                key="AHN2 RAW SAMPLES",
                name="Netherlands AHN2 0.5m (Raw Samples)",
                collection="AHN/AHN2_05M_RUW",
                band="elevation",
                resolution=0.5,
                description="0.5m raw LiDAR sample points rasterized for the Netherlands (2007-2012)",
                is_collection=False,
            ),
            "AHN3": DEMDataset(
                key="AHN3",
                name="Netherlands AHN3 0.5m",
                collection="AHN/AHN3",
                band="dtm",
                resolution=0.5,
                description="0.5m LiDAR DTM and DSM for the Netherlands, third acquisition cycle (2014-2019)",
                is_collection=True,
            ),
            "AHN4": DEMDataset(
                key="AHN4",
                name="Netherlands AHN4 0.5m",
                collection="AHN/AHN4",
                band="dtm",
                resolution=0.5,
                description="0.5m LiDAR DTM and DSM for the Netherlands, fourth acquisition cycle (2020-2022)",
                is_collection=True,
            ),
            "GLOBATHY": DEMDataset(
                key="GLOBATHY",
                name="GLOBathy Global Lakes Bathymetry",
                collection="projects/sat-io/open-datasets/GLOBathy/GLOBathy_bathymetry",
                band="b1",
                resolution=30,
                description="30m maximum depth bathymetry for 1.4 million global lakes and reservoirs (2022)",
                is_collection=False,
            ),
        }

    def list_datasets(self):
        """Return all datasets"""
        return list(self._datasets.values())

    def get_dataset(self, key: str) -> DEMDataset:
        """Return an specific dataset searched by key"""
        if key not in self._datasets:
            raise ValueError(f"Dataset '{key}' not found.")
        return self._datasets[key]

    def get_image(self, key: str) -> ee.Image:
        """Return a dataset image"""

        dataset = self.get_dataset(key)
        return dataset.get_image()

    def is_available(self, key: str, region: ee.Geometry) -> bool:
        """
        Return true if the dataset is available in the loaded image region

        Args:
            key: data registry key
            region: ee region

        Returns:
            True if the dataset is availible in that region and false if it is'nt
        """
        dataset = self.get_dataset(key)

        try:
            if dataset.is_collection:
                collection = ee.ImageCollection(dataset.collection)
                count = collection.filterBounds(region).size()

                return count.getInfo() > 0

            else:
                image = ee.Image(dataset.collection)
                intersection = image.geometry().intersection(region, 1)

                return intersection.area().getInfo() > 0

        except Exception:
            return False
