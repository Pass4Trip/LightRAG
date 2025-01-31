import asyncio
import sys
import logging
from pathlib import Path

# Ajouter le chemin parent pour importer les modules
sys.path.append(str(Path(__file__).parent.parent))

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from api.lightrag_query import init_lightrag, QueryRequest, query_messages

async def main():
    try:
        # Test d'initialisation de LightRAG
        logger.info("🔍 Test d'initialisation de LightRAG")
        rag = init_lightrag()
        logger.info("✅ Initialisation réussie")

        # Test de requête de base
        logger.info("\n🔍 Test de requête de base")
        query_request = QueryRequest(
            question="donne moi un restaurant a lyon au calme",
            user_id="vinh",
            mode="hybrid",
            limit=5
        )
        
        try:
            result = await query_messages(query_request)
            logger.info("✅ Requête réussie")
            logger.info(f"📋 Résultat : {result}")
        except Exception as query_ex:
            logger.error(f"❌ Erreur lors de la requête : {query_ex}")
            logger.error(f"Détails de l'exception : {sys.exc_info()[2]}")
            raise

        # Test avec filtres
        logger.info("\n🔍 Test de requête avec filtres")
        filtered_request = QueryRequest(
            question="Restaurants à Lyon",
            vdb_filter=["activity", "restaurant"],
            limit=3
        )
        
        try:
            filtered_result = await query_messages(filtered_request)
            logger.info("✅ Requête avec filtres réussie")
            logger.info(f"📋 Résultat : {filtered_result}")
        except Exception as query_ex:
            logger.error(f"❌ Erreur lors de la requête avec filtres : {query_ex}")
            logger.error(f"Détails de l'exception : {sys.exc_info()[2]}")
            raise

    except Exception as e:
        logger.error(f"❌ Erreur globale : {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
