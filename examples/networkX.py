import networkx as nx
import xml.etree.ElementTree as ET
import os
import random

def load_and_process_graphml(file_path):
    # Cette fonction charge un fichier GraphML, extrait les noeuds et les arêtes, et retourne les arêtes et l'arbre XML.
    print(f"Chargement du fichier GraphML depuis: {file_path}")
    # Chargement du fichier GraphML
    try:
        tree = ET.parse(file_path)
        print("Fichier GraphML chargé avec succès.")
        root = tree.getroot()
    except Exception as e:
        print(f"Erreur lors de la lecture du fichier: {e}")
        return None

    # Espaces de noms
    ns = {'graphml': 'http://graphml.graphdrawing.org/xmlns'}

    # Récupération des noeuds et des arêtes
    edges = []
    for edge in root.findall('.//graphml:edge', ns):
        #print(f"Traitement de l'arête: source={edge.get('source')}, target={edge.get('target')}")
        source = edge.get('source')
        target = edge.get('target')
        edges.append((source, target))

    return edges, root

def create_graph(edges):
    # Cette fonction crée un graphe NetworkX à partir d'une liste d'arêtes.
    print("Création du graph NetworkX...")
    G = nx.Graph()
    # Ajout des edges à partir de la liste au graph NetworkX
    for source, target in edges:
        G.add_edge(source, target)
        #print(f"Ajout d'une arête au graph: source={source}, target={target}")
    return G

def find_neighbors(graph, entity):
    # Cette fonction trouve les voisins directs d'une entité donnée dans le graphe.
    # Elle ne retourne que les voisins qui sont de type 'RESTAURANT'.
    # Retourne les voisins de l'entité donnée, filtrant uniquement les entités de type 'RESTAURANT'
    if entity in graph:
        neighbors = [n for n in graph.neighbors(entity) if 'RESTAURANT' in n]
        return neighbors
    else:
        print(f"L'entité '{entity}' n'existe pas dans le graph")
        return []

def list_entities_without_edges(graph):
    # Cette fonction liste toutes les entités dans le graphe qui n'ont aucune arête connectée.
    # Liste toutes les entités qui n'ont aucun edge
    entities_without_edges = [node for node in graph.nodes if graph.degree(node) == 0]
    print("Entités sans arêtes dans NetworkX :", entities_without_edges)
    return entities_without_edges

def list_entities_not_in_graph(root, graph):
    # Cette fonction liste les entités présentes dans le fichier GraphML mais absentes dans le graphe NetworkX.
    ns = {'graphml': 'http://graphml.graphdrawing.org/xmlns'}

    # Liste des entités présentes dans le fichier GraphML
    entities_in_graphml = {node.get('id') for node in root.findall('.//graphml:node', ns)}
    # Liste des entités présentes dans le graphe NetworkX
    entities_in_graph = set(graph.nodes())

    # Trouver les entités présentes dans GraphML mais pas dans NetworkX
    entities_not_in_graph = entities_in_graphml - entities_in_graph

    # Afficher les entités absentes dans le graphe NetworkX
    if entities_not_in_graph:
        print(f"Nombre d'entités présentes dans GraphML mais absentes dans le graphe NetworkX: {len(entities_not_in_graph)}")
        print("Liste des entités absentes dans le graphe NetworkX:")
        for entity in entities_not_in_graph:
            print(entity)
    else:
        print("Toutes les entités présentes dans GraphML sont également dans le graphe NetworkX.")

def match_entity_to_restaurant(entities_without_edges, restaurant_descriptions):
    # Cette fonction cherche des correspondances entre les entités sans arêtes et les descriptions des restaurants fournies.
    print("Correspondance des entités sans arêtes avec les restaurants...")
    # Correspondance entre les entités sans arêtes et les descriptions des restaurants
    matches = {}
    for entity in entities_without_edges:
        for restaurant, description in restaurant_descriptions.items():
            if entity.lower() in description.lower() or entity.lower() in restaurant.lower():
                matches[entity] = restaurant
                print(f"Correspondance trouvée: '{entity}' correspond à '{restaurant}'")
                break
    return matches

def load_restaurant_descriptions(file_path):
    # Cette fonction charge les descriptions des restaurants à partir d'un fichier texte.
    # Elle retourne un dictionnaire associant chaque nom de restaurant à sa description.
    print(f"Chargement des descriptions des restaurants depuis: {file_path}")
    # Charger les descriptions des restaurants à partir du fichier fourni
    restaurant_descriptions = {}
    print("Début du traitement des descriptions des restaurants...")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            restaurants = content.split('****************')
            for restaurant in restaurants:
                lines = restaurant.split('\n')
                name = lines[0].replace('Restaurant : ', '').strip()
                description = ' '.join(lines[2:]).strip()
                restaurant_descriptions[name] = description
    except Exception as e:
        print(f"Erreur lors de la lecture du fichier des restaurants: {e}")
    return restaurant_descriptions

def main(entity):
    # Fonction principale qui gère le flux de traitement :
    # 1. Charger le fichier GraphML et extraire les arêtes.
    # 2. Créer le graphe NetworkX.
    # 3. Trouver les voisins de l'entité spécifiée.
    # 4. Identifier les entités sans arêtes.
    # 5. Charger les descriptions des restaurants.
    # 6. Correspondre les entités sans arêtes avec des restaurants.
    # Nom du fichier d'entrée
    file_path = '/Users/vinh/Documents/LightRAG/examples/restaurant_openai_p4t_v2/graph_chunk_entity_relation.graphml'
    restaurant_file_path = '/Users/vinh/Documents/LightRAG/resto.txt'
    
    # Charger et prétraiter le fichier
    edges, root = load_and_process_graphml(file_path)
    if edges is None:
        return

    # Créer le graph
    graph = create_graph(edges)
    
    # Exemple d'utilisation pour trouver les voisins d'une entité
    neighbors = find_neighbors(graph, entity)
    print(f"Les voisins de l'entité '{entity}' sont: {neighbors}")

    # Vérifier les entités sans arêtes
    entities_without_edges = list_entities_without_edges(graph)

    # Charger les descriptions des restaurants
    restaurant_descriptions = load_restaurant_descriptions(restaurant_file_path)

    # Trouver les correspondances entre entités sans arêtes et restaurants
    matches = match_entity_to_restaurant(entities_without_edges, restaurant_descriptions)
    for entity, restaurant in matches.items():
        print(f"L'entité '{entity}' correspond au restaurant '{restaurant}'")
        # Proposition d'ajout d'une arête entre l'entité et le restaurant
        print(f"Proposition d'ajout: <edge source=\"{entity}\" target=\"{restaurant}\" />")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python script.py <entity>")
    else:
        entity = sys.argv[1]
        main(entity)
