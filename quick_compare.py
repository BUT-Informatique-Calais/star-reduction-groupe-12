"""Script rapide pour utiliser le Comparateur Avant/Après
"""

from image_comparator import ImageComparator
import os


def main():
    """Démonstration des fonctionnalités du comparateur."""
    
    print("\n--- Comparateur Avant/Après ---\n")
    
    # Chemins des images
    before_path = "./results/original.png"
    after_path = "./results/image_finale.png"
    
    # Vérifier que les fichiers existent
    if not os.path.exists(before_path) or not os.path.exists(after_path):
        print("Erreur : Les fichiers d'images n'existent pas")
        print("Assurez-vous d'avoir exécuté phase2_masque.py d'abord")
        return
    
    try:
        #creer le comparateur
        comparator = ImageComparator(
            before_path,
            after_path,
            title="Comparateur Avant/Après - Réduction d'Étoiles"
        )
        
        #menu interactif
        while True:
            print("\n--- Menu ---")
            print("1. Comparaison côte à côte")
            print("2. Analyse de différence (soustraction)")
            print("3. Analyse de différence (valeur absolue)")
            print("4. Comparaison d'histogrammes")
            print("5. Mode clignotement")
            print("6. Mode interactif")
            print("7. Générer tous les fichiers")
            print("8. Quitter")
            
            choice = input("\nChoisissez une option (1-8) : ").strip()
            
            if choice == '1':
                comparator.compare_side_by_side(
                    save_path="./results/comparison_side_by_side.png"
                )
                
            elif choice == '2':
                comparator.difference_analysis(
                    method='subtraction',
                    save_path="./results/difference_analysis_subtract.png"
                )
                
            elif choice == '3':
                comparator.difference_analysis(
                    method='absolute',
                    save_path="./results/difference_analysis_absolute.png"
                )
                
            elif choice == '4':
                comparator.histogram_comparison(
                    save_path="./results/histogram_comparison.png"
                )
                
            elif choice == '5':
                comparator.blink_comparison(
                    interval=800,
                    num_cycles=3,
                    save_path="./results/blink_comparison.gif"
                )
                
            elif choice == '6':
                comparator.create_interactive_blend(
                    save_path="./results/interactive_blend.png"
                )
                
            elif choice == '7':
                comparator.compare_side_by_side(
                    save_path="./results/01_comparison_side_by_side.png"
                )
                comparator.difference_analysis(
                    method='subtraction',
                    save_path="./results/02_difference_subtraction.png"
                )
                comparator.difference_analysis(
                    method='absolute',
                    save_path="./results/03_difference_absolute.png"
                )
                comparator.histogram_comparison(
                    save_path="./results/04_histogram_comparison.png"
                )
                comparator.blink_comparison(
                    interval=800,
                    num_cycles=2,
                    save_path="./results/05_blink_comparison.gif"
                )
                
                print("\nFichiers générés avec succès")
                
            elif choice == '8':
                print("\nAu revoir")
                break
                
            else:
                print("Option invalide")
        
    except FileNotFoundError as e:
        print(f"Erreur : {e}")
    except Exception as e:
        print(f"Erreur : {e}")


if __name__ == "__main__":
    main()
