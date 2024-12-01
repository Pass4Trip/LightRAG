from prefect_sqlalchemy import SqlAlchemyConnector
from prefect import flow, task
from prefect.blocks.system import Secret
from prefect.cache_policies import NONE

from sqlalchemy import create_engine, text

import os
import certifi
import ssl
import time
import requests
import pika
import json


# Configuration SSL
os.environ['SSL_CERT_FILE'] = certifi.where()
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()
os.environ['CURL_CA_BUNDLE'] = certifi.where()



class Note():
    """Classe pour stocker la distribution des notes d'un restaurant.
    Chaque attribut représente le nombre de notes pour chaque étoile (1 à 5)."""
    onestar = 0
    twostar = 0
    threestar = 0
    fourstar = 0
    fivestar = 0



class RabbitMQ:
    """Gestionnaire de connexion RabbitMQ avec support multi-environnements."""
    
    def __init__(self, environnement: str = "local"):
        """Initialise la connexion RabbitMQ selon l'environnement.
        
        Args:
            environnement (str): "local" ou "production"
        """
        self.user = 'rabbitmq'
        self.password = 'mypassword'
        self.host = '51.77.200.196'
        self.port = 30645  # Port AMQP (5672 -> 30645)
        self.connection = None
        self.channel = None
        self.max_retries = 3
        
    def connect(self):
        """Établit la connexion à RabbitMQ avec gestion des tentatives."""
        retry_count = 0
        while retry_count < self.max_retries:
            try:
                credentials = pika.PlainCredentials(
                    self.user,
                    self.password
                )
                parameters = pika.ConnectionParameters(
                    host=self.host,
                    port=self.port,
                    credentials=credentials
                )
                self.connection = pika.BlockingConnection(parameters)
                self.channel = self.connection.channel()
                print(f"Connexion RabbitMQ établie sur {self.host}:{self.port}")
                return
            except Exception as e:
                retry_count += 1
                if retry_count == self.max_retries:
                    raise Exception(f"Échec de connexion à RabbitMQ après {self.max_retries} tentatives: {str(e)}")
                print(f"Tentative {retry_count}/{self.max_retries} échouée, nouvelle tentative...")
                
    def close(self):
        """Ferme proprement la connexion RabbitMQ si elle existe."""
        if self.connection:
            self.connection.close()
            print("Connexion RabbitMQ fermée")
            
    def consume(self, queue_name, callback):
        """Configure la consommation de messages d'une queue.
        
        Args:
            queue_name (str): Nom de la queue à écouter
            callback (callable): Fonction à appeler pour chaque message reçu
        
        Raises:
            Exception: Si la connexion n'est pas établie
        """
        if not self.connection:
            raise Exception("Connexion RabbitMQ non établie")
        self.channel.basic_consume(queue=queue_name, on_message_callback=callback, no_ack=True)
        
    def publish(self, queue_name, message, restaurantId):
        """Publie un message dans une queue avec configuration de durabilité.
        
        Args:
            queue_name (str): Nom de la queue cible
            message (bytes): Message à envoyer (encodé en UTF-8)
            restaurantId (int): ID du restaurant concerné
        
        Raises:
            Exception: Si la connexion n'est pas établie
        """
        if not self.connection:
            raise Exception("Connexion RabbitMQ non établie")
        self.channel.queue_declare(queue=queue_name, durable=True)
        self.channel.basic_publish(exchange='', routing_key=queue_name, body=message, properties=pika.BasicProperties(delivery_mode=2))

@task(log_prints=True)
def bdd_connection(environnement: str = "local"):
    """Établit la connexion à la base de données PostgreSQL.
    
    Args:
        environnement (str, optional): "local" ou "production". Defaults to "local".
        
    Returns:
        SqlAlchemyConnector: Connexion à la base de données
        
    Raises:
        Exception: Si la connexion échoue
    """
    print(f"⏰ Connexion BDD - Début: {time.strftime('%H:%M:%S')}")
    
    try:
        # Chargement du block selon l'environnement
        print("🔑 Chargement du block PostgreSQL...")
        block_name = "postgres-local" if environnement == "local" else "postgres-prod"
        block = SqlAlchemyConnector.load(block_name)
        
        # Affichage des informations de connexion (masquées)
        print("\n📝 Informations de connexion:")
        connection_info = block.connection_info
        print(f"  • Base de données: {connection_info.database}")
        print(f"  • Hôte: {connection_info.host}")
        print(f"  • Port: {connection_info.port}")
        print(f"  • Utilisateur: {connection_info.username}")
        
        # Test de la connexion
        print("\n🔌 Test de la connexion...")
        with block.get_connection(begin=False) as conn:
            result = conn.execute(text("SELECT 1"))
            result.scalar()
        print("✅ Connexion établie avec succès!")
        
        return block
        
    except Exception as e:
        print(f"\n❌ Erreur de connexion: {str(e)}")
        raise
    finally:
        print(f"\n⏰ Connexion BDD - Fin: {time.strftime('%H:%M:%S')}")

@task(log_prints=True)
def prepare_db(database):
    """Prépare la table des résumés en la réinitialisant.
    
    Args:
        database (SqlAlchemyConnector): Connexion à la base de données
    
    Side effects:
        - Supprime la table longresume si elle existe
        - Crée une nouvelle table longresume
    """
    print("🔄 Préparation de la base de données...")
    try:
        with database.get_connection(begin=False) as conn:
            # Suppression de la table si elle existe
            conn.execute(text("DROP TABLE IF EXISTS restaurants.longresume;"))
            
            # Création de la nouvelle table
            conn.execute(text("""CREATE TABLE IF NOT EXISTS restaurants.longresume (id SERIAL PRIMARY KEY, restaurantId INT REFERENCES restaurants.information(id), resume TEXT);"""))
            print("✅ Table longresume créée avec succès!")
    except Exception as e:
        print(f"❌ Erreur lors de la préparation de la base: {str(e)}")
        raise

@task(log_prints=True)
def get_information(database):
    """Récupère les informations de base de tous les restaurants.
    
    Args:
        database (SqlAlchemyConnector): Connexion à la base de données
    
    Returns:
        list[dict]: Liste des restaurants avec leurs informations de base
    """
    print("📊 Récupération des informations des restaurants...")
    try:
        with database.get_connection(begin=False) as conn:
            result = conn.execute(text("""
                SELECT id, title, description, price, categoryname 
                FROM restaurants.information;
            """))
            # Convertir les résultats en dictionnaires pour un accès plus facile
            restaurants = [dict(row._mapping) for row in result]
            print(f"✅ {len(restaurants)} restaurants trouvés")
            return restaurants
    except Exception as e:
        print(f"❌ Erreur lors de la récupération des restaurants: {str(e)}")
        raise

@task(log_prints=True)
def get_reviews(database, restaurant_id):
    """Récupère tous les avis d'un restaurant.
    
    Args:
        database (SqlAlchemyConnector): Connexion à la base de données
        restaurant_id (int): ID du restaurant
    
    Returns:
        list[dict]: Liste des avis
    """
    print(f"📝 Récupération des avis du restaurant {restaurant_id}...")
    try:
        with database.get_connection(begin=False) as conn:
            result = conn.execute(text("""
                SELECT text, foodrating, servicerating, atmosphererating
                FROM restaurants.reviews
                WHERE restaurantid = :id;
            """), {"id": restaurant_id})
            # Conversion des Row en dictionnaires
            reviews = [dict(row._mapping) for row in result]
            print(f"✅ {len(reviews)} avis trouvés")
            return reviews
    except Exception as e:
        print(f"❌ Erreur lors de la récupération des avis: {str(e)}")
        raise

@task(log_prints=True)
def get_notes_distribution(database, restaurant_id):
    """Récupère la distribution des notes d'un restaurant.
    
    Args:
        database (SqlAlchemyConnector): Connexion à la base de données
        restaurant_id (int): ID du restaurant
    
    Returns:
        Note: Objet contenant la distribution des notes
    """
    print(f"⭐ Récupération des notes du restaurant {restaurant_id}...")
    try:
        with database.get_connection(begin=False) as conn:
            result = conn.execute(text("""
                SELECT onestar, twostar, threestar, fourstar, fivestar 
                FROM restaurants.reviewsdistribution 
                WHERE restaurantid = :id;
            """), {"id": restaurant_id})
            
            notes = Note()
            if row := result.fetchone():  # Using walrus operator for Python 3.8+
                # Directement assigner les valeurs depuis la table reviewsdistribution
                notes.onestar = row.onestar or 0     # Utilisation de 'or 0' pour gérer les NULL
                notes.twostar = row.twostar or 0
                notes.threestar = row.threestar or 0
                notes.fourstar = row.fourstar or 0
                notes.fivestar = row.fivestar or 0
                print("✅ Distribution des notes récupérée")
            else:
                print("ℹ️ Aucune distribution de notes trouvée")
            
            return notes
            
    except Exception as e:
        print(f"❌ Erreur lors de la récupération des notes: {str(e)}")
        raise

@task(log_prints=True)
def get_tags(database, restaurant_id):
    """Récupère les tags associés à un restaurant.
    
    Args:
        database (SqlAlchemyConnector): Connexion à la base de données
        restaurant_id (int): ID du restaurant
    
    Returns:
        list[str]: Liste des tags du restaurant
    """
    print(f"🏷️ Récupération des tags du restaurant {restaurant_id}...")
    try:
        with database.get_connection(begin=False) as conn:
            result = conn.execute(text("""
                SELECT title FROM restaurants.reviewstags WHERE restaurantid = :id;
            """), {"id": restaurant_id})
            tags = [row.title for row in result]  
            print(f"✅ {len(tags)} tags trouvés")
            return tags
    except Exception as e:
        print(f"❌ Erreur lors de la récupération des tags: {str(e)}")
        raise

@task(log_prints=True)
def get_additional_info(database, restaurant_id):
    """Récupère les informations additionnelles d'un restaurant.
    
    Args:
        database (SqlAlchemyConnector): Connexion à la base de données
        restaurant_id (int): ID du restaurant
    
    Returns:
        list[str]: Liste des catégories d'informations additionnelles où info = 'true'
    """
    print(f"ℹ️ Récupération des infos additionnelles du restaurant {restaurant_id}...")
    try:
        with database.get_connection(begin=False) as conn:
            result = conn.execute(text("""
                SELECT category FROM restaurants.additionalinfo 
                WHERE restaurantid = :id AND info = 'true';
            """), {"id": restaurant_id})
            
            info = [row.category for row in result]
            print(f"✅ {len(info)} informations additionnelles trouvées")
            return info
            
    except Exception as e:
        print(f"❌ Erreur lors de la récupération des informations additionnelles: {str(e)}")
        raise

@task(log_prints=True)
def prepare_message(restaurant, reviews, notes, tags, additional_info):
    """Prépare le message à envoyer à l'API de génération de résumé.
    
    Args:
        restaurant (dict): Informations de base du restaurant
        reviews (list[dict]): Liste des avis
        notes (Note): Distribution des notes
        tags (list[str]): Liste des tags
        additional_info (list[str]): Informations additionnelles
    
    Returns:
        str: Message formaté en JSON
    """
    # Conversion de l'objet Note en dictionnaire
    notes_dict = {
        "onestar": notes.onestar,
        "twostar": notes.twostar,
        "threestar": notes.threestar,
        "fourstar": notes.fourstar,
        "fivestar": notes.fivestar
    }
    
    message = {
        'restaurant': dict(restaurant),  # Assure que c'est un dictionnaire
        'reviews': reviews,  # Déjà converti en liste de dictionnaires
        'notes': notes_dict,
        'tags': tags,
        'additional_info': additional_info
    }
    
    try:
        return json.dumps(message)
    except TypeError as e:
        print(f"❌ Erreur de sérialisation JSON: {str(e)}")
        # Log plus détaillé pour le débogage
        print("Types des données:")
        print(f"restaurant: {type(restaurant)}")
        print(f"reviews: {type(reviews)}, premier élément: {type(reviews[0]) if reviews else 'aucun'}")
        print(f"notes: {type(notes)}")
        print(f"tags: {type(tags)}")
        print(f"additional_info: {type(additional_info)}")
        raise

@task(log_prints=True, cache_policy=NONE)  # Désactivation du cache pour cette tâche
def enrich(database, information, rabbitmq):
    """Enrichit les données de chaque restaurant et envoie à RabbitMQ.
    
    Args:
        database (SqlAlchemyConnector): Connexion à la base de données
        information (list[dict]): Liste des restaurants à traiter
        rabbitmq (RabbitMQ): Instance de connexion RabbitMQ
    
    Side effects:
        - Publie des messages dans la queue RabbitMQ
        - Reset les connexions DB après chaque restaurant
    """
    print("🔄 Début de l'enrichissement des données...")
    
    try:
        for restaurant in information:
            print(f"\n📍 Traitement du restaurant {restaurant['id']}")
            reviews = get_reviews(database, restaurant['id'])
            notes = get_notes_distribution(database, restaurant['id'])
            tags = get_tags(database, restaurant['id'])
            additional_info = get_additional_info(database, restaurant['id'])
            
            message = prepare_message(restaurant, reviews, notes, tags, additional_info)
            
            try:
                # Log détaillé du message
                print(f"\n📋 Contenu du message pour le restaurant {restaurant['id']}:")
                print(f"  • Titre: {restaurant['title']}")
                print(f"  • Nombre d'avis: {len(reviews)}")
                print(f"  • Tags: {', '.join(tags)}")
                print(f"  • Infos additionnelles: {', '.join(additional_info)}")
                print(f"  • Distribution des notes: {notes.__dict__}")
                
                rabbitmq.publish('queue_vinh_test', message.encode('utf-8'), restaurant['id'])
                print(f"✅ Message publié pour le restaurant {restaurant['id']}")
            except Exception as e:
                print(f"❌ Erreur lors de la publication du message: {str(e)}")
                raise
    except Exception as e:
        print(f"❌ Erreur lors de l'enrichissement: {str(e)}")
        raise
    finally:
        print("\n🏁 Fin de l'enrichissement des données")


@flow(log_prints=True)
def enrich_data_long_resume_vinh(environnement: str = "local"):
    """Flow principal pour l'enrichissement des données restaurants.
    
    Args:
        environnement (str, optional): "local" ou "production". Defaults to "local".
    
    Flow steps:
        1. Connexion à la base de données
        2. Initialisation RabbitMQ
        3. Préparation de la table de résumés
        4. Récupération des informations restaurants
        5. Enrichissement et envoi des données
    """
    print(f"🚀 Démarrage du flow - Environnement: {environnement}")
    
    try:
        # Récupération du block de connexion
        print("🔌 Connexion à la base de données...")
        database_block = bdd_connection(environnement)
        print("✅ Connexion établie")

        # Test de la connexion
        print("📊 Test de la connexion...")
        with database_block.get_connection(begin=False) as conn:
            result = conn.execute(text("SELECT 1"))
            result.scalar()
        print("🎉 Test réussi!")

        # Initialisation de RabbitMQ
        print("🐰 Initialisation de RabbitMQ...")
        rabbitmq = RabbitMQ(environnement)
        rabbitmq.connect()

        try:
            # Préparation de la base et récupération des données
            prepare_db(database_block)
            information = get_information(database_block)
            
            # Enrichissement des données
            enrich(database_block, information, rabbitmq)
        finally:
            # Fermeture propre de RabbitMQ
            print("👋 Fermeture de la connexion RabbitMQ...")
            rabbitmq.close()
            
    except Exception as e:
        print(f"❌ Erreur dans le flow: {str(e)}")
        raise
    else:
        print("✨ Flow terminé avec succès!")

if __name__ == "__main__":
    import subprocess
    import time
    import sys
    import threading
    
    def run_service():
        print("🚀 Démarrage du service...")
        enrich_data_long_resume_vinh.serve()

    def trigger_flow():
        print("⏳ Attente de 5 secondes pour laisser le temps au service de démarrer...")
        time.sleep(5)
        print("🎯 Déclenchement du flow...")
        subprocess.run(["prefect", "deployment", "run", "enrich-data-long-resume-vinh/enrich-data-long-resume-vinh"])

    try:
        # Démarrage du service dans un thread séparé
        service_thread = threading.Thread(target=run_service)
        service_thread.daemon = True
        service_thread.start()

        # Déclenchement du flow
        trigger_flow()

        # Garder le programme en vie
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 Arrêt du programme...")
        sys.exit(0)