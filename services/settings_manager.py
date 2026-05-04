# -*- coding: utf-8 -*-
"""
Settings management module.

Handles persistence of user preferences and plugin settings in QGIS.
"""

from qgis.core import QgsSettings


class SettingsManager:
    """Manages plugin settings and user preferences in QGIS."""

    SETTINGS_PREFIX = "qgis-EasyDEM/"
    DOWNLOAD_FOLDER_KEY = SETTINGS_PREFIX + "dem_download_folder"

    @staticmethod
    def save_download_folder(folder_path: str) -> None:
        """
        Persist the chosen download folder in QGIS settings.

        Args:
            folder_path: Absolute path to the download folder.
        """
        settings = QgsSettings()
        settings.setValue(SettingsManager.DOWNLOAD_FOLDER_KEY, folder_path)

    @staticmethod
    def load_download_folder() -> str:
        """
        Return the previously saved download folder, or empty string if not set.

        Returns:
            Absolute path to the saved download folder, or empty string.
        """
        settings = QgsSettings()
        return settings.value(SettingsManager.DOWNLOAD_FOLDER_KEY, "", type=str)
