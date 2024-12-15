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

# Print DEFAULT_ENTITY_TYPES to verify local version
print("DEFAULT_ENTITY_TYPES:", PROMPTS["DEFAULT_ENTITY_TYPES"])

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
        """Traite un message reçu de RabbitMQ."""
        async with message.process():
            try:
                # Vérifier que LightRAG est initialisé
                if self.rag is None:
                    logger.error("LightRAG n'est pas initialisé")
                    self.initialize_rag()
                    if self.rag is None:
                        raise RuntimeError("Impossible d'initialiser LightRAG")

                # Décoder le message JSON
                body = message.body.decode()
                msg_data = json.loads(body)
                logger.info(f"Message brut reçu de RabbitMQ: {body}")
                
                # Extraire le CID et traiter le message
                cid = msg_data.get("cid")
                logger.info(f"Traitement du restaurant CID {cid}")
                
                # Traiter le résumé avec LightRAG
                resume = msg_data.get("resume", "")
                if resume:
                    logger.info(f"Début de l'insertion du document dans LightRAG pour le CID {cid}")
                    try:
                        await self.rag.ainsert(resume)
                        logger.info(f"Document inséré avec succès dans LightRAG pour le CID {cid}")
                    except Exception as e:
                        logger.error(f"Erreur lors de l'insertion dans LightRAG: {str(e)}")
                        logger.error(traceback.format_exc())
                        raise
                    
                    logger.info(f"Message traité avec succès pour le CID {cid}")
                else:
                    logger.warning(f"Résumé vide pour le CID {cid}")
                    
            except json.JSONDecodeError as e:
                logger.error(f"Erreur de décodage JSON: {str(e)}")
            except Exception as e:
                logger.error(f"Erreur inattendue dans process_message: {str(e)}")
                logger.error(traceback.format_exc())
                raise

    async def start(self):
        """Démarre la consommation des messages de manière asynchrone."""
        try:
            # Créer la connexion et le canal
            _, channel = await self._create_async_connection()
            
            # Configurer la queue
            queue = await channel.declare_queue(self.queue_name, durable=True)
            
            # Démarrer la consommation
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
                log_level="DEBUG",
            )
            logger.info("LightRAG initialisé avec succès")
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