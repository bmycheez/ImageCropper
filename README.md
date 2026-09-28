# ImageCropper — Fast Patch Cropping for Defect Labeling

A lightweight GUI tool to cut fixed-size patches (default **1024×1024**) from large inspection images, speeding up defect-labeling for AOI deep-learning datasets.

## ✨ Features
- Select an input folder → browse images one by one
- Pan/zoom on high-resolution images; click to place the crop window
- Saves each patch with its origin in the filename: `{name}_x-{left}_y-{top}.{ext}` → easy to trace back to the source image
- Boundary check prevents out-of-image crops

## 🚀 Run
```bash
pip install numpy pillow matplotlib pyqt5
python image_cropper.py
```
Change `CROP_WIDTH` / `CROP_HEIGHT` at the top of the script for other patch sizes.

## Roadmap
- [ ] Standalone `.exe` build (PyInstaller)
