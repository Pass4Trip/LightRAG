from pymilvus import connections, utility

# Charger la base de données depuis l'environnement
import os
db_name = os.environ.get("MILVUS_DB_NAME", "lightrag")

def connect_to_milvus():
    """
    Connexion à Milvus et affichage de la base sélectionnée.
    """
    connections.connect(alias="default", host="localhost", port="19530", db_name=db_name)
    print(f"✅ Connecté à Milvus avec la base de données : {db_name}")
    print(f"📋 Bases disponibles : {utility.list_databases()}")


connect_to_milvus()