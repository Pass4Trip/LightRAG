#!/usr/bin/env python3
import os
import sys
import logging
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Ajouter le chemin local de LightRAG au Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Charger les variables d'environnement
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from lightrag.lightrag import LightRAG
from lightrag.llm import gpt_4o_complete
from lightrag.utils import EmbeddingFunc
from lightrag.kg.milvus_impl import MilvusVectorDBStorage
from lightrag.kg.neo4j_impl import Neo4jKnowledgeGraph

# Configuration Milvus - utiliser les valeurs de .env ou les valeurs par défaut
if not os.environ.get("MILVUS_URI"):
    os.environ["MILVUS_URI"] = "tcp://localhost:19530"

# Données sur Zulli
ZULLI_DATA = [
    {
        "text": """
        Zulli est un passionné de gastronomie italienne authentique, particulièrement des pâtes fraîches maison et des pizzas napolitaines. 
        Il apprécie les restaurants qui utilisent des ingrédients de haute qualité et qui respectent les traditions culinaires.
        Sa préférence va aux établissements qui proposent une ambiance chaleureuse et familiale.
        """,
        "metadata": {
            "custom_id": "Zulli",
            "entity_type": "Person",
            "preferences": ["Italian cuisine", "Fresh pasta", "Neapolitan pizza", "High-quality ingredients", "Traditional cooking", "Warm atmosphere"]
        }
    },
    {
        "text": """
        Les critères de Zulli pour un bon restaurant italien incluent :
        - Des pâtes fraîches faites maison
        - Une carte des vins italiens bien fournie
        - Un four à pizza traditionnel
        - Un chef d'origine italienne
        - Une ambiance authentique
        """,
        "metadata": {
            "custom_id": "Zulli_preferences",
            "entity_type": "Preferences",
            "related_to": "Zulli"
        }
    }
]

async def main():
    try:
        # Initialiser les composants
        logger.info("Initialisation des composants...")
        vector_db = MilvusVectorDBStorage(
            uri=os.environ.get("MILVUS_URI", "tcp://localhost:19530"),
            embedding_func=EmbeddingFunc(),
            namespace="lightrag"  # Utiliser la base lightrag
        )
        
        knowledge_graph = Neo4jKnowledgeGraph()
        
        # Initialiser LightRAG
        logger.info("Initialisation de LightRAG...")
        rag = LightRAG(
            llm_func=gpt_4o_complete,
            embedding_func=EmbeddingFunc(),
            vector_db=vector_db,
            knowledge_graph=knowledge_graph
        )
        
        # Insérer les données
        logger.info("Insertion des données sur Zulli...")
        for item in ZULLI_DATA:
            logger.info(f"Insertion : {item['metadata']['custom_id']}")
            await rag.ainsert(
                item["text"],
                metadata=item["metadata"]
            )
        
        logger.info("Données insérées avec succès !")
        
    except Exception as e:
        logger.error(f"Erreur lors de l'insertion des données : {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
