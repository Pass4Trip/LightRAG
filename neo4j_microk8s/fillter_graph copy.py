import logging
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv
import json

# Configuration du logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Charger les variables d'environnement
load_dotenv()

class Neo4jGraphFilter:
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

    def filter_nodes(self, node_ids):
        """
        Filtre les nœuds du graphe Neo4j en utilisant custom_id
        
        Args:
            node_ids (List[str]): Liste des custom_id de nœuds à filtrer
        
        Returns:
            list: Liste des nœuds et relations filtrés
        """
        with self.driver.session() as session:
            query = """
            // Trouver les nœuds par leur custom_id
            MATCH (n)
            WHERE n.custom_id IN $node_ids
            
            // Récupérer les nœuds et leurs relations
            MATCH (n)-[r]-(connected)
            RETURN 
                n AS source_node, 
                r AS relationship, 
                connected AS target_node,
                labels(n) AS source_labels,
                labels(connected) AS target_labels,
                properties(n) AS source_properties,
                properties(r) AS relationship_properties,
                properties(connected) AS target_properties
            """
            
            try:
                # Créer la requête finale avec les identifiants
                final_query = query.replace("$node_ids", str(node_ids))
                logger.info("Requête Cypher finale :\n" + final_query)
                
                logger.debug(f"Filtrage des nœuds avec custom_id : {node_ids}")
                
                result = session.run(query, {"node_ids": node_ids})
                
                # Collecter les résultats
                filtered_results = []
                for record in result:
                    filtered_results.append({
                        'source_node': {
                            'node': dict(record['source_node']),
                            'labels': record['source_labels'],
                            'properties': record['source_properties']
                        },
                        'relationship': {
                            'relation': dict(record['relationship']),
                            'properties': record['relationship_properties']
                        },
                        'target_node': {
                            'node': dict(record['target_node']),
                            'labels': record['target_labels'],
                            'properties': record['target_properties']
                        }
                    })
                
                logger.info(f"Filtrage réussi : {len(filtered_results)} résultats trouvés")
                
                return filtered_results
            
            except Exception as e:
                logger.error(f"Erreur lors du filtrage du graphe Neo4j : {e}")
                raise

def save_filtered_results_to_json(filtered_results):
    """
    Sauvegarde les résultats filtrés dans un fichier JSON.
    
    Args:
        filtered_results (list): Liste des résultats filtrés
    
    Returns:
        str: Chemin du fichier JSON sauvegardé
    """
    # Créer le dossier de sauvegarde s'il n'existe pas
    save_dir = os.path.join(os.path.dirname(__file__), 'filtered_results')
    os.makedirs(save_dir, exist_ok=True)
    
    # Générer un nom de fichier unique basé sur la date et l'heure
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"filtered_results_{timestamp}.json"
    filepath = os.path.join(save_dir, filename)
    
    # Sauvegarder les résultats
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(filtered_results, f, indent=2, ensure_ascii=False)
    
    logger.info(f" Résultats sauvegardés dans : {filepath}")
    return filepath

def main():
    # Exemples d'identifiants à filtrer
    test_node_ids = [
        "13294163500777077759",  # Nom de nœud
        "lea",  # Nom de nœud
    ]
    
    try:
        # Initialiser le filtre
        graph_filter = Neo4jGraphFilter()
        
        # Filtrer les nœuds
        filtered_results = graph_filter.filter_nodes(test_node_ids)
        
        # Afficher les informations de base
        logger.info(f"Type du Resultat du filtrage: {type(filtered_results)}")
        logger.debug(f"Resultats du filtrage: {filtered_results}")
        
        # Sauvegarder dans un fichier JSON
        json_filepath = save_filtered_results_to_json(filtered_results)
        
    except Exception as e:
        logger.error(f"Erreur lors du filtrage : {e}")
    finally:
        # Fermer le driver Neo4j
        graph_filter.driver.close()

if __name__ == "__main__":
    main()