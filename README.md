# EasyDEM

A QGIS plugin for DEM (Digital Elevation Model) processing using Google Earth Engine.

---

## Project Structure

```
qgis-EasyDEM/
├── __init__.py          # QGIS entry point — registers the plugin via classFactory()
├── easy.py              # Plugin controller — owns the QGIS lifecycle (initGui, unload, run)
├── easy_dialog.py       # UI layer — dialog window and widget definitions
├── resources.py         # Compiled Qt resources (icons, etc.)
├── pavement.py          # Build/dev task automation (paver)
├── services/
│   ├── __init__.py      # Exports service classes
│   └── gee_service.py   # Google Earth Engine business logic
└── extlibs/             # Vendored third-party dependencies (ee, urllib3, etc.)
```

---

## Architecture

The codebase follows a **UI / Service** separation:

### `easy.py` — Plugin Controller
The QGIS plugin entry point. Handles toolbar/menu registration (`initGui`), teardown (`unload`), and launches the dialog (`run`). This is the glue between QGIS and the rest of the plugin — it should instantiate services and pass them into the dialog, not contain business logic itself.

### `easy_dialog.py` — UI Layer
Contains `easydemDialog(QDialog)`. Responsible only for building widgets and emitting signals. It must not import `ee` or call any GEE SDK directly.

Internal conventions:
- `_setup_ui()` — constructs and arranges all widgets
- `_connect_signals()` — wires Qt signals to handler methods
- `on_*` methods — stub handlers that delegate to a service (currently `pass`)

Current widgets:
| Widget | Attribute | Purpose |
|---|---|---|
| QPushButton | `btn_authenticate` | Triggers GEE authentication |
| QPushButton | `btn_reset_auth` | Resets existing GEE credentials |
| QLineEdit | `project_id_input` | User-supplied GCP project ID |

### `services/gee_service.py` — GEE Service
Contains `GEEService`. All Earth Engine SDK calls go here. Methods are currently stubs (`pass`) ready to be implemented.

| Method | Signature | Purpose |
|---|---|---|
| `authenticate` | `(project_id: str)` | Authenticates with GEE using the given project |
| `reset_authentication` | `()` | Clears stored GEE credentials |

---

## Adding a New Feature

1. **UI changes** — edit `easy_dialog.py`. Add widgets in `_setup_ui`, connect signals in `_connect_signals`, add an `on_*` handler stub.
2. **Business logic** — add a method to `GEEService` (or create a new service file under `services/`).
3. **Wire them up** — in `easy.py`, pass the service into the dialog and connect the dialog's handler to the service method.

> Keep the dialog ignorant of the GEE SDK. Keep the service ignorant of Qt widgets.

---

## Dependencies

Bundled under `extlibs/` so no extra `pip install` is needed in the QGIS environment. The path is injected into `sys.path` by `__init__.py` before any plugin code runs.

Key bundled packages: `earthengine-api`, `urllib3`, `pyparsing`, `pyasn1`.

---

## Development Setup

This plugin targets **QGIS LTR**. To reload the plugin during development use the [Plugin Reloader](https://plugins.qgis.org/plugins/plugin_reloader/) QGIS plugin.
