import os
from pathlib import Path
from dotenv import load_dotenv
from pymilvus import connections, Collection, utility

# Charger les variables d'environnement
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

def clear_milvus_database():
    try:
        # Récupérer les variables d'environnement
        milvus_uri = os.environ.get("MILVUS_URI", "tcp://localhost:19530")
        db_name = os.environ.get("MILVUS_DB_NAME", "lightrag")
        
        print("🔥 Nettoyage de la base de données Milvus en cours...")
        print(f" URI: {milvus_uri}")
        print(f" Base de données: {db_name}")
        
        # Connexion à Milvus
        connections.connect(
            alias="default",
            uri=milvus_uri,
            db_name=db_name
        )
        
        print("✅ Connexion à Milvus réussie!")
        
        # Liste des collections existantes
        collections = utility.list_collections()
        
        if not collections:
            print("\n⚠️ Aucune collection trouvée dans la base de données Milvus.")
            return
        
        # Supprimer chaque collection
        for coll_name in collections:
            try:
                collection = Collection(coll_name)
                collection.drop()
                print(f"✅ Collection {coll_name} supprimée avec succès")
            except Exception as e:
                print(f"❌ Erreur lors de la suppression de {coll_name}: {str(e)}")
    
    except Exception as e:
        print(f"❌ Erreur lors de la suppression des collections Milvus : {str(e)}")
    finally:
        connections.disconnect("default")

if __name__ == "__main__":
    clear_milvus_database()
