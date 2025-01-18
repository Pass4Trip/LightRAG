# Centralisation des documentations Swagger pour plusieurs pods FastAPI

## Objectif
Centraliser les documentations Swagger de deux pods FastAPI distincts en utilisant une combinaison d'une instance dédiée et d'un reverse proxy.

---

## Approche 1 : Instance dédiée pour centraliser les documentations

### Étape 1 : Créer une instance centrale FastAPI

Créez une nouvelle application FastAPI qui récupère les documentations Swagger des deux pods via leurs URLs exposées.

```python
from fastapi import FastAPI
import httpx

app = FastAPI()

# Récupérer les docs du Pod 1
@app.get("/pod1/docs", include_in_schema=False)
async def pod1_docs():
    async with httpx.AsyncClient() as client:
        response = await client.get("http://pod1-url/docs")
    return response.json()

# Récupérer les docs du Pod 2
@app.get("/pod2/docs", include_in_schema=False)
async def pod2_docs():
    async with httpx.AsyncClient() as client:
        response = await client.get("http://pod2-url/docs")
    return response.json()

# Endpoint pour centraliser les liens
@app.get("/docs", include_in_schema=False)
async def unified_docs():
    return {
        "pod1_docs": "http://your-central-instance.com/pod1/docs",
        "pod2_docs": "http://your-central-instance.com/pod2/docs"
    }
```

### Étape 2 : Déployer cette instance centrale

- Déployez cette application sur votre serveur VPS ou dans un nouveau pod Kubernetes.
- Exposez-la via un port ou une URL publique.

---

## Approche 2 : Utiliser un reverse proxy pour simplifier l'accès

### Étape 1 : Installer et configurer NGINX

Si ce n'est pas encore fait, installez NGINX :
```bash
sudo apt update && sudo apt install nginx
```

### Étape 2 : Configurer NGINX pour router les documentations

Créez ou modifiez un fichier de configuration NGINX pour inclure les routes suivantes :

```nginx
server {
    listen 80;

    # Proxy pour les docs du Pod 1
    location /docs/pod1/ {
        proxy_pass http://pod1-url/docs/;
    }

    # Proxy pour les docs du Pod 2
    location /docs/pod2/ {
        proxy_pass http://pod2-url/docs/;
    }
}
```

- **Remplacez** `pod1-url` et `pod2-url` par les adresses IP ou noms de domaine des pods.
- Rechargez la configuration NGINX :
```bash
sudo nginx -s reload
```

### Étape 3 : Accéder aux documentations centralisées

Après configuration, les documentations des deux pods seront accessibles via :
- `http://your-server.com/docs/pod1/`
- `http://your-server.com/docs/pod2/`

---

## Recommandations supplémentaires

1. **Supervision des performances** :
   - Utilisez un outil comme Prometheus ou Grafana pour surveiller l'utilisation des endpoints exposés.

2. **Sécurisation des endpoints** :
   - Ajoutez une authentification ou des restrictions IP pour protéger vos documentations.

3. **API Gateway** :
   - Pour un système plus robuste et évolutif, envisagez d'intégrer une API Gateway comme Traefik ou Kong pour centraliser et sécuriser les routes.

---

## Conclusion
Cette configuration permet de centraliser et simplifier l'accès aux documentations Swagger des différents pods tout en maintenant leur isolation. Vous pouvez choisir entre l'approche simple avec un reverse proxy ou une instance centrale FastAPI pour une gestion plus personnalisée.