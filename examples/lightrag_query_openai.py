import os
from dotenv import load_dotenv
from pathlib import Path
import sys

# Add local LightRAG source to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lightrag.lightrag import LightRAG, QueryParam
from lightrag.llm import gpt_4o_mini_complete


import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Chargement des variables d'environnement
load_dotenv()

def init_lightrag():
    """
    Initialise LightRAG avec MongoDB, Neo4j et Milvus
    Utilise les variables d'environnement pour les connexions
    """
    working_dir = "./data"
    
    # Création du répertoire de travail s'il n'existe pas
    if not os.path.exists(working_dir):
        os.makedirs(working_dir)
        logger.info(f"Répertoire de travail créé: {working_dir}")
    
    try:
        # Initialisation de LightRAG
        rag = LightRAG(
            working_dir=working_dir,
            llm_model_func=gpt_4o_mini_complete,
            kv_storage="MongoKVStorage",      # MongoDB pour le stockage clé-valeur
            vector_storage="MilvusVectorDBStorage",  # Milvus pour les vecteurs
            graph_storage="Neo4JStorage",     # Neo4j pour le graphe
            log_level="INFO"
        )
        logger.info("LightRAG initialisé avec succès")
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

if __name__ == "__main__":
    try:
        # Exemple d'utilisation
        #question = "Quels sont les restaurants avec une bonne accessibilité PMR?"
        #question = "Sais tu si je dois proposer à Vinh une nouvelle offre de voyager dédié au jeu de moins de 25 ans ?" 
        question = "Liste moi ce que tu sais sur Vinh qui me permettra de lui proposer la meilleur activté le week end prochain" 
        response = query_lightrag(question)
        print(f"\nQuestion: {question}")
        print(f"\nRéponse: {response}")
    except Exception as e:
        logger.error(f"Erreur dans le programme principal: {str(e)}")
