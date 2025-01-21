import os
from dotenv import load_dotenv
from neo4j import GraphDatabase
import logging
import socket
import subprocess

# Configuration du logging
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Charger les variables d'environnement
load_dotenv()

def get_neo4j_credentials():
    """
    Récupère les credentials Neo4j depuis le secret Kubernetes
    
    Returns:
        tuple: (username, password)
    """
    try:
        # Commande pour récupérer le secret NEO4J_AUTH
        cmd = "microk8s kubectl get secret p4t-neo4j-auth -o jsonpath='{.data.NEO4J_AUTH}' | base64 -d"
        
        # Exécuter la commande via SSH
        result = subprocess.run(f"ssh vps-ovh '{cmd}'", 
                                shell=True, 
                                capture_output=True, 
                                text=True, 
                                check=True)
        
        # Diviser le résultat en username et password
        credentials = result.stdout.strip().split('/')
        
        if len(credentials) != 2:
            logger.error("Format des credentials incorrect")
            return None, None
        
        return credentials[0], credentials[1]
    
    except subprocess.CalledProcessError as e:
        logger.error(f"Erreur lors de la récupération des credentials : {e}")
        return None, None
    except Exception as e:
        logger.error(f"Erreur inattendue : {e}")
        return None, None

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
        # Configuration par défaut pour le serveur VPS
        # Utiliser l'URI NodePort externe pour la connexion depuis l'extérieur du cluster
        default_uri = 'bolt://vps-af24e24d.vps.ovh.net:32045'
        
        # Récupérer les credentials du secret si non fournis
        if not (username and password):
            k8s_username, k8s_password = get_neo4j_credentials()
            username = username or k8s_username
            password = password or k8s_password
        
        # Priorité : paramètres passés > variables d'environnement > secret K8s > configuration par défaut
        self.uri = uri or os.getenv('NEO4J_URI', default_uri)
        self.username = username or os.getenv('NEO4J_USERNAME', 'neo4j')
        self.password = password or os.getenv('NEO4J_PASSWORD', 'my-initial-password')
        
        logger.debug(f"Configuration de connexion : URI={self.uri}, Username={self.username}")
        
        # Vérification des informations de connexion
        if not all([self.uri, self.username, self.password]):
            logger.error("Informations de connexion Neo4j incomplètes")
            raise ValueError("Informations de connexion Neo4j manquantes.")
        
        # Test de connexion socket avant la connexion Neo4j
        try:
            parsed_uri = self.uri.replace('bolt://', '').split(':')
            hostname = parsed_uri[0]
            port = int(parsed_uri[1]) if len(parsed_uri) > 1 else 32045  # Forcer le port NodePort
            
            logger.debug(f"Test de connexion socket : {hostname}:{port}")
            with socket.create_connection((hostname, port), timeout=5) as sock:
                logger.info(f"Connexion socket réussie à {hostname}:{port}")
        except Exception as socket_err:
            logger.error(f"Erreur de connexion socket : {socket_err}")
            raise
        
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.username, self.password))
            logger.info(f"Connexion à Neo4j établie : {self.uri}")
            
            # Test de requête
            with self.driver.session() as session:
                result = session.run("RETURN 1 AS test")
                test_value = result.single()['test']
                logger.info(f"Test de requête réussi. Valeur retournée : {test_value}")
        
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
                result = session.run("MATCH (n) DETACH DELETE n")
                deleted_nodes = result.consume().counters.nodes_deleted
                deleted_relationships = result.consume().counters.relationships_deleted
                
                logger.warning(f"🗑️ Base de données Neo4j vidée : {deleted_nodes} nœuds et {deleted_relationships} relations supprimés.")
        except Exception as e:
            logger.error(f"❌ Erreur lors de la suppression des données Neo4j : {e}")
            raise
        finally:
            self.driver.close()

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
                return [record.values()[0] for record in result]
        except Exception as e:
            logger.error(f"Erreur lors de l'exécution de la requête Cypher : {e}")
            raise

def main():
    try:
        cleaner = Neo4jCleaner()
        cleaner.clear_database()
    except Exception as e:
        logger.error(f"Erreur fatale : {e}")
        raise

if __name__ == "__main__":
    main()
