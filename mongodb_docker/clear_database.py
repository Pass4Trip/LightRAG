import os
from pathlib import Path
from dotenv import load_dotenv
from pymongo import MongoClient

# Charger les variables d'environnement
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

def clear_mongodb_database():
    try:
        print("🔥 Nettoyage de la base de données MongoDB en cours...")
        # Récupérer les variables d'environnement avec les mêmes noms que dans LightRAG
        mongodb_uri = os.environ.get("MONGO_URI", "mongodb://root:root@localhost:27017/")
        db_name = os.environ.get("MONGO_DATABASE", "LightRAG")
        
        print(f" URI: {mongodb_uri}")
        print(f" Base de données cible: {db_name}")
        
        # Connexion à MongoDB
        client = MongoClient(mongodb_uri)
        db = client[db_name]
        
        # Tester la connexion
        db.command('ping')
        print(" Connexion à MongoDB réussie!")
        
        # Liste des collections
        collections = db.list_collection_names()
        
        if not collections:
            print("\n Aucune collection trouvée dans la base de données MongoDB.")
            return
        
        print(f"Traitement de la base de données: {db_name}")
        
        # Supprimer chaque collection
        for coll_name in collections:
            try:
                db[coll_name].drop()
                print(f" Collection {coll_name} supprimée avec succès")
            except Exception as e:
                print(f" Erreur lors de la suppression de {coll_name}: {str(e)}")
        
    except Exception as e:
        print(f" Erreur lors de la suppression des collections MongoDB : {str(e)}")
    finally:
        client.close()

if __name__ == "__main__":
    clear_mongodb_database()
