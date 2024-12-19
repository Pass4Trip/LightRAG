from pymilvus import MilvusClient, Collection
import os
from dotenv import load_dotenv
from neo4j import GraphDatabase
import numpy as np
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Charger les variables d'environnement
load_dotenv()

class Neo4jQueryExecutor:
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
                return [record.values()[0] for record in result]
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

# Paramètres de connexion Milvus
MILVUS_HOST = "localhost"
MILVUS_PORT = "19530"
MILVUS_DB_NAME = "lightrag"

def connect_milvus(host: str = MILVUS_HOST, 
                   port: str = MILVUS_PORT, 
                   db_name: str = MILVUS_DB_NAME):
    """
    Établit une connexion à Milvus.
    
    Args:
        host (str): Hôte Milvus
        port (str): Port Milvus
        db_name (str): Nom de la base de données
    
    Returns:
        bool: True si la connexion est réussie
    """
    try:
        from pymilvus import connections
        connections.connect(alias="default", host=host, port=port, db_name=db_name)
        return True
    except Exception as e:
        logger.error(f"Erreur de connexion à Milvus : {e}")
        return False

def get_user_preferences_nodes(neo4j_client, custom_id):
    """
    Récupère les IDs des nœuds de préférences utilisateur pour un utilisateur donné
    
    Args:
        neo4j_client (Neo4jQueryExecutor): Client Neo4j
        custom_id (str): ID personnalisé de l'utilisateur
    
    Returns:
        list: Liste des IDs de nœuds de préférences utilisateur
    """
    query = """
    MATCH (n {custom_id: $custom_id})-[r:LIKES]-(m)
    WHERE m.entity_type = 'user_preference'
    RETURN collect(m.entity_id) AS entity_ids
    """
    
    try:
        return neo4j_client.execute_cypher_query(query, {"custom_id": custom_id})[0]
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des préférences utilisateur : {e}")
        return []

def get_positive_points_nodes(neo4j_client):
    """
    Récupère les IDs des nœuds de type 'positive_point'
    
    Args:
        neo4j_client (Neo4jQueryExecutor): Client Neo4j
    
    Returns:
        list: Liste des IDs de nœuds de type 'positive_point'
    """
    query = """
    MATCH (m)
    WHERE m.entity_type = 'positive_point'
    RETURN collect(m.entity_id) AS entity_ids
    """
    
    try:
        return neo4j_client.execute_cypher_query(query)[0]
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des points positifs : {e}")
        return []

def compute_ann_correlations_with_filter(collection_name, node_ids, target_node_ids, top_k=5):
    """
    Calcule les corrélations ANN avec un filtrage sur les nœuds cibles
    
    Args:
        collection_name (str): Nom de la collection Milvus
        node_ids (list): Liste des IDs de nœuds sources
        target_node_ids (list): Liste des IDs de nœuds cibles
        top_k (int, optional): Nombre de corrélations à retourner. Défaut à 5.
    
    Returns:
        list: Liste des corrélations ANN filtrées
    """
    if not connect_milvus():
        return []
    
    try:
        from pymilvus import Collection, utility
        
        # Vérifier si la collection existe
        if collection_name not in utility.list_collections():
            logger.error(f"La collection '{collection_name}' n'existe pas.")
            logger.error(f"Collections disponibles : {utility.list_collections()}")
            return []
        
        # Charger la collection
        collection = Collection(collection_name)
        collection.load()
        
        # Préparer les résultats
        correlations = []
        
        # Pour chaque nœud source
        for source_node_id in node_ids:
            # Récupérer l'embedding du nœud source
            source_query_expr = f'id == "{source_node_id}"'
            source_results = collection.query(
                expr=source_query_expr, 
                output_fields=["id", "vector", "content"]
            )
            
            if not source_results:
                logger.warning(f"Aucun résultat trouvé pour le nœud source {source_node_id}")
                continue
            
            # Extraire l'embedding du nœud source
            source_embedding = source_results[0].get('vector')
            
            if source_embedding is None:
                logger.warning(f"Pas d'embedding trouvé pour le nœud {source_node_id}")
                continue
            
            # Recherche des voisins les plus proches
            search_params = {
                "metric_type": "COSINE",
                "params": {"nprobe": 10}
            }
            
            results = collection.search(
                data=[source_embedding],
                anns_field="vector",
                param=search_params,
                limit=top_k + 1,  # +1 pour exclure le nœud source lui-même
                output_fields=["id", "content"]
            )
            
            # Filtrer et formater les résultats
            source_correlations = []
            for result in results[0]:
                if (result.id not in [source_node_id] and 
                    result.id in target_node_ids):
                    source_correlations.append({
                        "correlated_node_id": result.id,
                        "distance": result.distance,
                        "content": result.entity.get('content')
                    })
                
                if len(source_correlations) == top_k:
                    break
            
            # Ajouter les corrélations si non vides
            if source_correlations:
                correlations.append({
                    "source_node_id": source_node_id,
                    "correlations": source_correlations
                })
        
        return correlations
    
    except Exception as e:
        logger.error(f"Erreur lors du calcul des corrélations ANN : {e}")
        return []

def main():
    """
    Exemple d'utilisation de la fonction de corrélation ANN avec filtrage.
    """
    # Initialiser le client Neo4j
    neo4j_client = Neo4jQueryExecutor()
    
    try:
        # Exemple avec un utilisateur spécifique
        custom_id = 'lea'
        
        # Récupérer les IDs des préférences utilisateur
        user_preference_node_ids = get_user_preferences_nodes(neo4j_client, custom_id)
        logger.info(f"IDs des préférences utilisateur : {user_preference_node_ids}")
        
        # Récupérer les IDs des points positifs
        positive_points_node_ids = get_positive_points_nodes(neo4j_client)
        logger.info(f"IDs des points positifs : {positive_points_node_ids}")
        
        # Calculer les corrélations ANN
        correlations = compute_ann_correlations_with_filter(
            collection_name="entities", 
            node_ids=user_preference_node_ids, 
            target_node_ids=positive_points_node_ids
        )
        
        # Afficher les résultats
        print("\nRésultats des corrélations :")
        for result in correlations:
            source_node_id = result['source_node_id']
            
            # Préparer la liste des nœuds corrélés
            cypher_node_list = [source_node_id] + [corr['correlated_node_id'] for corr in result['correlations']]
            
            # Générer la requête Cypher
            cypher_query = f"""
MATCH (n)
WHERE n.entity_id IN {cypher_node_list}
RETURN n
"""
            
            print(f"\nNœud source : {source_node_id}")
            print("Requête Cypher :")
            print(cypher_query)
            
            print("Corrélations :")
            for corr in result['correlations']:
                print(f"  - Nœud : {corr['correlated_node_id']}")
                print(f"    Distance : {corr['distance']}")
                print(f"    Contenu : {corr['content']}")
    
    except Exception as e:
        logger.error(f"Erreur lors de l'exécution : {e}")
    
    finally:
        # Fermer la connexion Neo4j
        neo4j_client.close()

if __name__ == "__main__":
    main()
