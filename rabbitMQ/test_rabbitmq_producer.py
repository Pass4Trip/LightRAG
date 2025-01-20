import pika
import os
from dotenv import load_dotenv

load_dotenv()

# Paramètres RabbitMQ
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT"))
RABBITMQ_USER = os.getenv("RABBITMQ_USER")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD")
QUEUE_NAME = os.getenv("RABBITMQ_QUEUE")

def send_test_message():
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
    connection_params = pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        port=RABBITMQ_PORT,
        credentials=credentials
    )
    
    connection = pika.BlockingConnection(connection_params)
    channel = connection.channel()
    
    # Déclarer la queue
    channel.queue_declare(queue=QUEUE_NAME, durable=True)
    
    # Message de test
    message = '{"type": "user", "user_id": "valentin", "user_info": "Valentin est un fan de jeux video"}'
    
    channel.basic_publish(
        exchange='',
        routing_key=QUEUE_NAME,
        body=message,
        properties=pika.BasicProperties(delivery_mode=2)  # Message persistant
    )
    
    print(f"🚀 Message de test envoyé à la queue {QUEUE_NAME}")
    
    connection.close()

if __name__ == "__main__":
    send_test_message()
