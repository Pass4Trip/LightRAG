import os

from lightrag import LightRAG, QueryParam
from lightrag.llm import ollama_complete, ollama_embedding
from lightrag.utils import EmbeddingFunc

WORKING_DIR = "./nano-vectorDB"

if not os.path.exists(WORKING_DIR):
    os.mkdir(WORKING_DIR)

rag = LightRAG(
    working_dir=WORKING_DIR,
    llm_model_func=ollama_complete,
    llm_model_name="qwen2.5m",
    embedding_func=EmbeddingFunc(
        embedding_dim=768,
        max_token_size=8192,
        func=lambda texts: ollama_embedding(texts, embed_model="nomic-embed-text"),
    ),
)


with open("./resto.txt") as f:
    rag.insert(f.read())


# Perform hybrid search
print(
    rag.query("Donne moi la liste de tous les restaurants situées à Paris", param=QueryParam(mode="naive"))
)

# Perform hybrid search
print(
    rag.query("Donne moi la liste de tous les restaurants situées à Paris", param=QueryParam(mode="local"))
)

# Perform hybrid search
print(
    rag.query("Donne moi la liste de tous les restaurants situées à Paris", param=QueryParam(mode="global"))
)

# Perform hybrid search
print(
    rag.query("Donne moi la liste de tous les restaurants situées à Paris", param=QueryParam(mode="hybrid"))
)
