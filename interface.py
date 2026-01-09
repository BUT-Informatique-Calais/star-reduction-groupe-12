from astropy.io import fits
from astropy.stats import sigma_clipped_stats
from photutils.detection import DAOStarFinder
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.animation import FuncAnimation
import cv2 as cv
import numpy as np
import tkinter as tk
from tkinter import filedialog, ttk, scrolledtext
import os
import threading
import requests
import json
import time
from pathlib import Path
from scipy.ndimage import gaussian_filter
from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.wcs import WCS
import warnings
from photutils.utils.exceptions import NoDetectionsWarning
from astropy.wcs import FITSFixedWarning

warnings.filterwarnings('ignore', category=NoDetectionsWarning)
warnings.filterwarnings('ignore', category=FITSFixedWarning)
warnings.filterwarnings('ignore', message='.*passwords.*')
warnings.filterwarnings('ignore', message='.*Gaia Archive.*')


class StarReductionGUI:
    
    def __init__(self, root):
        self.root = root
        self.root.title("Star Reduction - Interface Temps Réel")
        self.root.geometry("1400x800")
        
        self.fits_file = None
        self.data = None
        self.image = None
        self.data_gray = None
        
        self.kernel_size = tk.IntVar(value=7)
        self.threshold_multiplier = tk.DoubleVar(value=1.5)
        self.reduction_factor = tk.DoubleVar(value=0.5)
        self.fwhm = tk.DoubleVar(value=3.0)
        
        self.update_id = None
        
        self.animation = None
        self.is_blinking = False
        
        self.setup_ui()
        
    def setup_ui(self):
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        control_frame = ttk.LabelFrame(main_frame, text="Contrôles", padding=10)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        ttk.Button(control_frame, text="Charger fichier FITS", 
                   command=self.load_fits).pack(fill=tk.X, pady=5)
        
        self.file_label = ttk.Label(control_frame, text="Aucun fichier chargé", 
                                     wraplength=200)
        self.file_label.pack(pady=5)
        
        ttk.Separator(control_frame, orient='horizontal').pack(fill=tk.X, pady=10)
        
        ttk.Label(control_frame, text="Taille du noyau d'érosion:").pack(anchor=tk.W)
        kernel_scale = ttk.Scale(control_frame, from_=3, to=15, 
                                 variable=self.kernel_size, 
                                 orient=tk.HORIZONTAL,
                                 command=self.on_param_change)
        kernel_scale.pack(fill=tk.X, pady=5)
        self.kernel_label = ttk.Label(control_frame, text=f"Valeur: {self.kernel_size.get()}")
        self.kernel_label.pack(anchor=tk.W)
        
        ttk.Label(control_frame, text="Seuil de détection (sigma):").pack(anchor=tk.W, pady=(10,0))
        threshold_scale = ttk.Scale(control_frame, from_=0.5, to=5.0, 
                                    variable=self.threshold_multiplier,
                                    orient=tk.HORIZONTAL,
                                    command=self.on_param_change)
        threshold_scale.pack(fill=tk.X, pady=5)
        self.threshold_label = ttk.Label(control_frame, text=f"Valeur: {self.threshold_multiplier.get():.2f}")
        self.threshold_label.pack(anchor=tk.W)
        
        ttk.Label(control_frame, text="FWHM (largeur étoiles):").pack(anchor=tk.W, pady=(10,0))
        fwhm_scale = ttk.Scale(control_frame, from_=1.0, to=10.0, 
                               variable=self.fwhm,
                               orient=tk.HORIZONTAL,
                               command=self.on_param_change)
        fwhm_scale.pack(fill=tk.X, pady=5)
        self.fwhm_label = ttk.Label(control_frame, text=f"Valeur: {self.fwhm.get():.1f}")
        self.fwhm_label.pack(anchor=tk.W)
        
        ttk.Label(control_frame, text="Facteur de réduction:").pack(anchor=tk.W, pady=(10,0))
        reduction_scale = ttk.Scale(control_frame, from_=0.0, to=1.0, 
                                    variable=self.reduction_factor,
                                    orient=tk.HORIZONTAL,
                                    command=self.on_param_change)
        reduction_scale.pack(fill=tk.X, pady=5)
        self.reduction_label = ttk.Label(control_frame, text=f"Valeur: {self.reduction_factor.get():.2f}")
        self.reduction_label.pack(anchor=tk.W)
        
        ttk.Separator(control_frame, orient='horizontal').pack(fill=tk.X, pady=10)
        
        ttk.Button(control_frame, text="Sauvegarder le résultat", 
                   command=self.save_result).pack(fill=tk.X, pady=5)
        
        self.blink_button = ttk.Button(control_frame, text="Mode Clignotement", 
                   command=self.toggle_blink_mode)
        self.blink_button.pack(fill=tk.X, pady=5)
        
        ttk.Button(control_frame, text="Astrométrie (Phase 3)", 
                   command=self.run_astrometry).pack(fill=tk.X, pady=5)
        
        self.info_label = ttk.Label(control_frame, text="", 
                                     foreground="green", wraplength=200)
        self.info_label.pack(pady=10)
        
        image_frame = ttk.Frame(main_frame)
        image_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.fig, self.axes = plt.subplots(1, 2, figsize=(12, 6))
        self.fig.tight_layout(pad=3.0)
        
        self.axes[0].set_title("Image originale")
        self.axes[0].axis('off')
        
        self.axes[1].set_title("Image avec réduction des étoiles")
        self.axes[1].axis('off')
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=image_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
    def load_fits(self):
        file_path = filedialog.askopenfilename(
            title="Sélectionner un fichier FITS",
            filetypes=[("FITS files", "*.fits"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
            
        try:
            self.fits_file = file_path
            hdul = fits.open(file_path)
            self.data = hdul[0].data
            
            if self.data.ndim == 3 and self.data.shape[0] == 3:
                self.data = np.transpose(self.data, (1, 2, 0))
            
            self.data = self.data.astype(np.float32)
            
            if self.data.ndim == 3:
                self.image = np.zeros_like(self.data, dtype=np.float32)
                for i in range(self.data.shape[2]):
                    channel = self.data[:, :, i]
                    self.image[:, :, i] = (channel - channel.min()) / (channel.max() - channel.min())
                self.data_gray = np.mean(self.data, axis=2).astype(np.float32)
            else:
                self.image = (self.data - self.data.min()) / (self.data.max() - self.data.min())
                self.data_gray = self.data.astype(np.float32)
            
            hdul.close()
            
            self.axes[0].clear()
            self.axes[0].set_title("Image originale")
            if self.data.ndim == 3:
                self.axes[0].imshow(self.image)
            else:
                self.axes[0].imshow(self.image, cmap='gray')
            self.axes[0].axis('off')
            self.canvas.draw()
            
            filename = os.path.basename(file_path)
            self.file_label.config(text=f"Fichier: {filename}")
            self.info_label.config(text="OK!", foreground="green")
            
            self.apply_reduction()
            
        except Exception as e:
            self.info_label.config(text=f"Erreur: {str(e)}", foreground="red")
    
    def on_param_change(self, event=None):
        self.kernel_label.config(text=f"Valeur: {self.kernel_size.get()}")
        self.threshold_label.config(text=f"Valeur: {self.threshold_multiplier.get():.2f}")
        self.fwhm_label.config(text=f"Valeur: {self.fwhm.get():.1f}")
        self.reduction_label.config(text=f"Valeur: {self.reduction_factor.get():.2f}")
        
        if self.update_id:
            self.root.after_cancel(self.update_id)
        
        self.update_id = self.root.after(200, self.apply_reduction)
    
    def apply_reduction(self):
        if self.data is None:
            return
        
        try:
            mean, median, std = sigma_clipped_stats(self.data_gray, sigma=3.0)
            
            sources = None
            threshold_base = median + (self.threshold_multiplier.get() * std)
            
            for multiplier in [1.0, 0.8, 0.6, 0.4]:
                threshold = median + (self.threshold_multiplier.get() * std * multiplier)
                try:
                    daofind = DAOStarFinder(fwhm=self.fwhm.get(), threshold=threshold, sharplo=0.2, sharphi=1.0)
                    sources = daofind(self.data_gray - median)
                    if sources and len(sources) >= 3:
                        break
                except:
                    continue
            
            if not sources or len(sources) == 0:
                try:
                    threshold = median + std
                    daofind = DAOStarFinder(fwhm=self.fwhm.get(), threshold=threshold, sharplo=0.1, sharphi=1.5)
                    sources = daofind(self.data_gray - median)
                except:
                    sources = None
            
            if sources and len(sources) > 0:
                mask = np.zeros(self.data_gray.shape, dtype=np.float32)
                flux_max = sources['flux'].max()
                
                for source in sources:
                    x = int(source['xcentroid'])
                    y = int(source['ycentroid'])
                    flux = source['flux']
                    rayon = int(3 + 12 * (flux / flux_max))
                    rayon = max(3, min(rayon, 15))
                    cv.circle(mask, (x, y), rayon, 1.0, -1)
                
                mask_adouci = cv.GaussianBlur(mask, (21, 21), 0)
                
                kernel_size = self.kernel_size.get()
                if kernel_size % 2 == 0:
                    kernel_size += 1
                
                if self.data.ndim == 3:
                    image_float = self.image * 255.0
                    image_erodee = np.zeros_like(image_float, dtype=np.float32)
                    for i in range(image_float.shape[2]):
                        image_erodee[:, :, i] = cv.medianBlur(image_float[:, :, i].astype(np.uint8), kernel_size).astype(np.float32)
                    image_erodee = image_erodee / 255.0
                    
                    mask_3d = np.stack([mask_adouci] * 3, axis=2)
                    facteur = self.reduction_factor.get()
                    difference = self.image - image_erodee
                    image_finale = self.image - (facteur * mask_3d * difference)
                else:
                    image_float = self.image * 255.0
                    image_erodee = cv.medianBlur(image_float.astype(np.uint8), kernel_size).astype(np.float32) / 255.0
                    
                    facteur = self.reduction_factor.get()
                    difference = self.image - image_erodee
                    image_finale = self.image - (facteur * mask_adouci * difference)
                
                self.result_image = image_finale
                self.axes[1].clear()
                self.axes[1].set_title("Image avec réduction des étoiles")
                if self.data.ndim == 3:
                    self.axes[1].imshow(np.clip(image_finale, 0, 1))
                else:
                    self.axes[1].imshow(np.clip(image_finale, 0, 1), cmap='gray')
                self.axes[1].axis('off')
                self.canvas.draw()
                
                self.info_label.config(
                    text=f"{len(sources)} étoiles",
                    foreground="green"
                )
            else:
                self.result_image = self.image.copy()
                self.axes[1].clear()
                self.axes[1].set_title("Image avec réduction des étoiles")
                if self.data.ndim == 3:
                    self.axes[1].imshow(self.image)
                else:
                    self.axes[1].imshow(self.image, cmap='gray')
                self.axes[1].axis('off')
                self.canvas.draw()
                
                self.info_label.config(text="Aucune étoile détectée", foreground="orange")
                
        except Exception as e:
            self.info_label.config(text=f"Erreur: {str(e)}", foreground="red")
    
    def save_result(self):
        if not hasattr(self, 'result_image'):
            self.info_label.config(text="Pas de résultat!", foreground="red")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Sauvegarder l'image",
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                if self.data.ndim == 3:
                    plt.imsave(file_path, np.clip(self.result_image, 0, 1))
                else:
                    plt.imsave(file_path, np.clip(self.result_image, 0, 1), cmap='gray')
                self.info_label.config(text=f"Sauvegardé!", foreground="green")
            except Exception as e:
                self.info_label.config(text=f"Erreur save: {str(e)}", foreground="red")
    
    def toggle_blink_mode(self):
        if not hasattr(self, 'result_image') or self.data is None:
            self.info_label.config(text="Pas de résultat!", foreground="red")
            return
        
        if self.is_blinking:
            self.stop_blinking()
        else:
            self.start_blinking()
    
    def start_blinking(self):
        try:
            self.is_blinking = True
            self.blink_button.config(text="Vue Avant/Apres")
            
            self.axes[1].set_visible(False)
            self.axes[0].set_position([0.05, 0.05, 0.9, 0.9])
            
            images = [self.image, self.result_image]
            labels = ['AVANT', 'APRÈS']
            
            def update(frame):
                self.axes[0].clear()
                self.axes[0].axis('off')
                
                current_img = images[frame % 2]
                current_label = labels[frame % 2]
                
                if self.data.ndim == 3:
                    self.axes[0].imshow(np.clip(current_img, 0, 1))
                else:
                    self.axes[0].imshow(np.clip(current_img, 0, 1), cmap='gray')
                
                self.axes[0].text(0.5, 0.05, current_label, 
                                transform=self.axes[0].transAxes,
                                ha='center', fontsize=16, fontweight='bold',
                                bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.8))
                
                return []
            
            self.animation = FuncAnimation(self.fig, update, frames=100,
                                         interval=800, repeat=True, blit=False)
            
            self.canvas.draw()
            self.info_label.config(text="Mode clignotement actif", foreground="blue")
            
        except Exception as e:
            self.info_label.config(text=f"Erreur animation: {str(e)}", foreground="red")
            self.is_blinking = False
    
    def stop_blinking(self):
        try:
            self.is_blinking = False
            self.blink_button.config(text="Mode Clignotement")
            
            if self.animation:
                self.animation.event_source.stop()
                self.animation = None
            
            self.axes[1].set_visible(True)
            self.axes[0].set_position([0.125, 0.11, 0.352, 0.77])
            self.axes[1].set_position([0.547, 0.11, 0.352, 0.77])
            
            self.axes[0].clear()
            self.axes[0].set_title("Image originale")
            if self.data.ndim == 3:
                self.axes[0].imshow(self.image)
            else:
                self.axes[0].imshow(self.image, cmap='gray')
            self.axes[0].axis('off')
            
            self.axes[1].clear()
            self.axes[1].set_title("Image avec réduction des étoiles")
            if self.data.ndim == 3:
                self.axes[1].imshow(np.clip(self.result_image, 0, 1))
            else:
                self.axes[1].imshow(np.clip(self.result_image, 0, 1), cmap='gray')
            self.axes[1].axis('off')
            
            self.canvas.draw()
            self.info_label.config(text="Vue normale", foreground="green")
            
        except Exception as e:
            self.info_label.config(text=f"Erreur: {str(e)}", foreground="red")


    def run_astrometry(self):
        if self.fits_file is None:
            self.info_label.config(text="Charger un fichier FITS d'abord!", foreground="red")
            return
        
        self.info_label.config(text="Astrométrie en cours...", foreground="blue")
        
        def log(message):
            pass
        
        def run_astrometry_thread():
            try:
                if self.is_blinking:
                    self.root.after(0, self.stop_blinking)
                
                API_KEY = "siupcwbetlrmnrwm"
                API_URL = "http://nova.astrometry.net/api/"
                
                with fits.open(self.fits_file) as hdul:
                    image = hdul[0].data.astype(float)
                
                if len(image.shape) == 3:
                    image = image[0]
                
                image_norm = (image - image.min()) / (image.max() - image.min())
                
                USE_API = True
                
                response = requests.post(
                    API_URL + "login",
                    data={'request-json': json.dumps({"apikey": API_KEY})}
                )
                if response.status_code == 200:
                    session = response.json()
                    if session['status'] == 'success':
                        session_id = session['session']
                    else:
                        USE_API = False
                else:
                    USE_API = False
                
                if USE_API:
                    with open(self.fits_file, 'rb') as f:
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
                            submission_id = result['subid']
                        else:
                            USE_API = False
                    else:
                        USE_API = False
                
                if USE_API:
                    start_time = time.time()
                    timeout = 300
                    job_id = None
                    
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
                                                break
                                            elif status == 'failure':
                                                USE_API = False
                                                break
                                        except json.JSONDecodeError:
                                            pass
                        except Exception as e:
                            pass
                        
                        time.sleep(5)
                    
                    if job_id is None or time.time() - start_time >= timeout:
                        USE_API = False
                
                if USE_API and job_id:
                    response = requests.get(API_URL + f"jobs/{job_id}/calibration/")
                    if response.status_code == 200:
                        calibration = response.json()
                        
                        wcs_url = f"http://nova.astrometry.net/wcs_file/{job_id}"
                        response = requests.get(wcs_url)
                        
                        if response.status_code == 200:
                            wcs_path = "temp_wcs.fits"
                            with open(wcs_path, 'wb') as f:
                                f.write(response.content)
                            
                            try:
                                wcs = WCS(wcs_path)
                                os.remove(wcs_path)
                                
                                try:
                                    from astroquery.gaia import Gaia
                                    
                                    ra_center = calibration.get('ra')
                                    dec_center = calibration.get('dec')
                                    pixscale = calibration.get('pixscale')
                                    
                                    diagonal_pixels = np.sqrt(image.shape[0]**2 + image.shape[1]**2)
                                    diagonal_arcsec = diagonal_pixels * pixscale
                                    radius_deg = (diagonal_arcsec / 3600.0) / 2.0 * 1.1
                                    
                                    query = f"""
                                    SELECT TOP 10000
                                        ra, dec, phot_g_mean_mag
                                    FROM gaiadr3.gaia_source
                                    WHERE 
                                        CONTAINS(POINT('ICRS', ra, dec),
                                                CIRCLE('ICRS', {ra_center}, {dec_center}, {radius_deg})) = 1
                                        AND phot_g_mean_mag < 20
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
                                    
                                    mask = np.zeros(image.shape, dtype=np.uint8)
                                    n_masked = 0
                                    n_total = 0
                                    
                                    for percentile_threshold in [85, 75, 65, 50]:
                                        intensity_threshold = np.percentile(image, percentile_threshold)
                                        mask = np.zeros(image.shape, dtype=np.uint8)
                                        n_masked = 0
                                        n_total = 0
                                        
                                        for star in stars:
                                            coord = SkyCoord(ra=star['ra']*u.degree, dec=star['dec']*u.degree)
                                            x, y = wcs.world_to_pixel(coord)
                                            
                                            x = int(x)
                                            y = int(y)
                                            
                                            if 0 <= x < image.shape[1] and 0 <= y < image.shape[0]:
                                                n_total += 1
                                                
                                                pixel_value = image[y, x]
                                                
                                                if pixel_value > intensity_threshold:
                                                    radius = int(18 - star['mag'])
                                                    radius = max(2, min(radius, 12))
                                                    
                                                    cv.circle(mask, (x, y), radius, 255, -1)
                                                    n_masked += 1
                                        
                                        if n_masked >= 5 or percentile_threshold == 50:
                                            break
                                    
                                    method = "Astrometry.net + Gaia DR3"
                                    
                                except Exception as e:
                                    USE_API = False
                                    
                            except Exception as e:
                                if os.path.exists(wcs_path):
                                    os.remove(wcs_path)
                                USE_API = False
                        else:
                            USE_API = False
                    else:
                        USE_API = False
                
                if not USE_API or n_masked == 0:
                    from photutils.detection import DAOStarFinder
                    
                    mean = np.mean(image)
                    median = np.median(image)
                    std = np.std(image)
                    
                    for threshold_multiplier in [3.0, 2.5, 2.0, 1.5]:
                        threshold = median + threshold_multiplier * std
                        
                        for fwhm_val in [3.0, 4.0, 5.0]:
                            try:
                                daofind = DAOStarFinder(fwhm=fwhm_val, threshold=threshold, sharplo=0.2, sharphi=1.0)
                                sources = daofind(image)
                                
                                if sources and len(sources) >= 5:
                                    mask = np.zeros(image.shape, dtype=np.uint8)
                                    for source in sources:
                                        x = int(source['xcentroid'])
                                        y = int(source['ycentroid'])
                                        flux = source['flux']
                                        
                                        radius = max(5, min(int(3 + np.log10(max(flux/1000, 1))), 30))
                                        cv.circle(mask, (x, y), radius, 255, -1)
                                    
                                    method = f"DAOStarFinder (seuil={threshold_multiplier}σ, fwhm={fwhm_val})"
                                    n_masked = len(sources)
                                    break
                            except:
                                continue
                        
                        if 'sources' in locals() and sources and len(sources) >= 5:
                            break
                    
                    if not ('sources' in locals() and sources and len(sources) > 0):
                        try:
                            threshold = median + 1.0 * std
                            daofind = DAOStarFinder(fwhm=5.0, threshold=threshold, sharplo=0.1, sharphi=1.5)
                            sources = daofind(image)
                            
                            if sources and len(sources) > 0:
                                mask = np.zeros(image.shape, dtype=np.uint8)
                                for source in sources:
                                    x = int(source['xcentroid'])
                                    y = int(source['ycentroid'])
                                    flux = source['flux']
                                    
                                    radius = max(5, min(int(3 + np.log10(max(flux/1000, 1))), 30))
                                    cv.circle(mask, (x, y), radius, 255, -1)
                                
                                method = "DAOStarFinder (mode permissif)"
                                n_masked = len(sources)
                            else:
                                mask = np.zeros(image.shape, dtype=np.uint8)
                                method = "Aucune étoile détectée"
                                n_masked = 0
                        except:
                            mask = np.zeros(image.shape, dtype=np.uint8)
                            method = "Aucune étoile détectée"
                            n_masked = 0
                
                Path("results").mkdir(exist_ok=True)
                plt.imsave("results/astrometry_masque.png", mask, cmap='gray')
                
                def update_display():
                    self.axes[1].set_visible(True)
                    self.axes[0].set_position([0.125, 0.11, 0.352, 0.77])
                    self.axes[1].set_position([0.547, 0.11, 0.352, 0.77])
                    
                    self.axes[0].clear()
                    self.axes[0].imshow(image_norm, cmap='gray', vmin=0, vmax=1)
                    self.axes[0].set_title(f"Original\n({method})")
                    self.axes[0].axis('off')
                    
                    self.axes[1].clear()
                    self.axes[1].imshow(mask, cmap='gray')
                    self.axes[1].set_title(f"Masque catalogue\n({np.sum(mask > 0)} pixels)")
                    self.axes[1].axis('off')
                    
                    self.fig.tight_layout()
                    self.canvas.draw()
                    
                    self.fig.savefig("results/astrometry_comparaison.jpg", dpi=150, bbox_inches='tight')
                    
                    if n_masked > 0:
                        self.info_label.config(text=f"Astrométrie OK! ({n_masked} étoiles)", foreground="green")
                    else:
                        self.info_label.config(text="Aucune étoile détectée", foreground="orange")
                
                self.root.after(0, update_display)
                
            except Exception as e:
                def show_error():
                    self.info_label.config(text=f"Erreur: {str(e)}", foreground="red")
                self.root.after(0, show_error)
        
        thread = threading.Thread(target=run_astrometry_thread, daemon=True)
        thread.start()


if __name__ == "__main__":
    root = tk.Tk()
    app = StarReductionGUI(root)
    root.mainloop()

