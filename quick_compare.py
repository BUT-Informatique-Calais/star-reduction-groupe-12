"""Script rapide pour utiliser le Comparateur Avant/Après"""

from comparateur_image import ImageComparator
import os


def main():
    before_path = "./results/original.png"
    after_path = "./results/image_finale.png"
    
    if not os.path.exists(before_path) or not os.path.exists(after_path):
        print("Erreur : Les fichiers d'images n'existent pas")
        return
    
    try:
        comparator = ImageComparator(before_path, after_path, title="Réduction d'Étoiles")
        
        print("\n--- Visualisation Avant/Après ---\n")
        
        while True:
            print("1. Comparaison côte à côte")
            print("2. Mode clignotement")
            print("3. Analyse de soustraction (détection pertes)")
            print("4. Quitter\n")
            
            choice = input("Choisissez (1-4) : ").strip()
            
            if choice == '1':
                comparator.compare_side_by_side(save_path="./results/comparison.png")
                
            elif choice == '2':
                comparator.blink_comparison(interval=800, num_cycles=3, save_path="./results/blink.gif")
                
            elif choice == '3':
                comparator.difference_analysis(method='subtraction', save_path="./results/difference.png")
                
            elif choice == '4':
                break
                
            else:
                print("Option invalide\n")
        
    except Exception as e:
        print(f"Erreur : {e}")


if __name__ == "__main__":
    main()
