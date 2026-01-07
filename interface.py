"""
Interface Graphique pour la Réduction des Étoiles - VERSION INCOMPLETE
SAÉ S3.C2 - Star Reduction Project
"""

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
        self.root.title("Star Reduction - Interface")
        self.root.geometry("1400x800")
        
        self.fits_file = None
        self.data = None
        # TODO
        
        self.kernel_size = tk.IntVar(value=7)
        self.threshold_multiplier = tk.DoubleVar(value=1.5)
        # TODO
        
        self.setup_ui()
        
    def setup_ui(self):
        
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        control_frame = ttk.LabelFrame(main_frame, text="Contrôles", padding=10)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        ttk.Button(control_frame, text="Charger fichier FITS", 
                   command=self.load_fits).pack(fill=tk.X, pady=5)
        
        # TODO
        
        ttk.Separator(control_frame, orient='horizontal').pack(fill=tk.X, pady=10)
        
        ttk.Label(control_frame, text="Taille du noyau d'érosion:").pack(anchor=tk.W)
        kernel_scale = ttk.Scale(control_frame, from_=3, to=15, 
                                 variable=self.kernel_size, 
                                 orient=tk.HORIZONTAL)
        kernel_scale.pack(fill=tk.X, pady=5)
        
        # TODO
        
        ttk.Separator(control_frame, orient='horizontal').pack(fill=tk.X, pady=10)
        
        ttk.Button(control_frame, text="Appliquer la réduction", 
                   command=self.apply_reduction).pack(fill=tk.X, pady=5)
        
        # TODO
        
        image_frame = ttk.Frame(main_frame)
        image_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # TODO
        
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
            
            # TODO
            
            hdul.close()
            
            # TODO
            
            print(f"Fichier chargé: {os.path.basename(file_path)}")
            
        except Exception as e:
            print(f"Erreur: {str(e)}")
    
    def apply_reduction(self):
        if self.data is None:
            print("Aucun fichier chargé!")
            return
        
        try:
            print("Début du traitement...")
            
            # TODO
            
            print("Traitement non implémenté!")
            
        except Exception as e:
            print(f"Erreur: {str(e)}")
    
    def save_result(self):
        # TODO
        pass


if __name__ == "__main__":
    root = tk.Tk()
    app = StarReductionGUI(root)
    root.mainloop()
