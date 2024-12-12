import os
import pika
import json
import logging
from dotenv import load_dotenv
from pathlib import Path

# Charger les variables d'environnement
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Configuration du logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Récupérer les paramètres de connexion depuis les variables d'environnement
RABBITMQ_USERNAME = os.getenv('RABBITMQ_USERNAME', 'guest')
RABBITMQ_PASSWORD = os.getenv('RABBITMQ_PASSWORD', 'guest')
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'localhost')
RABBITMQ_PORT = int(os.getenv('RABBITMQ_PORT', '5672'))

# Paramètres de connexion
connection_params = pika.ConnectionParameters(
    host=RABBITMQ_HOST,
    port=RABBITMQ_PORT,
    credentials=pika.PlainCredentials(RABBITMQ_USERNAME, RABBITMQ_PASSWORD)
)

try:
    # Établir la connexion
    connection = pika.BlockingConnection(connection_params)
    channel = connection.channel()

    # Déclarer la queue
    queue_name = 'queue_vinh_test'
    channel.queue_declare(queue=queue_name, durable=True)

    # Préparer le message
    message = {
        "restaurant_id": "junk_lyon_test",
        "resume": "JUNK LYON est un restaurant de burgers à Lyon offrant une ambiance chaleureuse. Les portions sont généreuses et les plats sont de qualité. Malgré quelques critiques sur la taille des portions, c'est un endroit recommandé pour les amateurs de burgers."
    }

    # Publier le message
    channel.basic_publish(
        exchange='',
        routing_key=queue_name,
        body=json.dumps(message),
        properties=pika.BasicProperties(
            delivery_mode=2  # Message persistant
        )
    )

    logger.info(f" [x] Message envoyé: {message}")

except Exception as e:
    logger.error(f"Erreur lors de l'envoi du message: {e}")
    import traceback
    logger.error(traceback.format_exc())

finally:
    # Fermer la connexion
    if 'connection' in locals() and not connection.is_closed:
        connection.close()