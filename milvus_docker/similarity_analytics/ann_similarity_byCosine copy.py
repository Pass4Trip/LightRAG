import numpy as np
import logging
from typing import List, Dict

# Configuration du logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_embedding(text: str, model="text-embedding-3-small") -> np.ndarray:
    """
    Génère un embedding pour un texte donné.
    
    Args:
        text (str): Texte à vectoriser
        model (str): Modèle d'embedding
    
    Returns:
        np.ndarray: Vecteur d'embedding
    """
    try:
        from openai import OpenAI
        client = OpenAI()
        
        response = client.embeddings.create(
            input=text,
            model=model
        )
        return np.array(response.data[0].embedding)
    except Exception as e:
        logger.error(f"Erreur lors de la génération de l'embedding : {e}")
        # Embedding aléatoire si OpenAI échoue
        return np.random.rand(1536)

def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """
    Calcule la similarité cosinus entre deux vecteurs.
    
    Args:
        vec1 (np.ndarray): Premier vecteur
        vec2 (np.ndarray): Deuxième vecteur
    
    Returns:
        float: Distance cosinus (plus proche de 0 = plus similaire)
    """
    return 1 - np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

def compute_ann_correlations(
    source_text: str, 
    target_texts: List[str], 
    top_k: int = 5, 
    distance_threshold: float = 0.7
) -> List[Dict]:
    """
    Calcule les corrélations ANN entre un texte source et des textes cibles.
    
    Args:
        source_text (str): Texte source
        target_texts (List[str]): Liste des textes cibles
        top_k (int): Nombre maximum de résultats
        distance_threshold (float): Seuil de distance
    
    Returns:
        List[Dict]: Liste des corrélations
    """
    # Générer l'embedding du texte source
    source_embedding = generate_embedding(source_text)
    
    # Générer les embeddings des textes cibles
    target_embeddings = [generate_embedding(text) for text in target_texts]
    
    # Calculer les distances
    distances = [
        cosine_similarity(source_embedding, target_emb) 
        for target_emb in target_embeddings
    ]
    
    # Créer une liste de résultats
    correlations = [
        {
            "target_text": target_texts[i],
            "distance": distances[i],
            "index": i
        }
        for i in range(len(target_texts))
        if distances[i] < distance_threshold
    ]
    
    # Trier par distance
    correlations.sort(key=lambda x: x["distance"])
    
    # Retourner les top_k résultats
    return correlations[:top_k]

def main():
    # Exemple de textes
    source_text = "lea est passionnée par les pizzas napolitaines"
    target_texts = [
        "Le restaurant se distingue par la diversité de ses plats, incluant des classiques asiatiques et des spécialités.<SEP>Les clients apprécient particulièrement la variété des plats, en particulier les pizzas et les pâtes."
    ]
    
    # Calculer les corrélations
    correlations = compute_ann_correlations(
        source_text, 
        target_texts, 
        top_k=5, 
        distance_threshold=0.7
    )
    
    # Afficher les résultats
    print("Corrélations ANN :")
    for corr in correlations:
        print(f"Texte: {corr['target_text']}")
        print(f"Distance: {corr['distance']}\n")

if __name__ == "__main__":
    main()
