#!/usr/bin/env python3
import os
import argparse
from neo4j_backup import Neo4jBackup
from neo4j_restore import Neo4jRestore
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def sync_to_prod(backup_dir=None):
    """
    Synchronise la base de données locale vers la production.
    
    Args:
        backup_dir (str, optional): Répertoire pour stocker les backups
    """
    try:
        # 1. Créer un backup de la base locale
        logger.info("Création du backup de la base locale...")
        backup_client = Neo4jBackup(
            uri="bolt://localhost:7688",
            username="neo4j",
            password="testpassword123",
            backup_dir=backup_dir
        )
        
        backup_file = backup_client.backup_database()
        if not backup_file:
            raise ValueError("Échec de la création du backup")
        
        logger.info(f"Backup créé : {backup_file}")
        backup_client.close()
        
        # 2. Vérifier les variables d'environnement pour la production
        if not os.getenv('NEO4J_PASSWORD'):
            raise ValueError("NEO4J_PASSWORD n'est pas défini")
        
        # 3. Restaurer le backup dans la base de production
        logger.info("Restauration dans la base de production...")
        restore_client = Neo4jRestore()
        
        stats = restore_client.restore_database(backup_file)
        restore_client.close()
        
        # 4. Afficher les statistiques
        logger.info("\n=== Statistiques de synchronisation ===")
        logger.info(f"Nœuds restaurés : {stats['nodes_created']}")
        logger.info(f"Relations restaurées : {stats['relationships_created']}")
        logger.info(f"Labels : {', '.join(stats['labels_created'])}")
        logger.info("=====================================")
        
        return True
        
    except Exception as e:
        logger.error(f"Erreur lors de la synchronisation : {e}")
        import traceback
        logger.error(f"Trace complète : {traceback.format_exc()}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Synchronisation Neo4j Local vers Production')
    parser.add_argument('--backup-dir', type=str, help='Répertoire de sauvegarde personnalisé')
    parser.add_argument('--force', action='store_true', help='Forcer la synchronisation sans confirmation')
    
    args = parser.parse_args()
    
    # Demander confirmation avant de synchroniser vers la production
    if not args.force:
        print("\n⚠️  ATTENTION ⚠️")
        print("Vous êtes sur le point de synchroniser la base locale vers la production.")
        print("Cette opération va écraser les données de production.")
        confirmation = input("\nÊtes-vous sûr de vouloir continuer ? (oui/NON) : ")
        
        if confirmation.lower() != 'oui':
            print("Opération annulée.")
            return
    
    if sync_to_prod(args.backup_dir):
        print("Synchronisation réussie !")
    else:
        print("Échec de la synchronisation. Vérifiez les logs pour plus de détails.")

if __name__ == "__main__":
    main()
