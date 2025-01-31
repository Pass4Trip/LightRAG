import os
import sys

# Ajouter le répertoire du projet au PYTHONPATH
project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_dir)

import asyncio
import logging
from typing import Dict, Any

from neo4j import AsyncGraphDatabase
from neo4j.exceptions import Neo4jError

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename=os.path.join(os.path.dirname(__file__), 'graph_integrity.log')
)
logger = logging.getLogger(__name__)

class Neo4jGraphIntegrity:
    def __init__(
        self, 
        uri: str = None, 
        username: str = None, 
        password: str = None
    ):
        """
        Initialise la connexion à Neo4j pour la vérification d'intégrité.
        
        Args:
            uri (str, optional): URI de connexion. Par défaut, utilise la variable d'environnement.
            username (str, optional): Nom d'utilisateur. Par défaut, utilise la variable d'environnement.
            password (str, optional): Mot de passe. Par défaut, utilise la variable d'environnement.
        """
        self.uri = uri or os.environ.get("NEO4J_URI")
        self.username = username or os.environ.get("NEO4J_USERNAME")
        self.password = password or os.environ.get("NEO4J_PASSWORD")
        
        self._driver = None
    
    async def connect(self):
        """Établit la connexion avec Neo4j."""
        if not self._driver:
            try:
                self._driver = AsyncGraphDatabase.driver(
                    self.uri, 
                    auth=(self.username, self.password)
                )
                logger.info("Connexion à Neo4j établie avec succès")
            except Exception as e:
                logger.error(f"Erreur de connexion à Neo4j : {e}")
                raise
    
    async def close(self):
        """Ferme la connexion avec Neo4j."""
        if self._driver:
            await self._driver.close()
            logger.info("Connexion à Neo4j fermée")
    
    async def validate_graph_integrity(self, repair: bool = False, debug: bool = False) -> Dict[str, Any]:
        """
        Valide et répare potentiellement l'intégrité du graphe Neo4j.
        
        Args:
            repair (bool): Si True, tente de réparer les problèmes détectés
            debug (bool): Si True, affiche des informations détaillées sur chaque nœud et edge
        
        Returns:
            Dict[str, Any]: Statistiques de validation et réparation
        """
        stats = {
            "total_nodes_checked": 0,
            "total_edges_checked": 0,
            "invalid_nodes": 0,
            "invalid_edges": 0,
            "repaired_nodes": 0,
            "repaired_edges": 0,
            "deleted_nodes": 0,
            "deleted_edges": 0
        }
        
        async with self._driver.session() as session:
            try:
                # Vérification des nœuds
                nodes_query = """
                MATCH (n)
                RETURN 
                    labels(n) as node_labels, 
                    properties(n) as node_properties,
                    elementId(n) as node_id,
                    n.custom_id as custom_id
                """
                logger.info(f"Requête de vérification des nœuds : {nodes_query}")
                nodes_result = await session.run(nodes_query)
                nodes = await nodes_result.data()
                logger.info(f"Nombre de nœuds trouvés : {len(nodes)}")
                
                for node in nodes:
                    stats["total_nodes_checked"] += 1
                    
                    # Critères de validation des nœuds
                    is_node_valid = all([
                        node.get('node_labels') is not None,
                        node.get('node_properties') is not None,
                        node.get('custom_id') is not None
                    ])
                    
                    if debug:
                        logger.info(f"Détails du nœud : {node}")
                    
                    if not is_node_valid:
                        logger.warning(f"Nœud invalide détecté : {node}")
                        stats["invalid_nodes"] += 1
                        
                        if repair:
                            # Réparation ou suppression des nœuds invalides
                            repair_node_query = """
                            MATCH (n)
                            WHERE elementId(n) = $node_id
                            SET n.validation_status = 'repaired'
                            SET n.custom_id = coalesce(n.custom_id, $node_id)
                            RETURN n
                            """
                            
                            try:
                                await session.run(
                                    repair_node_query, 
                                    {
                                        "node_id": node['node_id'], 
                                        "custom_id": node.get('custom_id') or node['node_id']
                                    }
                                )
                                stats["repaired_nodes"] += 1
                            except Exception as e:
                                logger.warning(f"Impossible de réparer le nœud {node['node_id']}: {e}")
                                
                                # Suppression du nœud si réparation impossible
                                delete_node_query = """
                                MATCH (n)
                                WHERE elementId(n) = $node_id
                                DETACH DELETE n
                                """
                                await session.run(
                                    delete_node_query, 
                                    {"node_id": node['node_id']}
                                )
                                stats["deleted_nodes"] += 1
            
                # Vérification des edges
                edges_query = """
                MATCH (start)-[r]->(end)
                RETURN 
                    type(r) as relation_type, 
                    properties(r) as edge_properties,
                    elementId(start) as start_id,
                    elementId(end) as end_id,
                    elementId(r) as edge_id,
                    start.custom_id as start_custom_id,
                    end.custom_id as end_custom_id
                """
                logger.info(f"Requête de vérification des edges : {edges_query}")
                edges_result = await session.run(edges_query)
                edges = await edges_result.data()
                logger.info(f"Nombre d'edges trouvés : {len(edges)}")
                
                for edge in edges:
                    stats["total_edges_checked"] += 1
                    
                    # Critères de validation des edges
                    is_edge_valid = all([
                        edge.get('relation_type') is not None,
                        edge.get('edge_properties') is not None,
                        edge.get('start_custom_id') is not None,
                        edge.get('end_custom_id') is not None
                    ])
                    
                    if debug:
                        logger.info(f"Détails de l'edge : {edge}")
                    
                    if not is_edge_valid:
                        logger.warning(f"Edge invalide détecté : {edge}")
                        stats["invalid_edges"] += 1
                        
                        if repair:
                            # Réparation ou suppression des edges invalides
                            repair_edge_query = """
                            MATCH ()-[r]->()
                            WHERE elementId(r) = $edge_id
                            SET r.weight = coalesce(r.weight, 1.0)
                            SET r.description = coalesce(r.description, 'Relation non spécifiée')
                            RETURN r
                            """
                            
                            try:
                                await session.run(
                                    repair_edge_query, 
                                    {"edge_id": edge['edge_id']}
                                )
                                stats["repaired_edges"] += 1
                            except Exception as e:
                                logger.warning(f"Impossible de réparer l'edge {edge['edge_id']}: {e}")
                                
                                # Suppression de l'edge si réparation impossible
                                delete_edge_query = """
                                MATCH ()-[r]->()
                                WHERE elementId(r) = $edge_id
                                DELETE r
                                """
                                await session.run(
                                    delete_edge_query, 
                                    {"edge_id": edge['edge_id']}
                                )
                                stats["deleted_edges"] += 1
                
                logger.info(f"Résultats de la validation du graphe : {stats}")
                return stats
        
            except Neo4jError as e:
                logger.error(f"Erreur Neo4j lors de la validation : {e}")
                raise
            except Exception as e:
                logger.error(f"Erreur inattendue lors de la validation : {e}")
                raise

async def main():
    """Point d'entrée principal pour l'exécution du script."""
    graph_integrity = Neo4jGraphIntegrity()
    
    try:
        await graph_integrity.connect()
        
        # Validation sans réparation
        validation_stats = await graph_integrity.validate_graph_integrity(repair=False, debug=True)
        logger.info(f"Statistiques de validation : {validation_stats}")
        
        # Si des problèmes sont détectés, lancer la réparation
        if (validation_stats['invalid_nodes'] > 0 or 
            validation_stats['invalid_edges'] > 0):
            logger.warning("Problèmes d'intégrité détectés. Lancement de la réparation.")
            repair_stats = await graph_integrity.validate_graph_integrity(repair=True, debug=True)
            logger.info(f"Statistiques de réparation : {repair_stats}")
    
    except Exception as e:
        logger.error(f"Erreur lors de la vérification d'intégrité : {e}")
    
    finally:
        await graph_integrity.close()

if __name__ == "__main__":
    asyncio.run(main())
