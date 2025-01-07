#!/usr/bin/env python3
import os
import json
import logging
from datetime import datetime
from neo4j import GraphDatabase

__version__ = "1.1.0"

# Configuration du logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Neo4jBackup:
    def __init__(self, 
                 uri="bolt://vps-af24e24d.vps.ovh.net:32045", 
                 username="neo4j", 
                 password=None,
                 backup_dir=None,
                 database="neo4j"):
        """
        Initialise une connexion à la base de données Neo4j.
        
        Args:
            uri (str): URI de connexion à la base de données
            username (str): Nom d'utilisateur
            password (str, optional): Mot de passe. Si None, utilise la variable d'environnement.
            backup_dir (str, optional): Répertoire de sauvegarde. Par défaut, utilise ./backups
            database (str, optional): Nom de la base de données
        """
        # Utiliser le mot de passe de l'environnement si non fourni
        if password is None:
            password = os.getenv('NEO4J_PASSWORD')
            if not password:
                raise ValueError("Aucun mot de passe fourni. Définissez NEO4J_PASSWORD.")
        
        # Définir le répertoire de backup
        if backup_dir is None:
            backup_dir = os.path.join(os.path.dirname(__file__), 'backups')
        
        # Créer le répertoire de backup s'il n'existe pas
        os.makedirs(backup_dir, exist_ok=True)
        
        try:
            self.driver = GraphDatabase.driver(uri, auth=(username, password))
            self.database = database
            self.backup_dir = backup_dir
            
            logger.info(f"Connexion à Neo4j établie : {uri} (base : {database})")
        except Exception as e:
            logger.error(f"Erreur de connexion à Neo4j : {e}")
            raise

    def _get_database_info(self):
        """
        Récupère des informations sur la base de données.
        
        Returns:
            list: Liste des informations de chaque label
        """
        try:
            with self.driver.session(database=self.database) as session:
                # Récupérer les informations sur les nœuds par label
                node_info_query = """
                    MATCH (n)
                    WITH labels(n) as node_labels
                    UNWIND node_labels as label
                    WITH label, count(*) as node_count
                    RETURN 
                        node_count, 
                        label as node_labels, 
                        1 as unique_label_count
                """
                result = session.run(node_info_query)
                node_info = [
                    {
                        'node_count': record['node_count'], 
                        'node_labels': record['node_labels'], 
                        'unique_label_count': record['unique_label_count']
                    } 
                    for record in result
                ]
                
                logger.info(f"Nombre total de nœuds : {sum(info['node_count'] for info in node_info)}")
                return node_info
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des informations de la base : {e}")
            raise

    def backup_database(self):
        """
        Sauvegarde la base de données dans un fichier JSON.
        
        Returns:
            str: Chemin du fichier de sauvegarde
        """
        try:
            # Récupérer les informations de la base de données
            self._get_database_info()
            
            # Récupérer tous les nœuds et leurs relations
            with self.driver.session(database=self.database) as session:
                # Récupérer tous les nœuds
                nodes_query = """
                    MATCH (n)
                    RETURN 
                        id(n) as node_id,
                        labels(n) as labels,
                        properties(n) as properties
                """
                nodes_result = session.run(nodes_query)
                nodes = [
                    {
                        'id': record['node_id'],
                        'labels': record['labels'], 
                        'properties': dict(record['properties'])
                    } 
                    for record in nodes_result
                ]
                
                # Récupérer toutes les relations
                relationships_query = """
                    MATCH ()-[r]->()
                    RETURN 
                        elementId(startNode(r)) as start_node_id,
                        elementId(endNode(r)) as end_node_id,
                        labels(startNode(r)) as start_labels,
                        labels(endNode(r)) as end_labels,
                        type(r) as type,
                        properties(r) as properties
                """
                relationships_result = session.run(relationships_query)
                relationships = [
                    {
                        'start_node_id': record['start_node_id'],
                        'end_node_id': record['end_node_id'],
                        'start_label': record['start_labels'][0] if record['start_labels'] else 'Unknown',
                        'end_label': record['end_labels'][0] if record['end_labels'] else 'Unknown',
                        'type': record['type'],
                        'properties': dict(record['properties'])
                    } 
                    for record in relationships_result
                ]
            
            # Préparer les données de sauvegarde
            backup_data = {
                'nodes': nodes,
                'relationships': relationships
            }
            
            # Générer le nom de fichier
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"neo4j_backup_{timestamp}.json"
            backup_path = os.path.join(self.backup_dir, backup_filename)
            
            # Sauvegarder dans un fichier JSON
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2)
            
            # Journaliser les statistiques
            logger.info(f"Sauvegarde terminée : {backup_path}")
            logger.info(f"Nombre de nœuds sauvegardés : {len(nodes)}")
            logger.info(f"Nombre de relations sauvegardées : {len(relationships)}")
            logger.info(f"Taille du fichier de sauvegarde : {os.path.getsize(backup_path)} octets")
            
            return backup_path
        
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde : {e}")
            import traceback
            logger.error(f"Trace complète : {traceback.format_exc()}")
            raise

    def close(self):
        """
        Ferme la connexion à la base de données.
        """
        try:
            self.driver.close()
            logger.info("Connexion Neo4j fermée")
        except Exception as e:
            logger.error(f"Erreur lors de la fermeture de la connexion : {e}")

if __name__ == "__main__":
    # Test simple
    backup = Neo4jBackup()
    backup.backup_database()
    backup.close()
