import sys
import os
import json

# Ajouter le chemin du projet pour importer secu.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lightrag.secu import SecurityManager

def main():
    # Initialiser le gestionnaire de sécurité
    sec_manager = SecurityManager()

    # Identifiant utilisateur
    user_id = "john_doe"

    print(" Démonstration du module de sécurité \n")

    # Afficher le contenu initial du fichier JSON
    print("Contenu initial du fichier JSON :")
    try:
        with open(sec_manager.secu_file, 'r') as f:
            initial_content = json.load(f)
            print(json.dumps(initial_content, indent=2))
    except Exception as e:
        print(f"Erreur de lecture du fichier : {e}")

    # 1. Générer une paire de clés RSA
    print("\n1. Génération des clés RSA pour l'utilisateur...")
    user_keys = sec_manager.generate_rsa_key_pair(user_id)
    print("   Clés générées avec succès !")

    # Afficher le contenu du fichier JSON après génération
    print("\nContenu du fichier JSON après génération :")
    try:
        with open(sec_manager.secu_file, 'r') as f:
            updated_content = json.load(f)
            print(json.dumps(updated_content, indent=2))
    except Exception as e:
        print(f"Erreur de lecture du fichier : {e}")

    # 2. Chiffrer des données sensibles
    sensitive_data = "Informations confidentielles de John Doe"
    print(f"\n2. Chiffrement des données : {sensitive_data}")
    encrypted_data = sec_manager.encrypt_data(sensitive_data, user_keys['public_key'])
    print("   Données chiffrées avec succès !")

    # 3. Déchiffrer les données
    print("\n3. Déchiffrement des données...")
    decrypted_data = sec_manager.decrypt_data(encrypted_data, user_keys['private_key'])
    print(f"   Données déchiffrées : {decrypted_data}")
    
    # Vérification du déchiffrement
    assert sensitive_data == decrypted_data, "Erreur de déchiffrement !"

    # 4. Générer un token d'accès
    print("\n4. Génération d'un token d'accès...")
    access_token = sec_manager.generate_access_token(user_id)
    print("   Token généré avec succès !")

    # 5. Vérifier le token
    print("\n5. Vérification du token...")
    payload = sec_manager.verify_access_token(access_token)
    print(f"   Token valide pour l'utilisateur : {payload['user_id']}")

    # 6. Récupérer les clés de l'utilisateur
    print("\n6. Récupération des clés...")
    retrieved_keys = sec_manager.get_user_keys(user_id)
    print("   Clés récupérées avec succès !")

    # COMMENTÉ : Suppression des clés
    # print("\n7. Suppression des clés...")
    # sec_manager.delete_user_keys(user_id)
    # print("   Clés supprimées avec succès !")

    # Afficher le contenu final du fichier JSON
    print("\nContenu final du fichier JSON :")
    try:
        with open(sec_manager.secu_file, 'r') as f:
            final_content = json.load(f)
            print(json.dumps(final_content, indent=2))
    except Exception as e:
        print(f"Erreur de lecture du fichier : {e}")

    print("\n Démonstration terminée avec succès ! ")

if __name__ == "__main__":
    main()
