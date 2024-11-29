import os
from dotenv import load_dotenv
import asyncio
from lightrag import LightRAG, QueryParam
from lightrag.llm import openai_complete_if_cache, openai_embedding
from lightrag.utils import EmbeddingFunc
import numpy as np
import requests

# Load environment variables from .env file
load_dotenv()

WORKING_DIR = "./nano-vectorDB"

if not os.path.exists(WORKING_DIR):
    os.mkdir(WORKING_DIR)


# async def llm_model_func(
#     prompt, system_prompt=None, history_messages=[], **kwargs
# ) -> str:
#     return await openai_complete_if_cache(
#         "solar-mini",
#         prompt,
#         system_prompt=system_prompt,
#         history_messages=history_messages,
#         #api_key=os.getenv("UPSTAGE_API_KEY"),
#         api_key="null",
#         base_url="https://11434-01jasnwfwqv3hg9e1faaabm8zf.cloudspaces.litng.ai/",
#         **kwargs,
#     )


# async def embedding_func(texts: list[str]) -> np.ndarray:
#     return await openai_embedding(
#         texts,
#         model="solar-embedding-1-large-query",
#         api_key=os.getenv("UPSTAGE_API_KEY"),
#         base_url="https://bge-m3.endpoints.kepler.ai.cloud.ovh.net/api/text2vec",
#     )






async def llm_model_func(
    prompt, system_prompt=None, history_messages=[], **kwargs
) -> str:
    url = "https://llama-3-1-70b-instruct.endpoints.kepler.ai.cloud.ovh.net/api/openai_compat/v1/chat/completions"
    
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    
    # Add history messages
    messages.extend(history_messages)
    
    # Add current prompt
    messages.append({"role": "user", "content": prompt})
    
    payload = {
        "max_tokens": kwargs.get("max_tokens", 512),
        "messages": messages,
        "model": "Meta-Llama-3_1-70B-Instruct",
        "temperature": kwargs.get("temperature", 0),
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.getenv('OVH_AI_ENDPOINTS_ACCESS_TOKEN')}",
    }
    
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        response_data = response.json()
        return response_data["choices"][0]["message"]["content"]
    else:
        raise Exception(f"Error from OVH API: {response.status_code}")

async def embedding_func(texts: list[str]) -> np.ndarray:
    url = "https://multilingual-e5-base.endpoints.kepler.ai.cloud.ovh.net/api/text2vec"
    headers = {
        "Content-Type": "text/plain",
        "Authorization": f"Bearer {os.getenv('OVH_AI_ENDPOINTS_ACCESS_TOKEN')}",
    }
    
    embeddings = []
    for text in texts:
        response = requests.post(url, data=text, headers=headers)
        if response.status_code == 200:
            embeddings.append(response.json())
        else:
            raise Exception(f"Error from OVH API: {response.status_code}")
    
    return np.array(embeddings)



# function test
async def test_funcs():
    result = await llm_model_func("How are you?")
    print("llm_model_func: ", result)

    result = await embedding_func(["How are you?"])
    print("embedding_func: ", result)


asyncio.run(test_funcs())

# Cette solution ne marche pas dans LightRAG
# Définir le prompt personnalisé pour l'extraction d'entités
custom_entity_extraction_prompt = """-Goal-
Given a text document about restaurants, identify all relevant entities and their relationships.

-Steps-
1. Identify all entities. For each identified entity, extract the following information:
- entity_name: Name of the entity, capitalized
- entity_type: One of the following types: [{entity_types}]
- entity_description: Comprehensive description of the entity's attributes
Format each entity as ("entity"{tuple_delimiter}<entity_name>{tuple_delimiter}<entity_type>{tuple_delimiter}<entity_description>

2. From the entities identified in step 1, identify all pairs of (source_entity, target_entity) that are *clearly related* to each other.
For each pair of related entities, extract the following information:
- source_entity: name of the source entity, as identified in step 1
- target_entity: name of the target entity, as identified in step 1
- relationship_description: explanation of how the entities are related (e.g., "Ce restaurant propose cette cuisine", "Ce restaurant est situé à cet endroit")
- relationship_strength: a numeric score (1-10) indicating the importance of this relationship
- relationship_keywords: key words that describe the nature of the relationship (e.g., "propose", "situé à", "spécialisé en")
Format each relationship as ("relationship"{tuple_delimiter}<source_entity>{tuple_delimiter}<target_entity>{tuple_delimiter}<relationship_description>{tuple_delimiter}<relationship_keywords>{tuple_delimiter}<relationship_strength>)

3. Identify high-level key words that summarize the main aspects of the restaurant.
Format the content-level key words as ("content_keywords"{tuple_delimiter}<high_level_keywords>)"""

# Définir les types d'entités personnalisés
custom_entity_types = ["restaurant", "cuisine", "prix", "ambiance", "localisation", "specialite", "horaire", "contact"]

rag = LightRAG(
    working_dir=WORKING_DIR,
    llm_model_func=llm_model_func,
    embedding_func=EmbeddingFunc(
        embedding_dim=1024, max_token_size=8192, func=embedding_func
    ),
    addon_params={
        "entity_extraction_prompt": custom_entity_extraction_prompt,
        "entity_types": custom_entity_types
    }
)


with open("/Users/vinh/Documents/LightRAG/resto.txt") as f:
    rag.insert(f.read())

# # Perform naive search
# print(
#     rag.query("What are the top themes in this story?", param=QueryParam(mode="naive"))
# )

# # Perform local search
# print(
#     rag.query("What are the top themes in this story?", param=QueryParam(mode="local"))
# )

# # Perform global search
# print(
#     rag.query("What are the top themes in this story?", param=QueryParam(mode="global"))
# )

# # Perform hybrid search
# print(
#     rag.query("Donne moi un restaurant avec du traditionnelle.", param=QueryParam(mode="hybrid"))
# )
