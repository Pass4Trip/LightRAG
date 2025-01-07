#!/usr/bin/env python3
import os
import json
from neo4j import GraphDatabase
import logging
import re

# Configuration du logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def clean_label(label):
    """
    Nettoie un label pour le rendre compatible avec Neo4j.
    
    Args:
        label (str): Le label à nettoyer
    
    Returns:
        str: Le label nettoyé
    """
    # Remplacer les espaces et caractères spéciaux par des underscores
    cleaned_label = re.sub(r'[^a-zA-Z0-9_]', '_', label)
    
    # Ajouter un préfixe 'restore_' pour éviter les conflits
    return f"restore_{cleaned_label}"

class Neo4jRestore:
    """
    Classe pour restaurer des sauvegardes dans une base de données Neo4j.
    """
    
    def __init__(self, uri=None, username=None, password=None, database="neo4j"):
        """
        Initialise la connexion à Neo4j.
        
        Args:
            uri (str): URI de connexion Neo4j
            username (str): Nom d'utilisateur
            password (str): Mot de passe
            database (str): Nom de la base de données
        """
        # Utiliser les variables d'environnement si non spécifiées
        self.uri = uri or os.getenv('NEO4J_URI', 'bolt://localhost:7687')
        self.username = username or os.getenv('NEO4J_USERNAME', 'neo4j')
        self.password = password or os.getenv('NEO4J_PASSWORD')
        self.database = database
        
        if not self.password:
            raise ValueError("Le mot de passe est requis")
        
        # Initialiser la connexion
        try:
            self.driver = GraphDatabase.driver(
                self.uri, 
                auth=(self.username, self.password)
            )
            logger.info(f"Connexion à Neo4j établie : {self.uri}")
        except Exception as e:
            raise ConnectionError(f"Erreur de connexion à Neo4j : {e}")
    
    def close(self):
        """Ferme la connexion à Neo4j."""
        if hasattr(self, 'driver'):
            self.driver.close()
            logger.info("Connexion Neo4j fermée")
    
    def restore_database(self, backup_file):
        """
        Restaure une base de données à partir d'un fichier de sauvegarde.
        
        Args:
            backup_file (str): Chemin vers le fichier de sauvegarde
            
        Returns:
            dict: Statistiques de restauration
        """
        try:
            # Charger les données de backup
            with open(backup_file, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            nodes = backup_data['nodes']
            relationships = backup_data['relationships']
            
            # Dictionnaire pour mapper les anciens IDs aux nouveaux
            id_mapping = {}
            
            # Restaurer les nœuds
            with self.driver.session(database=self.database) as session:
                for node in nodes:
                    # Nettoyer le label
                    clean_labels = [clean_label(label) for label in node['labels']]
                    
                    # Créer le nœud avec les propriétés
                    with session.begin_transaction() as tx:
                        create_node_query = f"""
                        CREATE (n:{':'.join(clean_labels)})
                        SET n = $properties
                        RETURN elementId(n) as new_id
                        """
                        result = tx.run(create_node_query, properties=node['properties'])
                        record = result.single()
                        new_id = record['new_id']
                        
                        # Mapper l'ancien ID au nouvel ID
                        id_mapping[node['id']] = new_id
            
            # Restaurer les relations
            with self.driver.session(database=self.database) as session:
                for rel in relationships:
                    # Récupérer les nœuds de départ et d'arrivée
                    start_node_element_id = id_mapping.get(rel['start_node_id'])
                    end_node_element_id = id_mapping.get(rel['end_node_id'])
                    
                    if start_node_element_id is None or end_node_element_id is None:
                        logger.warning(f"Impossible de restaurer la relation : nœuds introuvables. Type : {rel['type']}")
                        continue
                    
                    # Requête pour créer la relation
                    create_rel_query = """
                    MATCH (start) WHERE elementId(start) = $start_node_id
                    MATCH (end) WHERE elementId(end) = $end_node_id
                    CREATE (start)-[r:""" + rel['type'] + """ $properties]->(end)
                    """
                    
                    try:
                        session.run(
                            create_rel_query, 
                            start_node_id=start_node_element_id, 
                            end_node_id=end_node_element_id, 
                            properties=rel['properties']
                        )
                    except Exception as e:
                        logger.error(f"Erreur lors de la restauration de la relation : {e}")
                        logger.error(f"Détails de la relation : {rel}")
                        continue
            
            # Retourner les statistiques
            return {
                'nodes_created': len(nodes),
                'relationships_created': len(relationships),
                'labels_created': list(set([
                    clean_label(label) 
                    for node in nodes 
                    for label in node['labels']
                ]))
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la restauration : {e}")
            import traceback
            logger.error(f"Trace complète : {traceback.format_exc()}")
            raise

if __name__ == "__main__":
    # Test simple
    restore = Neo4jRestore()
    # Spécifiez un fichier de backup valide pour tester
    # restore.restore_database('path/to/backup.json')
