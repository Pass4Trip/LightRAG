#!/usr/bin/env python3
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv
import sys
from pathlib import Path

# Charger les variables d'environnement
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

def get_zulli_info(tx):
    """
    Récupère toutes les informations sur Zulli et ses relations
    """
    query = """
    MATCH (n {custom_id: 'Zulli'})-[r]-(m)
    RETURN 
        n.description as zulli_desc,
        n.entity_type as zulli_type,
        type(r) as relation_type,
        r.description as relation_desc,
        m.description as related_desc,
        m.entity_type as related_type
    """
    
    result = tx.run(query)
    info = []
    for record in result:
        info.append({
            'zulli_desc': record['zulli_desc'],
            'zulli_type': record['zulli_type'],
            'relation_type': record['relation_type'],
            'relation_desc': record['relation_desc'],
            'related_desc': record['related_desc'],
            'related_type': record['related_type']
        })
    return info

def get_zulli_restaurant_preferences(tx):
    """
    Récupère les restaurants qui correspondent aux préférences de Zulli
    """
    query = """
    MATCH (z {custom_id: 'Zulli'})-[:LIKES|PREFERS]->(p)
    WITH z, collect(p) as preferences
    MATCH (r:Restaurant)
    WHERE ALL(pref IN preferences WHERE (r)-[:HAS_CHARACTERISTIC]->(pref))
    RETURN r.name as restaurant_name, 
           r.description as restaurant_desc,
           r.location as restaurant_location
    """
    
    result = tx.run(query)
    restaurants = []
    for record in result:
        restaurants.append({
            'name': record['restaurant_name'],
            'description': record['restaurant_desc'],
            'location': record['restaurant_location']
        })
    return restaurants

def main():
    # Connexion à Neo4j
    uri = os.getenv("NEO4J_URI", "neo4j://vps-af24e24d.vps.ovh.net:32719")
    username = os.getenv("NEO4J_USERNAME", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "my-initial-password")
    
    driver = GraphDatabase.driver(uri, auth=(username, password))
    
    try:
        with driver.session() as session:
            # Récupérer les informations générales sur Zulli
            info = session.execute_read(get_zulli_info)
            
            if not info:
                print("Aucune information trouvée sur Zulli")
                return
            
            print("\nInformations sur Zulli :")
            print("=" * 50)
            
            # Afficher les informations de manière organisée
            for item in info:
                print(f"\nType: {item['zulli_type']}")
                print(f"Description: {item['zulli_desc']}")
                print(f"Relation: {item['relation_type']}")
                print(f"Description relation: {item['relation_desc']}")
                print(f"Entité liée ({item['related_type']}): {item['related_desc']}")
                print("-" * 50)
            
            # Récupérer et afficher les restaurants correspondant aux préférences
            print("\nRestaurants recommandés pour Zulli :")
            print("=" * 50)
            
            restaurants = session.execute_read(get_zulli_restaurant_preferences)
            if not restaurants:
                print("Aucun restaurant correspondant aux préférences de Zulli n'a été trouvé")
            else:
                for restaurant in restaurants:
                    print(f"\nNom: {restaurant['name']}")
                    print(f"Description: {restaurant['description']}")
                    print(f"Emplacement: {restaurant['location']}")
                    print("-" * 50)
                
    finally:
        driver.close()

if __name__ == "__main__":
    main()
