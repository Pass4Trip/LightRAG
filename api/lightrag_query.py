from pathlib import Path
import sys
import logging
import asyncio
import traceback
from typing import Dict, Any, Optional, List

from fastapi import APIRouter, HTTPException, FastAPI
from pydantic import BaseModel
import uvicorn

# Ajout du chemin parent pour importer LightRAG
sys.path.append(str(Path(__file__).parent.parent))

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialisation de LightRAG
from lightrag.lightrag import LightRAG, QueryParam
from lightrag.llm import gpt_4o_mini_complete  # Ajout de cet import
from lightrag.kg.milvus_impl import MilvusVectorDBStorage
from lightrag.kg.mongo_impl import MongoKVStorage
from lightrag.kg.neo4j_impl import Neo4JStorage

# Créer un router pour cet API
router = APIRouter()

class QueryRequest(BaseModel):
    """
    Modèle de requête pour la recherche
    """
    question: str
    user_id: Optional[str] = "anonymous"
    mode: Optional[str] = "hybrid"
    vdb_filter: Optional[List[str]] = []
    limit: Optional[int] = 10
    offset: Optional[int] = 0

def init_lightrag() -> LightRAG:
    """
    Initialise et configure l'instance LightRAG
    """
    try:
        # Configuration Milvus
        milvus_config = {
            "uri": "vps-af24e24d.vps.ovh.net:31723",
            "username": "root",
            "password": "Milvus"
        }

        rag = LightRAG(
            working_dir=str(Path(__file__).parent.parent / "api"),
            llm_model_func=gpt_4o_mini_complete,
            kv_storage="MongoKVStorage",
            vector_storage="MilvusVectorDBStorage",
            graph_storage="Neo4JStorage",
            log_level=logging.INFO,
            enable_llm_cache=False,
            vector_db_storage_cls_kwargs=milvus_config
        )
        return rag
    except Exception as e:
        logger.error(f"Erreur d'initialisation de LightRAG : {e}")
        raise

@router.post("/")
async def query_messages(query_request: QueryRequest):
    """
    Endpoint pour rechercher des messages dans LightRAG

    Args:
        query_request (QueryRequest): Paramètres de recherche

    Returns:
        Dict[str, Any]: Résultats de la recherche
    """
    try:
        logger.info(f"Requête de recherche reçue : {query_request}")
        
        # Initialiser LightRAG
        rag = init_lightrag()
        
        # Préparer les paramètres de requête
        query_param = QueryParam(mode=query_request.mode)
        
        # Exécuter la requête
        response = await rag.aquery(
            query_request.question, 
            param=query_param, 
            vdb_filter=query_request.vdb_filter, 
            user_id=query_request.user_id
        )
        
        return {
            "status": "success",
            "question": query_request.question,
            "response": response,
            "total": 1  # À ajuster selon vos besoins
        }

    except Exception as e:
        logger.error(f"Erreur lors de la recherche de messages : {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

# Créer l'application FastAPI
app = FastAPI(
    title="LightRAG Query API",
    description="API pour effectuer des requêtes avec LightRAG",
    version="0.1.0"
)

# Inclure le router
app.include_router(router, tags=["Query"])