import os
import logging
import sys
from datetime import datetime
from pymilvus import MilvusClient
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Configuration du logging plus détaillée
log_dir = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(log_dir, exist_ok=True)

log_filename = os.path.join(log_dir, f'relationship_cleanup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')

logging.basicConfig(
    level=logging.INFO,  # Changé à DEBUG pour plus de détails
    format='%(asctime)s - %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler(sys.stdout)  # Ajout de la sortie standard
    ]
)

# Charger les variables d'environnement
load_dotenv()

class RelationshipChecker:
    def __init__(self):
        # Logs des variables d'environnement
        logging.debug(f"MILVUS_URI: {os.getenv('MILVUS_URI')}")
        logging.debug(f"MILVUS_TOKEN: {bool(os.getenv('MILVUS_TOKEN'))}")  # Ne pas afficher le token

        try:
            # Connexion à Milvus avec la base 'lightrag'
            self.milvus_client = MilvusClient(
                uri=os.getenv('MILVUS_URI', 'http://localhost:19530'),
                token=os.getenv('MILVUS_TOKEN', ''),
                db_name='lightrag'
            )
            
            # Lister les collections
            collections = self.milvus_client.list_collections()
            logging.info(f"Collections dans 'lightrag': {collections}")

            # Vérifier si 'relationships' existe
            if 'relationships' not in collections:
                logging.warning("Collection 'relationships' non trouvée dans 'lightrag'")
                logging.info("Collections disponibles : " + ", ".join(collections))
                return

        except Exception as e:
            logging.error(f"Erreur de connexion à Milvus : {e}")
            logging.error(f"Détails de l'erreur : {sys.exc_info()}")
            return

        # Connexion à Neo4j
        neo4j_uri = os.getenv('NEO4J_URI')
        neo4j_username = os.getenv('NEO4J_USERNAME')
        neo4j_password = os.getenv('NEO4J_PASSWORD')
        
        logging.debug(f"Neo4j URI: {neo4j_uri}")
        logging.debug(f"Neo4j Username: {neo4j_username}")
        
        self.neo4j_driver = GraphDatabase.driver(
            neo4j_uri, 
            auth=(neo4j_username, neo4j_password)
        )

        # Liste pour stocker les IDs supprimés
        self.deleted_ids = []

    def check_relationships(self):
        # Vérifier si la connexion Milvus est établie
        if not hasattr(self, 'milvus_client'):
            logging.error("Impossible de se connecter à Milvus")
            return

        try:
            # Requête sur la collection 'relationships' dans 'lightrag'
            relationships = self.milvus_client.query(
                collection_name='relationships',
                filter='',
                output_fields=['id'],  # Récupérer l'ID de Milvus
                limit=1000  # Ajout explicite d'une limite
            )

            logging.info(f"Total relationships to check: {len(relationships)}")
            logging.info(f"IDs des relations à vérifier : {[rel['id'] for rel in relationships]}")

            # Vérification des relations
            for relationship in relationships:
                milvus_id = relationship['id']
                logging.debug(f"Vérification de la relation Milvus ID: {milvus_id}")
                
                # Vérifier l'existence dans Neo4j
                with self.neo4j_driver.session() as session:
                    result = session.run(
                        "MATCH (src)-[r {relation_id: $relation_id}]->(tgt) RETURN src, r, tgt",
                        relation_id=milvus_id  # Utiliser l'ID Milvus comme relation_id Neo4j
                    )
                    
                    # Si aucun résultat, supprimer de Milvus
                    if not result.peek():
                        logging.warning(f"Relation {milvus_id} non trouvée dans Neo4j. Suppression...")
                        logging.info(f"Détails de suppression - Collection: relationships, ID: {milvus_id}")
                        self.milvus_client.delete(
                            collection_name='relationships', 
                            filter=f"id == '{milvus_id}'"  # Filtrer par ID Milvus
                        )
                        self.deleted_ids.append(milvus_id)
                        logging.info(f"Relation {milvus_id} supprimée de Milvus")

        except Exception as e:
            logging.error(f"Erreur lors de la requête sur la collection : {e}")
            logging.error(f"Détails de l'erreur : {sys.exc_info()}")

    def log_summary(self):
        logging.info("\n--- SUMMARY ---")
        logging.info(f"Total relations supprimées: {len(self.deleted_ids)}")
        logging.info("Relations supprimées:")
        for relation_id in self.deleted_ids:
            logging.info(relation_id)

    def __del__(self):
        self.neo4j_driver.close()

def main():
    checker = RelationshipChecker()
    checker.check_relationships()
    checker.log_summary()

if __name__ == "__main__":
    main()