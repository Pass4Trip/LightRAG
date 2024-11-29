import os
from dotenv import load_dotenv
import asyncio
from lightrag import LightRAG, QueryParam
from lightrag.llm import openai_complete_if_cache, openai_embedding
from lightrag.utils import EmbeddingFunc
import numpy as np
import requests
import pika
import json
import time
from typing import Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential, before_sleep_log, retry_if_exception_type
import logging
from requests.exceptions import HTTPError, RequestException, Timeout

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

WORKING_DIR = "./nano-vectorDB"

if not os.path.exists(WORKING_DIR):
    os.mkdir(WORKING_DIR)

class RabbitMQConsumer:
    def __init__(self):
        self.user = 'rabbitmq'
        self.password = 'mypassword'
        self.host = '51.77.200.196'
        self.port = 30645
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

    async def initialize_rag(self) -> LightRAG:
        """
        Initialise l'instance LightRAG avec les configurations nécessaires
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
            )
        )
        return rag

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

    async def process_message(self, ch, method, properties, body):
        try:
            # Décoder le message JSON
            restaurant_data = json.loads(body)
            restaurant_id = restaurant_data.get('id', 'Unknown')
            logger.info(f"Traitement du restaurant {restaurant_id}")
            
            # Préparer le document pour LightRAG
            document = self.prepare_document(restaurant_data)
            
            # Ajouter le document à LightRAG
            if self.rag is None:
                self.rag = await self.initialize_rag()
            
            await self.rag.ainsert(document)
            logger.info(f"Document ajouté avec succès pour le restaurant {restaurant_id}")
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement du message: {str(e)}", exc_info=True)
            raise

    def prepare_document(self, restaurant_data: Dict[str, Any]) -> str:
        """
        Prépare un document formaté à partir des données du restaurant
        """
        doc_parts = [
            f"Restaurant: {restaurant_data.get('name', 'Unknown')}",
            f"ID: {restaurant_data.get('id', 'Unknown')}",
            f"Adresse: {restaurant_data.get('address', 'Unknown')}",
            f"Type de cuisine: {', '.join(restaurant_data.get('tags', []))}",
            "Informations additionnelles:",
        ]
        
        # Ajouter les avis s'ils existent
        if 'reviews' in restaurant_data:
            doc_parts.append("Avis des clients:")
            for review in restaurant_data['reviews']:
                doc_parts.append(f"- {review.get('comment', '')}")
        
        return "\n".join(doc_parts)

    def start_consuming(self, queue_name: str = "queue_vinh_test"):
        """
        Démarre la consommation des messages de la queue
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
