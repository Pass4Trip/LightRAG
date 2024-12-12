import os
from dotenv import load_dotenv
from lightrag import LightRAG, QueryParam

# Chargement des variables d'environnement
load_dotenv()

def init_lightrag():
    """
    Initialise LightRAG avec MongoDB, Neo4j et Milvus
    Utilise les variables d'environnement pour les connexions
    """
    working_dir = "./data"
    
    # Création du répertoire de travail s'il n'existe pas
    if not os.path.exists(working_dir):
        os.makedirs(working_dir)
    
    # Initialisation de LightRAG
    rag = LightRAG(
        working_dir=working_dir,
        kv_storage="MongoKVStorage",      # MongoDB pour le stockage clé-valeur
        vector_storage="MilvusVectorDBStorage",  # Milvus pour les vecteurs
        graph_storage="Neo4JStorage",     # Neo4j pour le graphe
        log_level="DEBUG"
    )
    
    return rag

def query_lightrag(question: str, mode: str = "hybrid"):
    """
    Interroge LightRAG avec une question
    
    Args:
        question (str): La question à poser
        mode (str): Mode de recherche ('naive', 'local', 'global', 'hybrid')
    
    Returns:
        str: La réponse générée
    """
    rag = init_lightrag()
    return rag.query(question, param=QueryParam(mode=mode))

if __name__ == "__main__":
    # Exemple d'utilisation
    question = "Quels sont les restaurants avec une bonne accessibilité PMR?"
    response = query_lightrag(question)
    print(f"\nQuestion: {question}")
    print(f"\nRéponse: {response}")
