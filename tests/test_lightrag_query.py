import asyncio
import sys
from pathlib import Path

# Ajouter le chemin parent pour importer les modules
sys.path.append(str(Path(__file__).parent.parent))

from api.lightrag_query import init_lightrag, QueryRequest, query_messages

async def main():
    try:
        # Test d'initialisation de LightRAG
        print("🔍 Test d'initialisation de LightRAG")
        rag = init_lightrag()
        print("✅ Initialisation réussie")

        # Test de requête de base
        print("\n🔍 Test de requête de base")
        query_request = QueryRequest(
            question="Trouve-moi un restaurant à Lyon",
            user_id="test_user",
            mode="hybrid",
            limit=5
        )
        
        result = await query_messages(query_request)
        print("✅ Requête réussie")
        print(f"📋 Résultat : {result}")

        # Test avec filtres
        print("\n🔍 Test de requête avec filtres")
        filtered_request = QueryRequest(
            question="Restaurants à Lyon",
            vdb_filter=["activity", "restaurant"],
            limit=3
        )
        
        filtered_result = await query_messages(filtered_request)
        print("✅ Requête avec filtres réussie")
        print(f"📋 Résultat : {filtered_result}")

    except Exception as e:
        print(f"❌ Erreur : {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
