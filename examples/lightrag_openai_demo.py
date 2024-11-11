import os

from lightrag import LightRAG, QueryParam
from lightrag.llm import gpt_4o_mini_complete

WORKING_DIR = "./restaurant_openai_p4t_test"

if not os.path.exists(WORKING_DIR):
    os.mkdir(WORKING_DIR)

rag = LightRAG(
    working_dir=WORKING_DIR,
    llm_model_func=gpt_4o_mini_complete,
    # llm_model_func=gpt_4o_complete
)


with open("/Users/vinh/Documents/LightRAG/resto.txt") as f:
    rag.insert(f.read())


# # Perform hybrid search
# print(
#     rag.query("Donne moi la liste de tous les restaurants situées à Paris", param=QueryParam(mode="naive"))
# )

# # Perform hybrid search
# print(
#     rag.query("Donne moi la liste de tous les restaurants situées à Paris", param=QueryParam(mode="local"))
# )

# # Perform hybrid search
# print(
#     rag.query("Donne moi la liste de tous les restaurants situées à Paris", param=QueryParam(mode="global"))
# )

# # Perform hybrid search
# print(
#     rag.query("Donne moi une liste de restaurants italien calme pour un diner d'affaire. Et donne moi les plats à prendre", param=QueryParam(mode="hybrid"))
# )
