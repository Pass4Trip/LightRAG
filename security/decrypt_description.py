import sys
from pathlib import Path

# Add local LightRAG source to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import logging
from lightrag.secu import SecurityManager

# Configuration du logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def decrypt_description(user_id: str, encrypted_description: str) -> str:
    """
    Déchiffre une description chiffrée pour un utilisateur donné.
    
    Args:
        user_id (str): Identifiant de l'utilisateur
        encrypted_description (str): Description chiffrée
    
    Returns:
        str: Description déchiffrée, ou None en cas d'erreur
    """
    # Chemin du fichier de clés de sécurité
    security_keys_path = '/Users/vinh/Documents/LightRAG/security/security_keys.json'
    
    # Initialiser le gestionnaire de sécurité
    sec_manager = SecurityManager()
    
    try:
        # Charger les clés de sécurité
        with open(security_keys_path, 'r') as f:
            security_keys = json.load(f) or {}
        
        # Récupérer la clé privée de l'utilisateur
        user_private_key = security_keys.get(user_id, {}).get('private_key')
        
        if not user_private_key:
            logger.error(f"Aucune clé privée trouvée pour l'utilisateur {user_id}")
            return None
        
        # Déchiffrer la description
        decrypted_description = sec_manager.decrypt_data(
            encrypted_description, 
            user_private_key
        )
        
        logger.info(f"Description déchiffrée avec succès pour l'utilisateur {user_id}")
        return decrypted_description
    
    except FileNotFoundError:
        logger.error(f"Fichier de clés de sécurité non trouvé : {security_keys_path}")
    except json.JSONDecodeError:
        logger.error(f"Erreur de décodage du fichier de clés : {security_keys_path}")
    except Exception as e:
        logger.error(f"Erreur lors du déchiffrement : {e}")
    
    return None

def main():
    # Exemple d'utilisation
    user_id = 'lea'
    encrypted_description = input("Entrez la description chiffrée : ")
    
    decrypted = decrypt_description(user_id, encrypted_description)
    if decrypted:
        print("Description déchiffrée :", decrypted)
    else:
        print("Impossible de déchiffrer la description.")

if __name__ == "__main__":
    main()