import os
import jwt
import json
import base64
import logging
from datetime import datetime, timedelta
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding as asymmetric_padding
from cryptography.hazmat.backends import default_backend

logger = logging.getLogger(__name__)

class SecurityManager:
    def __init__(self, secu_file='/Users/vinh/Documents/LightRAG/security/security_keys.json'):
        self.secu_file = secu_file
        # Créer le répertoire s'il n'existe pas
        os.makedirs(os.path.dirname(secu_file), exist_ok=True)
        
        # Initialiser le fichier JSON s'il n'existe pas
        if not os.path.exists(secu_file):
            with open(secu_file, 'w') as f:
                json.dump({}, f)

    def _load_keys(self):
        """Charge les clés depuis le fichier JSON."""
        try:
            with open(self.secu_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _save_keys(self, keys_data):
        """Sauvegarde les clés dans le fichier JSON."""
        with open(self.secu_file, 'w') as f:
            json.dump(keys_data, f, indent=4)

    def generate_rsa_key_pair(self, user_id, key_size=4096):
        """
        Génère une paire de clés RSA pour un utilisateur.
        
        Args:
            user_id (str): Identifiant unique de l'utilisateur
            key_size (int, optional): Taille de la clé RSA. Défaut à 4096.
        """
        try:
            # Générer la paire de clés avec une taille plus grande
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=key_size,
                backend=default_backend()
            )
            public_key = private_key.public_key()

            # Sérialiser les clés
            private_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            public_pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )

            # Charger les clés existantes ou initialiser
            try:
                with open(self.secu_file, 'r') as f:
                    keys_data = json.load(f) or {}
            except (FileNotFoundError, json.JSONDecodeError):
                keys_data = {}

            # Stocker les nouvelles clés
            keys_data[user_id] = {
                'private_key': private_pem.decode('utf-8'),
                'public_key': public_pem.decode('utf-8')
            }

            # Sauvegarder les clés
            with open(self.secu_file, 'w') as f:
                json.dump(keys_data, f, indent=2)

            logger.info(f"Clés RSA générées pour l'utilisateur {user_id}")
        except Exception as e:
            logger.error(f"Erreur lors de la génération des clés RSA : {e}")
            raise

    def encrypt_data(self, data, public_key_pem, max_chunk_size=470):
        """Chiffre des données avec une clé publique RSA 4096 bits."""
        try:
            if not data:
                raise ValueError("Les données à chiffrer ne peuvent pas être vides")
            if not public_key_pem or not isinstance(public_key_pem, str):
                raise ValueError("La clé publique doit être une chaîne valide")
            
            public_key = serialization.load_pem_public_key(public_key_pem.encode('utf-8'))
            
            # Conversion en chaîne si ce n'est pas déjà le cas
            data_str = str(data)
            
            # Découpage en fragments
            fragments = [data_str[i:i + max_chunk_size] for i in range(0, len(data_str), max_chunk_size)]
            
            # Chiffrer chaque fragment
            encrypted_fragments = []
            for i, fragment in enumerate(fragments):
                try:
                    fragment_bytes = fragment.encode('utf-8')
                    encrypted_fragment = public_key.encrypt(
                        fragment_bytes,
                        asymmetric_padding.OAEP(
                            mgf=asymmetric_padding.MGF1(algorithm=hashes.SHA256()),
                            algorithm=hashes.SHA256(),
                            label=None
                        )
                    )
                    encrypted_fragments.append(base64.b64encode(encrypted_fragment).decode('utf-8'))
                except Exception as e:
                    logger.error(f"Erreur lors du chiffrement du fragment {i}: {str(e)}")
                    raise ValueError(f"Erreur de chiffrement du fragment {i}: {str(e)}")
            
            # Retourner un seul fragment ou un tableau JSON
            return json.dumps(encrypted_fragments) if len(encrypted_fragments) > 1 else encrypted_fragments[0]
            
        except Exception as e:
            logger.error(f"Erreur de chiffrement : {str(e)}")
            raise

    def decrypt_data(self, encrypted_data, private_key_pem):
        """Déchiffre des données avec une clé privée RSA 4096 bits."""
        try:
            if not encrypted_data:
                raise ValueError("Les données chiffrées ne peuvent pas être vides")
            if not private_key_pem or not isinstance(private_key_pem, str):
                raise ValueError("La clé privée doit être une chaîne valide")
            
            private_key = serialization.load_pem_private_key(
                private_key_pem.encode('utf-8'),
                password=None
            )
            
            try:
                # Essayer de décoder comme un tableau JSON
                encrypted_fragments = json.loads(encrypted_data)
                if isinstance(encrypted_fragments, list):
                    decrypted_fragments = []
                    for i, encrypted_fragment_base64 in enumerate(encrypted_fragments):
                        try:
                            encrypted_bytes = base64.b64decode(encrypted_fragment_base64.encode('utf-8'))
                            decrypted_fragment = private_key.decrypt(
                                encrypted_bytes,
                                asymmetric_padding.OAEP(
                                    mgf=asymmetric_padding.MGF1(algorithm=hashes.SHA256()),
                                    algorithm=hashes.SHA256(),
                                    label=None
                                )
                            )
                            decrypted_fragments.append(decrypted_fragment.decode('utf-8'))
                        except Exception as e:
                            logger.error(f"Erreur lors du déchiffrement du fragment {i}: {str(e)}")
                            continue
                    
                    if not decrypted_fragments:
                        raise ValueError("Aucun fragment n'a pu être déchiffré")
                    return ''.join(decrypted_fragments)
            except json.JSONDecodeError:
                # Si ce n'est pas un JSON valide, traiter comme un fragment unique
                try:
                    encrypted_bytes = base64.b64decode(encrypted_data.encode('utf-8'))
                    decrypted_data = private_key.decrypt(
                        encrypted_bytes,
                        asymmetric_padding.OAEP(
                            mgf=asymmetric_padding.MGF1(algorithm=hashes.SHA256()),
                            algorithm=hashes.SHA256(),
                            label=None
                        )
                    )
                    return decrypted_data.decode('utf-8')
                except base64.binascii.Error as e:
                    logger.error(f"Erreur de décodage base64: {str(e)}")
                    raise ValueError("Format de données chiffrées invalide")
                
        except Exception as e:
            logger.error(f"Erreur de déchiffrement : {str(e)}")
            raise

    def generate_access_token(self, user_id, expiration_hours=24):
        """Génère un token d'accès JWT."""
        payload = {
            'user_id': user_id,
            'exp': datetime.utcnow() + timedelta(hours=expiration_hours)
        }
        secret_key = os.environ.get('JWT_SECRET_KEY', 'default_secret_key')
        return jwt.encode(payload, secret_key, algorithm='HS256')

    def verify_access_token(self, token):
        """Vérifie la validité d'un token d'accès."""
        try:
            secret_key = os.environ.get('JWT_SECRET_KEY', 'default_secret_key')
            payload = jwt.decode(token, secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    def get_user_keys(self, user_id):
        """Récupère les clés d'un utilisateur."""
        keys_data = self._load_keys()
        return keys_data.get(user_id)

    def delete_user_keys(self, user_id):
        """Supprime les clés d'un utilisateur."""
        keys_data = self._load_keys()
        if user_id in keys_data:
            del keys_data[user_id]
            self._save_keys(keys_data)
            return True
        return False

# Exemple d'utilisation
if __name__ == "__main__":
    sec_manager = SecurityManager()
    
    # Génération de clés pour un utilisateur
    user_keys = sec_manager.generate_rsa_key_pair("user123")
    
    # Chiffrement de données
    data_to_encrypt = "Données personnelles sensibles"
    encrypted_data = sec_manager.encrypt_data(data_to_encrypt, user_keys['public_key'])
    
    # Déchiffrement de données
    decrypted_data = sec_manager.decrypt_data(encrypted_data, user_keys['private_key'])
    
    # Génération de token
    token = sec_manager.generate_access_token("user123")
    print(f"Token généré : {token}")
    
    # Vérification de token
    payload = sec_manager.verify_access_token(token)
    print(f"Payload du token : {payload}")
    
    # Récupération des clés
    retrieved_keys = sec_manager.get_user_keys("user123")
    print(f"Clés récupérées : {retrieved_keys}")
    
    # Suppression des clés
    sec_manager.delete_user_keys("user123")
