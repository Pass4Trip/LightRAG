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
        
        if not collections:
            print("\n⚠️ Aucune collection trouvée dans la base de données.")
            return
        
        print("\n📋 Collections à supprimer:")
        for coll_name in collections:
            print(f"   - {coll_name}")
        
        # Demander confirmation
        confirmation = input(f"\n⚠️ Êtes-vous sûr de vouloir supprimer toutes les collections de la base {db_name}? (oui/non): ")
        
        if confirmation.lower() != "oui":
            print("\n❌ Opération annulée.")
            return
        
        # Supprimer chaque collection
        for coll_name in collections:
            try:
                collection = Collection(coll_name)
                collection.drop()
                print(f"✅ Collection {coll_name} supprimée avec succès")
            except Exception as e:
                print(f"❌ Erreur lors de la suppression de {coll_name}: {str(e)}")
        
        print("\n✅ Nettoyage terminé!")
        
        # Vérifier qu'il ne reste plus de collections
        remaining_collections = utility.list_collections()
        if not remaining_collections:
            print("📁 La base de données est maintenant vide")
        else:
            print(f"⚠️ Il reste encore {len(remaining_collections)} collection(s)")
        
        # Déconnexion
        connections.disconnect("default")
        print("\n🔌 Déconnexion réussie!")
        
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")

if __name__ == "__main__":
    clear_milvus_database()
