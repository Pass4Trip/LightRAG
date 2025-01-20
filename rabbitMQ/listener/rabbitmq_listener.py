import os
import logging
import pika
import json
import httpx
import asyncio

# Configuration du logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paramètres de connexion RabbitMQ depuis les variables d'environnement
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', '51.77.200.196')
RABBITMQ_PORT = int(os.getenv('RABBITMQ_PORT', 30645))
RABBITMQ_USER = os.getenv('RABBITMQ_USER', 'rabbitmq')
RABBITMQ_PASSWORD = os.getenv('RABBITMQ_PASSWORD', 'mypassword')
RABBITMQ_QUEUE = os.getenv('RABBITMQ_QUEUE', 'queue_vinh_test')

# Configuration flexible de l'API d'insertion
API_LIGHTRAG_URL = os.getenv('API_LIGHTRAG_URL', 'http://localhost:8000/insert/')

logger.info(f"🌐 URL d'insertion configurée : {API_LIGHTRAG_URL}")

async def send_to_insert_api(payload: dict):
    """
    Envoie un message à l'API d'insertion de LightRAG
    
    Args:
        payload (dict): Message à insérer
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(API_LIGHTRAG_URL, json=payload)
            
            if response.status_code == 200:
                logger.info(f"✅ Message inséré avec succès : {payload.get('type', 'unknown')}")
            else:
                logger.error(f"❌ Échec de l'insertion : {response.status_code} - {response.text}")
    
    except httpx.RequestError as e:
        logger.error(f"❌ Erreur de requête réseau : {e}")
    except httpx.HTTPStatusError as e:
        logger.error(f"❌ Erreur HTTP : {e}")
    except Exception as e:
        logger.error(f"❌ Erreur inattendue lors de l'envoi à l'API : {e}")

def callback(ch, method, properties, body):
    """
    Fonction de callback appelée à la réception de chaque message
    """
    try:
        # Décoder le message
        message = body.decode('utf-8')
        
        # Tenter de parser comme JSON si possible
        try:
            parsed_message = json.loads(message)
            logger.info(f"📨 Message reçu (JSON) : {parsed_message}")
            
            # Lancer l'envoi à l'API de manière asynchrone
            asyncio.create_task(send_to_insert_api(parsed_message))
        
        except json.JSONDecodeError:
            logger.info(f"📨 Message reçu (texte brut) : {message}")
        
        # Acquittement du message
        ch.basic_ack(delivery_tag=method.delivery_tag)
    
    except Exception as e:
        logger.error(f"❌ Erreur lors du traitement du message : {e}")
        # Rejeter le message en cas d'erreur
        ch.basic_reject(delivery_tag=method.delivery_tag, requeue=False)

def start_consuming():
    """
    Démarrer la consommation de messages depuis la queue
    """
    try:
        # Établir la connexion
        credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
        parameters = pika.ConnectionParameters(
            host=RABBITMQ_HOST, 
            port=RABBITMQ_PORT,
            credentials=credentials
        )
        
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        
        # Déclarer la queue
        channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)
        
        # Configuration du QoS
        channel.basic_qos(prefetch_count=1)
        
        # Commencer à consommer
        logger.info(f"🚀 Démarrage de l'écoute sur la queue {RABBITMQ_QUEUE}")
        channel.basic_consume(
            queue=RABBITMQ_QUEUE, 
            on_message_callback=callback
        )
        
        # Démarrer la consommation
        channel.start_consuming()
    
    except Exception as e:
        logger.error(f"❌ Erreur de connexion ou de consommation : {e}")

def main():
    """
    Point d'entrée principal
    """
    try:
        logger.info("🔌 Initialisation du listener RabbitMQ")
        start_consuming()
    except KeyboardInterrupt:
        logger.info("🛑 Arrêt demandé par l'utilisateur")
    except Exception as e:
        logger.error(f"❌ Erreur critique : {e}")

if __name__ == "__main__":
    main()
