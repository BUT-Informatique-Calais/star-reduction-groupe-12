import numpy as np
import matplotlib.pyplot as plt
from astropy.io import fits
import cv2
import requests
import time
import json
from pathlib import Path
from scipy.ndimage import gaussian_filter
from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.wcs import WCS

API_KEY = "siupcwbetlrmnrwm"
API_URL = "http://nova.astrometry.net/api/"

def login_astrometry(api_key):
    response = requests.post(
        API_URL + "login",
        data={'request-json': json.dumps({"apikey": api_key})}
    )
    if response.status_code == 200:
        session = response.json()
        if session['status'] == 'success':
            print(f"Connexion reussie (session: {session['session']})")
            return session['session']
    print(f"Echec connexion: {response.text}")
    return None

def upload_image(session_id, image_path):
    print(f"\nUpload de {image_path}...")
    
    with open(image_path, 'rb') as f:
        files = {'file': f}
        data = {
            'request-json': json.dumps({
                'session': session_id,
                'publicly_visible': 'n',
                'allow_modifications': 'd',
                'allow_commercial_use': 'd',
            })
        }
        
        response = requests.post(
            API_URL + "upload",
            files=files,
            data=data
        )
    
    if response.status_code == 200:
        result = response.json()
        if result['status'] == 'success':
            subid = result['subid']
            print(f"Upload reussi (submission ID: {subid})")
            return subid
    
    print(f"Echec upload: {response.text}")
    return None

def wait_for_job(submission_id, timeout=300):
    print(f"\nAttente du traitement (max {timeout}s)...")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            response = requests.get(
                API_URL + f"submissions/{submission_id}"
            )
            
            if response.status_code == 200:
                result = response.json()
                jobs = result.get('jobs', [])
                
                if jobs:
                    job_id = jobs[0]
                    job_response = requests.get(API_URL + f"jobs/{job_id}")
                    
                    if job_response.status_code == 200:
                        try:
                            job_status = job_response.json()
                            status = job_status.get('status')
                            
                            if status == 'success':
                                print(f"\nTraitement termine (job ID: {job_id})")
                                return job_id
                            elif status == 'failure':
                                print(f"\nEchec du traitement: {job_status}")
                                return None
                            else:
                                elapsed = int(time.time() - start_time)
                                print(f"  En cours... ({elapsed}s, status: {status})", end='\r')
                        except json.JSONDecodeError:
                            elapsed = int(time.time() - start_time)
                            print(f"  En cours... {elapsed}s)", end='\r')
                    elif job_response.status_code == 404:
                        elapsed = int(time.time() - start_time)
                        print(f"  En cours... ({elapsed}s)", end='\r')
        except Exception as e:
            elapsed = int(time.time() - start_time)
            print(f"  En cours... ({elapsed}s)", end='\r')
        
        time.sleep(5)
    
    print(f"\nTimeout apres {timeout}s")
    return None

def get_calibration(job_id):
    print(f"\nRecuperation des donnees de calibration...")
    
    response = requests.get(API_URL + f"jobs/{job_id}/calibration/")
    if response.status_code == 200:
        calib = response.json()
        print(f"Calibration recuperee")
        print(f"  RA: {calib.get('ra', 'N/A')}, Dec: {calib.get('dec', 'N/A')}")
        print(f"  Echelle: {calib.get('pixscale', 'N/A')} arcsec/pixel")
        return calib
    
    print(f"Echec recuperation calibration")
    return None

def get_objects_in_field(job_id):
    print(f"\nRecuperation du catalogue d'objets...")
    
    response = requests.get(API_URL + f"jobs/{job_id}/objects_in_field/")
    if response.status_code == 200:
        objects = response.json()
        print(f"{len(objects)} objets detectes")
        return objects
    
    print(f"Echec recuperation catalogue")
    return None

def get_annotations(job_id):
    print(f"\nRecuperation des annotations...")
    
    response = requests.get(API_URL + f"jobs/{job_id}/annotations/")
    if response.status_code == 200:
        annotations = response.json()
        print(f"{len(annotations)} annotations recuperees")
        return annotations
    
    print(f"Echec recuperation annotations")
    return None

def get_wcs_from_calibration(job_id):
    print(f"\nTelechargement de la calibration WCS...")
    
    wcs_url = f"http://nova.astrometry.net/wcs_file/{job_id}"
    response = requests.get(wcs_url)
    
    if response.status_code != 200:
        print(f"Echec telechargement WCS")
        return None
    
    wcs_path = "temp_wcs.fits"
    with open(wcs_path, 'wb') as f:
        f.write(response.content)
    
    try:
        wcs = WCS(wcs_path)
        import os
        os.remove(wcs_path)
        print(f"WCS recupere avec succes")
        return wcs
    except Exception as e:
        print(f"Erreur lecture WCS: {e}")
        import os
        if os.path.exists(wcs_path):
            os.remove(wcs_path)
        return None

def get_stars_from_gaia(ra_center, dec_center, image_shape, pixscale, mag_limit=18):
    diagonal_pixels = np.sqrt(image_shape[0]**2 + image_shape[1]**2)
    diagonal_arcsec = diagonal_pixels * pixscale
    radius_deg = (diagonal_arcsec / 3600.0) / 2.0
    radius_deg *= 1.1
    
    print(f"\nInterrogation catalogue Gaia DR3...")
    print(f"  Centre: RA={ra_center:.4f}, Dec={dec_center:.4f}")
    print(f"  Rayon calcule: {radius_deg:.4f} degres ({diagonal_arcsec/60:.2f} arcmin)")
    print(f"  Magnitude limite: {mag_limit}")
    
    try:
        from astroquery.gaia import Gaia
        
        query = f"""
        SELECT TOP 10000
            ra, dec, phot_g_mean_mag
        FROM gaiadr3.gaia_source
        WHERE 
            CONTAINS(POINT('ICRS', ra, dec),
                    CIRCLE('ICRS', {ra_center}, {dec_center}, {radius_deg})) = 1
            AND phot_g_mean_mag < {mag_limit}
        ORDER BY phot_g_mean_mag
        """
        
        job = Gaia.launch_job(query)
        results = job.get_results()
        
        stars = []
        for row in results:
            stars.append({
                'ra': row['ra'],
                'dec': row['dec'],
                'mag': row['phot_g_mean_mag']
            })
        
        print(f"{len(stars)} etoiles recuperees depuis Gaia DR3")
        return stars
        
    except Exception as e:
        print(f"Erreur interrogation Gaia: {e}")
        print(f"Installer astroquery: pip install astroquery")
        return None

def create_mask_from_catalog(image_shape, stars, wcs, image_data, intensity_threshold=None):
    print(f"\nCreation masque depuis catalogue Gaia...")
    
    if intensity_threshold is None:
        intensity_threshold = np.percentile(image_data, 85)
    
    print(f"  Seuil intensite: {intensity_threshold:.1f}")
    
    mask = np.zeros(image_shape, dtype=np.uint8)
    n_masked = 0
    n_total = 0
    
    for star in stars:
        coord = SkyCoord(ra=star['ra']*u.degree, dec=star['dec']*u.degree)
        x, y = wcs.world_to_pixel(coord)
        
        x = int(x)
        y = int(y)
        
        if 0 <= x < image_shape[1] and 0 <= y < image_shape[0]:
            n_total += 1
            
            pixel_value = image_data[y, x]
            
            if pixel_value > intensity_threshold:
                radius = int(18 - star['mag'])
                radius = max(2, min(radius, 12))
                
                cv2.circle(mask, (x, y), radius, 255, -1)
                n_masked += 1
    
    print(f"{n_masked}/{n_total} etoiles masquees (visibles sur l'image)")
    return mask, n_masked

if API_KEY == "votre_cle_api_ici":
    print("ATTENTION : Vous devez configurer votre cle API Astrometry.net")
    print("Utilisation de DAOStarFinder en backup...\n")
    USE_API = False
else:
    USE_API = True

print("Chargement de l'image...")
image_path = "examples/test_M31_linear.fits"
with fits.open(image_path) as hdul:
    image = hdul[0].data.astype(float)

if len(image.shape) == 3:
    image = image[0]
    print(f"Image RGB detectee, utilisation du premier canal")

image_norm = (image - image.min()) / (image.max() - image.min())
print(f"Image chargee : {image.shape}")

if USE_API:
    session_id = login_astrometry(API_KEY)
    if not session_id:
        print("\nImpossible de se connecter a l'API")
        USE_API = False

if USE_API:
    submission_id = upload_image(session_id, image_path)
    if not submission_id:
        print("\nImpossible d'uploader l'image")
        USE_API = False

if USE_API:
    job_id = wait_for_job(submission_id, timeout=300)
    if not job_id:
        print("\nLe traitement a echoue ou timeout")
        USE_API = False

if USE_API:
    calibration = get_calibration(job_id)
    objects = get_objects_in_field(job_id)
    annotations = get_annotations(job_id)
    
    if calibration:
        wcs = get_wcs_from_calibration(job_id)
        
        if wcs:
            ra_center = calibration.get('ra')
            dec_center = calibration.get('dec')
            pixscale = calibration.get('pixscale')
            
            stars = get_stars_from_gaia(ra_center, dec_center, image.shape, pixscale, mag_limit=20)
            
            if stars:
                masque, n_stars = create_mask_from_catalog(
                    image.shape,
                    stars,
                    wcs,
                    image
                )
                print(f"Masque cree : {np.sum(masque > 0)} pixels masques ({100*np.sum(masque > 0)/masque.size:.2f}%)")
                method = "Astrometry.net + Gaia DR3"
            else:
                print("\nImpossible de recuperer catalogue Gaia")
                USE_API = False
        else:
            print("\nImpossible de recuperer WCS")
            USE_API = False
    else:
        print("\nImpossible de recuperer la calibration")
        USE_API = False
        USE_API = False

if not USE_API:
    print("\n--- Utilisation de DAOStarFinder en backup ---")
    from photutils.detection import DAOStarFinder
    from scipy.ndimage import gaussian_filter
    
    mean = np.mean(image)
    std = np.std(image)
    threshold = mean + 3 * std
    
    daofind = DAOStarFinder(fwhm=5.0, threshold=threshold)
    sources = daofind(image)
    
    print(f"{len(sources)} etoiles detectees")
    
    masque = np.zeros(image.shape, dtype=np.uint8)
    for source in sources:
        x = int(source['xcentroid'])
        y = int(source['ycentroid'])
        flux = source['flux']
        
        radius = max(5, min(int(3 + np.log10(flux/1000)), 30))
        cv2.circle(masque, (x, y), radius, 255, -1)
    
    print(f"Masque cree : {np.sum(masque > 0)} pixels masques ({100*np.sum(masque > 0)/masque.size:.2f}%)")
    method = "DAOStarFinder (backup)"

Path("results").mkdir(exist_ok=True)

plt.imsave("results/astrometry_masque.png", masque, cmap='gray')

print("\nImages sauvegardees :")
print("  - results/astrometry_masque.png")

fig, axes = plt.subplots(1, 2, figsize=(14, 6))

axes[0].imshow(image_norm, cmap='gray', vmin=0, vmax=1)
axes[0].set_title(f"Original\n({method})")
axes[0].axis('off')

axes[1].imshow(masque, cmap='gray')
axes[1].set_title(f"Masque catalogue\n({np.sum(masque > 0)} pixels)")
axes[1].axis('off')

plt.tight_layout()
plt.savefig("results/astrometry_comparaison.jpg", dpi=150, bbox_inches='tight')
print("  - results/astrometry_comparaison.jpg")


