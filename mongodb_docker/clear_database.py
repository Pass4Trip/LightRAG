import os
from pathlib import Path
from dotenv import load_dotenv
from pymongo import MongoClient

# Charger les variables d'environnement
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

def clear_mongodb_database():
    try:
        # Récupérer les variables d'environnement avec les mêmes noms que dans LightRAG
        mongodb_uri = os.environ.get("MONGO_URI", "mongodb://root:root@localhost:27017/")
        db_name = os.environ.get("MONGO_DATABASE", "LightRAG")
        
        print(f" Connexion à MongoDB...")
        print(f" Base de données cible: {db_name}")
        print(f" URI: {mongodb_uri}")
        
        # Connexion à MongoDB
        client = MongoClient(mongodb_uri)
        db = client[db_name]
        
        # Tester la connexion
        db.command('ping')
        print(" Connexion à MongoDB réussie!")
        
        # Liste des collections
        collections = db.list_collection_names()
        
        if not collections:
            print("\n Aucune collection trouvée dans la base de données.")
            return
        
        print("\n Collections trouvées:")
        for coll_name in collections:
            count = db[coll_name].count_documents({})
            print(f"   - {coll_name} ({count} documents)")
        
        # Demander confirmation
        confirmation = input(f"\n Êtes-vous sûr de vouloir supprimer toutes les collections de la base {db_name}? (oui/non): ")
        
        if confirmation.lower() != "oui":
            print("\n Opération annulée.")
            return
        
        # Supprimer chaque collection
        for coll_name in collections:
            try:
                db[coll_name].drop()
                print(f" Collection {coll_name} supprimée avec succès")
            except Exception as e:
                print(f" Erreur lors de la suppression de {coll_name}: {str(e)}")
        
        print("\n Nettoyage terminé!")
        
        # Vérifier qu'il ne reste plus de collections
        remaining_collections = db.list_collection_names()
        if not remaining_collections:
            print(" La base de données est maintenant vide")
        else:
            print(f" Il reste encore {len(remaining_collections)} collection(s)")
        
        # Fermer la connexion
        client.close()
        print("\n Déconnexion réussie!")
        
    except Exception as e:
        print(f" Erreur: {str(e)}")

if __name__ == "__main__":
    clear_mongodb_database()
