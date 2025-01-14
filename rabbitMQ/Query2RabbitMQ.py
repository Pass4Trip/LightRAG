"""
Module de transfert des résumés de la base PostgreSQL vers RabbitMQ.

Ce script lit les résumés stockés dans la table longresume et les injecte 
dans la queue RabbitMQ pour traitement ultérieur.
"""

import os
import logging
import json
import traceback
import pika

# Charger les variables d'environnement
from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def get_rabbitmq_connection():
    """
    Établit une connexion à RabbitMQ.
    
    Returns:
        pika.BlockingConnection: Connexion RabbitMQ
    """
    try:
        # Récupération des variables d'environnement
        RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'localhost')
        RABBITMQ_PORT = int(os.getenv('RABBITMQ_PORT', 5672))
        RABBITMQ_USER = os.getenv('RABBITMQ_USER', 'guest')
        RABBITMQ_PASSWORD = os.getenv('RABBITMQ_PASSWORD', 'guest')
        
        # Paramètres de connexion
        credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
        parameters = pika.ConnectionParameters(
            host=RABBITMQ_HOST, 
            port=RABBITMQ_PORT, 
            credentials=credentials
        )
        
        # Établir la connexion
        connection = pika.BlockingConnection(parameters)
        logger.info(f"✅ Connexion réussie à RabbitMQ sur {RABBITMQ_HOST}:{RABBITMQ_PORT}")
        
        return connection
    
    except Exception as e:
        logger.error(f"❌ Erreur de connexion à RabbitMQ : {e}")
        logger.error(f"Détails de l'erreur : {traceback.format_exc()}")
        raise

def transfer_query_reponse_to_rabbitmq(
    source_node_id: str = "16204433116771456015", 
    target_node_id: str = "3091293945615310311", 
    description: str = "Requête de test pour transfert RabbitMQ",
    queue_name: str = 'queue_vinh_test'
):
    """
    Transfert un message de requête vers RabbitMQ avec des paramètres hardcodés.
    
    :param source_node_id: ID du nœud source
    :param target_node_id: ID du nœud cible
    :param description: Description de la requête
    :param queue_name: Nom de la queue RabbitMQ
    """
    try:
        # Établir la connexion RabbitMQ
        connection = get_rabbitmq_connection()
        channel = connection.channel()
        
        # Déclarer la queue
        channel.queue_declare(queue=queue_name, durable=True)
        
        # Préparer le message
        message = {
            "type": "query",
            "source_node": source_node_id,
            "target_node": target_node_id,
            "description": description
        }
        
        # Convertir le message en JSON
        message_body = json.dumps(message, ensure_ascii=False)
        
        # Publier le message
        channel.basic_publish(
            exchange='',
            routing_key=queue_name,
            body=message_body,
            properties=pika.BasicProperties(
                delivery_mode=2,  # Rendre le message persistant
            )
        )
        
        logger.info(f"✅ Message transféré vers RabbitMQ (queue: {queue_name})")
        logger.info(f"📨 Message: {message}")
        
        # Fermer la connexion
        connection.close()
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du transfert vers RabbitMQ : {e}")
        logger.error(traceback.format_exc())

def main():
    """Point d'entrée principal du script"""
    try:
        transfer_query_reponse_to_rabbitmq()
    except Exception as e:
        logger.error(f"Erreur d'exécution : {e}")

if __name__ == "__main__":
    main()
