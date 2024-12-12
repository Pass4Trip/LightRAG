import os
import logging
from typing import Dict, Any
import json
import pika
from tenacity import retry, stop_after_attempt, wait_exponential, before_sleep_log, retry_if_exception_type
from requests.exceptions import HTTPError, RequestException, Timeout
from lightrag import LightRAG
from lightrag.utils import EmbeddingFunc
import asyncio
import numpy as np
import yaml
import traceback
import sys
from pathlib import Path

# Add the examples directory to Python path
sys.path.append(str(Path(__file__).parent))
from prompt import PROMPTS, GRAPH_FIELD_SEP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_config():
    """
    Charge la configuration depuis différentes sources:
    1. Variables d'environnement (pour Kubernetes)
    2. Fichier .env local
    3. Valeurs par défaut
    """
    # Essayer de charger depuis un fichier .env local
    env_file = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_file):
        logger.info(f"Chargement de la configuration depuis {env_file}")
        with open(env_file) as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key.strip()] = value.strip().strip('"\'')

    # Configuration par défaut (uniquement les valeurs non-sensibles)
    defaults = {
        "RABBITMQ_USERNAME": "guest",
        "RABBITMQ_HOST": "localhost",
        "RABBITMQ_PORT": "5672",
        "NEO4J_URI": "bolt://localhost:7687",
        "NEO4J_USERNAME": "neo4j",
        "PREFECT_ACCOUNT_ID": "",
        "PREFECT_WORKSPACE_ID": "",
        "VECTOR_DB_PATH": "./nano-vectorDB"
    }

    # Vérifier les variables sensibles requises
    required_secrets = [
        "RABBITMQ_PASSWORD",
        "NEO4J_PASSWORD",
        "OVH_LLM_API_TOKEN"
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
                             f"Veuillez la définir dans votre fichier .env ou dans les secrets Kubernetes.")
        config[secret] = value

    return config

def verify_environment():
    """
    Vérifie que toutes les variables d'environnement nécessaires sont présentes
    et affiche leur statut.
    """
    # Toutes les variables requises
    required_vars = {
        "Non-sensibles": {
            "RABBITMQ_USERNAME": "Nom d'utilisateur RabbitMQ",
            "RABBITMQ_HOST": "Hôte RabbitMQ",
            "RABBITMQ_PORT": "Port RabbitMQ",
            "NEO4J_URI": "URI Neo4j",
            "NEO4J_USERNAME": "Nom d'utilisateur Neo4j",
            "PREFECT_ACCOUNT_ID": "ID du compte Prefect",
            "PREFECT_WORKSPACE_ID": "ID de l'espace de travail Prefect",
            "VECTOR_DB_PATH": "Chemin de la base de données vectorielle"
        },
        "Secrets": {
            "RABBITMQ_PASSWORD": "Mot de passe RabbitMQ",
            "NEO4J_PASSWORD": "Mot de passe Neo4j",
            "OVH_LLM_API_TOKEN": "Token API OVH LLM"
        }
    }

    missing_vars = []
    status = []

    # Vérifier toutes les variables
    for category, vars_dict in required_vars.items():
        status.append(f"\n=== {category} ===")
        for var, description in vars_dict.items():
            value = os.getenv(var)
            if value is None:
                status.append(f"❌ {description} ({var}): Non défini")
                missing_vars.append(var)
            else:
                # Masquer les valeurs des secrets
                if category == "Secrets":
                    display_value = "********"
                else:
                    display_value = value
                status.append(f"✅ {description} ({var}): {display_value}")

    # Afficher le statut
    logger.info("\nStatut des variables d'environnement:\n" + "\n".join(status))

    # S'il manque des variables, lever une exception
    if missing_vars:
        raise RuntimeError(
            f"\nVariables d'environnement manquantes:\n"
            f"{', '.join(missing_vars)}\n"
            f"Veuillez les définir dans votre fichier .env ou dans Kubernetes."
        )

    return True

def is_kubernetes():
    """
    Détecte si l'application s'exécute dans un environnement Kubernetes.
    
    Returns:
        bool: True si dans Kubernetes, False sinon
    """
    return os.path.exists('/var/run/secrets/kubernetes.io')

def setup_working_directory(base_dir, config):
    """
    Configure le répertoire de travail en fonction de l'environnement (Kubernetes ou local).
    
    Args:
        base_dir (str): Répertoire de base pour le stockage
        config (dict): Configuration contenant VECTOR_DB_PATH
        
    Returns:
        str: Chemin du répertoire de travail configuré
    """
    if is_kubernetes():
        # Pour Kubernetes/microk8s, utiliser le chemin configuré
        working_dir = config["VECTOR_DB_PATH"]
        logger.info("Environnement Kubernetes détecté, utilisation du répertoire: %s", working_dir)
    else:
        # Pour Mac local, utiliser le répertoire dans le projet
        working_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "nano-vectorDB")
        logger.info("Environnement local détecté, utilisation du répertoire: %s", working_dir)
    
    # Créer le répertoire s'il n'existe pas
    os.makedirs(working_dir, exist_ok=True)
    return working_dir

# Charger la configuration
config = load_config()

# Vérifier les variables d'environnement au démarrage
verify_environment()

# Configuration du répertoire de travail
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WORKING_DIR = setup_working_directory(BASE_DIR, config)

# Configuration Prefect
os.environ["PREFECT_API_URL"] = f"https://api.prefect.cloud/api/accounts/{config['PREFECT_ACCOUNT_ID']}/workspaces/{config['PREFECT_WORKSPACE_ID']}"
PREFECT_PROFILE='cloud'

# Set environment variables for Neo4J
os.environ["NEO4J_URI"] = config["NEO4J_URI"]
os.environ["NEO4J_USERNAME"] = config["NEO4J_USERNAME"]
os.environ["NEO4J_PASSWORD"] = config["NEO4J_PASSWORD"]

# Set environment variables for OVH
os.environ["OVH_AI_ENDPOINTS_ACCESS_TOKEN"] = config["OVH_LLM_API_TOKEN"]

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

        # Charger la configuration
        self.user = config["RABBITMQ_USERNAME"]
        self.password = config["RABBITMQ_PASSWORD"]
        self.host = config["RABBITMQ_HOST"]
        self.port = config["RABBITMQ_PORT"]

        # Configuration Neo4j
        os.environ["NEO4J_URI"] = config["NEO4J_URI"]
        os.environ["NEO4J_USERNAME"] = config["NEO4J_USERNAME"]
        os.environ["NEO4J_PASSWORD"] = config["NEO4J_PASSWORD"]

        # Configuration OVH
        os.environ["OVH_AI_ENDPOINTS_ACCESS_TOKEN"] = config["OVH_LLM_API_TOKEN"]

        self.connection = None
        self.channel = None
        self.rag = None
        self.max_retries = 3
        self.current_retry_count = 0
        self.consecutive_500_errors = 0
        self.max_consecutive_500_errors = 5
        self.backoff_factor = 1.5
        
        # Create and set event loop
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

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

        # Set the event loop for Neo4j
        asyncio.set_event_loop(self.loop)
        
        # Initialiser LightRAG
        rag = LightRAG(
            working_dir=WORKING_DIR,
            llm_model_func=llm_model_func,
            embedding_func=EmbeddingFunc(
                embedding_dim=768,  # Dimension for multilingual-e5-base model
                max_token_size=8192,
                func=embedding_func
            ),
            kv_storage="JsonKVStorage",
            vector_storage="NanoVectorDBStorage",
            graph_storage="Neo4JStorage",
            log_level="DEBUG",
            prompts=PROMPTS,
            graph_field_sep=GRAPH_FIELD_SEP
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
            # Initialiser LightRAG si ce n'est pas déjà fait
            if self.rag is None:
                self.rag = await self.initialize_rag()

            # Décoder le message JSON
            message = json.loads(body.decode())
            restaurant_data = message.get("restaurant", {})
            
            if not restaurant_data:
                logging.error("Données de restaurant manquantes dans le message")
                return

            logging.info(f"Traitement du restaurant {restaurant_data.get('title')} (ID: {restaurant_data.get('id')})")
            
            # Préparer le document pour LightRAG
            document = self.prepare_document(restaurant_data)
            
            # Insérer le document dans LightRAG
            await self.rag.ainsert(document)
            
            # Acquitter le message
            ch.basic_ack(delivery_tag=method.delivery_tag)
            
        except Exception as e:
            logging.error(f"Erreur lors du traitement du message: {e}")
            if hasattr(e, '__traceback__'):
                logging.error(traceback.format_exc())
            # En cas d'erreur, on acquitte quand même le message pour éviter qu'il ne soit renvoyé
            ch.basic_ack(delivery_tag=method.delivery_tag)

    def callback(self, ch, method, properties, body):
        """Wrapper synchrone pour process_message."""
        try:
            asyncio.set_event_loop(self.loop)
            self.loop.run_until_complete(self.process_message(ch, method, properties, body))
        except Exception as e:
            logging.error(f"Error in callback: {e}")
            if hasattr(e, '__traceback__'):
                logging.error(traceback.format_exc())
            ch.basic_ack(delivery_tag=method.delivery_tag)

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
        """Ferme la connexion RabbitMQ."""
        if self.channel and not self.channel.is_closed:
            self.channel.close()
        if self.connection and not self.connection.is_closed:
            self.connection.close()
        if self.loop and not self.loop.is_closed():
            self.loop.close()

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
            # Déclarer la queue
            self.channel.queue_declare(queue=queue_name, durable=True)
            
            # Configurer la consommation des messages
            self.channel.basic_qos(prefetch_count=1)
            self.channel.basic_consume(
                queue=queue_name,
                on_message_callback=self.callback
            )
            
            logging.info(f"En attente de messages sur la queue {queue_name}...")
            self.channel.start_consuming()
            
        except Exception as e:
            logging.error(f"Erreur lors de la consommation: {e}")
            if hasattr(e, '__traceback__'):
                logging.error(traceback.format_exc())
            raise

if __name__ == "__main__":
    # Créer et démarrer le consommateur
    consumer = RabbitMQConsumer()
    consumer.connect()
    consumer.start_consuming()