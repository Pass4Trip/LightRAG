#!/usr/bin/env python3
import os
import json
from datetime import datetime
from neo4j import GraphDatabase
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Neo4jBackup:
    """
    Classe pour créer des sauvegardes de base de données Neo4j.
    """
    
    def __init__(self, uri=None, username=None, password=None, database="neo4j", backup_dir=None):
        """
        Initialise la connexion à Neo4j.
        
        Args:
            uri (str): URI de connexion Neo4j
            username (str): Nom d'utilisateur
            password (str): Mot de passe
            database (str): Nom de la base de données
            backup_dir (str): Répertoire pour les sauvegardes
        """
        # Utiliser les variables d'environnement si non spécifiées
        self.uri = uri or os.getenv('NEO4J_URI', 'bolt://localhost:7687')
        self.username = username or os.getenv('NEO4J_USERNAME', 'neo4j')
        self.password = password or os.getenv('NEO4J_PASSWORD')
        self.database = database
        
        if not self.password:
            raise ValueError("Le mot de passe est requis")
        
        # Configurer le répertoire de backup
        self.backup_dir = backup_dir or os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 
            'backups'
        )
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # Initialiser la connexion
        try:
            self.driver = GraphDatabase.driver(
                self.uri, 
                auth=(self.username, self.password)
            )
            logger.info(f"Connexion à Neo4j établie : {self.uri} (base : {self.database})")
        except Exception as e:
            raise ConnectionError(f"Erreur de connexion à Neo4j : {e}")
    
    def close(self):
        """Ferme la connexion à Neo4j."""
        if hasattr(self, 'driver'):
            self.driver.close()
            logger.info("Connexion Neo4j fermée")
    
    def get_database_info(self):
        """
        Récupère les informations de base sur la base de données.
        
        Returns:
            list: Liste des informations sur la base de données
        """
        with self.driver.session(database=self.database) as session:
            result = session.run("""
                MATCH (n)
                WITH labels(n) as labels, count(n) as count
                RETURN count, labels, count(distinct labels) as unique_label_count
            """)
            info = [
                {
                    'node_count': record['count'],
                    'node_labels': record['labels'],
                    'unique_label_count': record['unique_label_count']
                }
                for record in result
            ]
            logger.info(f"Informations de la base de données : {info}")
            total_nodes = sum(item['node_count'] for item in info)
            logger.info(f"Nombre total de nœuds : {total_nodes}")
            return info
    
    def backup_database(self):
        """
        Crée une sauvegarde de la base de données.
        
        Returns:
            str: Chemin vers le fichier de sauvegarde
        """
        try:
            # Vérifier l'état de la base
            self.get_database_info()
            
            # Récupérer tous les nœuds
            with self.driver.session(database=self.database) as session:
                nodes_result = session.run("""
                    MATCH (n)
                    RETURN 
                        id(n) as id,
                        labels(n) as labels,
                        properties(n) as properties
                    """)
                nodes = [
                    {
                        'id': record['id'],
                        'labels': record['labels'],
                        'properties': record['properties']
                    }
                    for record in nodes_result
                ]
            
            # Récupérer toutes les relations
            with self.driver.session(database=self.database) as session:
                rels_result = session.run("""
                    MATCH ()-[r]->()
                    RETURN 
                        id(startNode(r)) as start_id,
                        id(endNode(r)) as end_id,
                        type(r) as type,
                        properties(r) as properties
                    """)
                relationships = [
                    {
                        'start_id': record['start_id'],
                        'end_id': record['end_id'],
                        'type': record['type'],
                        'properties': record['properties']
                    }
                    for record in rels_result
                ]
            
            # Créer le fichier de backup
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = os.path.join(
                self.backup_dir,
                f'neo4j_backup_{timestamp}.json'
            )
            
            backup_data = {
                'nodes': nodes,
                'relationships': relationships,
                'metadata': {
                    'timestamp': timestamp,
                    'database': self.database,
                    'uri': self.uri
                }
            }
            
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False)
            
            # Log des statistiques
            file_size = os.path.getsize(backup_file)
            logger.info(f"Sauvegarde terminée : {backup_file}")
            logger.info(f"Nombre de nœuds sauvegardés : {len(nodes)}")
            logger.info(f"Nombre de relations sauvegardées : {len(relationships)}")
            logger.info(f"Taille du fichier de sauvegarde : {file_size} octets")
            
            return backup_file
            
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde : {e}")
            import traceback
            logger.error(f"Trace complète : {traceback.format_exc()}")
            return None

if __name__ == "__main__":
    # Test simple
    backup = Neo4jBackup()
    backup.backup_database()
    backup.close()
