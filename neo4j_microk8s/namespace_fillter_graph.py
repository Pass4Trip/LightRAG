import logging
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

# Configuration du logging avancé
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [DynamicSubGraph] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('dynamic_subgraph_processing.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

load_dotenv()

class DynamicSubGraphStreamProcessor:
    def __init__(self, uri=None, username=None, password=None):
        """
        Initialise un processeur de sous-graphes dynamiques pour streaming
        
        Args:
            uri (str, optional): URI de la base de données Neo4j
            username (str, optional): Nom d'utilisateur Neo4j
            password (str, optional): Mot de passe Neo4j
        """
        self.uri = uri or os.getenv('NEO4J_URI')
        self.username = username or os.getenv('NEO4J_USERNAME')
        self.password = password or os.getenv('NEO4J_PASSWORD')
        
        if not all([self.uri, self.username, self.password]):
            raise ValueError("Informations de connexion Neo4j manquantes.")
        
        self.driver = GraphDatabase.driver(self.uri, auth=(self.username, self.password))
        logger.info(f"Connexion à Neo4j établie : {self.uri}")
    
    def create_stream_subgraph(self, stream_id: Optional[str] = None, ttl: int = 3600) -> str:
        """
        Crée un nouveau sous-graphe dynamique avec une durée de vie configurable
        
        Args:
            stream_id (str, optional): Identifiant unique du flux. Généré si non fourni.
            ttl (int, optional): Durée de vie du sous-graphe en secondes. Défaut: 1 heure
        
        Returns:
            str: Identifiant du sous-graphe créé
        """
        stream_id = stream_id or str(uuid.uuid4())
        expires_at = datetime.now() + timedelta(seconds=ttl)
        
        with self.driver.session() as session:
            query = """
            CREATE (sg:StreamSubGraph {
                stream_id: $stream_id, 
                created_at: $created_at,
                expires_at: $expires_at
            })
            RETURN sg.stream_id AS stream_id
            """
            
            try:
                result = session.run(query, {
                    "stream_id": stream_id,
                    "created_at": datetime.now().isoformat(),
                    "expires_at": expires_at.isoformat()
                })
                
                logger.info(f"Sous-graphe de streaming créé : {stream_id}")
                logger.info(f"Expire le : {expires_at}")
                
                return stream_id
            
            except Exception as e:
                logger.error(f"Erreur lors de la création du sous-graphe : {e}")
                raise
    
    def add_node_to_subgraph(self, stream_id: str, node_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ajoute un nœud à un sous-graphe de streaming
        
        Args:
            stream_id (str): Identifiant du sous-graphe
            node_data (dict): Données du nœud à ajouter
        
        Returns:
            dict: Nœud ajouté avec ses propriétés
        """
        with self.driver.session() as session:
            query = """
            MATCH (sg:StreamSubGraph {stream_id: $stream_id})
            CREATE (n:StreamNode:DynamicNode {
                node_id: $node_id,
                stream_id: $stream_id,
                added_at: $added_at
            })
            SET n += $node_properties
            CREATE (sg)-[:CONTAINS_NODE]->(n)
            RETURN properties(n) AS node_properties
            """
            
            try:
                node_id = node_data.get('node_id') or str(uuid.uuid4())
                node_properties = {
                    k: v for k, v in node_data.items() 
                    if k not in ['node_id', 'stream_id']
                }
                
                result = session.run(query, {
                    "stream_id": stream_id,
                    "node_id": node_id,
                    "added_at": datetime.now().isoformat(),
                    "node_properties": node_properties
                })
                
                record = result.single()
                logger.info(f"Nœud ajouté au sous-graphe {stream_id} : {node_id}")
                
                return dict(record['node_properties'])
            
            except Exception as e:
                logger.error(f"Erreur lors de l'ajout du nœud : {e}")
                raise
    
    def add_edge_to_subgraph(self, stream_id: str, source_node_id: str, target_node_id: str, edge_type: str, **properties) -> Dict[str, Any]:
        """
        Ajoute une relation entre deux nœuds dans un sous-graphe de streaming
        
        Args:
            stream_id (str): Identifiant du sous-graphe
            source_node_id (str): Identifiant du nœud source
            target_node_id (str): Identifiant du nœud cible
            edge_type (str): Type de relation
            **properties: Propriétés supplémentaires de la relation
        
        Returns:
            dict: Relation ajoutée avec ses propriétés
        """
        with self.driver.session() as session:
            query = """
            MATCH (source:StreamNode {node_id: $source_node_id, stream_id: $stream_id}),
                  (target:StreamNode {node_id: $target_node_id, stream_id: $stream_id})
            CREATE (source)-[r:STREAM_RELATION {
                type: $edge_type,
                stream_id: $stream_id,
                added_at: $added_at
            }]->(target)
            SET r += $edge_properties
            RETURN properties(r) AS edge_properties
            """
            
            try:
                result = session.run(query, {
                    "stream_id": stream_id,
                    "source_node_id": source_node_id,
                    "target_node_id": target_node_id,
                    "edge_type": edge_type,
                    "added_at": datetime.now().isoformat(),
                    "edge_properties": properties
                })
                
                record = result.single()
                logger.info(f"Relation ajoutée au sous-graphe {stream_id} : {source_node_id} -> {target_node_id}")
                
                return dict(record['edge_properties'])
            
            except Exception as e:
                logger.error(f"Erreur lors de l'ajout de la relation : {e}")
                raise
    
    def query_subgraph(self, stream_id: str, query_params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Interroge un sous-graphe de streaming
        
        Args:
            stream_id (str): Identifiant du sous-graphe
            query_params (dict, optional): Paramètres de requête optionnels
        
        Returns:
            list: Résultats de la requête
        """
        with self.driver.session() as session:
            query = """
            MATCH (sg:StreamSubGraph {stream_id: $stream_id})
            OPTIONAL MATCH (sg)-[:CONTAINS_NODE]->(n:StreamNode)
            OPTIONAL MATCH (n)-[r:STREAM_RELATION]->(target:StreamNode)
            RETURN 
                properties(n) AS node_properties, 
                labels(n) AS node_labels,
                properties(r) AS relation_properties,
                properties(target) AS target_node_properties
            """
            
            try:
                result = session.run(query, {"stream_id": stream_id})
                
                query_results = []
                for record in result:
                    query_results.append({
                        'node': dict(record['node_properties']),
                        'node_labels': list(record['node_labels']),
                        'relation': dict(record['relation_properties']) if record['relation_properties'] else None,
                        'target_node': dict(record['target_node_properties']) if record['target_node_properties'] else None
                    })
                
                logger.info(f"Requête sur le sous-graphe {stream_id} : {len(query_results)} résultats")
                return query_results
            
            except Exception as e:
                logger.error(f"Erreur lors de la requête du sous-graphe : {e}")
                raise
    
    def get_extended_subgraph(self, stream_id: str, max_depth: int = 3) -> List[Dict[str, Any]]:
        """
        Récupère un sous-graphe étendu à partir d'un sous-graphe de streaming
        
        Args:
            stream_id (str): Identifiant du sous-graphe
            max_depth (int, optional): Profondeur maximale de exploration. Défaut: 3
        
        Returns:
            list: Résultats du sous-graphe étendu
        """
        with self.driver.session() as session:
            query = """
            // Trouver tous les nœuds du sous-graphe de streaming
            MATCH (sg:StreamSubGraph {stream_id: $stream_id})
            MATCH (sg)-[:CONTAINS_NODE]->(startNode:StreamNode)

            // Étendre la recherche à tous les nœuds connectés
            MATCH path = (startNode)-[*0..3]-(connectedNode)
            WHERE connectedNode:StreamNode OR NOT connectedNode:StreamSubGraph

            RETURN 
                DISTINCT connectedNode AS node,
                labels(connectedNode) AS node_labels,
                properties(connectedNode) AS node_properties,
                relationships(path) AS relationships,
                [r in relationships(path) | type(r)] AS relationship_types,
                [r in relationships(path) | properties(r)] AS relationship_properties
            """
            
            try:
                result = session.run(query, {
                    "stream_id": stream_id
                })
                
                extended_subgraph = []
                for record in result:
                    extended_subgraph.append({
                        'node': dict(record['node']),
                        'node_labels': list(record['node_labels']),
                        'node_properties': dict(record['node_properties']),
                        'relationships': [dict(rel) for rel in record['relationships']],
                        'relationship_types': list(record['relationship_types']),
                        'relationship_properties': [dict(props) for props in record['relationship_properties']]
                    })
                
                logger.info(f"Sous-graphe étendu pour {stream_id} : {len(extended_subgraph)} nœuds")
                return extended_subgraph
            
            except Exception as e:
                logger.error(f"Erreur lors de la récupération du sous-graphe étendu : {e}")
                raise
    
    def cleanup_expired_subgraphs(self):
        """
        Nettoie les sous-graphes expirés
        """
        with self.driver.session() as session:
            query = """
            MATCH (sg:StreamSubGraph)
            WHERE datetime(sg.expires_at) < datetime()
            OPTIONAL MATCH (sg)-[:CONTAINS_NODE]->(n:StreamNode)
            OPTIONAL MATCH (n)-[r:STREAM_RELATION]->()
            DETACH DELETE r, n, sg
            """
            
            try:
                result = session.run(query)
                deleted_count = result.consume().counters.nodes_deleted
                logger.info(f"Nettoyage des sous-graphes expirés : {deleted_count} nœuds supprimés")
            
            except Exception as e:
                logger.error(f"Erreur lors du nettoyage des sous-graphes : {e}")
                raise
    
    def close(self):
        """
        Ferme la connexion au driver Neo4j
        """
        if self.driver:
            self.driver.close()
            logger.info("Connexion Neo4j fermée")

def main():
    processor = DynamicSubGraphStreamProcessor()
    
    try:
        # Créer un sous-graphe de streaming
        stream_id = processor.create_stream_subgraph(ttl=3600)  # 1 heure
        
        # Ajouter des nœuds
        node1 = processor.add_node_to_subgraph(stream_id, {
            'node_id': 'user_lea', 
            'entity_type': 'user', 
            'name': 'Lea'
        })
        
        node2 = processor.add_node_to_subgraph(stream_id, {
            'node_id': 'restaurant_lyon', 
            'entity_type': 'activity', 
            'name': 'Restaurant Les Adrets'
        })
        
        # Ajouter une relation
        relation = processor.add_edge_to_subgraph(
            stream_id, 
            'user_lea', 
            'restaurant_lyon', 
            'RECOMMENDS',
            rating=4.5
        )
        
        # Récupérer le sous-graphe étendu
        extended_subgraph = processor.get_extended_subgraph(stream_id)
        logger.info("Sous-graphe étendu :")
        for item in extended_subgraph:
            logger.info(item)
        
        # Interroger le sous-graphe
        results = processor.query_subgraph(stream_id)
        logger.info("Résultats de la requête :")
        for result in results:
            logger.info(result)
        
        # Nettoyer les sous-graphes expirés
        processor.cleanup_expired_subgraphs()
    
    except Exception as e:
        logger.error(f"Erreur lors du traitement du flux : {e}")
    
    finally:
        processor.close()

if __name__ == "__main__":
    main()