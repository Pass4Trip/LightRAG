import os
import subprocess
import asyncio
import json
import pika
import time
import logging
import traceback
from prefect import task, flow
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Configuration du logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler("/tmp/rabbitmq_consumer.log", mode='w'),
        logging.StreamHandler()
    ]
)

# Débogage des variables d'environnement
logging.debug(f"Variables d'environnement : {dict(os.environ)}")

# Paramètres RabbitMQ
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "51.77.200.196")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", 30645))
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "rabbitmq")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD")
QUEUE_NAME = os.getenv("RABBITMQ_QUEUE", "queue_vinh_test")

# Chemin vers le script à exécuter
SCRIPT_PATH = "/Users/vinh/Documents/LightRAG/api/lightrag_insert_openai.py"

@task(log_prints=True)
def traiter_message(message: str):
    try:
        logging.info(f"🔍 Message reçu : {message}")
        
        # Convertir le message en JSON si possible
        try:
            message_data = json.loads(message)
            logging.info(f"📦 Détails du message : {message_data}")
        except json.JSONDecodeError:
            logging.warning("⚠️ Le message n'est pas un JSON valide")
        
        # Vérifier si le script existe
        if not os.path.exists(SCRIPT_PATH):
            logging.error(f"❌ Le script {SCRIPT_PATH} n'existe pas !")
            return False
        
        # Lancer le script lightrag_insert_openai.py avec des informations détaillées
        logging.info(f"🚀 Tentative de lancement de {SCRIPT_PATH}")
        
        # Utiliser subprocess.run pour une capture complète
        result = subprocess.run(
            ["python", "-u", SCRIPT_PATH],
            capture_output=True, 
            text=True,
            env={
                **os.environ,  # Conserver les variables d'environnement existantes
                "RABBITMQ_MESSAGE": message,  # Passer le message au script
                "PYTHONUNBUFFERED": "1"  # Forcer l'affichage immédiat
            },
            timeout=120  # Timeout de 2 minutes
        )
        
        # Créer un fichier de trace pour chaque exécution
        trace_file = f"/tmp/lightrag_insert_trace_{int(time.time())}.log"
        with open(trace_file, 'w') as f:
            f.write(f"Script exécuté : {SCRIPT_PATH}\n")
            f.write(f"Message reçu : {message}\n")
            f.write(f"Code de retour : {result.returncode}\n")
            f.write("Sortie standard :\n")
            f.write(result.stdout)
            f.write("\nSortie d'erreur :\n")
            f.write(result.stderr)
        
        logging.info(f"📄 Trace sauvegardée dans {trace_file}")
        
        if result.returncode == 0:
            logging.info("✅ Script exécuté avec succès")
            logging.info(f"Sortie standard :\n{result.stdout}")
            return True
        else:
            logging.error("❌ Erreur lors de l'exécution du script")
            logging.error(f"Code de retour : {result.returncode}")
            logging.error(f"Sortie d'erreur :\n{result.stderr}")
            return False
        
    except subprocess.TimeoutExpired:
        logging.error("⏰ Le script a dépassé le temps d'exécution autorisé")
        return False
    except Exception as e:
        logging.error(f"❌ Erreur fatale : {e}")
        logging.error(traceback.format_exc())
        return False

@flow(log_prints=True)
def consumer_flow():
    try:
        # Configurer les credentials RabbitMQ
        credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
        connection_params = pika.ConnectionParameters(
            host=RABBITMQ_HOST,
            port=RABBITMQ_PORT,
            credentials=credentials
        )
        
        # Établir la connexion
        connection = pika.BlockingConnection(connection_params)
        channel = connection.channel()

        # Déclarer la queue
        channel.queue_declare(queue=QUEUE_NAME, durable=True)

        def callback(ch, method, properties, body):
            message = body.decode()
            result = traiter_message.submit(message)  # Exécution asynchrone avec Prefect
            
            # Vérifier le résultat de l'exécution
            if result.result():
                ch.basic_ack(delivery_tag=method.delivery_tag)
            else:
                # En cas d'échec, on peut choisir de rejeter le message ou le replacer dans la queue
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

        # Configuration de la consommation
        channel.basic_qos(prefetch_count=1)  # Un message à la fois
        channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback)
        
        logging.info(f"🚀 En attente des messages dans la queue '{QUEUE_NAME}'... CTRL+C pour arrêter")
        channel.start_consuming()

    except Exception as e:
        logging.error(f"❌ Erreur lors de la connexion à RabbitMQ : {e}")
        logging.error(traceback.format_exc())

if __name__ == "__main__":
    # Tuer les processus existants de lightrag_insert_openai.py
    try:
        subprocess.run(["pkill", "-f", "lightrag_insert_openai.py"], check=False)
    except Exception as e:
        logging.warning(f"Erreur lors de l'arrêt des processus existants : {e}")
    
    consumer_flow()