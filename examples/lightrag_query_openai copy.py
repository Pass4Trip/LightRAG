#!/usr/bin/env python3
import os
import sys
import logging
import re
from typing import Dict, Any, Optional, List, Union
import json
import aio_pika
import asyncio
from pathlib import Path
from dotenv import load_dotenv
import uuid
from datetime import datetime
import traceback
import time
import argparse

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Configuration des logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)  # Sortie des logs sur stdout
    ]
)
logger = logging.getLogger(__name__)

# Add local LightRAG source to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lightrag.lightrag import LightRAG, QueryParam
from lightrag.llm import gpt_4o_mini_complete, gpt_4o_complete
from lightrag.utils import EmbeddingFunc
from lightrag.prompt import PROMPTS
from lightrag.kg.mongo_impl import MongoKVStorage
from lightrag.kg.milvus_impl import MilvusVectorDBStorage

# Configuration Milvus - utiliser les valeurs de .env ou les valeurs par défaut
if not os.environ.get("MILVUS_URI"):
    os.environ["MILVUS_URI"] = "tcp://localhost:19530"

def init_lightrag():
    """
    Initialise LightRAG avec MongoDB, Neo4j et Milvus
    Utilise les variables d'environnement pour les connexions
    """
    working_dir = "./data"
    
    # Création du répertoire de travail s'il n'existe pas
    if not os.path.exists(working_dir):
        os.makedirs(working_dir)
        logger.debug(f"Répertoire de travail créé: {working_dir}")
    
    try:
        # Initialisation de LightRAG
        rag = LightRAG(
            working_dir=working_dir,
            llm_model_func=gpt_4o_mini_complete,
            enable_llm_cache=False,  # Désactive le cache ici
            kv_storage="MongoKVStorage",      # MongoDB pour le stockage clé-valeur
            vector_storage="MilvusVectorDBStorage",  # Milvus pour les vecteurs
            graph_storage="Neo4JStorage",     # Neo4j pour le graphe
            log_level="INFO"
        )
        logger.debug("LightRAG initialisé avec succès")
        return rag
    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation de LightRAG: {str(e)}")
        raise

def query_lightrag(
    question: str, 
    mode: str = "local", 
    node_filter: Optional[Union[str, List[str]]] = None, 
    verbose: bool = True,
    log_subgraph: bool = True
):
    """
    Interroge LightRAG avec une question
    
    Args:
        question (str): La question à poser
        mode (str): Mode de recherche ('naive', 'local', 'global', 'hybrid')
        node_filter (Optional[Union[str, List[str]]]): Filtre de nœuds (facultatif)
        verbose (bool): Mode verbeux pour plus de détails
        log_subgraph (bool): Logger les détails du sous-graphe courant
    
    Returns:
        str: La réponse générée
    """
    try:
        # Validation des arguments
        if not question:
            raise ValueError("La question ne peut pas être vide")
        
        if mode not in ["naive", "local", "global", "hybrid"]:
            raise ValueError(f"Mode non valide : {mode}")
        
        # Initialisation de LightRAG
        rag = init_lightrag()
        
        # Log détaillé si mode verbeux
        if verbose:
            logger.info(f" Détails de la requête :")
            logger.info(f"   Question : {question}")
            logger.info(f"   Mode : {mode}")
            logger.info(f"   Filtres de nœuds : {node_filter}")
        
        # Préparation des paramètres de requête
        query_param = QueryParam(mode=mode)
        
        # Log de débogage pour le filtrage
        if node_filter:
            logger.debug(f"Filtrage des nœuds : {node_filter}")
            # Convertir en liste si nécessaire
            node_filter_list = node_filter if isinstance(node_filter, list) else [node_filter]
            
            # Liste pour stocker les nœuds valides
            valid_nodes = []
            
            # Vérifier les nœuds disponibles
            if hasattr(rag.chunk_entity_relation_graph, 'has_node'):
                for node_id in node_filter_list:
                    try:
                        # Vérifier l'existence du nœud
                        node_exists = asyncio.run(rag.chunk_entity_relation_graph.has_node(node_id))
                        
                        if node_exists:
                            valid_nodes.append(node_id)
                            logger.debug(f"Nœud {node_id} existe et sera utilisé pour le filtrage")
                        else:
                            logger.warning(f"Nœud {node_id} non trouvé, ignoré pour le filtrage")
                    
                    except Exception as e:
                        logger.warning(f"Erreur lors de la vérification du nœud {node_id} : {e}")
            
            # Mettre à jour node_filter avec les nœuds valides
            node_filter = valid_nodes if valid_nodes else None
            
            # Log final des nœuds de filtrage
            if node_filter:
                logger.info(f"Filtrage final des nœuds : {node_filter}")
            else:
                logger.warning("Aucun nœud valide trouvé pour le filtrage")
        
        # Exécution de la requête asynchrone
        response = asyncio.run(rag.aquery(
            question, 
            param=query_param, 
            node_filter=node_filter
        ))
        
        # Logger les détails du sous-graphe si demandé
        if log_subgraph and hasattr(rag.chunk_entity_relation_graph, 'get_current_subgraph_details'):
            rag.chunk_entity_relation_graph.get_current_subgraph_details()
        
        # Log du résultat
        if verbose:
            logger.info(f" Longueur de la réponse : {len(response)} caractères")
        
        logger.info("Réponse générée avec succès")
        return response
    
    except Exception as e:
        logger.error(f" Erreur lors de la génération de la réponse : {e}")
        logger.debug(traceback.format_exc())  # Trace complète en mode debug
        raise

if __name__ == "__main__":
    try:
        # Rediriger stderr vers /dev/null pour supprimer les logs gRPC
        sys.stderr = open(os.devnull, 'w')
        
        # Configurer le parser d'arguments
        parser = argparse.ArgumentParser(description="Interroger LightRAG")
        
        # Arguments principaux
        parser.add_argument(
            "--question", 
            type=str, 
            default="Donne moi les informations pertinentes concernant Zulli pour reserver un diner au restaurant", 
            help="Question à poser"
        )
        parser.add_argument(
            "--mode", 
            type=str, 
            default="hybrid", 
            choices=["naive", "local", "global", "hybrid"], 
            help="Mode de recherche"
        )
        
        # Arguments de filtrage
        parser.add_argument(
            "--node-filter", 
            nargs='+', 
            help="Filtres de nœuds (mots-clés)"
        )
        
        # Options de débogage
        parser.add_argument(
            "-v", "--verbose", 
            action="store_true", 
            help="Activer le mode verbeux"
        )
        parser.add_argument(
            "--debug", 
            action="store_true", 
            help="Activer le mode débogage (logs détaillés)"
        )
        parser.add_argument(
            "--log-subgraph", 
            action="store_true", 
            help="Logger les détails du sous-graphe courant"
        )
        
        # Analyser les arguments
        args = parser.parse_args()
        
        # Configurer le logging en fonction des arguments
        if args.debug:
            logging.getLogger().setLevel(logging.DEBUG)
        
        # Exécuter la requête avec les arguments
        response = query_lightrag(
            question=args.question, 
            mode=args.mode, 
            node_filter=args.node_filter,
            verbose=args.verbose,
            log_subgraph=args.log_subgraph
        )
        
        print(f"\n Question: {args.question}")
        print(f"\n Réponse: {response}")
    
    except Exception as e:
        logger.error(f" Erreur fatale : {e}")
        sys.exit(1)
