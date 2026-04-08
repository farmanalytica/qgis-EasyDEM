# -*- coding: utf-8 -*-
"""
GEE (Google Earth Engine) service layer.

All Earth Engine business logic lives here, keeping the UI layer free
of SDK-specific details.
"""

import os
import ee
from qgis.PyQt.QtCore import QSettings


class GEEService:
    SETTINGS_PROJECT_ID_KEY = "MyPlugin/projectID"

    def get_saved_project_id(self) -> str:

        return QSettings().value(self.SETTINGS_PROJECT_ID_KEY, "", type=str)

    def save_project_id(self, project_id) -> None:

        QSettings().setValue(self.SETTINGS_PROJECT_ID_KEY, project_id)

    def authenticate(self, project_id: str):

        try:
            try:
                ee.Initialize(project=project_id)

            except ee.EEException:
                ee.Authenticate()
                ee.Initialize(project=project_id)

            default_project_path = f"projects/{project_id}/assets/"

            ee.data.listAssets({"parent": default_project_path})

        except ee.EEException as e:
            error_msg = str(e)

            if "Earth Engine client library not initialized" in error_msg:
                raise Exception("Authentication failed. Please authenticate again.")
            else:
                raise Exception(
                    f"An error occurred during authentication or initialization: {error_msg}"
                )

        except Exception as e:
            raise Exception(f"An unexpected error occurred: {e}")

    def reset_authentication(self, silent=False):

        credentials_path = ee.oauth.get_credentials_path()

        if not os.path.exists(credentials_path):
            if silent:
                return None
            raise FileNotFoundError("No Earth Engine configuration found to clear.")

        os.remove(credentials_path)

        try:
            import importlib

            importlib.reload(ee.oauth)
            ee.Reset()
        except Exception:
            pass

        return "Earth Engine configuration cleared successfully."
