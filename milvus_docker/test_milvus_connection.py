import os
from pymilvus import MilvusClient
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_milvus_connection(db_name: str = ""):
    try:
        # Récupérer la configuration
        milvus_uri = os.environ.get("MILVUS_URI", "http://localhost:19530")
        user = os.environ.get("MILVUS_USER", "")
        password = os.environ.get("MILVUS_PASSWORD", "")
        token = os.environ.get("MILVUS_TOKEN", "")

        logger.info(f"\nTest de connexion pour la base de données: {db_name or 'default'}")
        logger.info(f"URI: {milvus_uri}")
        
        # Connexion à Milvus
        client = MilvusClient(
            uri=milvus_uri,
            user=user,
            password=password,
            token=token,
            db_name=db_name
        )
        
        logger.info("✅ Connexion réussie!")
        
        # Liste des collections
        logger.info("\nCollections disponibles:")
        collections = client.list_collections()
        logger.info(collections)
        
        # Statistiques des collections
        if collections:
            logger.info("\nStatistiques des collections:")
            for collection in collections:
                stats = client.get_collection_stats(collection)
                logger.info(f"{collection}: {stats}")
        
        return collections
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la connexion: {str(e)}")
        return []

if __name__ == "__main__":
    # Tester la connexion à la base par défaut
    default_collections = test_milvus_connection()
    
    # Tester la connexion à la base lightrag
    lightrag_collections = test_milvus_connection("lightrag")
