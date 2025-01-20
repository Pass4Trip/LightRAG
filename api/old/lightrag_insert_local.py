import os
import sys
import logging
import re
from typing import Dict, Any
import json
import asyncio
from pathlib import Path
from dotenv import load_dotenv
import uuid
from datetime import datetime
import traceback
import time

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
from lightrag.kg.neo4j_impl import Neo4JStorage



# Configuration Milvus - utiliser les valeurs de .env ou les valeurs par défaut
if not os.environ.get("MILVUS_URI"):
    os.environ["MILVUS_URI"] = "tcp://localhost:19530"

def load_config():
    """
    Charge la configuration depuis différentes sources:
    1. Variables d'environnement (pour Kubernetes)
    2. Fichier .env local
    3. Valeurs par défaut
    """
    # Configuration par défaut
    defaults = {
        "RABBITMQ_USER": "guest",
        "RABBITMQ_HOST": "localhost",
        "RABBITMQ_PORT": "5672",
        "NEO4J_URI": "bolt://localhost:7687",
        "NEO4J_USERNAME": "neo4j",
        "VECTOR_DB_PATH": "./nano-vectorDB"
    }

    # Vérifier les variables sensibles requises
    required_secrets = [
        "RABBITMQ_PASSWORD",
        "NEO4J_PASSWORD"
    ]

    # Utiliser les variables d'environnement ou les valeurs par défaut
    config = {}
    
    # Charger les valeurs non-sensibles
    for key, default_value in defaults.items():
        config[key] = os.getenv(key, default_value)
        if not os.getenv(key):
            logger.debug(f"Utilisation de la valeur par défaut pour {key}: {default_value}")
    
    # Charger les secrets
    for secret in required_secrets:
        value = os.getenv(secret)
        if not value:
            raise RuntimeError(f"Variable d'environnement requise manquante : {secret}. "
                             f"Veuillez la définir dans votre fichier .env")
        config[secret] = value

    return config

class MessageProcessor:
    """
    Processeur de messages générique pour le traitement des données.
    Gère le traitement de différents types de messages sans dépendre de RabbitMQ.
    Supporte l'insertion de données dans LightRAG avec des métadonnées flexibles.
    """
    
    def __init__(self):
        # Charger la configuration
        self.config = load_config()
        
        # Configuration Neo4j
        os.environ["NEO4J_URI"] = self.config["NEO4J_URI"]
        os.environ["NEO4J_USERNAME"] = self.config["NEO4J_USERNAME"]
        os.environ["NEO4J_PASSWORD"] = self.config["NEO4J_PASSWORD"]

        # Initialiser le client OpenAI une seule fois
        self._initialize_openai()
        
        # Initialiser LightRAG
        self.rag = None
        self.initialize_rag()

    def _initialize_openai(self):
        """Initialise le client OpenAI une seule fois"""
        import openai
        openai.api_key = os.environ.get("OPENAI_API_KEY")

    def normalize_label(self, text: str) -> str:
        """Normalise un texte pour l'utiliser comme label."""
        return text.replace(" ", "_").upper()

    async def process_user_message(self, payload: dict):
        """
        Traite les messages de type 'user'
        
        Args:
            payload (dict): Charge utile du message
        """
        try:
            text = payload.get('user_info', '')
            user_id = payload.get('user_id')
            
            if not text:
                logger.warning("Message utilisateur vide")
                return
            
            # Insertion avec le prompt_domain et metadata
            await self.insert_to_lightrag(
                text, 
                prompt_domain='user',
                metadata={'user_id': user_id} if user_id else None
            )
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement du message utilisateur: {e}")
            logger.error(traceback.format_exc())

    async def process_activity_message(self, payload: dict):
        """
        Traite les messages de type 'activity'
        
        Args:
            payload (dict): Charge utile du message
        """
        try:
            resume = payload.get('resume')
            cid = payload.get('cid')
            city = payload.get('city')
            lat = payload.get('lat')
            lng = payload.get('lng')
            
            if not resume or not cid:
                logger.warning(f"Message activity incomplet: {payload}")
                return
            
            # Préparer les métadonnées
            metadata = {
                'cid': cid,
                'city': city,
                'custom_id': f"{cid}"  # Utiliser cid comme custom_id
            }
            
            # Ajouter les coordonnées si disponibles
            if lat is not None and lng is not None:
                metadata['lat'] = lat
                metadata['lng'] = lng
                logger.info(f"Coordonnées ajoutées pour l'activité : {lat}, {lng}")
            
            # Insertion avec le prompt_domain et metadata
            await self.insert_to_lightrag(
                resume, 
                prompt_domain='activity',
                metadata={
                    'cid': cid,
                    'city': city,
                    'custom_id': f"{cid}",
                    'lat': payload.get('lat'),
                    'lng': payload.get('lng')
                }
            )
        
        except Exception as e:
            logger.error(f"Erreur lors du traitement du message d'activité: {e}")
            logger.error(traceback.format_exc())


    async def process_event_message(self, payload: dict):
        """
        Traite les messages de type 'event'
        
        Args:
            payload (dict): Charge utile du message d'événement
        """
        try:
            # Extraction des attributs de l'événement
            event_id = payload.get('event_id')
            description = payload.get('description', 'Événement sans description')
            start_date = payload.get('start_date')
            end_date = payload.get('end_date')
            city = payload.get('city')
            
            if not event_id or not description:
                logger.warning(f"Message event incomplet: {payload}")
                return
            
            # Convertir l'ID en chaîne et le normaliser
            event_id_str = str(event_id)
            normalized_event_id = self.normalize_label(event_id_str)
            
            # Insertion avec le prompt_domain et metadata
            await self.insert_to_lightrag(
                description, 
                prompt_domain='event',
                metadata={
                    'event_id': normalized_event_id,
                    'start_date': start_date,
                    'end_date': end_date,
                    'city': city,
                    'custom_id': normalized_event_id  # Utiliser event_id normalisé comme custom_id
                }
            )
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement du message d'événement: {e}")
            logger.error(traceback.format_exc())

    async def process_memo_message(self, payload: dict):
        """
        Traite les messages de type 'memo'
        
        Args:
            payload (dict): Charge utile du message de mémo
        """
        try:
            # Extraction des attributs du mémo
            memo_id = payload.get('memo_id')
            description = payload.get('description', 'Mémo sans description')
            user_id = payload.get('user_id')  # Récupérer l'ID de l'utilisateur
            
            if not memo_id or not description:
                logger.warning(f"Message memo incomplet: {payload}")
                return
            
            # Convertir l'ID en chaîne et le normaliser
            memo_id_str = str(memo_id)
            normalized_memo_id = self.normalize_label(memo_id_str)
            
            # Normaliser l'ID utilisateur si présent
            normalized_user_id = self.normalize_label(str(user_id)) if user_id else None
            
            # Insertion avec le prompt_domain et metadata
            await self.insert_to_lightrag(
                description, 
                prompt_domain='memo',
                metadata={
                    'memo_id': normalized_memo_id,
                    'custom_id': normalized_memo_id,  # Utiliser memo_id normalisé comme custom_id
                    'user_id': normalized_user_id  # Ajouter l'ID utilisateur normalisé
                }
            )
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement du message de mémo: {e}")
            logger.error(traceback.format_exc())

    async def process_query_message(self, payload: dict):
        """
        Traite les messages de type 'query'
        
        Args:
            payload (dict): Dictionnaire contenant les informations de la requête
        """
        try:
            # Récupération du custom_id
            custom_id = payload.get('custom_id')
            if not custom_id:
                logger.warning("Aucun custom_id trouvé dans le message de query")
                return

            # Autres traitements existants
            user_id = payload.get('user_id', 'user_id_example')
            response = payload.get('response')
            timestamp = payload.get('timestamp')

            logger.info(f"Traitement de la query avec custom_id: {custom_id}")
            
            # Le reste du code de traitement reste inchangé
            metadata = {
                'custom_id': custom_id,
                'user_id': user_id,
                'timestamp': timestamp
            }

            # Insérer la query dans le système
            await self.insert_to_lightrag(
                response, 
                prompt_domain='query',
                metadata=metadata
            )

        except Exception as e:
            logger.error(f"Erreur lors du traitement du message de query: {e}")
            logger.error(traceback.format_exc())

    async def process_message(self, payload: dict):
        """
        Traite un message JSON brut sans retraitement
        
        :param message: Message JSON brut à traiter
        :return: Résultat du traitement du message
        """
        try:
            
            # Récupérer le type de message
            message_type = payload.get('type', 'activity')
            logger.info(f"Type de message reçu: {message_type}")
            logger.debug(f"Contenu du payload: {payload}")
            
            # Dispatcher vers le bon gestionnaire de message
            message_processors = {
                'user': self.process_user_message,
                'activity': self.process_activity_message,
                'event': self.process_event_message,
                'memo': self.process_memo_message,
                'query': self.process_query_message
            }
            
            # Utiliser le processeur correspondant ou par défaut 'activity'
            processor = message_processors.get(message_type, self.process_activity_message)
            
            return await processor(payload)
        
        except json.JSONDecodeError:
            logger.error(f"Impossible de décoder le message JSON : {message}")
            raise
        except Exception as e:
            logger.error(f"Erreur lors du traitement du message : {str(e)}")
            raise

    async def insert_to_lightrag(self, text: str, prompt_domain: str = 'activity', metadata: dict = None):
        """
        Méthode d'insertion asynchrone dans LightRAG
        
        :param text: Texte à insérer
        :param prompt_domain: Domaine du prompt
        :param metadata: Métadonnées optionnelles
        :return: Résultat de l'insertion
        """
        try:
            if not text:
                logger.warning("Tentative d'insertion d'un texte vide")
                return None
            
            # Insertion avec gestion des métadonnées
            result = await self.rag.ainsert(
                text, 
                prompt_domain=prompt_domain, 
                metadata=metadata or {}
            )
            
            return result
        
        except Exception as e:
            logger.error(f"Erreur lors de l'insertion dans LightRAG: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    def initialize_rag(self):
        """Initialise LightRAG avec la configuration appropriée."""
        try:
            # Définir la base de données Milvus si non définie
            if not os.environ.get("MILVUS_DB_NAME"):
                os.environ["MILVUS_DB_NAME"] = "lightrag"
            
            # Initialiser LightRAG avec le répertoire de travail actuel
            working_dir = str(Path(__file__).parent)
            
            # Initialiser LightRAG
            self.rag = LightRAG(
                working_dir=working_dir,
                llm_model_func=gpt_4o_mini_complete,
                kv_storage="MongoKVStorage",
                vector_storage="MilvusVectorDBStorage",
                graph_storage="Neo4JStorage",
                log_level="DEBUG",
            )
            logger.debug("LightRAG initialisé avec succès")
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation de LightRAG: {str(e)}")
            logger.error(traceback.format_exc())
            self.rag = None

from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import uvicorn



# Créer l'application FastAPI
app = FastAPI(title="LightRAG Insert API")

# Créer une instance du processeur de messages
message_processor = MessageProcessor()


@app.post("/insert")
async def insert_message(payload: Dict[str, Any]):
    """
    Endpoint pour insérer un message dans LightRAG

    Args:
        payload (Dict[str, Any]): Données JSON à traiter

    Returns:
        Dict[str, Any]: Résultat de l'insertion

    Raises:
        HTTPException: En cas d'erreur lors du traitement
    """
    try:

        # Insérer le message dans LightRAG
        # Logging des données reçues
        logger.info(f"Données reçues : {payload}")
        
        result = await message_processor.process_message(payload)

        return {
            "status": "success",
            "result": result
        }

    except Exception as e:
        logger.error(f"Erreur lors de l'insertion du message : {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # Lancement du serveur
    uvicorn.run(
        "lightrag_insert:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True
    )