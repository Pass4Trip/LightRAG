from pymilvus import connections, Collection, utility

# Paramètres de connexion à Milvus
MILVUS_HOST = "localhost"
MILVUS_PORT = "19530"
COLLECTION_NAME = "chunks"
MILVUS_DB_NAME = "lightrag"

def connect_to_milvus():
    """
    Connexion à Milvus.
    """
    connections.connect(alias="default", host=MILVUS_HOST, port=MILVUS_PORT, db_name=MILVUS_DB_NAME)
    print(f"✅ Connecté à Milvus (DB: {MILVUS_DB_NAME})!")

def list_collections():
    """
    Liste toutes les collections disponibles.
    """
    try:
        collections = utility.list_collections()
        print("📋 Collections disponibles :")
        for collection in collections:
            print(f" - {collection}")
        return collections
    except Exception as e:
        print(f"❌ Erreur lors de la récupération des collections : {e}")
        return []

def list_chunks(limit=20):
    """
    Liste les chunks avec leurs IDs.
    """
    collection = None
    try:
        # Vérifier si la collection existe
        collections = list_collections()
        if COLLECTION_NAME not in collections:
            raise ValueError(f"❌ La collection '{COLLECTION_NAME}' n'existe pas.")

        # Charger la collection
        collection = Collection(COLLECTION_NAME)
        collection.load()

        # Requête pour récupérer les chunks
        print(f"\n🔍 Récupération des {limit} premiers chunks...")
        
        # Afficher les noms de champs disponibles
        schema = collection.schema
        print("📊 Schéma de la collection :")
        for field in schema.fields:
            print(f" - {field.name} (type: {field.dtype})")

        # Requête pour obtenir les IDs
        results = collection.query(
            expr="",
            output_fields=["id"],
            limit=limit
        )

        # Affichage des résultats
        if results:
            print("\n📝 Liste des chunks :")
            for result in results:
                chunk_id = result.get('id', 'N/A')
                print(f"🆔 ID: {chunk_id}")
        else:
            print("❌ Aucun chunk trouvé dans la collection.")

    except Exception as e:
        print(f"❌ Erreur : {e}")
    finally:
        if collection:
            collection.release()
            print("🔌 Collection relâchée.")
        connections.disconnect("default")
        print("🔌 Déconnexion réussie!")

def retrieve_chunk_by_id(chunk_id):
    """
    Retrouve un chunk spécifique par son ID et affiche tous les champs disponibles.
    """
    collection = None
    try:
        # Connexion à Milvus
        connections.connect(alias="default", host=MILVUS_HOST, port=MILVUS_PORT, db_name=MILVUS_DB_NAME)
        
        # Vérifier si la collection existe
        collections = utility.list_collections()
        if COLLECTION_NAME not in collections:
            raise ValueError(f"❌ La collection '{COLLECTION_NAME}' n'existe pas.")

        # Charger la collection
        collection = Collection(COLLECTION_NAME)
        collection.load()

        # Récupérer le schéma de la collection pour connaître tous les champs
        schema = collection.schema
        all_fields = [field.name for field in schema.fields]
        print(f"🔎 Champs disponibles : {all_fields}")

        # Requête pour retrouver le chunk avec tous les champs
        print(f"🔍 Recherche du chunk avec l'ID : {chunk_id}")
        
        results = collection.query(
            expr=f"id == '{chunk_id}'",
            output_fields=all_fields,
            limit=1
        )

        # Affichage des résultats
        if results:
            chunk = results[0]
            print("\n📄 Détails complets du chunk :")
            
            # Afficher tous les champs avec leurs valeurs
            for field in all_fields:
                value = chunk.get(field)
                
                # Traitement spécifique pour certains types de champs
                if field == 'vector':
                    if value:
                        print(f"📊 {field.capitalize()} :")
                        print(f"   - Dimensions : {len(value)}")
                        print(f"   - Premières valeurs : {value[:5]}")
                        print(f"   - Dernières valeurs : {value[-5:]}")
                    else:
                        print(f"📊 {field.capitalize()} : Aucune valeur")
                elif field == 'content':
                    if value:
                        print(f"📝 {field.capitalize()} ({len(value)} caractères) :")
                        print(value[:1000] + ('...' if len(value) > 1000 else ''))
                else:
                    # Affichage standard pour les autres champs
                    print(f"📋 {field.capitalize()}: {value}")

        else:
            print(f"❌ Aucun chunk trouvé avec l'ID : {chunk_id}")

    except Exception as e:
        print(f"❌ Erreur : {e}")
    finally:
        if collection:
            collection.release()
            print("🔌 Collection relâchée.")
        connections.disconnect("default")
        print("🔌 Déconnexion réussie!")

if __name__ == "__main__":
    connect_to_milvus()
    
    # Exemple d'utilisation : décommentez et modifiez l'ID selon vos besoins
    # retrieve_chunk_by_id("chunk-047130a783b12bb89d6d6e08933e7864")
    
    #list_chunks(limit=5)  # Récupère les 20 premiers chunks
    retrieve_chunk_by_id("chunk-047130a783b12bb89d6d6e08933e7864")  # Exemple de chunk-ID