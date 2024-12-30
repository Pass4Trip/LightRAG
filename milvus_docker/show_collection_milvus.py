import os
from pathlib import Path
from dotenv import load_dotenv
from pymilvus import connections, Collection, utility

# Charger les variables d'environnement
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

def test_milvus_connection():
    try:
        # Récupérer les variables d'environnement
        milvus_uri = os.environ.get("MILVUS_URI", "tcp://localhost:19530")
        db_name = os.environ.get("MILVUS_DB_NAME", "lightrag")
        
        # Connexion à Milvus
        connections.connect(
            alias="default",
            uri=milvus_uri,
            db_name=db_name
        )
        
        print(f"✅ Connexion à Milvus réussie!")
        print(f"📁 Base de données: {db_name}")
        
        # Liste des collections existantes
        collections = utility.list_collections()
        print("\n📋 Collections existantes:")
        if not collections:
            print("   Aucune collection trouvée")
        else:
            for coll_name in collections:
                try:
                    collection = Collection(coll_name)
                    collection.load()
                    num_entities = collection.num_entities
                    print(f"\n   Collection: {coll_name}")
                    print(f"   - Nombre d'entités: {num_entities}")
                    
                    # Print schema details
                    print("   - Schema:")
                    for field in collection.schema.fields:
                        print(f"     * {field.name}:")
                        print(f"       - Type: {field.dtype}")
                        if field.params:
                            print(f"       - Params: {field.params}")
                        if field.is_primary:
                            print("       - Primary Key: True")
                        if field.auto_id:
                            print("       - Auto ID: True")
                        if field.description:
                            print(f"       - Description: {field.description}")
                            
                    # Print index details
                    print(f"   - Index: {collection.indexes[0].params if collection.indexes else 'Aucun index'}")
                    collection.release()
                except Exception as e:
                    print(f"\n   Collection: {coll_name}")
                    print(f"   - Erreur lors de la lecture des détails: {str(e)}")
        
        # Déconnexion
        connections.disconnect("default")
        print("\n🔌 Déconnexion réussie!")
        
    except Exception as e:
        print(f"❌ Erreur lors de la connexion: {str(e)}")

if __name__ == "__main__":
    test_milvus_connection()
