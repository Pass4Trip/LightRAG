import os
import logging
import pika
import json

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
        
        # Créer la connexion
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
