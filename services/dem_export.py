# import os

# from qgis.core import QgsSettings

# import os

# def get_unique_filepath(target_dir, base_filename):
#     """
#     Generates a unique filepath to prevent overwriting existing files.
#     """
#     base_filepath = os.path.join(target_dir, base_filename)
    
#     if not os.path.exists(base_filepath):
#         return base_filepath

#     name, ext = os.path.splitext(base_filename)
    
#     counter = 1
#     while True:
#         new_filename = f"{name}_{counter}{ext}"
#         new_filepath = os.path.join(target_dir, new_filename)
        
#         if not os.path.exists(new_filepath):
#             return new_filepath
            
#         counter += 1

# def save_download_folder(folder_path):
#     settings = QgsSettings()
#     settings.setValue("qgis-EasyDEM/dem_download_folder", folder_path)


# def load_download_folder():
#     settings = QgsSettings()
    
#     return settings.value("qgis-EasyDEM/dem_download_folder", "", type=str)

# def export_dem(default_output_dir, dem_filename="dem.tif"):
#     """
#     Determines the correct export path based on user settings and ensures
#     no files are overwritten.
#     """
#     custom_folder = load_download_folder()
    
#     if custom_folder and os.path.isdir(custom_folder):
#         target_dir = custom_folder
#     else:
#         target_dir = default_output_dir 
        
#     final_export_path = get_unique_filepath(target_dir, dem_filename)