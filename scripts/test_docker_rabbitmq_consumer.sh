#!/bin/bash
set -e

# Construire l'image Docker
docker build -t lightrag-rabbitmq-consumer:test -f rabbitMQ/docker/Dockerfile.rabbitmq_consumer .

# Exécuter un conteneur Docker avec les variables d'environnement
docker run --rm \
    -e RABBITMQ_HOST=51.77.200.196 \
    -e RABBITMQ_PORT=30645 \
    -e RABBITMQ_USER=rabbitmq \
    -e RABBITMQ_PASSWORD=mypassword \
    -e RABBITMQ_QUEUE=queue_vinh_test \
    -e OPENAI_API_KEY=$OPENAI_API_KEY \
    lightrag-rabbitmq-consumer:test
