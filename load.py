import os
import sys
import logging
import re
from typing import Dict, Any
import json
import pika
import asyncio
from pathlib import Path
from dotenv import load_dotenv
import uuid
from datetime import datetime

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

# Print DEFAULT_ENTITY_TYPES to verify local version
print("DEFAULT_ENTITY_TYPES:", PROMPTS["DEFAULT_ENTITY_TYPES"])

# Configuration Milvus
os.environ["MILVUS_URI"] = "tcp://localhost:19530"
os.environ["MILVUS_DB_NAME"] = "lightrag"

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
        config = load_config()
        self.user = config["RABBITMQ_USERNAME"]
        self.password = config["RABBITMQ_PASSWORD"]
        self.host = config["RABBITMQ_HOST"]
        self.port = config["RABBITMQ_PORT"]

        # Configuration Neo4j
        os.environ["NEO4J_URI"] = config["NEO4J_URI"]
        os.environ["NEO4J_USERNAME"] = config["NEO4J_USERNAME"]
        os.environ["NEO4J_PASSWORD"] = config["NEO4J_PASSWORD"]

        self.connection = None
        self.channel = None
        self.rag = None
        self.queue_name = "queue_vinh_test"

    def initialize_rag(self):
        """
        Initialise l'instance LightRAG avec les configurations nécessaires.
        """
        # Utiliser un chemin absolu pour le dossier de travail
        working_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "lightrag_storage"))
        
        if not os.path.exists(working_dir):
            os.makedirs(working_dir)
            logger.info(f"Dossier de travail créé : {working_dir}")

        self.rag = LightRAG(
            working_dir=working_dir,
            llm_model_func=gpt_4o_mini_complete,
            kv_storage="MongoKVStorage",
            vector_storage="MilvusVectorDBStorage",
            graph_storage="Neo4JStorage",
            log_level="DEBUG",
        )
        logger.info("DEBUG: LightRAG initialisé avec succès")

    def normalize_label(self, text: str) -> str:
        """Normalise un texte pour l'utiliser comme label Neo4j."""
        # Remplacer les espaces par des underscores et convertir en majuscules
        return text.replace(" ", "_").upper()

    def connect(self):
        """Établit la connexion à RabbitMQ de manière synchrone."""
        try:
            # Initialiser LightRAG
            self.initialize_rag()
            
            # Créer la connexion
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=self.host, port=self.port, credentials=pika.PlainCredentials(self.user, self.password))
            )
            
            # Créer le canal
            self.channel = self.connection.channel()
            
            # Déclarer la queue
            self.channel.queue_declare(queue=self.queue_name, durable=True)
            
            logger.info(f"Connexion RabbitMQ établie sur {self.host}:{self.port}")
        
        except Exception as e:
            logger.error(f"Erreur lors de la connexion à RabbitMQ: {str(e)}")
            raise

    async def process_message(self, ch, method, properties, body):
        """Traite de manière asynchrone un message reçu de RabbitMQ."""
        try:

            # Log du message brut reçu
            logger.info(f"Message brut reçu de RabbitMQ: {body.decode('utf-8')}")
                        
            # Décoder le message JSON
            data = json.loads(body)
            restaurant_resume = data.get('resume', {})
            restaurant_cid = data.get('cid', 'CID Unknown')
            
            logger.info(f"Traitement du restaurant CID {restaurant_cid}")
            

            try:
                logger.info("DEBUG: Début de l'insertion avec LightRAG")
                
                # Ajouter le texte à LightRAG et extraire les entités
                result = await self.rag.ainsert(restaurant_resume)
                
                logger.info(f"DEBUG: Résultat de l'insertion: {result}")
                logger.info(f"DEBUG: Insertion et extraction d'entités réussies pour {restaurant_cid}")
                
                # Acquitter le message
                ch.basic_ack(delivery_tag=method.delivery_tag)
            
            except Exception as lightrag_err:
                logger.error(f"DEBUG: Erreur lors de l'insertion/extraction avec LightRAG: {lightrag_err}")
                import traceback
                logger.error(traceback.format_exc())
                
                # Rejeter le message pour un traitement ultérieur
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
        
        except Exception as e:
            logger.error(f"DEBUG: Erreur inattendue dans process_message: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            # Rejeter le message en cas d'erreur inattendue
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    def start_consuming(self):
        """Commence à consommer des messages de manière synchrone."""
        try:
            # Configurer la consommation des messages
            self.channel.basic_qos(prefetch_count=1)
            
            # Définir la fonction de callback
            def on_message(ch, method, properties, body):
                # Créer une tâche asynchrone pour chaque message
                asyncio.run(self.process_message(ch, method, properties, body))
            
            # Configurer la consommation
            self.channel.basic_consume(
                queue=self.queue_name,
                on_message_callback=on_message,
                auto_ack=False  # Désactiver l'acquittement automatique
            )
            
            logger.info(f"DEBUG: En attente de messages sur {self.queue_name}")
            
            # Démarrer la consommation
            self.channel.start_consuming()
        
        except Exception as e:
            logger.error(f"DEBUG: Erreur lors de la consommation des messages: {e}")
            import traceback
            logger.error(traceback.format_exc())

    def close(self):
        """Ferme proprement la connexion RabbitMQ."""
        if self.connection:
            self.connection.close()

if __name__ == "__main__":
    # Configuration du logging
    logging.basicConfig(
        level=logging.INFO, 
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Créer le consommateur
    consumer = RabbitMQConsumer()
    
    def main():
        try:
            # Établir la connexion
            consumer.connect()
            
            # Démarrer la consommation des messages
            consumer.start_consuming()
        
        except Exception as e:
            logger.error(f"Erreur lors de l'exécution du consommateur: {e}")
            import traceback
            logger.error(traceback.format_exc())
        finally:
            # Fermer la connexion
            consumer.close()
    
    # Exécuter la fonction principale
    main()