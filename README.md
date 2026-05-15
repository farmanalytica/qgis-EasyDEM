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
├── __init__.py              # QGIS entry point — registers the plugin via classFactory()
├── easy.py                  # Plugin controller — owns the QGIS lifecycle (initGui, unload, run)
├── easy_dialog.py           # UI layer — dialog shell (header, stack, footer) and page navigation
├── dem_handler.py           # DEM orchestration — coordinates AOI management and service calls
├── resources.py             # Compiled Qt resources (icons, etc.)
├── build_plugin.py          # Full build script — clean extlibs, install deps, compile translations, zip
├── compile_translations.py  # Compiles i18n/*.ts → *.qm without needing lrelease
├── extlibs_manager.py       # Background extlibs downloader (QThread); triggered by __init__.py on first run when extlibs/ is absent
├── assets/
│   └── dem_catalog.json     # DEM dataset definitions (name, collection, band, resolution, bbox)
├── i18n/
│   ├── easydem_pt_BR.ts/.qm # Portuguese (Brazil)
│   ├── easydem_fr.ts/.qm    # French
│   ├── easydem_it.ts/.qm    # Italian
│   ├── easydem_es.ts/.qm    # Spanish
│   ├── easydem_hi.ts/.qm    # Hindi
│   └── easydem_zh_CN.ts/.qm # Chinese (Simplified)
├── view/
│   ├── __init__.py          # View package marker
│   ├── auth.py              # Authentication page widget construction (setup_auth_page)
│   ├── download_dem.py      # AOI/DEM page widget construction (setup_download_dem_page)
│   ├── sidebar.py           # Permanent collapsible navigation sidebar (Sidebar, SidebarNavButton)
│   └── styles.py            # Shared Qt stylesheet constants (STYLE_DIALOG, STYLE_BTN_PRIMARY, …)
└── services/
    ├── __init__.py          # Exports service classes
    ├── gee_service.py       # Google Earth Engine business logic
    ├── aoi_service.py       # AOI extraction and conversion to EE objects
    ├── dem_service.py       # Downloads DEM GeoTIFF from Google Earth Engine
    ├── dem_registry.py      # Loads and queries the DEM catalog; checks dataset availability
    ├── dem_renderer.py      # Color ramp rendering and raster layer styling
    ├── dataset_manager.py   # Dataset availability queries and UI updates
    ├── settings_manager.py  # Settings persistence (QgsSettings)
    └── map_utils.py         # Map-related utility functions
```

---

## Architecture

The codebase follows a **UI / Service** separation:

### `easy.py` — Plugin Controller
The QGIS plugin entry point. Handles toolbar/menu registration (`initGui`), teardown (`unload`), and launches the dialog (`run`). Service instantiation (`GEEService`, `DEMHandler`) and all signal wiring are deferred to `_finish_init()`, which is called only once extlibs are confirmed ready — either already extracted on disk, or after `ExtlibsDownloader` finishes and emits `download_done`. Until extlibs are ready, `run()` shows the loading page and waits for the downloader signal. This is the only place UI and services are wired together.

### `easy_dialog.py` — UI Layer
Contains `EasyDemDialog(QDialog)`. Owns the dialog shell only: fixed header, central `QStackedWidget`, and fixed footer. Page widget construction is delegated to `view/auth.py` and `view/download_dem.py`. No knowledge of services or the `ee` SDK — all signal connections are made externally by the controller.

Internal conventions:
- `_setup_ui()` — builds header, body row (sidebar + stack), and footer; calls `setup_auth_page` and `setup_download_dem_page`
- `_build_header()` — white bar with brand label, dynamic page-title label (`_header_title`), and help button
- `_build_footer()` — FARM Analytica logo and attribution text
- `show_loading_page()` / `show_auth_page()` / `show_aoi_page()` — switch the active stack page
- `_sync_page_state(index)` — connected to `stack.currentChanged`; updates `_header_title` and calls `sidebar.set_active_page()` to keep navigation state in sync regardless of what triggers the page switch
- Three pages managed by a `QStackedWidget`: `loading_page` (first-run dependency download), `auth_page` (shown once extlibs are ready), `aoi_page` (shown after authentication or via the skip shortcut)
- Permanent `Sidebar` instance lives in the body row; its `auth_requested` and `download_requested` signals are connected to `_nav_to_auth` and `_nav_to_download`

### `view/` — Page Modules

Page widget construction is split into isolated modules. Each module exposes a single `setup_*` function that receives the dialog instance and its page widget, then attaches interactive widgets directly to the dialog so `easy.py` can wire signals without importing the modules.

#### `view/auth.py`
Builds the authentication page (`setup_auth_page`). Layout: left info column + right credential card + bottom browse-without-auth shortcut.

| Widget | Attribute | Purpose |
|---|---|---|
| `QgsPasswordLineEdit` | `project_id_input` | User-supplied GCP project ID |
| `QPushButton` | `btn_authenticate` | Validates ID and triggers GEE authentication |
| `QPushButton` | `btn_reset_auth` | Clears stored GEE credentials |
| `QPushButton` | `btn_go_to_aoi` | Skips authentication and navigates to AOI page |

#### `view/download_dem.py`
Builds the AOI and DEM download page (`setup_download_dem_page`). Layout: scrollable content area (inputs + metadata + buffer) above a fixed footer (folder picker + action buttons). Also defines `LimitedPopupComboBox`, a `QComboBox` subclass that caps popup height for long dataset catalogs.

| Widget | Attribute | Purpose |
|---|---|---|
| `QgsMapLayerComboBox` | `layer_combo` | Polygon layer selector for AOI |
| `LimitedPopupComboBox` | `dem_combo` | Lists DEM datasets available for the selected AOI |
| `QTextBrowser` | `dem_info` | Shows selected DEM dataset metadata |
| `QSlider` | `buffer_slider` | AOI buffer in metres (−300 … +300) |
| `QLabel` | `buffer_value_lbl` | Live display of current buffer value |
| `QLineEdit` | `folder_input` | Download destination path (read-only display) |
| `QPushButton` | `btn_browse_folder` | Opens folder picker dialog |
| `QPushButton` | `btn_hybrid_layer` | Adds a Google Hybrid basemap layer to QGIS |
| `QPushButton` | `btn_download_dem` | Downloads and loads the selected DEM into QGIS |

#### `view/sidebar.py`
Defines `Sidebar(QFrame)` and `SidebarNavButton(QPushButton)`. The sidebar is a permanent collapsible navigation rail shown on all pages. It collapses to 64 px (icon only) and expands to 184 px on hover via `QVariantAnimation`.

| Widget / method | Purpose |
|---|---|
| `btn_auth` | Navigates to the authentication page; emits `auth_requested` |
| `btn_download` | Navigates to the AOI/download page; emits `download_requested` |
| `set_active_page(page)` | Highlights the button matching `'auth'` or `'download'`; called by `_sync_page_state` in the dialog |

#### `view/styles.py`
Shared Qt stylesheet string constants imported by both page modules and `easy_dialog.py`.

| Constant | Applied to |
|---|---|
| `STYLE_DIALOG` | `QDialog` base — grey background, dark text, thin scrollbar |
| `STYLE_BTN_PRIMARY` | Solid green call-to-action buttons |
| `STYLE_BTN_SECONDARY` | White/green-border navigation buttons |
| `STYLE_BTN_HELP` | Circular "?" help button in the header |
| `STYLE_AOI_PAGE` | AOI page panel card, field labels, combo boxes, metadata browser |

### `dem_handler.py` — DEM Handler
Contains `DEMHandler`. Orchestrates DEM operations and coordinates between services. Owns the current AOI state and QGIS map canvas interactions. Delegates rendering, dataset management, and settings persistence to specialized services.

| Method | Signature | Purpose |
|---|---|---|
| `handle_layer_changed` | `(layer)` | Zooms the map canvas to the selected layer, then debounces 300 ms before loading the AOI and refreshing the dataset combobox |
| `load_available_datasets` | `()` | Queries `DEMRegistry` directly; lists all datasets when unauthenticated, otherwise filters by AOI coverage |
| `handle_dem_service` | `(interface)` | Downloads the selected DEM (with optional buffer) and delegates to `DEMRenderer` to load and style it in QGIS |
| `handle_folder_selection` | `()` | Opens a folder picker and delegates to `SettingsManager` to persist the choice |
| `on_dataset_changed` | `()` | Delegates to `DatasetManager` to update the dataset info panel |
| `handle_hybrid_layer` | `()` | Loads the Google Hybrid basemap via `map_utils.hybrid_function()` and reports success via the message bar |

### `services/gee_service.py` — GEE Service
Contains `GEEService`. Imports `ee` and owns all Earth Engine SDK calls.

| Method | Signature | Purpose |
|---|---|---|
| `get_saved_project_id` | `()` | Returns the saved GCP project ID from `QSettings`, or empty string |
| `save_project_id` | `(project_id)` | Persists the GCP project ID to `QSettings`; connected to `project_id_input.textChanged` |
| `authenticate` | `(project_id: str)` | Authenticates with GEE using the given project; sets `is_authenticated = True` on success |
| `reset_authentication` | `()` | Clears stored GEE credentials and resets `is_authenticated` |

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

### `services/dem_renderer.py` — DEM Renderer
Contains `DEMRenderer`. Handles color ramp creation and raster layer styling for DEM visualization.

| Method | Signature | Purpose |
|---|---|---|
| `build_color_renderer` | `(provider, min_val, max_val)` | Creates a `QgsSingleBandPseudoColorRenderer` with a Magma color ramp for the given value range |
| `load_dem_to_qgis` | `(path: str, dataset_name: str)` | Loads a DEM GeoTIFF into QGIS, applies the color renderer, and adds it to the layer tree at the top |

### `services/dataset_manager.py` — Dataset Manager
Contains `DatasetManager`. Manages dataset availability queries and UI updates for the dataset combobox and info panel.

| Method | Signature | Purpose |
|---|---|---|
| `load_available_datasets` | `(dem_combo, current_aoi, current_aoi_bbox, on_error=None)` | Queries `DEMRegistry` for available datasets and populates the given combobox; executes with a wait cursor |
| `update_dataset_info` | `(dem_combo, dem_info_widget)` | Updates the dataset info panel when a different dataset is selected in the combobox |

### `services/settings_manager.py` — Settings Manager
Contains `SettingsManager`. Handles persistence of user preferences in QGIS settings.

| Method | Signature | Purpose |
|---|---|---|
| `save_download_folder` | `(folder_path: str)` | Persists the chosen DEM download folder in `QgsSettings` |
| `load_download_folder` | `()` | Returns the previously saved download folder, or an empty string if not set |

---

## Translations

The plugin ships UI strings in 7 languages: English (default), Portuguese (pt\_BR), French (fr), Italian (it), Spanish (es), Hindi (hi), and Chinese Simplified (zh\_CN).

The translation system follows the Qt standard: `.ts` XML source files are compiled to binary `.qm` files that `QTranslator` loads at runtime. The active locale is read from QGIS (`Settings → Options → General → Override system locale`).

### How it works

`easy.py` installs a `QTranslator` on plugin load and removes it on unload. Every user-visible string in `view/`, `easy_dialog.py`, `dem_handler.py`, and `services/gee_service.py` is wrapped with `_tr()` — a thin helper over `QCoreApplication.translate("EasyDem", text)`.

### Editing translations

Edit the relevant `i18n/easydem_<locale>.ts` file (standard Qt TS XML — one `<message>` per string, `<source>` matches the English literal, `<translation>` holds the target language text), then recompile.

### Compiling `.ts` → `.qm`

OSGeo4W does not bundle `lrelease`. Use the included Python script instead. Run in the **OSGeo4W Shell**:

```bat
cd C:\OSGeo4W\apps\qgis-ltr\python\plugins\qgis-EasyDEM
python-qgis-ltr compile_translations.py
```

This writes a `.qm` binary next to each `.ts` file. Reload the plugin in QGIS to pick up changes.

### Adding a new language

1. Create `i18n/easydem_<locale>.ts` (copy an existing file, update `language=` attribute and all `<translation>` entries).
2. Add the locale to the mapping in `easy.py` if its 2-char prefix differs from the file suffix (e.g. `'pt': 'pt_BR'`).
3. Run `compile_translations.py`.

---

## Adding a New Feature

1. **UI changes** — add widgets in the appropriate page module (`view/auth.py` or `view/download_dem.py`). Attach them to `dialog` so `easy.py` can reach them. Add shared styles to `view/styles.py`.
2. **Business logic** — add a method to the relevant service (or create a new service file under `services/`).
3. **Wire them up** — in `easy.py`, connect the new widget's signal to the service method.
4. **Translations** — wrap every new user-visible string with `_tr()`. Add a matching `<message>` entry to each `i18n/easydem_<locale>.ts` file, then run `compile_translations.py`.

> Keep the dialog ignorant of the GEE SDK. Keep the service ignorant of Qt widgets.

---

## For LLMs and AI Agents

If you are an AI assistant working on this codebase, read this before making changes.

**Layer boundaries — never cross these:**
- The UI (`easy_dialog.py` and `view/`) must not import `ee` or any service directly.
- Services (`services/`) must not import Qt widgets or reference QGIS APIs.
- `easy.py` is the only file allowed to wire UI to services.

**Where things live:**
- New widgets on the auth page → `view/auth.py` (`setup_auth_page`)
- New widgets on the AOI/download page → `view/download_dem.py` (`setup_download_dem_page`)
- Sidebar navigation changes (buttons, icons, expand/collapse behaviour) → `view/sidebar.py`
- New shared stylesheet constants → `view/styles.py`
- New signal connections → `easy.py` (inside `_finish_init()`)
- New DEM handler/orchestration logic → `dem_handler.py`
- New rendering/styling logic → `services/dem_renderer.py`
- New dataset management logic → `services/dataset_manager.py`
- New settings persistence logic → `services/settings_manager.py`
- New GEE logic → `services/gee_service.py`
- New AOI/geometry logic → `services/aoi_service.py`
- New DEM download logic → `services/dem_service.py`
- New DEM dataset entries → `assets/dem_catalog.json`
- New unrelated service → new file under `services/`, exported from `services/__init__.py`

---

## Development Setup

This plugin supports **QGIS 3.x LTR** and **QGIS 4.0+**.

**Clone the repository**

Clone directly into the QGIS plugins folder so QGIS can discover it:

```bash
# Windows QGIS 3.x
cd %APPDATA%\QGIS\QGIS3\profiles\default\python\plugins

# Windows QGIS 4.0+
cd %APPDATA%\QGIS\profiles\default\python\plugins

# Linux QGIS 3.x
cd ~/.local/share/QGIS/QGIS3/profiles/default/python/plugins

# Linux QGIS 4.0+
cd ~/.local/share/QGIS/profiles/default/python/plugins

git clone https://github.com/farmanalytica/qgis-EasyDEM
```

**Build and package**

Run `build_plugin.py` from the **OSGeo4W Shell** to do a full release build — clean extlibs, reinstall dependencies, compile translations, and produce a distributable zip:

```bat
cd C:\OSGeo4W\apps\qgis-ltr\python\plugins\qgis-EasyDEM
python-qgis-ltr build_plugin.py
```

Output: `dist/qgis-EasyDEM-plugin.zip`

To vendor only the Python dependencies without building the zip:

```bat
python-qgis-ltr -m pip install -r requirements.txt --target extlibs --upgrade --no-compile
```

**Compile translations**

After editing any `.ts` file, recompile in the **OSGeo4W Shell** (OSGeo4W does not bundle `lrelease`; use the included script instead):

```bat
cd C:\OSGeo4W\apps\qgis-ltr\python\plugins\qgis-EasyDEM
python-qgis-ltr compile_translations.py
```

**Hot-reload during development**

Install the [Plugin Reloader](https://plugins.qgis.org/plugins/plugin_reloader/) QGIS plugin to reload EasyDEM without restarting QGIS after each code change.
