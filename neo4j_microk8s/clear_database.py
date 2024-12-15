import os
from dotenv import load_dotenv
from neo4j import GraphDatabase
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Charger les variables d'environnement
load_dotenv()

class Neo4jCleaner:
    def __init__(self, uri=None, username=None, password=None):
        """
        Initialise la connexion à Neo4j
        
        Args:
            uri (str, optional): URI de la base de données Neo4j. 
                                 Par défaut, utilise la variable d'environnement NEO4J_URI.
            username (str, optional): Nom d'utilisateur. 
                                      Par défaut, utilise NEO4J_USERNAME.
            password (str, optional): Mot de passe. 
                                      Par défaut, utilise NEO4J_PASSWORD.
        """
        self.uri = uri or os.getenv('NEO4J_URI')
        self.username = username or os.getenv('NEO4J_USERNAME')
        self.password = password or os.getenv('NEO4J_PASSWORD')
        
        if not all([self.uri, self.username, self.password]):
            raise ValueError("Informations de connexion Neo4j manquantes. Vérifiez vos variables d'environnement.")
        
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.username, self.password))
            logger.info(f"Connexion à Neo4j établie : {self.uri}")
        except Exception as e:
            logger.error(f"Erreur de connexion à Neo4j : {e}")
            raise

    def clear_database(self):
        """
        Supprime tous les nœuds et relations de la base de données Neo4j
        sans demander de confirmation
        """
        try:
            logger.info(f"🔥 Nettoyage de la base de données Neo4j en cours... : {self.uri}")
            with self.driver.session() as session:
                # Suppression de tous les nœuds et relations
                session.run("MATCH (n) DETACH DELETE n")
                logger.warning("🗑️ Base de données Neo4j complètement vidée.")
        except Exception as e:
            logger.error(f"❌ Erreur lors de la suppression des données Neo4j : {e}")
        finally:
            self.driver.close()

def main():
    cleaner = Neo4jCleaner()
    cleaner.clear_database()

if __name__ == "__main__":
    main()
