import sys
import os
import logging
from typing import List, Dict
from neo4j import GraphDatabase

# Ajouter le chemin parent pour importer lightrag
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)

# Configuration globale par défaut
DEFAULT_GLOBAL_CONFIG = {
    "working_dir": os.path.dirname(__file__),
    "addon_params": {},
    "embedding_model": "text-embedding-ada-002",  # Exemple de modèle d'embedding
    "embedding_batch_num": 64,  # Ajout de la clé manquante
    "embedding_dim": 1536  # Dimension de l'embedding
}

class UserDuplicateFinder:
    def __init__(
        self, 
        uri: str = None, 
        username: str = None, 
        password: str = None
    ):
        """
        Initialise une connexion directe à Neo4j
        
        :param uri: URI de la base de données Neo4j
        :param username: Nom d'utilisateur pour la connexion
        :param password: Mot de passe pour la connexion
        """
        # Utiliser les variables d'environnement si non spécifiées
        self.uri = uri or os.getenv('NEO4J_URI', 'bolt://localhost:7687')
        self.username = username or os.getenv('NEO4J_USERNAME')
        self.password = password or os.getenv('NEO4J_PASSWORD')

        # Déboguer les informations de connexion
        logging.info(f"Tentative de connexion à Neo4j:")
        logging.info(f"URI: {self.uri}")
        logging.info(f"Nom d'utilisateur: {self.username}")
        logging.info(f"Mot de passe: {'*' * len(self.password) if self.password else 'Non défini'}")

        # Créer une connexion directe avec le driver Neo4j
        try:
            self.driver = GraphDatabase.driver(
                self.uri, 
                auth=(self.username, self.password)
            )
        except Exception as e:
            logging.error(f"Erreur de connexion à Neo4j : {e}")
            raise

    def find_duplicate_users_by_custom_id(self) -> List[Dict]:
        """
        Trouve les utilisateurs en double basés sur leur custom_id
        
        :return: Liste des doublons d'utilisateurs
        """
        try:
            # Requête Cypher pour trouver les doublons
            query = """
            MATCH (u)
            WHERE u.custom_id IS NOT NULL
            WITH u.custom_id AS custom_id, COLLECT(u) AS users
            WHERE SIZE(users) > 1
            RETURN custom_id, 
                   [user IN users | {
                       id: id(user), 
                       labels: labels(user), 
                       properties: properties(user)
                   }] AS duplicate_users
            """
            
            # Exécuter la requête de manière synchrone
            with self.driver.session() as session:
                result = session.run(query)
                duplicates = [record.data() for record in result]
            
            # Traiter et afficher les résultats
            if duplicates:
                logging.info("Doublons trouvés :")
                for duplicate in duplicates:
                    logging.info(f"Custom ID: {duplicate['custom_id']}")
                    for user in duplicate['duplicate_users']:
                        logging.info(f"  - Labels: {user['labels']}")
                        logging.info(f"    Propriétés: {user['properties']}")
            else:
                logging.info("Aucun doublon trouvé.")
            
            return duplicates
        
        except Exception as e:
            logging.error(f"Erreur lors de la recherche de doublons : {e}")
            return []

    def close(self):
        """
        Ferme la connexion au driver Neo4j
        """
        if self.driver:
            self.driver.close()

def main():
    finder = None
    try:
        # Initialisation de la connexion
        finder = UserDuplicateFinder()
        
        # Trouver les doublons par custom_id
        duplicates = finder.find_duplicate_users_by_custom_id()
        
    except Exception as e:
        logging.error(f"Erreur lors de la recherche de doublons : {e}")
    finally:
        if finder:
            finder.close()

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()
