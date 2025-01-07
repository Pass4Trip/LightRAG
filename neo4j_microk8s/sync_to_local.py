#!/usr/bin/env python3
import os
import argparse
from neo4j_backup import Neo4jBackup
from neo4j_restore import Neo4jRestore
import logging
from neo4j import GraphDatabase

__version__ = "1.1.0"

# Configuration du logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def sync_to_local(backup_dir=None):
    """
    Synchronise la base de données de production vers la base locale.
    
    Args:
        backup_dir (str, optional): Répertoire pour stocker les backups
    
    Returns:
        dict: Statistiques de synchronisation
    """
    try:
        # Vérifier que les variables d'environnement sont définies
        if not os.getenv('NEO4J_PASSWORD'):
            raise ValueError("NEO4J_PASSWORD n'est pas défini")
        
        # 1. Créer un backup de la base de production
        logger.info("Création du backup de la base de production...")
        backup_client = Neo4jBackup(backup_dir=backup_dir)
        
        backup_file = backup_client.backup_database()
        if not backup_file:
            raise ValueError("Échec de la création du backup")
        
        logger.info(f"Backup créé : {backup_file}")
        backup_client.close()
        
        # 2. Supprimer tous les nœuds de la base locale
        logger.info("Suppression de tous les nœuds de la base locale...")
        local_driver = GraphDatabase.driver(
            "bolt://localhost:7688", 
            auth=("neo4j", "testpassword123")
        )
        
        with local_driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
        
        local_driver.close()
        
        # 3. Restaurer le backup dans la base locale
        logger.info("Restauration dans la base locale...")
        restore_client = Neo4jRestore(
            uri="bolt://localhost:7688",
            username="neo4j",
            password="testpassword123"
        )
        
        stats = restore_client.restore_database(backup_file)
        restore_client.close()
        
        # 4. Afficher les statistiques
        logger.info("\n=== Statistiques de synchronisation ===")
        logger.info(f"Nœuds restaurés : {stats['nodes_created']}")
        logger.info(f"Relations restaurées : {stats['relationships_created']}")
        logger.info(f"Labels : {', '.join(stats['labels_created'])}")
        
        return stats
    
    except Exception as e:
        logger.error(f"Erreur lors de la synchronisation : {e}")
        raise

def main():
    parser = argparse.ArgumentParser(description='Synchronisation Neo4j Production vers Local')
    parser.add_argument('--backup-dir', type=str, help='Répertoire de sauvegarde personnalisé')
    
    args = parser.parse_args()
    
    stats = sync_to_local(args.backup_dir)
    if stats:
        logger.info("=====================================")
        logger.info(f"Nœuds restaurés : {stats['nodes_created']}")
        logger.info(f"Relations restaurées : {stats['relationships_created']}")
        logger.info(f"Labels : {', '.join(stats['labels_created'])}")
        logger.info("=====================================")
        print("Synchronisation réussie !")
    else:
        print("Échec de la synchronisation. Vérifiez les logs pour plus de détails.")

if __name__ == "__main__":
    main()
