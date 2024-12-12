from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType, utility
import numpy as np

def create_test_collection():
    try:
        # Connexion à Milvus
        connections.connect(alias="default", host='localhost', port='19530')
        print("✅ Connecté à Milvus")

        # Définition des champs de la collection
        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=200),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=128)
        ]

        # Création du schéma
        schema = CollectionSchema(fields=fields, description="Collection de test pour embeddings")

        # Création de la collection
        collection_name = "test_collection"
        
        # Suppression de la collection si elle existe déjà
        if utility.has_collection(collection_name):
            utility.drop_collection(collection_name)
            
        collection = Collection(name=collection_name, schema=schema)
        print(f"✅ Collection '{collection_name}' créée")

        # Création d'un index pour les recherches rapides
        index_params = {
            "metric_type": "L2",
            "index_type": "IVF_FLAT",
            "params": {"nlist": 128}
        }
        collection.create_index(field_name="embedding", index_params=index_params)
        print("✅ Index créé")

        # Préparation des données de test
        num_entities = 3
        text_data = [
            "Premier document de test",
            "Deuxième document pour l'exemple",
            "Troisième document avec des embeddings"
        ]
        # Simulation d'embeddings (en pratique, ils viendraient d'un modèle)
        embeddings = np.random.rand(num_entities, 128).tolist()

        # Insertion des données
        data = [
            text_data,
            embeddings
        ]
        collection.insert(data)
        print(f"✅ {num_entities} documents insérés")

        # Chargement de la collection en mémoire
        collection.load()

        # Test de recherche simple
        search_embedding = np.random.rand(128).tolist()
        search_param = {
            "metric_type": "L2",
            "params": {"nprobe": 10}
        }
        
        results = collection.search(
            data=[search_embedding],
            anns_field="embedding",
            param=search_param,
            limit=2,
            output_fields=["text"]
        )

        print("\nRésultats de la recherche:")
        for hits in results:
            for hit in hits:
                print(f"ID: {hit.id}, Distance: {hit.distance}, Texte: {hit.entity.get('text')}")

        # Déconnexion
        connections.disconnect("default")
        print("\n✅ Test complété avec succès!")

    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
        # S'assurer de la déconnexion même en cas d'erreur
        try:
            connections.disconnect("default")
        except:
            pass

if __name__ == "__main__":
    create_test_collection()
