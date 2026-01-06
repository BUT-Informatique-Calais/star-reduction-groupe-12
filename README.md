[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/zP0O23M7)

# Star Reduction Project - SAÉ S3.C2

This project implements morphological erosion techniques for astronomical image processing, specifically for star reduction in galaxy images.

## Overview

The goal is to reduce the visibility of stars in astronomical images while preserving the galaxy structure. This is achieved through:
- **Phase 1**: Simple morphological erosion tests
- **Phase 2**: Selective star reduction using mask-based interpolation

## Installation

### Virtual Environment

It is recommended to create a virtual environment before installing dependencies:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Dependencies
```bash
pip install -r requirements.txt
```

Required packages:
- `astropy` - FITS file handling
- `opencv-python` - Morphological operations
- `photutils` - Star detection (DAOStarFinder)
- `matplotlib` - Visualization
- `numpy` - Array operations

## Usage

### Phase 1: Simple Erosion
Tests morphological erosion with a 7×7 kernel on the entire image:
```bash
python erosion.py
```
Outputs: `original.png`, `eroded.png` in `results/`

### Phase 2: Selective Star Reduction
Detects stars, creates a mask, and applies selective reduction:
```bash
python phase2_masque.py
```
Outputs: `masque_binaire.png`, `masque_adouci.png`, `image_erodee.png`, `image_finale.png`, `avant_apres.jpg` in `results/`

You can adjust the reduction factor in `phase2_masque.py` (line ~65):
- `0.0` = no reduction
- `0.5` = moderate reduction
- `1.0` = maximum reduction

## Requirements

- Python 3.8+
- See `requirements.txt` for full dependency list

## Example Files
Example files are located in the `examples/` directory:
- `HorseHead.fits` - Monochrome nebula image
- `test_M31_linear.fits` - RGB Andromeda galaxy image (recommended)
- `test_M31_raw.fits` - Raw Andromeda galaxy image
