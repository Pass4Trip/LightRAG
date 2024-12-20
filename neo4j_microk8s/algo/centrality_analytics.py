import os
from dotenv import load_dotenv
from neo4j import GraphDatabase
import logging

# Définition de styles simples sans dépendance externe
class Style:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    GREEN = '\033[92m'
    CYAN = '\033[96m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'

def colored(text, color=None, attrs=None):
    """Simulation simple de colored sans dépendance externe"""
    color_map = {
        'green': Style.GREEN,
        'cyan': Style.CYAN,
        'yellow': Style.YELLOW,
        'red': Style.RED,
        'blue': Style.BLUE,
        'magenta': Style.MAGENTA
    }
    
    prefix = color_map.get(color, '')
    
    if attrs and 'bold' in attrs:
        prefix += Style.BOLD
    
    return f"{prefix}{text}{Style.RESET}"

# Configuration du logging
import logging
logging.getLogger('neo4j').setLevel(logging.ERROR)  # Masquer les avertissements Neo4j
logging.getLogger('urllib3').setLevel(logging.ERROR)  # Masquer les avertissements urllib3
logging.basicConfig(
    level=logging.ERROR,  # Niveau de log plus élevé
    format='%(message)s'  # Format de message minimal
)
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

def diagnostic_data_model(session, verbose=False):
    """
    Diagnostic du modèle de données Neo4j avec option de verbosité
    
    Args:
        session: Session Neo4j
        verbose: Booléen pour afficher ou non les détails complets
    """
    try:
        # Récupérer les labels existants
        labels_query = "CALL db.labels()"
        labels = [record['label'] for record in session.run(labels_query)]
        
        if verbose:
            print(colored("🔬 Diagnostic du Modèle de Données", 'cyan', attrs=['bold']))
            print("--------------------------------------------------")
            print(colored("Labels existants :", 'green'))
            for label in labels:
                print(colored(f"• {label}", 'yellow'))
        
        return labels
    except Exception as e:
        logger.error(f"Erreur lors du diagnostic du modèle de données : {e}")
        return []

def diagnostic_node_structure(session):
    print("\n" + colored("🔬 Diagnostic du Modèle de Données", "cyan", attrs=['bold']) + "\n" + "-"*50)
    
    # Diagnostic des labels existants
    label_query = """
    CALL db.labels() YIELD label
    RETURN label
    LIMIT 500
    """
    print(colored("🏷️ Labels existants :", "green"))
    labels = list(session.run(label_query))
    for label in labels:
        print(colored(f"• {label['label']}", "yellow"))
    
    # Diagnostic des types d'entités
    entity_type_query = """
    MATCH (n)
    WHERE n.entity_type IS NOT NULL
    WITH DISTINCT n.entity_type AS entity_types
    RETURN entity_types
    """
    print("\n" + colored("🔍 Types d'entités uniques :", "green"))
    entity_types = list(session.run(entity_type_query))
    for et in entity_types:
        print(colored(f"• {et['entity_types']}", "yellow"))
    
    # Diagnostic des propriétés
    property_query = """
    MATCH (n)
    UNWIND keys(n) AS prop
    WITH DISTINCT prop
    RETURN prop
    """
    print("\n" + colored("📋 Propriétés disponibles :", "green"))
    properties = list(session.run(property_query))
    for prop in properties:
        print(colored(f"• {prop['prop']}", "yellow"))

def extract_positive_points(session):
    """
    Extrait et analyse les points positifs à partir des descriptions des nœuds
    """
    query = """
    MATCH (n)
    WHERE 
        n.description IS NOT NULL AND 
        (
            n.description CONTAINS 'qualité' OR 
            n.description CONTAINS 'ambiance' OR 
            n.description CONTAINS 'service' OR 
            n.description CONTAINS 'accueil' OR 
            n.description CONTAINS 'délicieux'
        )
    WITH n, n.description AS description
    RETURN 
        description, 
        labels(n) AS node_labels,
        COUNT(DISTINCT n) AS occurrence_count,
        COLLECT(DISTINCT n.name)[0..5] AS sample_nodes
    ORDER BY occurrence_count DESC
    LIMIT 20
    """
    
    print("\n" + colored("🌟 Points Positifs Extraits", "green", attrs=['bold']) + "\n" + "-"*50)
    results = list(session.run(query))
    
    if not results:
        print(colored("❌ Aucun point positif trouvé.", "red"))
        return
    
    for i, record in enumerate(results, 1):
        print(colored(f"{i}. {record['description']}", "cyan"))
        print(colored(f"   • Présent dans {record['occurrence_count']} nœuds", "yellow"))
        print(colored(f"   • Labels des nœuds : {record['node_labels']}", "blue"))
        print(colored(f"   • Exemples de nœuds : {', '.join(record['sample_nodes'] or [])}\n", "blue"))

def analyze_positive_points_network(session):
    """
    Analyse le réseau des points positifs et leurs relations
    """
    query = """
    MATCH (n)
    WHERE 
        n.description IS NOT NULL AND 
        (
            n.description CONTAINS 'qualité' OR 
            n.description CONTAINS 'ambiance' OR 
            n.description CONTAINS 'service' OR 
            n.description CONTAINS 'accueil' OR 
            n.description CONTAINS 'délicieux'
        )
    WITH n, n.description AS description
    OPTIONAL MATCH (n)-[r]-(related)
    RETURN 
        description, 
        type(r) AS relation_type,
        labels(related) AS related_labels,
        COUNT(DISTINCT related) AS related_count,
        COLLECT(DISTINCT related.name)[0..5] AS sample_related_nodes
    ORDER BY related_count DESC
    LIMIT 20
    """
    
    print("\n" + colored("🔗 Réseau des Points Positifs", "green", attrs=['bold']) + "\n" + "-"*50)
    results = list(session.run(query))
    
    if not results:
        print(colored("❌ Aucune relation trouvée.", "red"))
        return
    
    for i, record in enumerate(results, 1):
        print(colored(f"{i}. Point Positif: {record['description']}", "cyan"))
        print(colored(f"   • Type de relation : {record['relation_type']}", "blue"))
        print(colored(f"   • Labels des nœuds liés : {record['related_labels']}", "blue"))
        print(colored(f"   • Nombre de nœuds liés : {record['related_count']}", "yellow"))
        print(colored(f"   • Exemples de nœuds liés : {', '.join(record['sample_related_nodes'] or [])}\n", "blue"))

def calculate_point_centrality(session):
    """
    Calcule la centralité des points positifs avec une analyse plus approfondie
    """
    query = """
    MATCH (n)
    WHERE 
        n.description IS NOT NULL AND 
        (
            n.description CONTAINS 'qualité' OR 
            n.description CONTAINS 'service' OR 
            n.description CONTAINS 'ambiance' OR
            n.description CONTAINS 'accueil' OR
            n.description CONTAINS 'délicieux'
        )
    
    WITH n, n.description AS description
    
    OPTIONAL MATCH (n)-[r]-(related_node)
    WHERE related_node.name IS NOT NULL
    
    WITH 
        description, 
        COUNT(DISTINCT related_node) AS connection_count,
        COLLECT(DISTINCT related_node.name)[0..10] AS sample_nodes,
        COLLECT(DISTINCT labels(related_node)) AS node_labels
    
    RETURN 
        description, 
        connection_count,
        sample_nodes,
        node_labels
    ORDER BY connection_count DESC
    LIMIT 20
    """
    
    print("\n" + colored("🌐 Points Positifs Centraux", "green", attrs=['bold']) + "\n" + "-"*50)
    results = list(session.run(query))
    
    if not results:
        print(colored("❌ Aucun point central trouvé.", "red"))
        return
    
    for i, record in enumerate(results, 1):
        print(colored(f"{i}. Description: {record['description']}", "cyan"))
        print(colored(f"   • Connecté à {record['connection_count']} nœuds", "yellow"))
        print(colored(f"   • Nœuds exemples : {', '.join(record['sample_nodes'])}", "blue"))
        print(colored(f"   • Labels des nœuds : {record['node_labels']}\n", "magenta"))

def main():
    graphQuery = Neo4jQuery()
    
    try:
        with graphQuery.driver.session() as session:
            # Diagnostics préalables
            diagnostic_data_model(session, verbose=False)
            diagnostic_node_structure(session)
            
            # Analyse de centralité des points positifs
            calculate_point_centrality(session)
    
    except Exception as e:
        print(colored(f"❌ Erreur lors de l'analyse : {e}", "red"))
    
    finally:
        graphQuery.close()

if __name__ == "__main__":
    main()
