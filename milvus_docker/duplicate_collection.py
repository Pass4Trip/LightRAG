import os
from pathlib import Path
from dotenv import load_dotenv
from pymilvus import connections, Collection, utility, Partition
import json

# Charger les variables d'environnement
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)


def duplicate_to_partition(collection_name="entities", partition_name="entities_filtered", filtered_ids=None):

        # Récupérer les variables d'environnement pour la connexion
        milvus_uri = os.environ.get("MILVUS_URI", "tcp://localhost:19530")
        db_name = os.environ.get("MILVUS_DB_NAME", "lightrag")
        
        # Se connecter à Milvus
        connections.connect(
            alias="default",
            uri=milvus_uri,
            db_name=db_name
        )
        print(f"✅ Connecté au serveur Milvus")

        # Charger la collection existante
        collection = Collection(collection_name)
        collection.load()
        print(f"📚 Collection '{collection_name}' chargée")

        # Créer la nouvelle partition
        partition = Partition(
           collection=collection,
           name=partition_name
        )
    
        # collection.create_partition(partition_name)
        # print(f"✅ Nouvelle partition créée : '{partition_name}'")

        # Construire l'expression de filtrage
        filter_expr = 'id in [' + ', '.join(f'"{id}"' for id in filtered_ids) + ']'
        print(f"🔍 Expression de filtrage : {filter_expr}")

        # Récupérer d'abord un document pour voir tous les champs disponibles
        sample = collection.query(
            expr="",
            output_fields=["*", "dynamic_fields"],  
            limit=1
        )
        
        if sample:
            # Extraire tous les champs disponibles (fixes et dynamiques)
            available_fields = set(["*", "dynamic_fields"])  
            if "dynamic_fields" in sample[0]:
                print("\n🔄 Champs dynamiques trouvés dans le premier document :")
                print(f"  {sample[0]['dynamic_fields']}")
            
            # Ajouter tous les autres champs détectés
            available_fields.update(sample[0].keys())
            
            print("\n📋 Tous les champs détectés :")
            for field in available_fields:
                print(f"  - {field}")
            
            # Convertir en liste pour la requête
            available_fields = list(available_fields)
        
        # Récupérer les données avec l'expression de filtrage
        results = collection.query(
            expr=filter_expr,
            output_fields=available_fields,  
            limit=10000
        )

        print(f"\n🔍 Nombre de résultats trouvés : {len(results)}")
        if results:
            print("📝 Structure du premier résultat :")
            for key, value in results[0].items():
                if key == "vector":
                    print(f"  - {key}: [vecteur de dimension {len(value)}]")
                else:
                    print(f"  - {key}: {value}")

        # Préparation des données pour l'insertion dans la nouvelle partition
        # Initialiser un dictionnaire pour stocker toutes les données
        insert_data = {}
        
        # Parcourir tous les résultats
        for result in results:
            # Traiter les champs standard
            for field in ['id', 'vector']:
                if field not in insert_data:
                    insert_data[field] = []
                
                # Conversion spéciale pour certains champs
                value = result.get(field)
                if field == 'vector' and value is not None:
                    # Convertir le vecteur en liste de float si nécessaire
                    if hasattr(value, 'tolist'):
                        value = value.tolist()
                    value = [float(x) for x in value]
                elif field == 'id':
                    value = str(value)
                
                insert_data[field].append(value)
        
        # Gérer les champs dynamiques
        dynamic_fields = result.get('dynamic_fields', {}) if results else {}
        
        # Ajouter les champs dynamiques
        if dynamic_fields:
            print("\n🔍 Champs dynamiques détectés :")
            for dyn_field, dyn_value in dynamic_fields.items():
                print(f"  - {dyn_field}")
                if dyn_field not in insert_data:
                    insert_data[dyn_field] = []
                
                # Collecter les valeurs pour ce champ dynamique
                field_values = []
                for result in results:
                    # Récupérer la valeur du champ dynamique, utiliser None si absent
                    dynamic_result = result.get('dynamic_fields', {})
                    field_values.append(dynamic_result.get(dyn_field))
                
                insert_data[dyn_field] = field_values
        
        # Afficher un résumé des données à insérer
        print("\n📊 Résumé des données à insérer :")
        for field, values in insert_data.items():
            if field == 'vector':
                print(f"  - {field}: {len(values)} vecteurs de dimension {len(values[0]) if values and values[0] else 0}")
            else:
                print(f"  - {field}: {len(values)} valeurs")

        # Insertion des données dans la nouvelle partition
        partition.insert(
           insert_data
        )

        # Vérification du nombre d'entités dans la nouvelle partition
        print(f"Nombre d'entités dans {partition_name} : {partition.num_entities}")


if __name__ == "__main__":
    # IDs à filtrer
    ids_to_filter = [
        "ent-0083fd68b176b558d7f14787622dc9fe",
        "ent-00a809937eddc44521da9521269e75c6"
    ]
    duplicate_to_partition(filtered_ids=ids_to_filter)
