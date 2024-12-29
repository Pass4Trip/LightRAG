import logging
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv
import time
import csv
import pandas as pd
import uuid
import re
from typing import List, Dict, Any, Optional

# Configuration du logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Charger les variables d'environnement
load_dotenv()

class Neo4jGraphFilter:
    def __init__(self, uri=None, username=None, password=None, namespace=None):
        """
        Initialise la connexion à Neo4j
        
        Args:
            uri (str, optional): URI de connexion à Neo4j. 
            username (str, optional): Nom d'utilisateur. 
            password (str, optional): Mot de passe. 
            namespace (str, optional): Namespace du sous-graphe. 
        """
        self.uri = uri or os.getenv('NEO4J_URI')
        self.username = username or os.getenv('NEO4J_USERNAME')
        self.password = password or os.getenv('NEO4J_PASSWORD')
        self.namespace = namespace or f"graph_{int(time.time())}"
        
        if not all([self.uri, self.username, self.password]):
            raise ValueError("Informations de connexion Neo4j manquantes.")
        
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.username, self.password))
            logger.info(f"Connexion à Neo4j établie : {self.uri}")
        
        except Exception as e:
            logger.error(f"Erreur de connexion à Neo4j : {e}")
            raise

    def create_indexes(self, attributes: List[str]):
        """
        Crée des index sur les attributs spécifiés
        
        Args:
            attributes (List[str]): Liste des attributs à indexer
        """
        # Désactivé temporairement en raison de problèmes de compatibilité
        logger.warning("La création d'index est temporairement désactivée")

    def create_sub_graph(self, source_ids, namespace=None):
        """
        Crée un sous-graphe basé sur les IDs source donnés.
        
        :param source_ids: Liste des custom_ids à copier
        :param namespace: Namespace optionnel pour le sous-graphe
        :return: Informations sur le sous-graphe créé
        """
        # Générer un namespace unique si non fourni
        if namespace is None:
            namespace = f"subgraph_{str(uuid.uuid4())}"
        
        # Requête Cypher améliorée pour récupérer tous les nœuds et relations connectés
        cypher_query = """
        WITH $source_ids AS source_ids
        
        // Trouver tous les nœuds avec les custom_ids donnés
        MATCH (n)
        WHERE n.custom_id IN source_ids
        
        // Trouver tous les chemins à partir de ces nœuds
        MATCH path = (n)-[*0..3]-(connected)
        
        // Collecter les nœuds uniques et leurs relations
        WITH DISTINCT nodes(path) AS unique_nodes, 
             relationships(path) AS unique_relations
        
        UNWIND unique_nodes AS node
        UNWIND unique_relations AS rel
        
        RETURN 
            node AS source_node, 
            rel AS relationship, 
            startNode(rel) AS start_node,
            endNode(rel) AS end_node,
            labels(node) AS node_labels,
            properties(node) AS node_properties,
            type(rel) AS relationship_type,
            properties(rel) AS relationship_properties
        """
        
        try:
            # Exécuter la requête et récupérer les résultats
            with self.driver.session() as session:
                # Nettoyer le namespace existant
                self.clean_namespace(namespace)
                
                # Exécuter la requête Cypher
                result = session.run(cypher_query, {"source_ids": source_ids})
                
                # Dictionnaires pour suivre les nœuds et relations déjà créés
                created_nodes = {}
                
                # Compteurs
                node_count = 0
                relation_count = 0
                
                # Traiter les résultats
                for record in result:
                    # Créer le nœud source s'il n'existe pas déjà
                    source_node_props = dict(record['node_properties'])
                    source_node_props['namespace'] = namespace
                    
                    # Nettoyer et formater les labels
                    source_labels = record['node_labels']
                    cleaned_labels = [re.sub(r'[^a-zA-Z0-9_]', '_', label) for label in source_labels]
                    
                    # Créer le nœud source
                    if record['source_node']['custom_id'] not in created_nodes:
                        with self.driver.session() as create_session:
                            # Utiliser des backticks pour les labels avec des espaces
                            label_str = ":".join(f"`{label}`" for label in source_labels)
                            create_node_query = f"""
                            CREATE (n:{label_str} $props) 
                            RETURN id(n) AS node_id
                            """
                            node_result = create_session.run(create_node_query, {"props": source_node_props})
                            node_id = node_result.single()['node_id']
                            created_nodes[record['source_node']['custom_id']] = node_id
                            node_count += 1
                    
                    # Créer la relation si elle existe
                    if record['relationship'] is not None:
                        rel_props = dict(record['relationship_properties'])
                        rel_props['namespace'] = namespace
                        
                        # Récupérer les IDs des nœuds de départ et d'arrivée
                        start_node_custom_id = record['start_node']['custom_id']
                        end_node_custom_id = record['end_node']['custom_id']
                        
                        # Créer les nœuds de départ et d'arrivée s'ils n'existent pas
                        start_node_id = created_nodes.get(start_node_custom_id)
                        end_node_id = created_nodes.get(end_node_custom_id)
                        
                        if start_node_id is not None and end_node_id is not None:
                            with self.driver.session() as create_rel_session:
                                create_rel_query = (
                                    "MATCH (a), (b) "
                                    "WHERE id(a) = $start_node_id AND id(b) = $end_node_id "
                                    f"CREATE (a)-[r:`{record['relationship_type']}` $props]->(b)"
                                )
                                create_rel_session.run(create_rel_query, {
                                    "start_node_id": start_node_id, 
                                    "end_node_id": end_node_id,
                                    "props": rel_props
                                })
                                relation_count += 1
                
                logging.info(f"📦 Nœuds copiés : {node_count}")
                logging.info(f"🔗 Relations copiées : {relation_count}")
                logging.info(f"📊 Sous-graphe créé : {namespace}")
                
                return {
                    "namespace": namespace,
                    "node_count": node_count,
                    "relation_count": relation_count
                }
        
        except Exception as e:
            logging.error(f"Erreur lors de la création du sous-graphe : {e}")
            raise

    def query_sub_graph(self, namespace: str, query_params: Dict[str, Any]) -> List[Dict]:
        """
        Requête sur un sous-graphe spécifique
        
        Args:
            namespace (str): Namespace du sous-graphe
            query_params (Dict[str, Any]): Paramètres de requête
        
        Returns:
            List[Dict]: Résultats de la requête
        """
        with self.driver.session() as session:
            query = """
            MATCH (n:FilteredGraph {namespace: $namespace})
            WHERE 
                all(key in keys($query_params) WHERE n[key] = $query_params[key])
            RETURN n
            """
            
            try:
                result = session.run(query, {
                    "namespace": namespace,
                    "query_params": query_params
                })
                
                return [dict(record['n']) for record in result]
            
            except Exception as e:
                logger.error(f"Erreur lors de la requête sur le sous-graphe : {e}")
                raise

    def cleanup_sub_graph(self, namespace: str, max_age_hours: int = 24):
        """
        Nettoie un sous-graphe
        
        Args:
            namespace (str): Namespace du sous-graphe à nettoyer
            max_age_hours (int, optional): Âge maximum en heures. Défaut: 24
        """
        with self.driver.session() as session:
            cleanup_query = """
            MATCH (n:FilteredGraph {namespace: $namespace})
            OPTIONAL MATCH (n)-[r:FILTERED_RELATION]->()
            DELETE r, n
            """
            
            try:
                session.run(cleanup_query, {"namespace": namespace})
                logger.info(f"Sous-graphe {namespace} nettoyé")
            
            except Exception as e:
                logger.error(f"Erreur lors du nettoyage du sous-graphe : {e}")
                raise

    def clean_namespace(self, namespace: str):
        """
        Nettoie le namespace existant
        
        Args:
            namespace (str): Namespace à nettoyer
        """
        with self.driver.session() as session:
            cleanup_query = """
            MATCH (n {namespace: $namespace})
            DETACH DELETE n
            """
            
            try:
                session.run(cleanup_query, {"namespace": namespace})
                logger.info(f"Namespace {namespace} nettoyé")
            
            except Exception as e:
                logger.error(f"Erreur lors du nettoyage du namespace : {e}")
                raise

    def close(self):
        """Ferme la connexion Neo4j"""
        if self.driver:
            self.driver.close()
            logger.info("Connexion Neo4j fermée")

def main():
    # Exemple d'utilisation
    graph_filter = Neo4jGraphFilter()
    
    try:
        # Créer des index
        graph_filter.create_indexes(['custom_id', 'name'])
        
        # Créer un sous-graphe
        # IMPORTANT : Remplacez ces IDs par des IDs réels de votre base de données
        source_ids = ['5390255707819795563', '3529332825818922980']
        
        # Vérifier d'abord les nœuds existants
        with graph_filter.driver.session() as session:
            check_query = """
            UNWIND $source_ids AS source_id
            MATCH (n)
            WHERE n.custom_id = source_id
            RETURN 
                source_id, 
                COUNT(n) AS node_count, 
                COLLECT(labels(n)) AS node_labels,
                COLLECT(properties(n)) AS node_properties
            """
            result = session.run(check_query, {"source_ids": source_ids})
            existing_nodes = list(result)
            
            print("🔍 Nœuds existants :")
            for node in existing_nodes:
                print(f"ID: {node['source_id']}")
                print(f"  Nombre : {node['node_count']}")
                print(f"  Labels : {node['node_labels']}")
                print(f"  Propriétés : {node['node_properties']}")
                print("---")
            
            # Vérifier les relations
            relations_query = """
            UNWIND $source_ids AS source_id
            MATCH (source {custom_id: source_id})
            OPTIONAL MATCH (source)-[r]->(target)
            RETURN 
                source_id, 
                type(r) AS relation_type, 
                target.custom_id AS target_id, 
                properties(r) AS relation_properties
            """
            relations_result = session.run(relations_query, {"source_ids": source_ids})
            existing_relations = list(relations_result)
            
            print("\n🔗 Relations existantes :")
            if not existing_relations:
                print("  Aucune relation trouvée.")
            else:
                for relation in existing_relations:
                    print(f"  Source ID: {relation['source_id']}")
                    print(f"  Relation Type: {relation['relation_type']}")
                    print(f"  Target ID: {relation['target_id']}")
                    print(f"  Relation Properties: {relation['relation_properties']}")
                    print("---")
        
        # Créer le sous-graphe
        namespace = graph_filter.create_sub_graph(
            source_ids
        )
        
        print(f"📦 Namespace créé : {namespace}")
        
        # Requêter le sous-graphe
        results = graph_filter.query_sub_graph(
            namespace['namespace'], 
            {'namespace': namespace['namespace']}  # Modifier pour correspondre à votre structure
        )
        
        print("📊 Résultats de la requête :")
        for result in results:
            print(result)
    
    except Exception as e:
        logger.error(f"❌ Erreur dans le main : {e}")
    
    finally:
        graph_filter.close()

if __name__ == "__main__":
    main()