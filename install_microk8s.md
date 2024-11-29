# Guide de Déploiement LightRAG avec MicroK8s

Ce guide détaille les étapes pour déployer LightRAG sur MicroK8s, une distribution Kubernetes légère et optimisée.

## 1. Prérequis

### Installation de MicroK8s
```bash
# Ubuntu
sudo snap install microk8s --classic

# Attendre que MicroK8s soit prêt
microk8s status --wait-ready
```

### Configuration des Addons MicroK8s
```bash
# Activer les addons nécessaires
microk8s enable dns
microk8s enable registry
microk8s enable storage
microk8s enable ingress
```

## 2. Préparation du Déploiement

### Structure des Fichiers
```
deployment/
├── Dockerfile
└── k8s/
    ├── lightrag-deployment.yaml
    ├── lightrag-service.yaml
    ├── lightrag-ingress.yaml
    └── lightrag-pvc.yaml
```

### Dockerfile
```dockerfile
FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Command to run the application
CMD ["python", "examples/lightrag_openai_compatible_demo.py"]
```

## 3. Configuration Kubernetes

### PersistentVolumeClaim (k8s/lightrag-pvc.yaml)
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: lightrag-pvc
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: microk8s-hostpath
  resources:
    requests:
      storage: 10Gi
```

### Deployment (k8s/lightrag-deployment.yaml)
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: lightrag
spec:
  replicas: 1
  selector:
    matchLabels:
      app: lightrag
  template:
    metadata:
      labels:
        app: lightrag
    spec:
      containers:
      - name: lightrag
        image: localhost:32000/lightrag:latest
        imagePullPolicy: Always
        resources:
          requests:
            memory: "2Gi"
            cpu: "1"
          limits:
            memory: "4Gi"
            cpu: "2"
        volumeMounts:
        - name: lightrag-data
          mountPath: /app/data
        env:
        - name: OVH_AI_ENDPOINTS_ACCESS_TOKEN
          valueFrom:
            secretKeyRef:
              name: ovh-secrets
              key: api-token
      volumes:
      - name: lightrag-data
        persistentVolumeClaim:
          claimName: lightrag-pvc
```

### Service (k8s/lightrag-service.yaml)
```yaml
apiVersion: v1
kind: Service
metadata:
  name: lightrag
spec:
  selector:
    app: lightrag
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8000
  type: ClusterIP
```

### Ingress (k8s/lightrag-ingress.yaml)
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: lightrag-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  rules:
  - host: lightrag.local
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: lightrag
            port:
              number: 80
```

## 4. Déploiement

### Construction et Push de l'Image
```bash
# Construire l'image Docker
docker build -t localhost:32000/lightrag:latest .

# Pousser l'image dans le registry local MicroK8s
docker push localhost:32000/lightrag:latest
```

### Déploiement sur MicroK8s
```bash
# Créer le namespace
microk8s kubectl create namespace lightrag

# Créer les secrets
microk8s kubectl create secret generic ovh-secrets \
  --from-literal=api-token='votre-token-ovh' \
  -n lightrag

# Appliquer les configurations
microk8s kubectl apply -f k8s/ -n lightrag
```

### Vérification du Déploiement
```bash
# Vérifier les pods
microk8s kubectl get pods -n lightrag

# Vérifier les services
microk8s kubectl get services -n lightrag

# Vérifier l'ingress
microk8s kubectl get ingress -n lightrag

# Consulter les logs
microk8s kubectl logs -f deployment/lightrag -n lightrag
```

## 5. Monitoring

### Activation du Monitoring
```bash
# Activer Prometheus et Grafana
microk8s enable prometheus
microk8s enable grafana

# Accéder aux dashboards Grafana
microk8s kubectl port-forward -n monitoring service/grafana 3000:3000
```

## 6. Maintenance

### Mise à Jour de l'Application
```bash
# Reconstruire l'image avec les modifications
docker build -t localhost:32000/lightrag:latest .
docker push localhost:32000/lightrag:latest

# Redémarrer le déploiement
microk8s kubectl rollout restart deployment lightrag -n lightrag
```

### Sauvegarde des Données
```bash
# Sauvegarder le PVC
microk8s kubectl get pvc lightrag-pvc -n lightrag -o yaml > lightrag-pvc-backup.yaml
```

## 7. Troubleshooting

### Vérification des Logs
```bash
# Logs des pods
microk8s kubectl logs -f deployment/lightrag -n lightrag

# Description des pods
microk8s kubectl describe pod -l app=lightrag -n lightrag
```

### Accès au Shell du Container
```bash
# Ouvrir un shell dans le pod
microk8s kubectl exec -it deployment/lightrag -n lightrag -- /bin/bash
```

### Vérification des Ressources
```bash
# Utilisation des ressources
microk8s kubectl top pods -n lightrag
```
