from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Importer les routers depuis vos fichiers d'API
from api.lightrag_insert import router as insert_router
from api.lightrag_query import router as query_router

# Créer l'application FastAPI principale
app = FastAPI(
    title="LightRAG API",
    description="API pour l'insertion et la recherche de données dans LightRAG",
    version="1.0.0"
)

# Ajouter les middlewares CORS pour permettre les requêtes cross-origin si nécessaire
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Autorise toutes les origines, ajustez selon vos besoins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclure les routers
app.include_router(insert_router, prefix="/insert", tags=["Insertion"])
app.include_router(query_router, prefix="/query", tags=["Recherche"])

# Point d'entrée optionnel
@app.get("/", tags=["Racine"])
async def root():
    return {"message": "Bienvenue sur l'API LightRAG"}