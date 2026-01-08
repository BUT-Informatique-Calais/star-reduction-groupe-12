from astropy.io import fits
from astropy.stats import sigma_clipped_stats
from photutils.detection import DAOStarFinder
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import cv2 as cv
import numpy as np
import tkinter as tk
from tkinter import filedialog, ttk
import os


class StarReductionGUI:
    
    def __init__(self, root):
        self.root = root
        self.root.title("Star Reduction - Interface Temps Réel")
        self.root.geometry("1400x800")
        
        # donnees du fichier FITS
        self.fits_file = None
        self.data = None
        self.image = None
        self.data_gray = None
        
        # parametres de l'algo
        self.kernel_size = tk.IntVar(value=7)
        self.threshold_multiplier = tk.DoubleVar(value=1.5)
        self.reduction_factor = tk.DoubleVar(value=0.5)
        self.fwhm = tk.DoubleVar(value=3.0)
        
        # pour eviter trop de calculs
        self.update_id = None
        
        self.setup_ui()
        
    def setup_ui(self):
        # construction de l'interface
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # panneau de gauche avec les controles
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
        
        self.info_label = ttk.Label(control_frame, text="", 
                                     foreground="green", wraplength=200)
        self.info_label.pack(pady=10)
        
        # zone d'affichage des images
        image_frame = ttk.Frame(main_frame)
        image_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 2 graphiques cote a cote
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
            # ouverture du FITS
            self.fits_file = file_path
            hdul = fits.open(file_path)
            self.data = hdul[0].data
            
            # reoriente si image couleur
            if self.data.ndim == 3 and self.data.shape[0] == 3:
                self.data = np.transpose(self.data, (1, 2, 0))
            
            self.data = self.data.astype(np.float32)
            
            # normalisation entre 0 et 1
            if self.data.ndim == 3:
                # traiter chaque canal RGB
                self.image = np.zeros_like(self.data, dtype=np.float32)
                for i in range(self.data.shape[2]):
                    channel = self.data[:, :, i]
                    self.image[:, :, i] = (channel - channel.min()) / (channel.max() - channel.min())
                # version gris pour detection
                self.data_gray = np.mean(self.data, axis=2).astype(np.float32)
            else:
                self.image = (self.data - self.data.min()) / (self.data.max() - self.data.min())
                self.data_gray = self.data.astype(np.float32)
            
            hdul.close()
            
            # affichage image chargee
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
            
            # applique direct la reduction
            self.apply_reduction()
            
        except Exception as e:
            self.info_label.config(text=f"Erreur: {str(e)}", foreground="red")
    
    def on_param_change(self, event=None):
        # maj des labels
        self.kernel_label.config(text=f"Valeur: {self.kernel_size.get()}")
        self.threshold_label.config(text=f"Valeur: {self.threshold_multiplier.get():.2f}")
        self.fwhm_label.config(text=f"Valeur: {self.fwhm.get():.1f}")
        self.reduction_label.config(text=f"Valeur: {self.reduction_factor.get():.2f}")
        
        # annule l'ancien update si pas encore execute
        if self.update_id:
            self.root.after_cancel(self.update_id)
        
        # lance un nouveau update apres 200ms
        self.update_id = self.root.after(200, self.apply_reduction)
    
    def apply_reduction(self):
        if self.data is None:
            return
        
        try:
            # detection des etoiles avec DAOStarFinder
            mean, median, std = sigma_clipped_stats(self.data_gray, sigma=3.0)
            threshold = median + (self.threshold_multiplier.get() * std)
            daofind = DAOStarFinder(fwhm=self.fwhm.get(), threshold=threshold)
            sources = daofind(self.data_gray - median)
            
            if sources:
                # creation masque binaire pour les etoiles
                mask = np.zeros(self.data_gray.shape, dtype=np.float32)
                flux_max = sources['flux'].max()
                
                # dessiner un cercle par etoile
                for source in sources:
                    x = int(source['xcentroid'])
                    y = int(source['ycentroid'])
                    flux = source['flux']
                    rayon = int(3 + 12 * (flux / flux_max))
                    rayon = max(3, min(rayon, 15))
                    cv.circle(mask, (x, y), rayon, 1.0, -1)
                
                # flou sur le masque pour transitions douces
                mask_adouci = cv.GaussianBlur(mask, (21, 21), 0)
                
                # filtre median pour reduire les etoiles
                kernel_size = self.kernel_size.get()
                # medianBlur necessite une taille impaire
                if kernel_size % 2 == 0:
                    kernel_size += 1
                
                if self.data.ndim == 3:
                    # filtre median sur image couleur
                    image_float = self.image * 255.0
                    image_erodee = np.zeros_like(image_float, dtype=np.float32)
                    for i in range(image_float.shape[2]):
                        image_erodee[:, :, i] = cv.medianBlur(image_float[:, :, i].astype(np.uint8), kernel_size).astype(np.float32)
                    image_erodee = image_erodee / 255.0
                    
                    # interpolation par soustraction de la difference
                    mask_3d = np.stack([mask_adouci] * 3, axis=2)
                    facteur = self.reduction_factor.get()
                    difference = self.image - image_erodee
                    image_finale = self.image - (facteur * mask_3d * difference)
                else:
                    # filtre median sur image monochrome
                    image_float = self.image * 255.0
                    image_erodee = cv.medianBlur(image_float.astype(np.uint8), kernel_size).astype(np.float32) / 255.0
                    
                    # interpolation par soustraction de la difference
                    facteur = self.reduction_factor.get()
                    difference = self.image - image_erodee
                    image_finale = self.image - (facteur * mask_adouci * difference)
                
                # affichage resultat
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
                self.info_label.config(text="Aucune étoile", foreground="orange")
                
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


if __name__ == "__main__":
    root = tk.Tk()
    app = StarReductionGUI(root)
    root.mainloop()

