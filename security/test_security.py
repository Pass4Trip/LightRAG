import os
import sys
import json
import unittest

# Ajouter le chemin du projet pour importer secu.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lightrag.secu import SecurityManager

class TestSecurityManager(unittest.TestCase):
    def setUp(self):
        # Utiliser un fichier de test temporaire
        self.test_keys_dir = os.path.dirname(os.path.abspath(__file__))
        os.makedirs(self.test_keys_dir, exist_ok=True)
        self.test_keys_file = os.path.join(self.test_keys_dir, 'test_security_keys.json')
        
        # Nettoyer le fichier de test avant chaque test
        if os.path.exists(self.test_keys_file):
            os.remove(self.test_keys_file)
        
        print(f"Répertoire de test : {self.test_keys_dir}")
        print(f"Fichier de test : {self.test_keys_file}")
        print(f"Le répertoire existe : {os.path.exists(self.test_keys_dir)}")
        print(f"Le répertoire est accessible en écriture : {os.access(self.test_keys_dir, os.W_OK)}")
        
        self.sec_manager = SecurityManager(secu_file=self.test_keys_file)
        
        # Vérifier si le fichier a été créé
        print(f"Le fichier existe après initialisation : {os.path.exists(self.test_keys_file)}")
        if os.path.exists(self.test_keys_file):
            with open(self.test_keys_file, 'r') as f:
                print("Contenu initial du fichier :")
                print(f.read())

    def tearDown(self):
        # Nettoyer le fichier de test après chaque test
        if os.path.exists(self.test_keys_file):
            # Afficher le contenu du fichier avant de le supprimer
            print(f"\n--- Contenu du fichier JSON ({self.test_keys_file}) ---")
            with open(self.test_keys_file, 'r') as f:
                json_content = json.load(f)
                print(json.dumps(json_content, indent=2))
                print("--- Fin du contenu JSON ---")
            os.remove(self.test_keys_file)

    def test_generate_rsa_key_pair(self):
        """Tester la génération de paire de clés RSA"""
        user_id = "test_user"
        user_keys = self.sec_manager.generate_rsa_key_pair(user_id)
        
        self.assertIn('private_key', user_keys)
        self.assertIn('public_key', user_keys)
        self.assertIn('created_at', user_keys)
        
        # Vérifier que le fichier existe et contient les clés
        self.assertTrue(os.path.exists(self.test_keys_file))
        with open(self.test_keys_file, 'r') as f:
            keys_data = json.load(f)
            self.assertIn(user_id, keys_data)

    def test_encrypt_decrypt_data(self):
        """Tester le chiffrement et déchiffrement de données"""
        user_id = "test_user"
        user_keys = self.sec_manager.generate_rsa_key_pair(user_id)
        
        original_data = "Données personnelles sensibles"
        encrypted_data = self.sec_manager.encrypt_data(original_data, user_keys['public_key'])
        decrypted_data = self.sec_manager.decrypt_data(encrypted_data, user_keys['private_key'])
        
        self.assertEqual(original_data, decrypted_data)

    def test_get_user_keys(self):
        """Tester la récupération des clés d'un utilisateur"""
        user_id = "test_user"
        original_keys = self.sec_manager.generate_rsa_key_pair(user_id)
        retrieved_keys = self.sec_manager.get_user_keys(user_id)
        
        self.assertEqual(original_keys, retrieved_keys)

    def test_delete_user_keys(self):
        """Tester la suppression des clés d'un utilisateur"""
        user_id = "test_user"
        self.sec_manager.generate_rsa_key_pair(user_id)
        
        # Vérifier que les clés existent
        self.assertIsNotNone(self.sec_manager.get_user_keys(user_id))
        
        # Supprimer les clés
        result = self.sec_manager.delete_user_keys(user_id)
        self.assertTrue(result)
        
        # Vérifier que les clés ont été supprimées
        self.assertIsNone(self.sec_manager.get_user_keys(user_id))

    def test_generate_verify_token(self):
        """Tester la génération et la vérification de token"""
        user_id = "test_user"
        token = self.sec_manager.generate_access_token(user_id)
        
        # Vérifier le token
        payload = self.sec_manager.verify_access_token(token)
        self.assertIsNotNone(payload)
        self.assertEqual(payload['user_id'], user_id)

    def test_invalid_token(self):
        """Tester la gestion d'un token invalide"""
        invalid_token = "invalid_token_string"
        payload = self.sec_manager.verify_access_token(invalid_token)
        self.assertIsNone(payload)

if __name__ == '__main__':
    unittest.main()
