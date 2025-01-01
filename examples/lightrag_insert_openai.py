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
        "RABBITMQ_USERNAME": "guest",
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

class RabbitMQConsumer:
    """
    Consommateur RabbitMQ asynchrone pour le traitement des données de restaurants.
    Cette classe gère la connexion à RabbitMQ, la réception des messages,
    et l'insertion des données dans LightRAG avec intégration Neo4j.
    """
    
    def __init__(self):
        # Charger la configuration
        self.config = load_config()
        self.user = self.config["RABBITMQ_USERNAME"]
        self.password = self.config["RABBITMQ_PASSWORD"]
        self.host = self.config["RABBITMQ_HOST"]
        self.port = self.config["RABBITMQ_PORT"]

        # Configuration Neo4j
        os.environ["NEO4J_URI"] = self.config["NEO4J_URI"]
        os.environ["NEO4J_USERNAME"] = self.config["NEO4J_USERNAME"]
        os.environ["NEO4J_PASSWORD"] = self.config["NEO4J_PASSWORD"]

        self.queue_name = "queue_vinh_test"
        
        # Initialiser le client OpenAI une seule fois
        self._initialize_openai()

        # Initialiser les connexions
        self.connection = None
        self.channel = None
        self.milvus_connection = None
        
        # Initialiser LightRAG
        self.rag = None
        self.initialize_rag()

    def _initialize_openai(self):
        """Initialise le client OpenAI une seule fois"""
        import openai
        openai.api_key = os.environ.get("OPENAI_API_KEY")

    def normalize_label(self, text: str) -> str:
        """Normalise un texte pour l'utiliser comme label Neo4j."""
        # Remplacer les espaces par des underscores et convertir en majuscules
        return text.replace(" ", "_").upper()

    async def _create_async_connection(self):
        """Crée une nouvelle connexion et un nouveau canal de manière asynchrone."""
        if self.connection is None or self.connection.is_closed:
            self.connection = await aio_pika.connect_robust(
                f"amqp://{self.user}:{self.password}@{self.host}:{self.port}/"
            )
        if self.channel is None or self.channel.is_closed:
            self.channel = await self.connection.channel()
            await self.channel.set_qos(prefetch_count=1)
            await self.channel.declare_queue(self.queue_name, durable=True)
        return self.connection, self.channel

    async def process_message(self, message: aio_pika.IncomingMessage):
        """Traite les messages de différents types de manière flexible"""
        logger.info(f"🔍 Début du traitement du message")
        logger.debug(f"🔍 Début du traitement du message: {message}")
        
        async with message.process():
            try:
                # Décodage du message
                body = message.body.decode()
                logger.debug(f"📨 Corps du message décodé: {body}")
                
                payload = json.loads(body)
                logger.debug(f"📦 Payload reçu: {payload}")
                
                # Validation du type de message
                message_type = payload.get('type')
                if not message_type:
                    logger.warning(f"❗ Message sans type: {payload}")
                    return
                
                logger.debug(f"🏷️ Type de message détecté: {message_type}")
                
                # Dictionnaire de stratégies de traitement
                message_handlers = {
                    'activity': self.process_activity_message,
                    'user': self.process_user_message,
                    'event': self.process_event_message,
                    'memo': self.process_memo_message
                }
                
                # Récupération et exécution du gestionnaire approprié
                handler = message_handlers.get(message_type)
                if handler:
                    logger.debug(f"🚀 Démarrage du traitement pour le type {message_type}")
                    await handler(payload)
                    logger.debug(f"✅ Traitement terminé pour le type {message_type}")
                else:
                    logger.warning(f"❌ Type de message non géré : {message_type}")
            
            except json.JSONDecodeError:
                logger.error(f"❌ Erreur de décodage JSON: {message.body}")
            except Exception as e:
                logger.error(f"❌ Erreur lors du traitement du message: {e}", exc_info=True)
            finally:
                logger.info("🏁 Fin du traitement du message")

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
            
            if not resume or not cid:
                logger.warning(f"Message activity incomplet: {payload}")
                return
            
            # Insertion avec le prompt_domain et metadata
            await self.insert_to_lightrag(
                resume, 
                prompt_domain='activity',
                metadata={
                    'cid': cid,
                    'city': city,
                    'custom_id': f"{cid}"  # Utiliser cid comme custom_id
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

    async def insert_to_lightrag(self, text: str, prompt_domain: str = 'activity', metadata: dict = None):
        """
        Méthode d'insertion dans LightRAG
        
        Args:
            text (str): Texte à insérer
            prompt_domain (str, optional): Domaine du prompt. Defaults to 'activity'.
            metadata (dict, optional): Métadonnées associées au texte. Defaults to None.
        """
        try:
            if self.rag is None:
                logger.error("LightRAG n'est pas initialisé")
                return
            
            logger.debug(f"Insertion dans LightRAG avec le domaine: {prompt_domain}")
            await self.rag.ainsert(text, prompt_domain=prompt_domain, metadata=metadata)
            
        except Exception as e:
            logger.error(f"Erreur lors de l'insertion dans LightRAG: {e}")
            logger.error(traceback.format_exc())

    async def consume(self):
        """
        Consomme les messages de la file d'attente RabbitMQ avec un timeout
        """
        try:
            # Créer la connexion et le canal si nécessaire
            await self.connect()
            
            # Déclarer la file d'attente
            queue = await self.channel.declare_queue(self.queue_name, auto_delete=False)
            
            logger.info(f"🔄 Démarrage de la consommation de la file {self.queue_name}")
            
            async with queue.iterator() as queue_iter:
                async for message in queue_iter:
                    try:
                        logger.debug(f"📥 Message reçu de la file {self.queue_name}")
                        await self.process_message(message)
                    except Exception as e:
                        logger.error(f"❌ Erreur lors du traitement du message: {e}", exc_info=True)
                        # Rejeter le message en cas d'erreur
                        await message.reject(requeue=False)
        
        except asyncio.CancelledError:
            logger.warning("🛑 Consommation annulée")
        except Exception as e:
            logger.error(f"❌ Erreur dans la consommation des messages: {e}", exc_info=True)
        finally:
            logger.info("🏁 Fin de la consommation des messages")
            # Fermer la connexion si nécessaire
            if hasattr(self, 'connection') and self.connection:
                await self.connection.close()

    async def start(self):
        """Démarre la consommation des messages de manière asynchrone."""
        try:
            # Créer la connexion et le canal
            _, channel = await self._create_async_connection()
            
            # Configurer la queue
            queue = await channel.declare_queue(self.queue_name, durable=True)
            
            logger.info("En attente de messages. Pour quitter, appuyez sur CTRL+C")
            await queue.consume(self.process_message)
            
            # Maintenir la connexion active
            try:
                await asyncio.Future()  # run forever
            except asyncio.CancelledError:
                pass
            
        except Exception as e:
            logger.error(f"Erreur lors de la consommation des messages: {e}")
            logger.error(traceback.format_exc())
            raise e
        finally:
            await self.close()

    async def close(self):
        """Ferme proprement toutes les connexions."""
        try:
            if self.rag:
                self.rag.close()
            
            if self.channel:
                await self.channel.close()
            
            if self.connection:
                await self.connection.close()
                
        except Exception as e:
            logger.error(f"Erreur lors de la fermeture des ressources: {e}")

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
                log_level="INFO",
            )
            logger.debug("LightRAG initialisé avec succès")
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation de LightRAG: {str(e)}")
            logger.error(traceback.format_exc())
            self.rag = None

if __name__ == "__main__":
    # Configuration du logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Créer le consommateur
    consumer = RabbitMQConsumer()
    
    async def main():
        try:
            await consumer.start()
        except KeyboardInterrupt:
            logger.info("Arrêt demandé par l'utilisateur")
        except Exception as e:
            logger.error(f"Erreur lors de l'exécution du consommateur: {e}")
            logger.error(traceback.format_exc())
        finally:
            await consumer.close()
    
    # Exécuter la fonction principale
    asyncio.run(main())