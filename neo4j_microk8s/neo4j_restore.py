#!/usr/bin/env python3
import os
import json
from neo4j import GraphDatabase
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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
                    # Ajouter le préfixe 'restore_' aux labels
                    labels = [f"restore_{label}" for label in node['labels']]
                    labels_str = ':'.join(labels)
                    
                    # Créer le nœud
                    result = session.run(f"""
                        CREATE (n:{labels_str})
                        SET n = $properties
                        RETURN id(n) as new_id
                        """,
                        properties=node['properties']
                    )
                    
                    # Stocker le mapping des IDs
                    new_id = result.single()['new_id']
                    id_mapping[node['id']] = new_id
            
            # Restaurer les relations
            with self.driver.session(database=self.database) as session:
                for rel in relationships:
                    # Ajouter le préfixe 'restore_' au type de relation
                    rel_type = f"restore_{rel['type']}"
                    
                    # Créer la relation
                    session.run("""
                            MATCH (start), (end)
                            WHERE id(start) = $start_id AND id(end) = $end_id
                            CREATE (start)-[r:""" + rel_type + """]->(end)
                            SET r = $properties
                            """,
                            start_id=id_mapping[rel['start_id']],
                            end_id=id_mapping[rel['end_id']],
                            properties=rel['properties']
                    )
            
            # Retourner les statistiques
            return {
                'nodes_created': len(nodes),
                'relationships_created': len(relationships),
                'labels_created': list(set([
                    f"restore_{label}" 
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
