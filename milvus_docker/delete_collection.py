from pymilvus import connections, utility
import argparse

def delete_collection(collection_name: str):
    """
    Supprime une collection Milvus.
    
    Args:
        collection_name (str): Nom de la collection à supprimer
    """
    try:
        # Connexion à Milvus
        connections.connect(alias="default", host='localhost', port='19530')
        print(f"✅ Connecté à Milvus")

        # Vérifier si la collection existe
        if not utility.has_collection(collection_name):
            print(f"❌ La collection '{collection_name}' n'existe pas")
            return

        # Suppression de la collection
        utility.drop_collection(collection_name)
        print(f"✅ Collection '{collection_name}' supprimée avec succès")

    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
    finally:
        # S'assurer de la déconnexion
        try:
            connections.disconnect("default")
            print("✅ Déconnexion réussie")
        except:
            pass

def main():
    parser = argparse.ArgumentParser(description='Supprime une collection Milvus')
    parser.add_argument('collection', type=str, help='Nom de la collection à supprimer')
    
    args = parser.parse_args()
    delete_collection(args.collection)

if __name__ == "__main__":
    main()
