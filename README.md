# EasyDEM

EasyDEM is a QGIS plugin that lets GIS analysts download and visualise Digital
Elevation Models (DEMs) directly inside QGIS, without leaving the desktop
environment.  Datasets are fetched on-demand from **Google Earth Engine** (GEE)
and clipped to a user-defined polygon Area of Interest (AOI), then loaded as a
styled raster layer with a Magma colour ramp.

The plugin targets field teams and analysts at agricultural and environmental
organisations who need quick access to elevation data over arbitrary boundaries
without writing GEE scripts.

**Requirements:** a Google Earth Engine account and a Google Cloud Console
project with the Earth Engine API enabled.

---

## Project Structure

```
qgis-EasyDEM/
├── __init__.py          # QGIS entry point — registers the plugin via classFactory()
├── easy.py              # Plugin controller — owns the QGIS lifecycle (initGui, unload, run)
├── easy_dialog.py       # UI layer — dialog window and widget definitions
├── dem_handler.py       # DEM handler — bridges dialog events to DEM services and QGIS rendering
├── resources.py         # Compiled Qt resources (icons, etc.)
├── pavement.py          # Build/dev task automation (paver)
├── assets/
│   └── dem_catalog.json # DEM dataset definitions (name, collection, band, resolution, bbox)
└── services/
    ├── __init__.py      # Exports service classes
    ├── gee_service.py   # Google Earth Engine business logic
    ├── aoi_service.py   # AOI extraction and conversion to EE objects
    ├── dem_service.py   # Downloads DEM GeoTIFF from Google Earth Engine
    └── dem_registry.py  # Loads and queries the DEM catalog; checks dataset availability
```

---

## Architecture

The codebase follows a **UI / Service** separation:

### `easy.py` — Plugin Controller
The QGIS plugin entry point. Handles toolbar/menu registration (`initGui`), teardown (`unload`), and launches the dialog (`run`). On first run it instantiates `GEEService`, `DEMHandler`, and connects all dialog signals to their handlers — this is the only place UI and services are wired together.

### `easy_dialog.py` — UI Layer
Contains `EasyDemDialog(QDialog)`. Responsible only for building widgets. It has no knowledge of services or the `ee` SDK — all signal connections are made externally by the controller.

Internal conventions:
- `_setup_ui()` — constructs and arranges all widgets
- Two pages managed by a `QStackedWidget`: `auth_page` shown on first open, `aoi_page` shown after successful authentication

Current widgets:
| Widget | Attribute | Page | Purpose |
|---|---|---|---|
| QPushButton | `btn_authenticate` | auth | Triggers GEE authentication |
| QPushButton | `btn_reset_auth` | auth | Resets existing GEE credentials |
| QLineEdit | `project_id_input` | auth | User-supplied GCP project ID |
| QgsMapLayerComboBox | `layer_combo` | aoi | Polygon layer selector for AOI |
| QComboBox | `dem_combo` | aoi | Lists DEM datasets available for the selected AOI |
| QTextBrowser | `dem_info` | aoi | Shows selected DEM dataset info |
| QPushButton | `btn_download_dem` | aoi | Downloads and loads the selected DEM into QGIS |

### `dem_handler.py` — DEM Handler
Contains `DEMHandler`. Bridges dialog events to the DEM services and owns the QGIS rendering pipeline. It holds the current AOI state and coordinates calls between `AOIService`, `DEMRegistry`, and `DEMService`. Requires the QGIS `interface` (`iface`) at construction for map canvas access.

| Method | Signature | Purpose |
|---|---|---|
| `handle_layer_changed` | `(layer)` | Zooms the map canvas to the selected layer, then updates the stored AOI and refreshes the dataset combobox |
| `load_available_datasets` | `()` | Queries `DEMRegistry` for datasets available in the current AOI and populates `dem_combo` |
| `handle_dem_service` | `(interface)` | Downloads the selected DEM and loads it into QGIS with a Magma color ramp |

### `services/gee_service.py` — GEE Service
Contains `GEEService`. Imports `ee` and owns all Earth Engine SDK calls.

| Method | Signature | Purpose |
|---|---|---|
| `authenticate` | `(project_id: str)` | Authenticates with GEE using the given project |
| `reset_authentication` | `()` | Clears stored GEE credentials |

### `services/aoi_service.py` — AOI Service
Contains `AOIService`. Extracts geometry from a QGIS layer and converts it to an `ee.FeatureCollection`.

| Method | Signature | Purpose |
|---|---|---|
| `get_aoi_from_layer` | `(layer: QgsVectorLayer)` | Returns `(ee.FeatureCollection, bbox)` from a layer object; bbox is `(min_x, min_y, max_x, max_y)` in EPSG:4326, computed locally from the QGIS geometry |
| `get_aoi_from_layer_id` | `(layer_id: str)` | Same, but looks up the layer by ID from the current project |

### `services/dem_service.py` — DEM Service
Contains `DEMService`. Downloads a DEM GeoTIFF from Google Earth Engine for a given AOI and dataset.

| Method | Signature | Purpose |
|---|---|---|
| `download_dem` | `(aoi_feature_collection, dataset_name: str)` | Clips the selected EE image to the AOI, downloads it as a GeoTIFF, and returns the temporary file path |

### `services/dem_registry.py` — DEM Registry
Contains `DEMDataset` and `DEMRegistry`. Loads dataset definitions from `assets/dem_catalog.json` and provides lookup and availability-check operations against Google Earth Engine.

| Method | Signature | Purpose |
|---|---|---|
| `list_datasets` | `()` | Returns all registered `DEMDataset` objects |
| `get_dataset` | `(name: str)` | Returns the `DEMDataset` for the given name |
| `get_image` | `(name: str)` | Returns the `ee.Image` for the given dataset |
| `is_available` | `(name: str, region, aoi_bbox=None)` | Checks whether the dataset has EE coverage over the given geometry; pass pre-computed `aoi_bbox` to skip the remote GEE bounds call |

---

## Adding a New Feature

1. **UI changes** — edit `easy_dialog.py`. Add widgets in `_setup_ui`.
2. **Business logic** — add a method to `GEEService` (or create a new service file under `services/`).
3. **Wire them up** — in `easy.py`, connect the new widget's signal to the service method.

> Keep the dialog ignorant of the GEE SDK. Keep the service ignorant of Qt widgets.

---

## For LLMs and AI Agents

If you are an AI assistant working on this codebase, read this before making changes.

**Layer boundaries — never cross these:**
- The UI (`easy_dialog.py`) must not import `ee` or any service directly.
- Services (`services/`) must not import Qt widgets or reference QGIS APIs.
- `easy.py` is the only file allowed to wire UI to services.

**Where things live:**
- New widgets → `easy_dialog.py` (`_setup_ui`)
- New signal connections → `easy.py` (inside the `if self.first_start` block in `run()`)
- New DEM handler logic (layer events, rendering) → `dem_handler.py`
- New GEE logic → `services/gee_service.py`
- New AOI/geometry logic → `services/aoi_service.py`
- New DEM download logic → `services/dem_service.py`
- New DEM dataset entries → `assets/dem_catalog.json`
- New unrelated service → new file under `services/`, exported from `services/__init__.py`

---

## Development Setup

This plugin targets **QGIS LTR**.

**Clone the repository**

Clone directly into the QGIS plugins folder so QGIS can discover it:

```bash
# Windows (QGIS LTR default location)
cd %APPDATA%\QGIS\QGIS3\profiles\default\python\plugins
git clone https://github.com/farmanalytica/qgis-EasyDEM
```

**Build tasks**

`pavement.py` contains automation tasks (via [Paver](https://pythonhosted.org/Paver/)).  Run `paver` from the project root to list available tasks.  After running the relevant Paver task, dependencies are installed directly into the QGIS Python environment — no separate virtual environment is needed.

**Hot-reload during development**

Install the [Plugin Reloader](https://plugins.qgis.org/plugins/plugin_reloader/) QGIS plugin to reload EasyDEM without restarting QGIS after each code change.
