from pymilvus import connections, Collection, utility

def test_milvus_connection():
    try:
        # Connexion à Milvus
        connections.connect(
            alias="default",
            host='localhost',
            port='19530'
        )
        
        print("✅ Connexion à Milvus réussie!")
        
        # Liste des collections existantes
        print("\nCollections existantes:")
        print(utility.list_collections())
        
        # Déconnexion
        connections.disconnect("default")
        print("\nDéconnexion réussie!")
        
    except Exception as e:
        print(f"❌ Erreur lors de la connexion: {str(e)}")

if __name__ == "__main__":
    test_milvus_connection()
