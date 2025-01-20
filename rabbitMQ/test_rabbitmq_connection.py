import pika
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

def test_rabbitmq_connection():
    try:
        # Paramètres de connexion
        credentials = pika.PlainCredentials(
            os.getenv("RABBITMQ_USER"), 
            os.getenv("RABBITMQ_PASSWORD")
        )
        connection_params = pika.ConnectionParameters(
            host=os.getenv("RABBITMQ_HOST"),
            port=int(os.getenv("RABBITMQ_PORT")),
            credentials=credentials
        )
        
        # Tentative de connexion
        connection = pika.BlockingConnection(connection_params)
        channel = connection.channel()
        
        # Test de déclaration de queue
        queue_name = os.getenv("RABBITMQ_QUEUE", "queue_vinh_test")
        channel.queue_declare(queue=queue_name, durable=True)
        
        print("✅ Connexion RabbitMQ réussie !")
        print(f"📍 Serveur : {os.getenv('RABBITMQ_HOST')}:{os.getenv('RABBITMQ_PORT')}")
        print(f"👤 Utilisateur : {os.getenv('RABBITMQ_USER')}")
        print(f"📨 Queue testée : {queue_name}")
        
        # Fermeture propre
        connection.close()
        return True
    
    except Exception as e:
        print(f"❌ Erreur de connexion : {e}")
        return False

if __name__ == "__main__":
    test_rabbitmq_connection()
