import os
from prefect.settings import PREFECT_API_URL
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
import yaml

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load Prefect worker configuration
try:
    # Try to load from YAML first
    with open('/etc/prefect/vinh_value_prefect_worker.yaml', 'r') as f:
        worker_config = yaml.safe_load(f)
        PREFECT_ACCOUNT_ID = worker_config['worker']['cloudApiConfig']['accountId']
        PREFECT_WORKSPACE_ID = worker_config['worker']['cloudApiConfig']['workspaceId']
        PREFECT_WORK_POOL = worker_config['worker']['config']['workPool']
except Exception as e:
    # Fallback to environment variables
    logger.warning(f"Could not load Prefect config from YAML: {e}, using environment variables")
    PREFECT_ACCOUNT_ID = os.getenv("PREFECT_ACCOUNT_ID")
    PREFECT_WORKSPACE_ID = os.getenv("PREFECT_WORKSPACE_ID")
    PREFECT_WORK_POOL = os.getenv("PREFECT_WORK_POOL")

    if not all([PREFECT_ACCOUNT_ID, PREFECT_WORKSPACE_ID]):
        raise RuntimeError("Prefect configuration not found in YAML or environment variables")

os.environ["PREFECT_API_URL"] = f"https://api.prefect.cloud/api/accounts/{PREFECT_ACCOUNT_ID}/workspaces/{PREFECT_WORKSPACE_ID}"

# Load secrets from Prefect
neo4j_secrets = Secret.load("neo4j-credentials").value
ovh_secrets = Secret.load("ovh-credentials").value
rabbitmq_secrets = Secret.load("rabbitmq-credentials").value

# Set environment variables for Neo4J
os.environ["NEO4J_URI"] = neo4j_secrets["uri"]
os.environ["NEO4J_USERNAME"] = neo4j_secrets["username"]
os.environ["NEO4J_PASSWORD"] = neo4j_secrets["password"]

# Set environment variables for OVH
os.environ["OVH_AI_ENDPOINTS_ACCESS_TOKEN"] = ovh_secrets["llm_api_token"]

# Get storage path
WORKING_DIR = os.getenv('VECTOR_DB_PATH', './nano-vectorDB')

# Create working directory if it doesn't exist
if not os.path.exists(WORKING_DIR):
    os.makedirs(WORKING_DIR, exist_ok=True)

class RabbitMQConsumer:
    def __init__(self):
        """Initialize RabbitMQ consumer with connection parameters from Prefect."""
        self.user = rabbitmq_secrets["username"]
        self.password = rabbitmq_secrets["password"]
        self.host = rabbitmq_secrets["host"]
        self.port = rabbitmq_secrets["port"]
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