import sys
from pathlib import Path

site_packages = Path(__file__).resolve().parent / "Libs" / "site-packages"
if str(site_packages) not in sys.path:
    sys.path.append(str(site_packages))

import os
import math
import tkinter as tk
from tkinter import filedialog
import unreal
from PIL import Image
import numpy as np

def select_tif_file():
    """
    Opens a native file picker for the user to select a GeoTIFF (.tif/.tiff) file.
    Configures Tkinter to prevent background zombie processes in Unreal Engine.
    Returns: The selected file path as a string, or an empty string if canceled.
    """
    # 1. Create and hide the window
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)

    # 2. Open the file picker
    file_path = filedialog.askopenfilename(
        title="Select GeoTIFF File",
        filetypes=[("TIFF Files", "*.tif;*.tiff")]
    )

    # 3. Kill the window immediately (No zombies!)
    root.destroy()

    # 4. Check the file
    if not file_path:
        print("No file selected.")
        return ""

    if not file_path.lower().endswith(('.tif', '.tiff')):
        print("Warning: The selected file is not a valid TIF file!")
        return ""

    print(f"Selected TIF file: {file_path}")
    return file_path

def validate_tif_file(file_path):
    """
    Validates if the file is a valid single-band elevation DEM TIFF.
    Returns: (is_valid: bool, error_message: str)
    """
    # 1. Check file existence and non-zero size
    if not os.path.exists(file_path):
        return False, f"File does not exist: {file_path}"

    if os.path.getsize(file_path) == 0:
        return False, "The selected file is empty (0 bytes)."

    # 2. Try to open and inspect the TIFF header
    try:
        with Image.open(file_path) as img:
            # Check format
            if img.format != "TIFF":
                return False, f"Invalid format '{img.format}'. File must be a TIFF image."

            # Check dimensions
            if img.width <= 0 or img.height <= 0:
                return False, f"Invalid dimensions: {img.width}x{img.height}."

            # Check channels/bands: DEM heightmaps must have exactly 1 band (elevation)
            bands = img.getbands()
            if len(bands) != 1:
                return False, (
                    f"Selected file has {len(bands)} channels {bands}.\n"
                    "Elevation DEM heightmaps must have only 1 channel (single-band)."
                )

            # 3. Read data into NumPy to check elevation values
            data = np.array(img)

            # Check for all NaN or empty data
            if np.all(np.isnan(data)):
                return False, "The file contains no valid elevation data (all values are NaN)."

            min_val = np.nanmin(data)
            max_val = np.nanmax(data)

            # Check for completely flat terrain (division by zero risk)
            if min_val == max_val:
                return False, f"The file is completely flat (min and max elevation are both {min_val})."

    except Exception as e:
        return False, f"Failed to read TIFF file:\n{str(e)}"

    return True, ""

def calculate_landscape_scale(img, min_val, max_val):
    """
    Calculates Unreal Landscape Scale (X, Y, Z) in Unreal Units (cm).
    - X and Y: Derived from GeoTIFF Tag 33550 (ModelPixelScaleTag)
    - Z: Normalized 16-bit elevation range relative to 512m base
    """
    scale_x = 100.0
    scale_y = 100.0

    # 1. Read Tag 33550 (ModelPixelScaleTag) if present
    if hasattr(img, "tag_v2") and 33550 in img.tag_v2:
        pixel_scale = img.tag_v2[33550]
        sx = float(pixel_scale[0])
        sy = float(pixel_scale[1])

        # If values are in degrees (WGS84, values < 0.1 degree):
        if sx < 0.1 and sy < 0.1:
            lat = 0.0
            if 33922 in img.tag_v2:  # ModelTiepointTag contains latitude
                tiepoint = img.tag_v2[33922]
                if len(tiepoint) >= 5:
                    lat = float(tiepoint[4])
            
            # Convert degrees to meters: 1 deg lat ≈ 111,320m
            meters_y = sy * 111320.0
            meters_x = sx * 111320.0 * math.cos(math.radians(lat))
            scale_x = meters_x * 100.0  # 1 meter = 100 Unreal Units
            scale_y = meters_y * 100.0
        else:
            # Already in meters (projected coordinate system)
            scale_x = sx * 100.0
            scale_y = sy * 100.0

    # 2. Calculate vertical Z scale
    height_range = max_val - min_val
    scale_z = (height_range * 100.0) / 512.0

    return round(scale_x, 2), round(scale_y, 2), round(scale_z, 2)

def convert_tif_to_16bit_png(file_path):
    """
    Converts a 32-bit float or integer DEM into a 16-bit unsigned integer array (0 to 65535).
    Uses NumPy vectorization to normalize the full elevation range without loops.
    Returns: (data_16bit: np.ndarray, min_elevation: float, max_elevation: float)
    """
    img = Image.open(file_path)

    data = np.array(img)

    # 1. Get min, max, and height range
    min_val = np.nanmin(data)
    max_val = np.nanmax(data)
    height_range = max_val - min_val
    # 2. Normalize and scale all 544,000 pixels in ONE step (no loops!)
    normalized = ((data - min_val) / height_range) * 65535.0
    # 3. Round and convert to 16-bit integers
    data_16bit = np.round(normalized).astype(np.uint16)

    return data_16bit, float(min_val), float(max_val)

def import_png_as_texture(png_path):
    """
    Imports a 16-bit PNG heightmap from disk into Unreal Engine as a Texture2D asset
    inside '/Game/ImportedHeightmaps' using Unreal's AssetTools.
    Returns: The imported unreal.Texture2D asset object.
    """
    # 1. Choose where inside the Unreal project to put the asset
    destination_path = "/Game/ImportedHeightmaps"
    asset_name = Path(png_path).stem

    # 2. Setup the import task
    task = unreal.AssetImportTask()
    task.filename = png_path
    task.destination_path = destination_path
    task.destination_name = asset_name
    task.replace_existing = True
    task.automated = True  # Don't show import popup dialogs
    task.save = True       # Automatically save the imported asset

    # 3. Execute the import
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    asset_tools.import_asset_tasks([task])

    # 4. Load the newly created Texture2D object and return it
    asset_path = f"{destination_path}/{asset_name}"
    texture_asset = unreal.EditorAssetLibrary.load_asset(asset_path)
    
    return texture_asset

def import_and_convert_tif(file_path):
    """
    Main conversion pipeline:
    1. Validates the input path and ensures the output folder exists.
    2. Converts GeoTIFF elevation data to a 16-bit grayscale PNG using PIL and NumPy.
    3. Calculates real-world XYZ landscape scale in Unreal Units.
    4. Imports the PNG into Unreal Engine as a Texture2D asset.
    Returns: (texture_2d, min_val, max_val, scale_x, scale_y, scale_z, output_path)
    """
    if not file_path or not os.path.exists(file_path):
        print("Warning: No valid file path provided for conversion.")
        return None, 0.0, 0.0, 0.0, 0.0, 0.0, ""

    output_path = ""
    try:
        # 1. Make sure the output folder exists: Content/ImportedHeightmaps/
        content_dir = unreal.Paths.project_content_dir()
        save_folder = os.path.join(content_dir, "ImportedHeightmaps")
        os.makedirs(save_folder, exist_ok=True)
        
        # 2. Create the output path (using the original name + .png)
        file_name = Path(file_path).stem + ".png"
        output_path = os.path.join(save_folder, file_name)

        # 3. Open image, compute scale and 16-bit PNG
        with Image.open(file_path) as img:
            data = np.array(img)
            min_val = float(np.nanmin(data))
            max_val = float(np.nanmax(data))
            height_range = max_val - min_val

            # Calculate X, Y, Z landscape scale
            scale_x, scale_y, scale_z = calculate_landscape_scale(img, min_val, max_val)

            # Check if aspect ratio is non-square and warn user
            if abs(scale_x - scale_y) > 1.0:
                res = unreal.EditorDialog.show_message(
                    "Non-Square Aspect Ratio Detected",
                    f"This GeoTIFF has non-square pixels:\n"
                    f"  Scale X: {scale_x}\n"
                    f"  Scale Y: {scale_y}\n\n"
                    f"Unreal Engine Landscapes enforce equal X and Y scale (uniform quads).\n\n"
                    f"Do you still want to proceed with importing?",
                    unreal.AppMsgType.YES_NO
                )
                if res != unreal.AppReturnType.YES:
                    print("Import canceled by user due to non-square aspect ratio.")
                    return None, 0.0, 0.0, 0.0, 0.0, 0.0, ""

            # Normalize and convert to 16-bit
            normalized = ((data - min_val) / height_range) * 65535.0
            data_16bit = np.round(normalized).astype(np.uint16)

            png_image = Image.fromarray(data_16bit, mode="I;16")
            png_image.save(output_path)

        print(f"Heightmap saved to: {output_path}")

        # 4. Import Texture2D asset
        texture_2d = import_png_as_texture(output_path)
        return texture_2d, min_val, max_val, scale_x, scale_y, scale_z, output_path

    except Exception as e:
        # Clean up partial/corrupted file if created midway
        if output_path and os.path.exists(output_path):
            try:
                os.remove(output_path)
            except OSError:
                pass
        error_msg = f"An error occurred during import:\n{str(e)}"
        print(f"Error: {error_msg}")
        unreal.EditorDialog.show_message("Import Failed", error_msg, unreal.AppMsgType.OK)
        return None, 0.0, 0.0, 100.0, 100.0, 0.0, ""

def check_selected_tif():
    """
    Initial workflow entry point for the Editor Utility Widget:
    1. Prompts user to pick a GeoTIFF file via file dialog.
    2. Validates the TIFF structure, channel count, and elevation data.
    3. Checks if the target PNG heightmap already exists in the project.
    Returns: (file_path: str, already_exists: bool, title: str, prompt_msg: str)
    """
    # 1. User picks file
    file_path = select_tif_file()
    if not file_path:
        return "", False, "No File Selected", "No file was selected."

    # 2. Validate the TIF file before anything else!
    is_valid, error_msg = validate_tif_file(file_path)
    if not is_valid:
        # Show error dialog directly in Unreal Editor
        unreal.EditorDialog.show_message("Invalid TIF File", error_msg, unreal.AppMsgType.OK)
        return "", False, "Invalid TIF File", error_msg

    # 3. Check if output PNG already exists
    content_dir = unreal.Paths.project_content_dir()
    save_folder = os.path.join(content_dir, "ImportedHeightmaps")
    file_name = Path(file_path).stem + ".png"
    output_path = os.path.join(save_folder, file_name)
    already_exists = os.path.exists(output_path)
    
    if already_exists:
        title = "Heightmap Already Exists"
        prompt_msg = (
            f"The heightmap '{file_name}' already exists at:\n"
            f"{output_path}\n\n"
            f"Do you want to replace it?"
        )
    else:
        title = ""
        prompt_msg = ""

    return file_path, already_exists, title, prompt_msg
