import os
import sys
import socket
import traceback
from pathlib import Path
from dotenv import load_dotenv
from pymilvus import connections, Collection, utility

# Use absolute path for loading .env
env_path = "/Users/vinh/Documents/LightRAG/.env"
load_dotenv(dotenv_path=env_path)

def check_port_open(host, port):
    """Check if a port is open on a given host."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception as e:
        print(f" ❌ Erreur lors de la vérification du port: {e}")
        return False

def clear_milvus_database():
    try:
        # Récupérer les variables d'environnement
        milvus_uri = os.environ.get("MILVUS_URI")
        milvus_username = os.environ.get("MILVUS_USERNAME")
        milvus_password = os.environ.get("MILVUS_PASSWORD")
        
        # Vérifier si l'URI est définie
        if not milvus_uri:
            raise ValueError("MILVUS_URI n'est pas définie dans le fichier .env")
        
        print(f" ℹ️ MILVUS_URI: {milvus_uri}")
        
        # Extraire l'hôte et le port de l'URI
        from urllib.parse import urlparse
        parsed_uri = urlparse(milvus_uri)
        host = parsed_uri.hostname
        port = parsed_uri.port
        
        print(f" 🔍 Diagnostic de connexion:")
        print(f"   - Hôte: {host}")
        print(f"   - Port: {port}")
        
        # Vérifier si le port est ouvert
        if not check_port_open(host, port):
            print(f" ❌ Le port {port} sur {host} est fermé ou inaccessible!")
            sys.exit(1)
        
        # Ajouter le préfixe tcp:// s'il n'est pas présent
        if not milvus_uri.startswith(('tcp://', 'http://', 'https://')):
            milvus_uri = f"tcp://{milvus_uri}"
        
        db_name = 'lightrag'
        
        print(" 🧹 Nettoyage de la base de données Milvus en cours...")
        print(f" 🌐 URI: {milvus_uri}")
        print(f" 📂 Base de données: {db_name}")
        
        # Paramètres de connexion
        connect_params = {
            "alias": "default",
            "uri": milvus_uri,
            "db_name": db_name
        }
        
        # Ajouter les identifiants si disponibles
        if milvus_username and milvus_password:
            connect_params["user"] = milvus_username
            connect_params["password"] = milvus_password
            print(" 🔐 Connexion avec authentification")
        
        # Connexion à Milvus avec gestion des erreurs détaillées
        try:
            connections.connect(**connect_params)
            print(" ✅ Connexion à Milvus réussie!")
        except Exception as conn_error:
            print(f" ❌ Erreur de connexion à Milvus: {conn_error}")
            print(f" 🔍 Détails de connexion:")
            print(f"   - URI: {milvus_uri}")
            print(f"   - Base de données: {db_name}")
            print(f"   - Nom d'utilisateur: {milvus_username}")
            print(" 🕵️ Traceback détaillé:")
            traceback.print_exc()
            sys.exit(1)
        
        # Liste des collections existantes
        collections = utility.list_collections()
        print(f" 📋 Collections existantes: {collections}")
        
        # Suppression de toutes les collections
        for coll_name in collections:
            try:
                collection = Collection(coll_name)
                collection.drop()
                print(f" ✅ Collection {coll_name} supprimée avec succès")
            except Exception as e:
                print(f" ❌ Erreur lors de la suppression de {coll_name}: {str(e)}")
    
    except Exception as e:
        print(f" ❌ Erreur lors du nettoyage de la base de données Milvus: {e}")
        traceback.print_exc()
        sys.exit(1)
    finally:
        try:
            connections.disconnect("default")
        except:
            pass

if __name__ == "__main__":
    clear_milvus_database()
