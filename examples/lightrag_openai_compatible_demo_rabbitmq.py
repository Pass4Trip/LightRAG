import os
from prefect.blocks.system import Secret
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

# Load secrets from Prefect
secrets = Secret.load("lightrag-secrets")
credentials = secrets.value

# Set environment variables
os.environ["NEO4J_URI"] = credentials["neo4j_uri"]
os.environ["NEO4J_USERNAME"] = credentials["neo4j_username"]
os.environ["NEO4J_PASSWORD"] = credentials["neo4j_password"]
os.environ["OVH_AI_ENDPOINTS_ACCESS_TOKEN"] = credentials["ovh_ai_token"]

# Get storage path
WORKING_DIR = os.getenv('VECTOR_DB_PATH', './nano-vectorDB')

# Create working directory if it doesn't exist
if not os.path.exists(WORKING_DIR):
    os.makedirs(WORKING_DIR, exist_ok=True)

class RabbitMQConsumer:
    def __init__(self):
        """Initialize RabbitMQ consumer with connection parameters from Prefect."""
        self.user = credentials["rabbitmq_username"]
        self.password = credentials["rabbitmq_password"]
        self.host = credentials["rabbitmq_host"]
        self.port = 5672  # Standard RabbitMQ port
        self.connection = None
        self.channel = None
        self.rag = None
        self.max_retries = 3
        self.current_retry_count = 0
        self.consecutive_500_errors = 0
        self.max_consecutive_500_errors = 5
        self.backoff_factor = 1.5

    def connect(self):
        """Establish connection to RabbitMQ."""
        try:
            # Create RabbitMQ connection
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=self.host,
                    port=self.port,
                    credentials=pika.PlainCredentials(self.user, self.password)
                )
            )
            self.channel = self.connection.channel()
            logger.info("Successfully connected to RabbitMQ")
            
        except Exception as e:
            logger.error(f"Error connecting to RabbitMQ: {str(e)}")
            raise

    def start_consuming(self, queue_name: str = "queue_vinh_test"):
        """Start consuming messages."""
        try:
            # Declare queue
            self.channel.queue_declare(queue=queue_name)
            
            # Configure consumption callback
            self.channel.basic_consume(
                queue=queue_name,
                on_message_callback=self.process_message,
                auto_ack=True
            )
            
            logger.info(f"\nStarting consumption on queue {queue_name}...")
            self.channel.start_consuming()
            
        except KeyboardInterrupt:
            logger.info("\nStopping consumer...")
            self.close()
        except Exception as e:
            logger.error(f"Error during consumption: {str(e)}")
            self.close()
            raise

    def close(self):
        """Close RabbitMQ connection."""
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            logger.info("RabbitMQ connection closed")

    def process_message(self, ch, method, properties, body):
        """Process received message."""
        try:
            message = json.loads(body)
            logger.info(f"Received message: {message}")
            # Add your message processing logic here
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            raise

if __name__ == "__main__":
    # Create and start consumer
    consumer = RabbitMQConsumer()
    consumer.connect()
    consumer.start_consuming()