import json
import sys
import os

# Ajouter le chemin du projet
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lightrag.secu import SecurityManager

def show_keys():
    sec_manager = SecurityManager()
    
    try:
        with open(sec_manager.secu_file, 'r') as f:
            keys_data = json.load(f)
            print("Contenu du fichier de clés :")
            print(json.dumps(keys_data, indent=2))
    except FileNotFoundError:
        print("Le fichier de clés n'existe pas.")
    except json.JSONDecodeError:
        print("Erreur de lecture du fichier JSON.")

if __name__ == "__main__":
    show_keys()
