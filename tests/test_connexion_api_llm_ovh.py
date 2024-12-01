import os
import requests
import numpy as np

print("TEST")
api_url = "https://multilingual-e5-base.endpoints.kepler.ai.cloud.ovh.net/api/text2vec"
text = ["Paris is the capital of France",
    "Paris is the capital of France",
    "Berlin is the capital of Germany",
    "This endpoint converts input sentence into a vector embeddings"]
# export OVH_AI_ENDPOINTS_ACCESS_TOKEN=eyJhbGciOiJFZERTQSJ9.eyJwcm9qZWN0IjoiMzE1M2Q2ZTZjMjZmNDM0YzhiNDVjNjFlNDA2NzIwMjIiLCJhdWQiOiIzNzM4NjExNjY0MDQzMDM0IiwiZXhwIjoxNzM1NDE3NjYzLCJqdGkiOiI0NzkzOGZkNS05NDQ3LTQ4ODctOTc0Ny1mNGI4NzRjODAxYzciLCJpc3MiOiJ0cmFpbmluZy5haS5jbG91ZC5vdmgubmV0Iiwic3ViIjoidGE2NTkyMDYtb3ZoIiwib3ZoVG9rZW4iOiI3elR5YmxlQ1JRNkx4WnZzdFF3dDRtUnVtcW1jRDF1aV9LdS1SS3c0VC0zTHE1a08zZjlraUtQSF9OY3NpVGp6Z2dHbXB2aHZnMnJncTM4cnBWUnpvanVEQnZqdld3ejRaRzFtOWtXOGpkNmVhNHpCSWJXVVd2TXlHVWV3amVLWWM5bkFuY0psQmg5b1hrVnFCWlp2eGhaMDY1R21tSUprOWVwWk5Gam8ta1MzSTd3VzlYbGNNYTNfcFdLOHRsUjBHSGJjRkszdE9pZXQzNmxYQTh6MUxKN2x3Wm51NmRDLVh6MlRDWGN4bVFlcGhsVEpWb0t3MEQtOXZGblMxckV5Y0dGcldWQk1UTDhwbHhxdkNSMm1QazMyOUVrOUhpUXUxekViWmNvT3FGR016b3dMOEd5Z1VZLWVSUERzbEtGTnB5bmlnU3hVRVF0QnNndm94cGE4M0tpS1FILU5BS19oSUwtR0t3VFdsaVY4cF9CdFpXNHJMNHpULUxqOHoyOExFS01uX1hpZ1FHY3RLckRkT1R6dnl1cEdXeDNvMVVWVmxkS0swaXQ5U3g5aUc4a18yWFVaalRTNGZrRWZjVDVvNm9GQVNkcVZKWE9vRTJjMWtCQ0NRTEhNRXJRbC1jdm5lWi1jYmE3enRJZ0VXdUdnZ2pIS0lHemZlNmNKTnAxXzE0d2x1cXFTcEROYVZrc2FJSklzc01WV0NOVlBaUy1IM0UxUXRyWnlTWUVrZTB1UE9sOVFUSndyR3BmTXBNNHZSR2czNkVDXzlnSnp6YXBXZENibnYwT1ZPemVwUXhBTG95VUl3M0drUEptc1N5eUQtWENnSndabjNJcEZ3QjhOODZNNFFlVFRITFcxby1oUGhrYmc3b05wSXZwU1JGUFNBUXItcFpIYlg0eHVKNW1Gd1I4bjd2aDJ3cVppY3JoZGpkTkxFZlJQTW1ZdzhhUmxJMnUwQnJybThlYmM1U1RFaXlKVlpuVy1FNTE5dXN4ckdjU0dXVVR4TEIyclFEbkswX08xMlRlVG81elRnaXJFRGVDcnNqRGJtbEItQ01PV3Y2WU5jQWRoaWJ2WmR4WmtRRklqZXpaRmtBdl9vTkFXRUZnQVdEN2lsM19FaVM3NDNzbkZqNUpHYXB2UC1IZDJZVFA1UFVwYmJNT0wtSGc5M2pqeWpTVnkzLXRGYjktbmMySFRsTFdHNG5wR2N1M2Q3N0tpSm80eXdpSnVwSWdiYlhtOTgtbHhnanota0pxZmh4UkZYa1lTSldzQUFwUUVaZUxmV1ZReFFFVHdIZi1sc0c4a2lsZnd4Qms0WktZb0xQLWZ5NDJvdkMycSJ9.fw8fL7oSy00Lo3dhpUwWNdms0t405r-Mbf3vVh2nCaElJwZTMLKsv0KWSQMdSzIh-kTpwWD7CtKs0ZUXYQd1Dw
headers = {
    "Content-Type": "text/plain",
    "Authorization": f"Bearer {os.getenv('OVH_AI_ENDPOINTS_ACCESS_TOKEN')}",
}

# sentence similarity function
def cosine_similarity(vec_source, vec_compare):
        return np.dot(vec_source, vec_compare)

response_data = []
sentence_similarity = {}
for s in range(len(text)):
    # generate embeddings vector
    response = requests.post(api_url, data=text[s], headers=headers)
    if response.status_code == 200:
        response_data.append(response.json())
        if s > 0:
            # calculate sentence similarity
            sentence_similarity[f"Similarity with sentence n°{s}"]="{:.3f}".format(cosine_similarity(response_data[0],
response_data[s]))
    else:
        print("Error:", response.status_code)
print(sentence_similarity)