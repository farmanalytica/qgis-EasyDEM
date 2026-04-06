# -*- coding: utf-8 -*-
"""
GEE (Google Earth Engine) service layer.

All Earth Engine business logic lives here, keeping the UI layer free
of SDK-specific details.
"""

import ee


class GEEService:
    def authenticate(self, project_id: str):
        print(f"Authenticating with GEE for project: {project_id}")

    def reset_authentication(self):
        print("Resetting GEE authentication")

