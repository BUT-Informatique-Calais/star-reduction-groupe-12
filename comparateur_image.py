"""Image Comparator Module"""

import cv2
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
from matplotlib.animation import FuncAnimation
import os


class ImageComparator:
    """Outil de comparaison d'images avant/après."""
    
    def __init__(self, image_before, image_after, title="Comparateur Avant/Après"):
        if isinstance(image_before, str):
            self.image_before = cv2.imread(image_before, cv2.IMREAD_UNCHANGED)
            if self.image_before is None:
                raise FileNotFoundError(f"Impossible de charger : {image_before}")
        else:
            self.image_before = image_before
            
        if isinstance(image_after, str):
            self.image_after = cv2.imread(image_after, cv2.IMREAD_UNCHANGED)
            if self.image_after is None:
                raise FileNotFoundError(f"Impossible de charger : {image_after}")
        else:
            self.image_after = image_after
        
        if self.image_before.shape != self.image_after.shape:
            raise ValueError(
                f"Les images doivent avoir la même taille. "
                f"Avant: {self.image_before.shape}, Après: {self.image_after.shape}"
            )
        
        self.title = title
        self.is_color = len(self.image_before.shape) == 3
        self.before_normalized = self._normalize(self.image_before)
        self.after_normalized = self._normalize(self.image_after)
        
    def _normalize(self, image):
        image_float = image.astype(np.float32)
        min_val = image_float.min()
        max_val = image_float.max()
        
        if max_val > min_val:
            normalized = (image_float - min_val) / (max_val - min_val)
        else:
            normalized = image_float
            
        return normalized
    
    def compare_side_by_side(self, save_path=None):
        fig, axes = plt.subplots(1, 2, figsize=(14, 6))
        fig.suptitle(self.title, fontsize=16, fontweight='bold')
        
        if self.is_color:
            axes[0].imshow(cv2.cvtColor(self.before_normalized, cv2.COLOR_BGR2RGB))
        else:
            axes[0].imshow(self.before_normalized, cmap='gray')
        axes[0].set_title('Image Originale', fontsize=12, fontweight='bold')
        axes[0].axis('off')
        
        if self.is_color:
            axes[1].imshow(cv2.cvtColor(self.after_normalized, cv2.COLOR_BGR2RGB))
        else:
            axes[1].imshow(self.after_normalized, cmap='gray')
        axes[1].set_title('Image Traitée', fontsize=12, fontweight='bold')
        axes[1].axis('off')
        
        plt.tight_layout()
        
        if save_path:
            os.makedirs(os.path.dirname(save_path) if os.path.dirname(save_path) else '.', exist_ok=True)
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"✓ Comparaison côte à côte sauvegardée : {save_path}")
        
        plt.show()
    
    def blink_comparison(self, interval=500, num_cycles=3, save_path=None):
        fig, ax = plt.subplots(figsize=(10, 8))
        fig.suptitle(f"{self.title} - Mode Clignotement", fontsize=14, fontweight='bold')
        
        images = []
        labels = []
        for _ in range(num_cycles):
            images.extend([self.before_normalized, self.after_normalized])
            labels.extend(['AVANT', 'APRÈS'])
        
        if self.is_color:
            im = ax.imshow(cv2.cvtColor(images[0], cv2.COLOR_BGR2RGB))
        else:
            im = ax.imshow(images[0], cmap='gray')
        
        text = ax.text(0.5, 0.05, '', transform=ax.transAxes, 
                      ha='center', fontsize=14, fontweight='bold',
                      bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        ax.axis('off')
        
        def update(frame):
            if self.is_color:
                im.set_data(cv2.cvtColor(images[frame % len(images)], cv2.COLOR_BGR2RGB))
            else:
                im.set_data(images[frame % len(images)])
            text.set_text(labels[frame % len(labels)])
            return im, text
        
        anim = FuncAnimation(fig, update, frames=len(images) * 2, 
                           interval=interval, repeat=True, blit=True)
        
        if save_path:
            os.makedirs(os.path.dirname(save_path) if os.path.dirname(save_path) else '.', exist_ok=True)
            anim.save(save_path, writer='pillow', fps=2)
            print(f" Animation de clignotement sauvegardée : {save_path}")
        
        plt.show()
        return anim
    
    def difference_analysis(self, method='subtraction', save_path=None):
        """TODO: Implémenter l'analyse des différences entre les deux images."""
        pass
    
    def _compute_statistics(self, difference):
        """TODO: Calculer les statistiques sur la différence."""
        pass
    
    def histogram_comparison(self, save_path=None):
        """TODO: Implémenter la comparaison des histogrammes."""
        pass
    
    def create_interactive_blend(self, save_path=None):
        """TODO: Implémenter le mode interactif pour blender entre avant et après."""
        pass


# TODO: Implémenter l'exemple d'utilisation
if __name__ == "__main__":
    pass
