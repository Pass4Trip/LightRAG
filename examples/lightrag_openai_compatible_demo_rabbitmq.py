import os
from prefect.settings import PREFECT_API_URL
from prefect.blocks.core import Block
from pydantic import SecretStr
import asyncio
from lightrag import LightRAG, QueryParam
from lightrag.llm import openai_complete_if_cache, openai_embedding
from lightrag.utils import EmbeddingFunc
import numpy as np
import requests
import pika
import json
import time
from typing import Dict, Any, Optional
from tenacity import retry, stop_after_attempt, wait_exponential, before_sleep_log, retry_if_exception_type
import logging
from requests.exceptions import HTTPError, RequestException, Timeout
import yaml

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Block definitions
class RabbitMQCredentials(Block):
    """Stores RabbitMQ credentials"""
    username: str
    password: SecretStr
    host: str
    port: str

class Neo4jCredentials(Block):
    """Stores Neo4j credentials"""
    uri: str
    username: str
    password: SecretStr

class OVHCredentials(Block):
    """Stores OVH credentials"""
    llm_api_token: SecretStr

# Load Prefect worker configuration
def load_prefect_config():
    """
    Charge la configuration Prefect en fonction de l'environnement d'exécution.
    Supporte deux modes :
    1. VPS OVH : utilise le fichier YAML
    2. Local : utilise les variables d'environnement
    """
    # Chemins possibles pour le fichier de configuration
    config_paths = [
        '/home/ubuntu/value_prefect_worker.yaml',  # Chemin VPS
        os.path.expanduser('~/.config/prefect/value_prefect_worker.yaml'),  # Chemin local
        'value_prefect_worker.yaml'  # Chemin relatif
    ]
    
    # Essayer de charger depuis YAML
    for config_path in config_paths:
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    worker_config = yaml.safe_load(f)
                    logger.info(f"Configuration chargée depuis {config_path}")
                    return (
                        worker_config['worker']['cloudApiConfig']['accountId'],
                        worker_config['worker']['cloudApiConfig']['workspaceId']
                    )
        except Exception as e:
            logger.debug(f"Impossible de charger {config_path}: {e}")
            continue
    
    # Si aucun fichier YAML n'est trouvé, utiliser les variables d'environnement
    logger.warning("Utilisation des variables d'environnement")
    account_id = os.getenv("PREFECT_ACCOUNT_ID")
    workspace_id = os.getenv("PREFECT_WORKSPACE_ID")
    
    if not all([account_id, workspace_id]):
        raise RuntimeError(
            "Configuration Prefect non trouvée. Vous devez soit :\n"
            "1. Avoir un fichier value_prefect_worker.yaml dans un des chemins suivants :\n"
            f"   {', '.join(config_paths)}\n"
            "2. Définir les variables d'environnement PREFECT_ACCOUNT_ID et PREFECT_WORKSPACE_ID"
        )
    
    return account_id, workspace_id

# Charger la configuration
PREFECT_ACCOUNT_ID, PREFECT_WORKSPACE_ID = load_prefect_config()

os.environ["PREFECT_API_URL"] = f"https://api.prefect.cloud/api/accounts/{PREFECT_ACCOUNT_ID}/workspaces/{PREFECT_WORKSPACE_ID}"
PREFECT_PROFILE='cloud'

# Load credentials from Prefect blocks
neo4j_block = Neo4jCredentials.load("neo4j-credentials")
ovh_block = OVHCredentials.load("ovh-credentials")
rabbitmq_block = RabbitMQCredentials.load("rabbitmq-credentials")

# Set environment variables for Neo4J
os.environ["NEO4J_URI"] = neo4j_block.uri
os.environ["NEO4J_USERNAME"] = neo4j_block.username
os.environ["NEO4J_PASSWORD"] = neo4j_block.password.get_secret_value()

# Set environment variables for OVH
os.environ["OVH_AI_ENDPOINTS_ACCESS_TOKEN"] = ovh_block.llm_api_token.get_secret_value()

# Get storage path
WORKING_DIR = os.getenv('VECTOR_DB_PATH', './nano-vectorDB')

# Create working directory if it doesn't exist
if not os.path.exists(WORKING_DIR):
    os.makedirs(WORKING_DIR, exist_ok=True)


class RabbitMQConsumer:
    """
    Consommateur RabbitMQ pour le traitement des données de restaurants.
    Cette classe gère la connexion à RabbitMQ, la réception des messages,
    et l'insertion des données dans LightRAG avec intégration Neo4j.

    Attributes:
        user (str): Nom d'utilisateur RabbitMQ
        password (str): Mot de passe RabbitMQ
        host (str): Hôte du serveur RabbitMQ
        port (int): Port du serveur RabbitMQ
        connection: Connexion RabbitMQ
        channel: Canal RabbitMQ
        rag: Instance de LightRAG
        max_retries (int): Nombre maximum de tentatives de reconnexion
        current_retry_count (int): Compteur de tentatives actuelles
        consecutive_500_errors (int): Compteur d'erreurs 500 consécutives
        max_consecutive_500_errors (int): Nombre maximum d'erreurs 500 autorisées
        backoff_factor (float): Facteur de temporisation pour les tentatives
    """

    def __init__(self):
        """Initialise le consommateur RabbitMQ avec les paramètres de connexion par défaut."""

        # Charger les credentials depuis le bloc Prefect
        rabbitmq_block = RabbitMQCredentials.load("rabbitmq-credentials")        

        # Utiliser les valeurs de l'instance chargée
        self.user = rabbitmq_block.username
        self.password = rabbitmq_block.password.get_secret_value()
        self.host = rabbitmq_block.host
        self.port = rabbitmq_block.port
        self.connection = None
        self.channel = None
        self.rag = None
        self.max_retries = 3
        self.current_retry_count = 0
        self.consecutive_500_errors = 0
        self.max_consecutive_500_errors = 5
        self.backoff_factor = 1.5        

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=2, min=10, max=30),
        before_sleep=before_sleep_log(logger, logging.INFO)
    )
    async def call_llm_api(self, url: str, payload: dict, headers: dict) -> dict:
        """Appelle l'API LLM avec retry en cas d'erreur"""
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur API LLM: {str(e)}")
            if response.status_code == 500:
                logger.info("Erreur 500 détectée, attente avant retry...")
                await asyncio.sleep(5)  # Attente supplémentaire pour les erreurs 500
            raise

    @retry(
        stop=stop_after_attempt(7),  # Increased max attempts
        wait=wait_exponential(multiplier=3, min=15, max=60),  # Increased wait times
        retry=retry_if_exception_type((HTTPError, Timeout)),
        before_sleep=before_sleep_log(logger, logging.INFO)
    )
    async def call_embedding_api(self, url: str, text: str, headers: dict) -> np.ndarray:
        """Appelle l'API d'embedding avec retry en cas d'erreur"""
        try:
            # Calculate dynamic timeout based on consecutive errors
            timeout = 30 * (self.backoff_factor ** self.consecutive_500_errors)
            
            # Add request ID for tracking
            request_id = os.urandom(8).hex()
            logger.info(f"Starting embedding request {request_id}")
            
            response = requests.post(url, data=text, headers=headers, timeout=timeout)
            
            if response.status_code == 500:
                self.consecutive_500_errors += 1
                logger.warning(f"HTTP 500 error (consecutive: {self.consecutive_500_errors})")
                
                if self.consecutive_500_errors >= self.max_consecutive_500_errors:
                    logger.error("Circuit breaker triggered: too many consecutive 500 errors")
                    raise Exception("Circuit breaker open: API service appears to be down")
                
                # Calculate adaptive sleep time
                sleep_time = 5 * (self.backoff_factor ** self.consecutive_500_errors)
                logger.info(f"Backing off for {sleep_time:.1f} seconds")
                await asyncio.sleep(sleep_time)
                
                raise HTTPError(f"HTTP 500 error on request {request_id}")
            
            response.raise_for_status()
            self.consecutive_500_errors = 0  # Reset on success
            return response.json()
            
        except Timeout:
            logger.error("Request timed out")
            raise
        except HTTPError as e:
            if e.response is not None:
                logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            raise

    async def initialize_rag(self):
        """
        Initialise l'instance LightRAG avec les configurations nécessaires.
        
        Cette méthode configure :
        1. Le modèle LLM et ses paramètres
        2. La fonction d'embedding et ses paramètres
        3. Le stockage vectoriel
        4. L'intégration Neo4j
        
        Returns:
            LightRAG: Instance configurée de LightRAG
            
        Note:
            Utilise les variables d'environnement pour la configuration Neo4j
        """
        async def llm_model_func(
            prompt, system_prompt=None, history_messages=[], **kwargs
        ) -> str:
            url = "https://llama-3-1-70b-instruct.endpoints.kepler.ai.cloud.ovh.net/api/openai_compat/v1/chat/completions"
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.extend(history_messages)
            messages.append({"role": "user", "content": prompt})
            
            payload = {
                "max_tokens": kwargs.get("max_tokens", 512),
                "messages": messages,
                "model": "Meta-Llama-3_1-70B-Instruct",
                "temperature": kwargs.get("temperature", 0),
            }
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {os.getenv('OVH_AI_ENDPOINTS_ACCESS_TOKEN')}",
            }
            
            response_data = await self.call_llm_api(url, payload, headers)
            return response_data["choices"][0]["message"]["content"]

        async def embedding_func(texts: list[str]) -> np.ndarray:
            url = "https://multilingual-e5-base.endpoints.kepler.ai.cloud.ovh.net/api/text2vec"
            headers = {
                "Content-Type": "text/plain",
                "Authorization": f"Bearer {os.getenv('OVH_AI_ENDPOINTS_ACCESS_TOKEN')}",
            }
            
            embeddings = []
            for text in texts:
                embedding = await self.call_embedding_api(url, text, headers)
                embeddings.append(embedding)
            
            return np.array(embeddings)

         # Initialiser LightRAG
        rag = LightRAG(
            working_dir=WORKING_DIR,
            llm_model_func=llm_model_func,
            embedding_func=EmbeddingFunc(
                embedding_dim=768,  # Updated for multilingual-e5-base model
                max_token_size=8192,
                func=embedding_func
            ),
            kg="Neo4JStorage",
            log_level="INFO",
        )
        return rag

    def normalize_label(self, text: str) -> str:
        """
        Normalise un texte pour l'utiliser comme label Neo4j.
        
        Cette fonction effectue les transformations suivantes :
        1. Remplace les espaces par des underscores
        2. Supprime les caractères spéciaux et accents
        3. Convertit en majuscules
        
        Args:
            text (str): Le texte à normaliser
            
        Returns:
            str: Le texte normalisé utilisable comme label Neo4j
            
        Example:
            >>> normalize_label("Café & Restaurant")
            "CAFE_RESTAURANT"
        """
        # Remplacer les espaces par des underscores
        text = text.replace(' ', '_')
        # Supprimer les caractères spéciaux et accents
        text = ''.join(c for c in text if c.isalnum() or c == '_')
        # Convertir en majuscules
        return text.upper()

    def prepare_document(self, restaurant_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prépare un document formaté à partir des données du restaurant.
        
        Cette fonction :
        1. Normalise le nom du restaurant pour l'utiliser comme label
        2. Normalise les tags pour les utiliser comme labels
        3. Structure les données pour l'insertion dans Neo4j
        
        Args:
            restaurant_data (Dict[str, Any]): Données brutes du restaurant contenant :
                - name: Nom du restaurant
                - id: Identifiant unique
                - description: Description du restaurant
                - address: Adresse
                - tags: Liste des tags/catégories
                - reviews: Liste des avis
                
        Returns:
            Dict[str, Any]: Document structuré pour LightRAG avec :
                - title: Nom du restaurant
                - id: Identifiant unique
                - content: Contenu détaillé
                - metadata: Labels et relations pour Neo4j
        """
        # Normaliser le nom du restaurant pour l'utiliser comme label
        restaurant_name = restaurant_data.get('name', 'Unknown')
        restaurant_label = self.normalize_label(restaurant_name)
        
        # Normaliser les tags pour les utiliser comme labels
        labels = [self.normalize_label(tag) for tag in restaurant_data.get('tags', [])]
        labels.append(restaurant_label)  # Ajouter le nom du restaurant comme label
        
        # S'assurer que tous les labels sont uniques
        labels = list(set(labels))
        
        # Créer le document avec les propriétés normalisées
        document = {
            "title": restaurant_name,
            "id": str(restaurant_data.get('id', 'Unknown')),
            "content": {
                "name": restaurant_name,
                "address": restaurant_data.get('address', 'Unknown'),
                "cuisine_types": restaurant_data.get('tags', []),
                "reviews": restaurant_data.get('reviews', [])
            },
            "metadata": {
                "labels": labels,
                "source": "restaurant_database",
                "relationships": [
                    {
                        "source_label": restaurant_label,
                        "target_label": self.normalize_label(tag),
                        "type": "HAS_TAG",
                        "properties": {
                            "weight": 1.0
                        }
                    } for tag in restaurant_data.get('tags', [])
                ]
            }
        }
        
        return document

    async def process_message(self, ch, method, properties, body):
        """
        Traite un message reçu de RabbitMQ de manière asynchrone.
        
        Cette méthode :
        1. Décode le message JSON
        2. Extrait les données du restaurant
        3. Prépare le document pour LightRAG
        4. Insère le document via ainsert()
        
        Args:
            ch: Canal RabbitMQ
            method: Méthode de livraison RabbitMQ
            properties: Propriétés du message
            body: Corps du message en JSON
            
        Raises:
            Exception: En cas d'erreur lors du traitement du message
        """
        try:
            # Décoder le message JSON
            data = json.loads(body)
            restaurant_data = data.get('restaurant', {})
            restaurant_id = restaurant_data.get('id', 'Unknown')
            restaurant_title = restaurant_data.get('title', 'Unknown')
            logger.info(f"Traitement du restaurant {restaurant_title} (ID: {restaurant_id})")
            
            # Préparer le document pour LightRAG
            document = self.prepare_document({
                'id': restaurant_id,
                'name': restaurant_title,
                'description': restaurant_data.get('description'),
                'address': restaurant_data.get('address'),
                'price': restaurant_data.get('price'),
                'tags': [restaurant_data.get('categoryname', 'Restaurant')],
                'reviews': data.get('reviews', [])
            })
            
            # Ajouter le document à LightRAG
            if self.rag is None:
                self.rag = await self.initialize_rag()
            
            await self.rag.ainsert(document)
            logger.info(f"Document ajouté avec succès pour le restaurant {restaurant_title}")
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement du message: {str(e)}", exc_info=True)
            raise

    def connect(self):
        retry_count = 0
        while retry_count < self.max_retries:
            try:
                credentials = pika.PlainCredentials(
                    self.user,
                    self.password
                )
                parameters = pika.ConnectionParameters(
                    host=self.host,
                    port=self.port,
                    credentials=credentials
                )
                self.connection = pika.BlockingConnection(parameters)
                self.channel = self.connection.channel()
                logger.info(f"Connexion RabbitMQ établie sur {self.host}:{self.port}")
                return
            except Exception as e:
                retry_count += 1
                if retry_count == self.max_retries:
                    raise Exception(f"Échec de connexion à RabbitMQ après {self.max_retries} tentatives: {str(e)}")
                logger.error(f"Tentative {retry_count}/{self.max_retries} échouée, nouvelle tentative...")
    
    def close(self):
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            logger.info("Connexion RabbitMQ fermée")

    def start_consuming(self, queue_name: str = "queue_vinh_test"):
        """
        Démarre la consommation des messages de la queue.
        
        Cette méthode configure la queue, déclare les paramètres de consommation,
        et lance la consommation des messages.
        
        Args:
            queue_name (str): Nom de la queue à consommer
            
        Raises:
            Exception: En cas d'erreur lors de la consommation
        """
        try:
            # Créer un nouveau canal si nécessaire
            if self.channel is None or self.channel.is_closed:
                self.channel = self.connection.channel()
            
            # Déclarer la queue comme durable
            try:
                queue_info = self.channel.queue_declare(
                    queue=queue_name,
                    durable=True,
                    passive=False  # Permet de créer la queue si elle n'existe pas
                )
                logger.info(f"\nInformations sur la queue {queue_name}:")
                logger.info(f"- Nombre de messages: {queue_info.method.message_count}")
                logger.info(f"- Nombre de consommateurs: {queue_info.method.consumer_count}")
            except Exception as e:
                logger.error(f"Erreur lors de la déclaration de la queue {queue_name}: {str(e)}")
                raise

            # S'assurer que les messages sont distribués équitablement
            self.channel.basic_qos(prefetch_count=1)
            
            # Configurer la callback de traitement des messages
            async def async_callback(ch, method, properties, body):
                try:
                    logger.info(f"Message reçu: {body[:200]}...")  # Afficher le début du message pour debug
                    await self.process_message(ch, method, properties, body)
                    # Acquitter le message seulement après traitement réussi
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                except Exception as e:
                    logger.error(f"Erreur lors du traitement du message: {str(e)}")
                    # En cas d'erreur, rejeter le message pour qu'il soit retraité
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

            def callback(ch, method, properties, body):
                asyncio.run(async_callback(ch, method, properties, body))
            
            # Configurer la consommation avec auto_ack=False pour la gestion manuelle des acquittements
            self.channel.basic_consume(
                queue=queue_name,
                on_message_callback=callback,
                auto_ack=False
            )
            
            logger.info(f"\nDémarrage de la consommation sur la queue {queue_name}...")
            self.channel.start_consuming()
            
        except KeyboardInterrupt:
            logger.info("\nArrêt du consommateur...")
            self.close()
        except Exception as e:
            logger.error(f"\nErreur lors de la consommation: {str(e)}")
            self.close()
            raise

if __name__ == "__main__":
    # Créer et démarrer le consommateur
    consumer = RabbitMQConsumer()
    consumer.connect()
    consumer.start_consuming()