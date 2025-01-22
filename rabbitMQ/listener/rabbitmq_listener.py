import os
import logging
import pika
import json
import httpx

# Configuration du logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paramètres de connexion RabbitMQ depuis les variables d'environnement
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', '51.77.200.196')  # Utiliser le nom de service Kubernetes
RABBITMQ_PORT = int(os.getenv('RABBITMQ_PORT', '30645'))  # Port standard de RabbitMQ
RABBITMQ_USER = os.getenv('RABBITMQ_USER', 'rabbitmq')
RABBITMQ_PASSWORD = os.getenv('RABBITMQ_PASSWORD', 'mypassword')
RABBITMQ_QUEUE = os.getenv('RABBITMQ_QUEUE', 'queue_vinh_test')

# Configuration flexible de l'API d'insertion
API_LIGHTRAG_URL = 'http://51.77.200.196:30080/insert/'

logger.debug(f"🌐 URL d'insertion configurée : {API_LIGHTRAG_URL}")

def sync_send_to_insert_api(payload: dict):
    """
    Version synchrone de l'envoi à l'API d'insertion de LightRAG avec gestion des timeouts
    
    Args:
        payload (dict): Message à insérer
    """
    try:
        # Configuration du client avec timeouts plus généreux
        with httpx.Client(
            timeout=httpx.Timeout(
                connect=10.0,   # Timeout de connexion
                read=60.0,      # Timeout de lecture très long
                write=60.0,     # Timeout d'écriture très long
                pool=60.0       # Timeout du pool de connexions
            ),
            follow_redirects=True,  # Activer le suivi des redirections
            max_redirects=3  # Limiter le nombre de redirections
        ) as client:
            # Log de débogage
            logger.info(f"🚀 Tentative d'insertion du message vers {API_LIGHTRAG_URL}")
            
            try:
                response = client.post(
                    API_LIGHTRAG_URL, 
                    json=payload
                )
                
                # Log détaillé de la requête et de la réponse
                logger.info(f"📡 Requête HTTP: {response.request.method} {response.request.url}")
                logger.info(f"📥 Réponse HTTP: {response.status_code} {response.reason_phrase}")
                
                if response.status_code == 200:
                    logger.info(f"✅ Message inséré avec succès : {payload.get('type', 'unknown')}")
                    return True
                else:
                    logger.error(f"❌ Échec de l'insertion : {response.status_code} - {response.text}")
                    return False
            
            except httpx.TimeoutException as e:
                logger.error(f"⏰ Timeout lors de l'envoi du message : {e}")
                return False
    
    except Exception as e:
        logger.error(f"❌ Erreur inattendue lors de l'envoi à l'API : {e}")
        return False

def callback(ch, method, properties, body):
    """
    Fonction de callback appelée à la réception de chaque message.
    Traite tous les messages RabbitMQ de manière synchrone.
    
    Args:
        ch (pika.channel.Channel): Canal de communication RabbitMQ
        method (pika.spec.Basic.Deliver): Méthode de livraison
        properties (pika.spec.BasicProperties): Propriétés du message
        body (bytes): Corps du message
    """
    try:
        # Décoder le message
        message = body.decode('utf-8')
        
        # Tenter de parser comme JSON si possible
        try:
            parsed_message = json.loads(message)
            logger.debug(f"📨 Message reçu (JSON) : {parsed_message}")
            
            # Envoi synchrone à l'API
            sync_send_to_insert_api(parsed_message)
        
        except json.JSONDecodeError:
            logger.error(f"📨 Message reçu (texte brut) : {message}")
        
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
