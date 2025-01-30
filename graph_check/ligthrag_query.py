import os
import sys
import logging
import re
from typing import Dict, Any
import json
import aio_pika
import asyncio
from pathlib import Path
from dotenv import load_dotenv
import uuid
from datetime import datetime
import traceback
import time
from neo4j import GraphDatabase
import sshtunnel

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add local LightRAG source to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lightrag.lightrag import LightRAG, QueryParam
from lightrag.llm import gpt_4o_mini_complete, gpt_4o_complete
from lightrag.utils import EmbeddingFunc
from lightrag.prompt import PROMPTS
from lightrag.kg.mongo_impl import MongoKVStorage
from lightrag.kg.milvus_impl import MilvusVectorDBStorage


    
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
            kv_storage="MongoKVStorage",      # MongoDB pour le stockage clé-valeur
            vector_storage="MilvusVectorDBStorage",  # Milvus pour les vecteurs
            graph_storage="Neo4JStorage",     # Neo4j pour le graphe
            log_level="INFO",
            enable_llm_cache=False  # Ajout du paramètre ici
        )
        logger.debug("LightRAG initialisé avec succès")
        return rag
    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation de LightRAG: {str(e)}")
        raise

def query_lightrag(question: str, mode: str = "hybrid"):
    """
    Interroge LightRAG avec une question
    
    Args:
        question (str): La question à poser
        mode (str): Mode de recherche ('naive', 'local', 'global', 'hybrid')
    
    Returns:
        str: La réponse générée
    """
    try:
        rag = init_lightrag()
        logger.info(f"Question posée: {question}")
        response = rag.query(question, param=QueryParam(mode=mode))
        logger.info("Réponse générée avec succès")
        return response
    except Exception as e:
        logger.error(f"Erreur lors de la requête: {str(e)}")
        raise

async def debug_graph_integrity():
    import logging
    import traceback
    
    # Configuration du logging
    logging.basicConfig(level=logging.DEBUG, 
                        format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    
    try:
        # Initialisation de LightRAG avec des paramètres explicites
        rag = LightRAG(
            working_dir="./data",
            llm_model_func=gpt_4o_mini_complete,
            kv_storage="MongoKVStorage",
            vector_storage="MilvusVectorDBStorage",
            graph_storage="Neo4JStorage",
            log_level="DEBUG",
            enable_llm_cache=False
        )
        
        # Configuration SSH et Neo4j
        ssh_host = '51.77.200.196'
        ssh_username = 'ubuntu'
        neo4j_host = '10.1.77.8'  # IP interne du pod
        neo4j_port = 7687
        
        # Établir un tunnel SSH
        tunnel = sshtunnel.SSHTunnelForwarder(
            (ssh_host, 22),
            ssh_username=ssh_username,
            remote_bind_address=(neo4j_host, neo4j_port)
        )
        tunnel.start()
        
        # Configuration Neo4j via le tunnel
        uri = f"bolt://{tunnel.local_bind_host}:{tunnel.local_bind_port}"
        username = "neo4j"
        password = os.getenv('NEO4J_PASSWORD', 'my-initial-password')
        
        # Connexion à Neo4j
        driver = GraphDatabase.driver(uri, auth=(username, password))
        
        # Diagnostic détaillé des bords problématiques
        with driver.session() as session:
            def safe_run_query(query, description):
                """
                Exécute une requête Neo4j de manière sécurisée avec gestion des erreurs
                """
                try:
                    logger.info(f"Exécution de la requête : {description}")
                    result = session.run(query)
                    records = list(result)
                    logger.info(f"Nombre de résultats pour {description} : {len(records)}")
                    return records
                except Exception as e:
                    logger.error(f"Erreur lors de l'exécution de {description}: {e}")
                    logger.error(traceback.format_exc())
                    return []
            
            # Requête pour identifier les relations sans propriétés
            relations_without_properties_query = """
            MATCH (start)-[r]->(end)
            WHERE keys(r) = []
            RETURN 
                type(r) AS relation_type, 
                count(*) AS problematic_count,
                collect({
                    start_node: start.name,
                    start_labels: labels(start),
                    end_node: end.name,
                    end_labels: labels(end)
                }) AS sample_details
            LIMIT 100
            """
            
            # Requête pour identifier les relations avec des nœuds problématiques
            problematic_nodes_query = """
            MATCH (start)-[r]->(end)
            WHERE 
                start.name IS NULL OR 
                end.name IS NULL OR
                size(labels(start)) = 0 OR
                size(labels(end)) = 0
            RETURN 
                type(r) AS relation_type, 
                count(*) AS problematic_count,
                collect({
                    start_node: start.name,
                    start_labels: labels(start),
                    end_node: end.name,
                    end_labels: labels(end)
                }) AS sample_details
            LIMIT 100
            """
            
            # Requête pour identifier les relations avec des propriétés nulles
            null_property_relations_query = """
            MATCH (start)-[r]->(end)
            WHERE 
                r.type IS NULL OR 
                r.keywords IS NULL OR 
                r.weight IS NULL OR
                r.description IS NULL
            RETURN 
                type(r) AS relation_type, 
                count(*) AS problematic_count,
                collect({
                    start_node: start.name,
                    start_labels: labels(start),
                    end_node: end.name,
                    end_labels: labels(end),
                    relation_properties: keys(r)
                }) AS sample_details
            LIMIT 100
            """
            
            # Exécution des requêtes avec gestion des erreurs
            relations_without_properties = safe_run_query(relations_without_properties_query, "Relations sans propriétés")
            problematic_nodes_relations = safe_run_query(problematic_nodes_query, "Relations avec nœuds problématiques")
            null_property_relations = safe_run_query(null_property_relations_query, "Relations avec propriétés nulles")
            
            # Analyse des résultats
            def analyze_results(results, title):
                """
                Analyse et log des résultats de requête
                """
                logger.info(f"\n🔍 {title} :")
                for record in results:
                    try:
                        relation_type = record.get('relation_type', 'N/A')
                        problematic_count = record.get('problematic_count', 0)
                        sample_details = record.get('sample_details', [])
                        
                        logger.info(f"\nType de relation : {relation_type}")
                        logger.info(f"Nombre de relations problématiques : {problematic_count}")
                        
                        for sample in sample_details[:5]:  # Limiter à 5 échantillons
                            logger.info(f"  - Nœud de départ : {sample.get('start_node', 'N/A')} (labels: {sample.get('start_labels', [])})")
                            logger.info(f"  - Nœud d'arrivée : {sample.get('end_node', 'N/A')} (labels: {sample.get('end_labels', [])})")
                            if 'relation_properties' in sample:
                                logger.info(f"  - Propriétés de la relation : {sample.get('relation_properties', [])}")
                            logger.info("---")
                    except Exception as e:
                        logger.error(f"Erreur lors de l'analyse d'un enregistrement : {e}")
            
            # Analyser chaque ensemble de résultats
            analyze_results(relations_without_properties, "Relations sans propriétés")
            analyze_results(problematic_nodes_relations, "Relations avec nœuds problématiques")
            analyze_results(null_property_relations, "Relations avec propriétés nulles")
        
        driver.close()
        tunnel.close()
        return None
    
    except Exception as e:
        logger.error(f"Erreur globale lors du diagnostic : {e}")
        logger.error(traceback.format_exc())
        return None

# Exécution du diagnostic
async def main():
    await debug_graph_integrity()

if __name__ == "__main__":
    asyncio.run(main())

if __name__ == "__main__":
    try:
        # Exemple d'utilisation
        #question = "dis moi ce que tu sais sur lea"
        question = "trouver moi un restaurant qui dispose d'une ambiance chaleureuse et si possible des burgers"

        rag = init_lightrag()
        
        # Exemple d'utilisation avec filtrage
        # node_list = [{'custom_id': 'ZUlli'}]
        

        # Préparation des paramètres de requête
        mode="hybrid"
        query_param = QueryParam(mode=mode)
        
        #vdb_filter= [ "Zulli"]
        #vdb_filter= ["lea"]
        vdb_filter= []

        # Exécution asynchrone de la requête
        response = asyncio.run(rag.aquery(question, param=query_param, vdb_filter=vdb_filter))
        
        print(f"\nQuestion: {question}")
        print(f"\nRéponse: {response}")
    except Exception as e:
        print(f"An error occurred: {e}")