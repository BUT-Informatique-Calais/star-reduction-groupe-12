[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/zP0O23M7)

# Star Reduction Project - SAÉ S3.C2

This project implements morphological erosion techniques for astronomical image processing, specifically for star reduction in galaxy images.

## Overview

The goal is to reduce the visibility of stars in astronomical images while preserving the galaxy structure. This is achieved through:
- **Phase 1**: Simple morphological erosion tests
- **Phase 2**: Selective star reduction using mask-based interpolation
- **Phase 3**: Astrometry-based star catalog matching (bonus)
- **GUI Interface**: Real-time interactive processing with visual feedback

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
- `requests` - API communication (for astrometry)
- `scipy` - Image processing utilities
- `tkinter` - GUI interface (included with Python)

## Usage

### Interactive GUI
Launch the graphical interface for real-time parameter adjustment:
```bash
python interface.py
```
Features:
- Load FITS files interactively
- Adjust parameters with live preview
- Before/after blink comparison mode
- Astrometry.net integration for star catalog matching
- Save results with custom names

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

### Phase 3: Astrometry-Based Reduction
python phase3_bonus_astrometry.py
```
This advanced method:
1. Uploads the image to Astrometry.net for plate solving
2. Retrieves WCS (World Coordinate System) calibration
3. Queries Gaia DR3 catalog for star positions and magnitudes
4. Creates precise masks based on catalog data
5. Applies weighted reduction based on star brightness

**Note**: Requires internet connection and valid API key in the script.

Outputs: `astrometry_masque_binaire.png`, `astrometry_masque_adouci.png`, `astrometry_image_finale.png`, `astrometry_avant_apres.jpg` in `results/`

## Parameters

### Star Detection
- **FWHM** (Full Width Half Maximum): Expected star size in pixels (default: 3.0)
- **Threshold Multiplier**: Detection sensitivity multiplier (default: 1.5)
  - Higher = fewer stars detected
  - Lower = more stars detected

### Erosion
- **Kernel Size**: Structuring element size for morphological erosion (default: 7×7)
  - Larger = more aggressive erosion
  - Must be odd number

### Reduction
- **Reduction Factor**: Blending ratio between original and eroded images
  - `0.0` = original image (no reduction)
  - `0.5` = 50% blend (moderate reduction)
  - `1.0` = fully eroded (maximum reduction)

## Project Structure

```
star-reduction-groupe-12-main/
├── erosion.py                    # Phase 1: Simple erosion
├── phase2_masque.py              # Phase 2: Mask-based reduction
├── phase3_bonus_astrometry.py    # Phase 3: Astrometry catalog matching
├── interface.py                  # Interactive GUI application
├── requirements.txt              # Python dependencies
├── README.md                     # This file
├── examples/                     # Sample FITS files
│   ├── HorseHead.fits           # Monochrome nebula
│   ├── test_M31_linear.fits     # RGB Andromeda galaxy
│   └── test_M31_raw.fits        # Raw Andromeda galaxy
└── results/                      # Output directory 
```

## Technical Details

### Morphological Erosion
Applies a structuring element to shrink bright regions (stars) while attempting to preserve larger structures (galaxies).

### Mask-Based Interpolation
1. Detects stars using DAOStarFinder (photutils)
2. Creates binary mask centered on detected stars
3. Applies Gaussian blur for smooth transitions
4. Blends original and eroded images using the mask as weight

### Astrometry Workflow
1. **Plate Solving**: Determines image orientation and scale
2. **Catalog Query**: Retrieves star catalog from Gaia DR3
3. **Mask Generation**: Creates masks weighted by star magnitude
4. **Selective Reduction**: Applies erosion only to cataloged stars

## Requirements

- Python 3.8+
- See `requirements.txt` for full dependency list

## Example Files
Example files are located in the `examples/` directory:
- `HorseHead.fits` - Monochrome nebula image
- `test_M31_linear.fits` - RGB Andromeda galaxy image (recommended)
- `test_M31_raw.fits` - Raw Andromeda galaxy image

## Troubleshooting

### Common Issues

**"No stars detected"**
- Lower the threshold multiplier
- Adjust FWHM to match actual star size
- Check image exposure/contrast

**Erosion too aggressive**
- Reduce kernel size
- Lower reduction factor
- Use mask-based methods (Phase 2/3)

**Astrometry.net timeout**
- Check internet connection
- Try smaller image or lower resolution
- Verify API key is valid

**GUI not responding**
- Processing can take time for large images
- Wait for progress updates in console
- Check terminal output for errors

## Tips for Best Results

1. **Use Phase 2 or 3** for galaxy images - preserves structure better than simple erosion
2. **Start with moderate parameters** - FWHM=3.0, threshold=1.5, reduction=0.5
3. **Use the GUI** for quick experimentation and parameter tuning
4. **Test on M31 example** - good balance of stars and galaxy structure
5. **For crowded fields** - Phase 3 with catalog matching gives most precise results

## Credits

**SAÉ S3.C2** - Astronomical Image Processing  
Developed as part of university curriculum for image analysis and astronomical data processing.

## License

Educational project - for academic use only.
