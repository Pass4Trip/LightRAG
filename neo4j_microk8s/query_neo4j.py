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

class Neo4jQuery:
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

    def execute_cypher_query(self, query, parameters=None):
        """
        Exécute une requête Cypher avec des paramètres optionnels
        
        Args:
            query (str): Requête Cypher à exécuter
            parameters (dict, optional): Paramètres de la requête
        
        Returns:
            list: Résultats de la requête
        """
        try:
            with self.driver.session() as session:
                result = session.run(query, parameters or {})
                return result
        except Exception as e:
            logger.error(f"Erreur lors de l'exécution de la requête Cypher : {e}")
            raise

    def close(self):
        """
        Ferme la connexion au driver Neo4j
        """
        if self.driver:
            self.driver.close()
            logger.info("Connexion Neo4j fermée.")

def main():
    graphQuery = Neo4jQuery()
    with graphQuery.driver.session() as session:
        result = session.run("MATCH (n) RETURN n LIMIT 2")
        # Convertir les résultats en liste pour pouvoir les parcourir plusieurs fois
        records = list(result)
        
        for record in records:
            # Récupérer les labels des nœuds
            node = record['n']
            labels = list(node.labels)
            print(f"Node Labels: {labels}")
            
            # Optionnel : afficher d'autres propriétés du nœud
            print(f"Node Properties: {dict(node)}")
            print("---")

if __name__ == "__main__":
    main()
