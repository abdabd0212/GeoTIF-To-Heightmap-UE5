# TIF Importer for Unreal Engine 5

## 1. Overview
The **TIF Importer** plugin imports GeoTIFF DEM files into Unreal Engine 5 and converts them into 16-bit PNG heightmaps with automated landscape scale calculation.

- **Plugin Name:** TIF Importer
- **Current Version:** 1.0.0
- **Supported Unreal Engine Versions:** 5.0+
- **Platforms:** Windows (64-bit)
- **Intended Audience:** Level Designers, Technical Artists

---

## 2. Features
- Imports `.tif` and `.tiff` DEM elevation files directly into Unreal Engine.
- Converts 32-bit elevation data into 16-bit PNG heightmaps using NumPy.
- Automated real-world XYZ landscape scale recommendation.
- Input data validation (rejects 0-byte, RGB, and flat files).
- Overwrite protection for existing assets.
- Pre-bundled NumPy and Pillow libraries (no manual pip install needed).

---

## 3. Installation

### 3.1 Requirements
- Unreal Engine 5.0 or newer
- Windows 10 or later

### 3.2 Installation Steps
1. Copy the `TIFImporter` folder into your project's `Plugins` directory:
   `/ProjectFolder/Plugins/TIFImporter`
2. Launch Unreal Engine and open your project.
3. Open **Edit -> Plugins**, enable **TIF Importer**, and restart if prompted.

---

## 4. Getting Started

### 4.1 Opening the Tool
1. In the Content Browser, click **Settings -> Show Plugin Content**.
2. Open **TIFImporter Content**, right-click **`EUW_TIFImporter`**, and select **Run Editor Utility Widget**.

### 4.2 Usage Guide
1. Click **Import TIF file** and select a `.tif` file from disk.
2. Confirm overwrite or aspect ratio prompts if they appear.
3. The plugin generates a 16-bit PNG in `Content/ImportedHeightmaps/` and imports the `Texture2D`.
4. Review the **Min/Max Height** and recommended **Landscape Scale**.
5. In **Landscape Mode** (`Shift + 2`), choose **Import from File**, select the generated PNG, apply the XYZ scale, and click **Import**.

---

## 5. User Interface

Import Section
| UI Element | Description |
|---|---|
| Import TIF file | Opens a file picker to select a `.tif` file from disk |
| Help | Displays usage instructions |

Heightmap Information Section
| Field | Description |
|---|---|
| Mini Height | Lowest elevation value in meters |
| Max Height | Highest elevation value in meters |
| Height Map | Asset preview of the imported texture |
| Height Map Path | Disk path to the generated 16-bit PNG |

Landscape Settings Section
| Field | Description |
|---|---|
| Landscape Scale | Recommended XYZ scale for Unreal's Landscape Transform |

---

## 6. Troubleshooting

| Issue | Cause | Solution |
|---|---|---|
| "No file selected." | File picker closed without selecting | Click **Import TIF file** and select a file |
| "The selected file is empty" | 0-byte or corrupted file | Re-download the DEM file |
| "Selected file has 3 channels" | RGB color image used instead of elevation | Use a single-band grayscale DEM |
| "Non-Square Aspect Ratio Detected" | TIF pixels are rectangular, not square | Click **Yes** to proceed or use a TIF with square pixels |
| "The heightmap already exists" | Target PNG already exists on disk | Click **Ok** to overwrite or **Cancel** to keep |
| Plugin Content not visible | Hidden by default in Unreal | In Content Browser: **Settings -> Show Plugin Content** |

---

## 7. Version History

| Version | Date | Notes |
|---|---|---|
| **1.0.0** | 2026-10-25 | Initial release |
