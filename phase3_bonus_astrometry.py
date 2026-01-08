import numpy as np
import matplotlib.pyplot as plt
from astropy.io import fits
import cv2
import requests
import time
import json
from pathlib import Path
from scipy.ndimage import gaussian_filter

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

def create_mask_from_calibration(image_shape, calibration, image_data):
    print(f"\nAPI Astrometry.net - champ identifie:")
    print(f"  RA={calibration.get('ra'):.2f}, Dec={calibration.get('dec'):.2f}")
    print(f"  Echelle: {calibration.get('pixscale'):.2f} arcsec/pixel")
    print(f"\nDetection locale avec DAOStarFinder...\n")
    
    from photutils.detection import DAOStarFinder
    from scipy.ndimage import gaussian_filter
    
    mean = np.mean(image_data)
    std = np.std(image_data)
    threshold = mean + 3 * std
    
    daofind = DAOStarFinder(fwhm=5.0, threshold=threshold)
    sources = daofind(image_data)
    
    print(f"{len(sources)} etoiles detectees")
    
    mask = np.zeros(image_shape, dtype=np.uint8)
    for source in sources:
        x = int(source['xcentroid'])
        y = int(source['ycentroid'])
        flux = source['flux']
        
        radius = max(5, min(int(3 + np.log10(flux/1000)), 30))
        cv2.circle(mask, (x, y), radius, 255, -1)
    
    return mask, len(sources)

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
        masque, n_stars = create_mask_from_calibration(
            image.shape, 
            calibration,
            image
        )
        
        print(f"Masque cree : {np.sum(masque > 0)} pixels masques ({100*np.sum(masque > 0)/masque.size:.2f}%)")
        method = "Astrometry.net + DAOStarFinder"
    else:
        print("\nImpossible de recuperer la calibration")
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

masque_adouci = gaussian_filter(masque.astype(float) / 255, sigma=3)

reduction_factor = 0.9
image_finale = image_norm.copy()
image_finale = image_norm * (1 - masque_adouci * reduction_factor)

print(f"\nReduction appliquee (facteur: {reduction_factor*100}%)")

Path("results").mkdir(exist_ok=True)

plt.imsave("results/astrometry_masque.png", masque, cmap='gray')
plt.imsave("results/astrometry_finale.png", image_finale, cmap='gray', vmin=0, vmax=1)

print("\nImages sauvegardees :")
print("  - results/astrometry_masque.png")
print("  - results/astrometry_finale.png")

fig, axes = plt.subplots(1, 3, figsize=(18, 6))

axes[0].imshow(image_norm, cmap='gray', vmin=0, vmax=1)
axes[0].set_title(f"Original\n({method})")
axes[0].axis('off')

axes[1].imshow(masque, cmap='Reds', alpha=0.7)
axes[1].set_title(f"Masque\n({np.sum(masque > 0)} pixels)")
axes[1].axis('off')

axes[2].imshow(image_finale, cmap='gray', vmin=0, vmax=1)
axes[2].set_title(f"Apres reduction\n({reduction_factor*100}% sur etoiles)")
axes[2].axis('off')

plt.tight_layout()
plt.savefig("results/astrometry_comparaison.jpg", dpi=150, bbox_inches='tight')
print("  - results/astrometry_comparaison.jpg")
