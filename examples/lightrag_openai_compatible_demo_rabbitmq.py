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

# Load environment variables from .env file
load_dotenv()

WORKING_DIR = "./restaurant_openai_p4t_test"

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
                print(f"Connexion RabbitMQ établie sur {self.host}:{self.port}")
                return
            except Exception as e:
                retry_count += 1
                if retry_count == self.max_retries:
                    raise Exception(f"Échec de connexion à RabbitMQ après {self.max_retries} tentatives: {str(e)}")
                print(f"Tentative {retry_count}/{self.max_retries} échouée, nouvelle tentative...")
    
    def close(self):
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            print("Connexion RabbitMQ fermée")

    async def process_message(self, ch, method, properties, body):
        try:
            # Décoder le message JSON
            restaurant_data = json.loads(body)
            
            # Préparer le document pour LightRAG
            document = self.prepare_document(restaurant_data)
            
            # Ajouter le document à LightRAG
            if self.rag is None:
                self.rag = await self.initialize_rag()
            
            await self.rag.add_documents([document])
            print(f"Document ajouté pour le restaurant {restaurant_data.get('id', 'Unknown')}")
            
        except Exception as e:
            print(f"Erreur lors du traitement du message: {str(e)}")

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
            
            response = requests.post(url, json=payload, headers=headers)
            if response.status_code == 200:
                response_data = response.json()
                return response_data["choices"][0]["message"]["content"]
            else:
                raise Exception(f"Error from OVH API: {response.status_code}")

        async def embedding_func(texts: list[str]) -> np.ndarray:
            url = "https://bge-m3.endpoints.kepler.ai.cloud.ovh.net/api/text2vec"
            headers = {
                "Content-Type": "text/plain",
                "Authorization": f"Bearer {os.getenv('OVH_AI_ENDPOINTS_ACCESS_TOKEN')}",
            }
            
            embeddings = []
            for text in texts:
                response = requests.post(url, data=text, headers=headers)
                if response.status_code == 200:
                    embeddings.append(response.json())
                else:
                    raise Exception(f"Error from OVH API: {response.status_code}")
            
            return np.array(embeddings)

        # Initialiser LightRAG
        rag = LightRAG(
            working_dir=WORKING_DIR,
            llm_model_func=llm_model_func,
            embedding_func=embedding_func,
        )
        
        return rag

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
                print(f"\nInformations sur la queue {queue_name}:")
                print(f"- Nombre de messages: {queue_info.method.message_count}")
                print(f"- Nombre de consommateurs: {queue_info.method.consumer_count}")
            except Exception as e:
                print(f"Erreur lors de la déclaration de la queue {queue_name}: {str(e)}")
                raise

            # S'assurer que les messages sont distribués équitablement
            self.channel.basic_qos(prefetch_count=1)
            
            # Configurer la callback de traitement des messages
            def callback(ch, method, properties, body):
                try:
                    print(f"Message reçu: {body[:200]}...")  # Afficher le début du message pour debug
                    asyncio.run(self.process_message(ch, method, properties, body))
                    # Acquitter le message seulement après traitement réussi
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                except Exception as e:
                    print(f"Erreur lors du traitement du message: {str(e)}")
                    # En cas d'erreur, rejeter le message pour qu'il soit retraité
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
            
            # Configurer la consommation avec auto_ack=False pour la gestion manuelle des acquittements
            self.channel.basic_consume(
                queue=queue_name,
                on_message_callback=callback,
                auto_ack=False
            )
            
            print(f"\nDémarrage de la consommation sur la queue {queue_name}...")
            self.channel.start_consuming()
            
        except KeyboardInterrupt:
            print("\nArrêt du consommateur...")
            self.close()
        except Exception as e:
            print(f"\nErreur lors de la consommation: {str(e)}")
            self.close()
            raise

if __name__ == "__main__":
    # Créer et démarrer le consommateur
    consumer = RabbitMQConsumer()
    consumer.connect()
    consumer.start_consuming()
