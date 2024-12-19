from pymilvus import connections, utility

# Paramètres de connexion
MILVUS_HOST = "localhost"
MILVUS_PORT = "19530"
MILVUS_DB_NAME = "lightrag"

connections.connect(alias="default", host=MILVUS_HOST, port=MILVUS_PORT, db_name=MILVUS_DB_NAME)
collections = utility.list_collections()
print("Collections existantes :", collections)