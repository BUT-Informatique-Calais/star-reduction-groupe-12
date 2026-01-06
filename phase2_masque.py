from astropy.io import fits
from astropy.stats import sigma_clipped_stats
from photutils.detection import DAOStarFinder
import matplotlib.pyplot as plt
import cv2 as cv
import numpy as np
import os

os.makedirs('./results', exist_ok=True)

# Chargement image FITS
fits_file = './examples/test_M31_linear.fits'
hdul = fits.open(fits_file)
data = hdul[0].data

if data.shape[0] == 3:
    data = np.transpose(data, (1, 2, 0))

data = data.astype(np.float32)

# Normalisation
image_float = np.zeros_like(data, dtype=np.float32)
for i in range(data.shape[2]):
    channel = data[:, :, i]
    image_float[:, :, i] = (channel - channel.min()) / (channel.max() - channel.min()) * 255.0

image = image_float.astype(np.uint8)
data_gray = np.mean(data, axis=2).astype(np.float32)

# Étape A : Détection étoiles
mean, median, std = sigma_clipped_stats(data_gray, sigma=3.0)

threshold = median + (1.5 * std)
daofind = DAOStarFinder(fwhm=3.0, threshold=threshold)
sources = daofind(data_gray - median)

if sources:
    mask = np.zeros(data_gray.shape, dtype=np.float32)
    flux_max = sources['flux'].max()
    
    for source in sources:
        x = int(source['xcentroid'])
        y = int(source['ycentroid'])
        flux = source['flux']
        rayon = int(3 + 12 * (flux / flux_max))
        rayon = max(3, min(rayon, 15))
        cv.circle(mask, (x, y), rayon, 1.0, -1)
    
    cv.imwrite('./results/masque_binaire.png', (mask * 255).astype(np.uint8))
    
    # Flou gaussien pour transitions douces
    mask_blur = cv.GaussianBlur(mask, (21, 21), 0)
    mask_normalized = mask_blur
    cv.imwrite('./results/masque_adouci.png', (mask_blur * 255).astype(np.uint8))
else:
    mask_normalized = np.zeros(data_gray.shape, dtype=np.float32)
    
# Étape B : Réduction localisée

# Version érodée (filtre médian)
image_eroded = np.zeros_like(image_float, dtype=np.float32)
for i in range(image_float.shape[2]):
    image_eroded[:, :, i] = cv.medianBlur(image_float[:, :, i].astype(np.uint8), 25).astype(np.float32)
cv.imwrite('./results/image_erodee.png', cv.cvtColor(image_eroded.astype(np.uint8), cv.COLOR_RGB2BGR))

# Interpolation avec facteur de réduction
facteur_reduction = 0.9

image_final = np.zeros_like(image_float, dtype=np.float32)
for i in range(image_float.shape[2]):
    difference = image_float[:, :, i] - image_eroded[:, :, i]
    image_final[:, :, i] = image_float[:, :, i] - (facteur_reduction * mask_normalized * difference)
image_final = np.clip(image_final, 0, 255).astype(np.uint8)

cv.imwrite('./results/image_finale.png', cv.cvtColor(image_final, cv.COLOR_RGB2BGR))

# Comparaison avant/après
fig, axes = plt.subplots(1, 2, figsize=(14, 7))
axes[0].imshow(image)
axes[1].imshow(image_final)
axes[0].set_title('Avant')
axes[1].set_title('Après')
for ax in axes:
    ax.axis('off')
plt.tight_layout()
plt.savefig('./results/avant_apres.jpg', dpi=150)

hdul.close()
